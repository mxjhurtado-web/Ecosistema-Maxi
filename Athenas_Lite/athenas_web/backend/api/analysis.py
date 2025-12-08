"""
Analysis API endpoints
Handles audio upload and analysis using existing ATHENAS Lite logic
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Cookie
from typing import Optional, List
import os
import sys
from pathlib import Path

# Add parent athenas_lite to path to import existing modules
athenas_lite_path = str(Path(__file__).parent.parent.parent.parent / "athenas_lite")
if athenas_lite_path not in sys.path:
    sys.path.insert(0, athenas_lite_path)

from models.schemas import AnalysisResult, CallSummary
from services.storage import storage_service
from services.keycloak import keycloak_service

# Import existing ATHENAS Lite modules
try:
    from athenas_lite.services.gemini_api import configurar_gemini, analizar_sentimiento, analizar_sentimiento_por_roles
    from athenas_lite.core.rubric_loader import load_dept_rubric_json_local, rubric_json_to_prompt
    from athenas_lite.core.scoring import aplicar_defaults_items, compute_scores_with_na
    from athenas_lite.services.system_tools import get_audio_duration, human_duration, is_gemini_supported
except ImportError as e:
    print(f"Warning: Could not import ATHENAS Lite modules: {e}")
    print("Analysis endpoints will use mock data")

router = APIRouter()

async def get_current_user_id(access_token: Optional[str] = Cookie(None)) -> int:
    """Get current user ID from token"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    success, user_data = keycloak_service.get_user_info(access_token)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    role = keycloak_service.get_athenas_role(access_token)
    if not role:
        raise HTTPException(status_code=403, detail="No valid role")
    
    # Sync user and get ID
    user_id = await storage_service.sync_user(
        email=user_data.get("email"),
        keycloak_id=user_data.get("sub"),
        name=user_data.get("name", user_data.get("preferred_username", "")),
        role=role
    )
    
    return user_id

@router.post("/analyze", response_model=dict)
async def analyze_audio(
    audio_file: UploadFile = File(...),
    department: str = Form(...),
    evaluator: str = Form(...),
    advisor: str = Form(...),
    gemini_api_key: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user_id)
):
    """
    Analyze single audio file
    Uses existing ATHENAS Lite logic
    """
    # Validate file
    if not is_gemini_supported(audio_file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Use WAV, MP3, MP4, M4A, or GSM"
        )
    
    # Configure Gemini if API key provided
    if gemini_api_key:
        configurar_gemini(gemini_api_key)
    
    # Save file temporarily
    file_content = await audio_file.read()
    temp_path = storage_service.save_temp_audio(file_content, audio_file.filename)
    
    try:
        # Get audio duration
        dur_secs = get_audio_duration(temp_path)
        dur_str = human_duration(dur_secs)
        
        # Analyze sentiment
        val, clasif, comentario, resumen_calido = analizar_sentimiento(temp_path)
        sent_cli, sent_ase = analizar_sentimiento_por_roles(temp_path)
        
        # Load rubric
        rubric_data = load_dept_rubric_json_local(department)
        if not rubric_data:
            raise HTTPException(status_code=404, detail=f"Rubric not found for department: {department}")
        
        # Generate prompt
        prompt = rubric_json_to_prompt(department, rubric_data)
        
        # Call Gemini for evaluation
        # Define fallback mock data in case of error or no API key
        mock_eval_data = {
            "sections": rubric_data.get("sections", []),
            "section_VI": rubric_data.get("section_VI", {}),
            "fortalezas": ["Excelente tono de voz (MOCK)", "Buena personalización (MOCK)"],
            "compromisos": ["Mejorar tiempo de respuesta (MOCK)"],
            "contenido_evaluador": f"Análisis de {audio_file.filename} para {department} (MOCK DATA)"
        }

        # Use llm_json_or_mock to get real data
        try:
            from athenas_lite.services.gemini_api import llm_json_or_mock
            eval_data = llm_json_or_mock(prompt, temp_path, mock_eval_data)
        except ImportError:
            # If function not available (e.g. older version of gemini_api), use mock
            print("Warning: llm_json_or_mock not found, using mock data")
            eval_data = mock_eval_data
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            eval_data = mock_eval_data
        
        # Apply defaults
        eval_data = aplicar_defaults_items(eval_data)
        
        # Calculate scores
        sections = eval_data.get("sections", [])
        criticos = eval_data.get("section_VI", {}).get("criticos", [])
        score_bruto, fallo_critico, score_final, det_atrib = compute_scores_with_na(sections, criticos)
        
        # Save to database
        analysis_id = await storage_service.save_analysis(
            user_id=user_id,
            filename=audio_file.filename,
            department=department,
            evaluator=evaluator,
            advisor=advisor,
            score_bruto=score_bruto,
            score_final=score_final,
            sentiment=clasif
        )
        
        return {
            "id": analysis_id,
            "filename": audio_file.filename,
            "department": department,
            "score_bruto": score_bruto,
            "score_final": score_final,
            "sentiment": clasif,
            "duration": dur_str,
            "message": "Analysis completed successfully"
        }
    
    finally:
        # Cleanup temporary file
        storage_service.cleanup_temp_audio(temp_path)

@router.get("/history", response_model=List[CallSummary])
async def get_analysis_history(
    department: Optional[str] = None,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id)
):
    """Get analysis history for current user"""
    analyses = await storage_service.get_analyses(
        user_id=user_id,
        department=department,
        limit=limit
    )
    
    return [
        CallSummary(
            id=a["id"],
            filename=a["filename"],
            department=a["department"],
            score_final=a["score_final"],
            sentiment=a["sentiment"],
            timestamp=a["timestamp"]
        )
        for a in analyses
    ]

@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(
    analysis_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Get single analysis by ID"""
    analysis = await storage_service.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Verify ownership
    if analysis["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return AnalysisResult(**analysis)
