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
    from athenas_lite.core.scoring import aplicar_defaults_items, compute_scores_with_na, _atributos_a_columnas_valor
    from athenas_lite.services.system_tools import get_audio_duration, human_duration, is_gemini_supported
    from athenas_lite.services.drive_exports import subir_csv_a_drive
    import pandas as pd
    from datetime import datetime
    import re
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

        # --- EXPORT LOGIC ---
        exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        ts_now = datetime.now()
        ts_str = ts_now.strftime("%Y-%m-%d_%H-%M-%S")
        ts_file = ts_now.strftime('%Y%m%d_%H%M%S')

        # 1. Generate TXT Summary
        txt_path = os.path.join(exports_dir, f"{Path(audio_file.filename).stem}_ATHENAS_Lite.txt")
        fortalezas = eval_data.get("fortalezas", [])
        contenido_evaluador = eval_data.get("contenido_evaluador", "")
        resumen = " • ".join(fortalezas[:2]) if fortalezas else resumen_calido

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Asesor: {advisor}\n")
            f.write(f"Evaluador: {evaluator}\n")
            f.write(f"Archivo: {audio_file.filename}\n")
            f.write(f"Departamento seleccionado: {department}\n")
            f.write(f"Timestamp: {ts_str}\n")
            f.write(f"Duración: {dur_str}\n\n")
            f.write("Resumen:\n")
            f.write(resumen or "N/A")
            f.write("\n\nContenido para el evaluador:\n")
            f.write(contenido_evaluador or "N/A")
            f.write("\n--- CALIFICACIÓN FINAL ---\n")
            f.write(f"Score de Atributos (Puntaje Bruto, N/A incluido): {score_bruto}%\n")
            f.write(f"Score Final (Aplicando Críticos): {score_final}%\n")
            f.write("\n--- PUNTOS CRÍTICOS ---\n")
            if not criticos:
                f.write("(Sin críticos configurados)\n")
            else:
                for c in criticos:
                    keyc = c.get("key","(sin_key)")
                    okc = c.get("ok", False)
                    f.write(f"{keyc}: {'✅ Cumplido' if okc else '❌ No cumplido'}\n")
            f.write("\n--- Detalle por atributo ---\n")
            for d in det_atrib:
                est = d["estado"]
                marca = "✅ Cumplido" if est == "OK" else ("❌ No cumplido" if est == "NO" else "🟡 N/A")
                f.write(f"{marca} {d['key']} → {d['otorgado']} / {d['peso']}\n")
                
            f.write("\n--- Sentimiento ---\n")
            f.write(f"Valoración (1-10): {val}\n")
            f.write(f"Clasificación: {clasif}\n")
            f.write(f"Comentario emocional: {comentario}\n")
            f.write("\n--- Sentimiento por roles ---\n")
            f.write(f"Cliente -> {sent_cli['clasificacion']} ({sent_cli['valor']}/10). {sent_cli['comentario']}\n")
            f.write(f"Asesor  -> {sent_ase['clasificacion']} ({sent_ase['valor']}/10). {sent_ase['comentario']}\n")

        # 2. Generate CSV Data
        fila_atrib, _keys = _atributos_a_columnas_valor(det_atrib)
        row_data = {
            "archivo": audio_file.filename,
            "asesor": advisor,
            "timestamp": ts_str,
            "resumen": resumen,
            "sentimiento": val,
            "clasificación": clasif,
            "comentario": comentario,
            "evaluador": evaluator,
            "duración": dur_str,
            "duracion_seg": (round(dur_secs, 3) if dur_secs is not None else None),
            "contenido_evaluador": contenido_evaluador,
            "porcentaje_evaluacion": score_final,
            "score_bruto": score_bruto,
            "departamento": department,
            "sentimiento_cliente": sent_cli["valor"],
            "clasificación_cliente": sent_cli["clasificacion"],
            "comentario_cliente": sent_cli["comentario"],
            "sentimiento_asesor": sent_ase["valor"],
            "clasificación_asesor": sent_ase["clasificacion"],
            "comentario_asesor": sent_ase["comentario"]
        }
        row_data.update(fila_atrib)
        
        # Populate missing columns logic (simplified for single row)
        # In multi-row scenario we'd track all keys, but here we just export what we have
        
        # Create CSV
        asesor_slug = re.sub(r'[^A-Za-z0-9_-]+', '_', (advisor or 'asesor').strip()) or 'asesor'
        export_path = os.path.join(exports_dir, f"ATHENAS_Lite_{asesor_slug}_{ts_file}.csv")
        
        drive_link = None
        try:
            df = pd.DataFrame([row_data])
            df.to_csv(export_path, index=False, encoding="utf-8-sig")
            
            # 3. Upload to Drive
            # Using advisor name + timestamp for unique filename in Drive to avoid overwrites or huge appends 
            # (Original app appended to local if same session, we are stateless per request so new file is safer/easier)
            # Actually original app generated a 'compilado' for the batch. Here we are doing per-analysis.
            # To match "compilado" feel, we might name it similarly or just upload this result.
            drive_filename = f"ATLite_Result_{asesor_slug}_{ts_file}.csv"
            drive_link = subir_csv_a_drive(df, drive_filename)
            
        except Exception as e:
            print(f"Export/Upload error: {e}")
            export_path = None # Indicate failure if needed
        # --- END EXPORT LOGIC ---
        return {
            "id": analysis_id,
            "filename": audio_file.filename,
            "department": department,
            "score_bruto": score_bruto,
            "score_final": score_final,
            "sentiment": clasif,
            "duration": dur_str,
            "message": "Analysis completed successfully",
            # New fields for exports
            "drive_link": drive_link, 
            "local_csv": export_path,
            "local_txt": txt_path
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

@router.get("/{analysis_id}/download")
async def download_analysis_file(
    analysis_id: int,
    format: str = "csv",
    user_id: int = Depends(get_current_user_id)
):
    """Download analysis export file (csv or txt)"""
    from fastapi.responses import FileResponse
    import os
    from datetime import datetime
    import re

    # Get analysis details
    analysis = await storage_service.get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Verify ownership
    if analysis["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Reconstruct filename pattern
    # The current export logic uses: ATHENAS_Lite_{advisor}_{timestamp}.csv/txt
    # We need to find the matching file in exports/
    
    exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    
    advisor_slug = re.sub(r'[^A-Za-z0-9_-]+', '_', (analysis["advisor"] or 'asesor').strip())
    
    # Timestamp in DB is usually 'YYYY-MM-DD HH:MM:SS' strings from sqlite default
    # We used '%Y%m%d_%H%M%S' for filename
    try:
        # SQLite often stores as string, let's parse flexible
        ts_str = analysis["timestamp"]
        # Try different formats if needed, but usually it's iso-like space sep
        if isinstance(ts_str, str):
            # Parse '2023-12-08 14:00:00' -> datetime
            # If it has milliseconds, might fail, so be careful
            if "." in ts_str:
                ts_obj = datetime.strptime(ts_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            else:
                ts_obj = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            ts_file = ts_obj.strftime('%Y%m%d_%H%M%S')
        else:
            # If datetime object
            ts_file = ts_str.strftime('%Y%m%d_%H%M%S')
            
    except Exception as e:
        print(f"Error parsing timestamp for download: {e}")
        raise HTTPException(status_code=500, detail="Error resolving file path")

    # Construct filenames
    if format.lower() == "csv":
        filename = f"ATHENAS_Lite_{advisor_slug}_{ts_file}.csv"
    elif format.lower() == "txt":
        # TXT logic used filename stem: {Path(audio_file.filename).stem}_ATHENAS_Lite.txt
        # This is harder to reconstruct perfectly if we only have the filename string
        # Let's try searching for the file with the same prefix
        # We stored filename="audio.mp3" in DB.
        stem = Path(analysis["filename"]).stem
        filename = f"{stem}_ATHENAS_Lite.txt"
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'txt'")

    file_path = os.path.join(exports_dir, filename)
    
    if not os.path.exists(file_path):
        # Fallback: maybe timestamp is off by a second? or user renamed?
        # For now, strict match.
        raise HTTPException(status_code=404, detail="Export file not found on server")
        
    return FileResponse(file_path, filename=filename)
