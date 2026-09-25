#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Parser Service for TEMIS
Extracts structured text, indexed paragraph blocks, raw tables, and ZIP Media Studio packages
from DOCX, PDF, VTT, SRT, JSON and ZIP packages with exact character offsets and timestamps.
"""

from typing import Optional, List, Dict, Any, Tuple
import io
import os
import json
import base64
import zipfile
import hashlib
from backend.models.narrative_source_model import ParagraphBlock


class DocumentParser:
    """Parse documents and extract indexed text blocks and screenshots for citation tracking"""
    
    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """Compute SHA256 hash of document bytes"""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def extract_text(file_content: bytes, file_extension: str) -> Optional[str]:
        """Extract continuous plain text from document (backward compatible)"""
        blocks = DocumentParser.extract_blocks(file_content, file_extension)
        if not blocks:
            return None
        return "\n\n".join([f"[{b.index}] {b.text}" for b in blocks])

    @staticmethod
    def extract_blocks(file_content: bytes, file_extension: str, filename: str = "document") -> List[ParagraphBlock]:
        """
        Extract list of sequentially indexed paragraph, table, or audio/video transcript blocks
        """
        ext = file_extension.lower().strip()
        try:
            if ext == '.zip':
                zip_data = DocumentParser.parse_zip_package(file_content, filename)
                return zip_data.get("blocks", [])
            elif ext == '.docx':
                return DocumentParser._extract_blocks_from_docx(file_content)
            elif ext == '.pdf':
                return DocumentParser._extract_blocks_from_pdf(file_content)
            elif ext in ['.vtt', '.srt']:
                from backend.services.audio_transcriber import AudioTranscriber
                text_content = file_content.decode("utf-8", errors="replace")
                return AudioTranscriber.parse_subtitle_file(text_content, filename)
            elif ext == '.json' or ext == '.temis.json':
                return DocumentParser._extract_blocks_from_json(file_content)
            elif ext in ['.txt', '.md', '.csv']:
                return DocumentParser._extract_blocks_from_plain_text(file_content)
            else:
                return DocumentParser._extract_blocks_from_plain_text(file_content)
        except Exception as e:
            print(f"[DocumentParser] Error extracting blocks: {e}")
            return []

    @classmethod
    def parse_zip_package(cls, zip_bytes: bytes, filename: str = "package.zip") -> Dict[str, Any]:
        """
        Decompress and parse a TEMIS Media Studio ZIP package in memory.
        Extracts:
        - keyframes gallery (Base64 data URIs)
        - transcript blocks with timestamps
        - project charter, SIPOC rows and diagram if present
        """
        blocks: List[ParagraphBlock] = []
        keyframes: List[Dict[str, Any]] = []
        charter: Dict[str, Any] = {}
        sipoc_rows: List[Dict[str, Any]] = []
        diagram: Dict[str, Any] = {}
        process_steps: List[Dict[str, Any]] = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                names = z.namelist()

                # 1. Extract Screenshots from capturas/ or image files
                img_names = sorted([
                    n for n in names 
                    if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
                    and not n.startswith('__MACOSX')
                ])

                for idx, img_name in enumerate(img_names, start=1):
                    img_bytes = z.read(img_name)
                    mime = "image/png" if img_name.lower().endswith('.png') else "image/jpeg"
                    b64_str = base64.b64encode(img_bytes).decode('utf-8')
                    data_uri = f"data:{mime};base64,{b64_str}"
                    base_filename = os.path.basename(img_name)

                    keyframes.append({
                        "index": idx,
                        "filename": base_filename,
                        "path": img_name,
                        "data_uri": data_uri,
                        "timestamp_formatted": f"Captura #{idx}",
                        "file_size_bytes": len(img_bytes)
                    })

                # 2. Extract JSON project packages
                json_names = [
                    n for n in names 
                    if n.lower().endswith(('.json', '.temis.json')) 
                    and not n.startswith('__MACOSX')
                ]

                for j_name in json_names:
                    try:
                        raw_json = z.read(j_name).decode('utf-8', errors='replace')
                        parsed = json.loads(raw_json)
                        if "project_charter" in parsed or "charter" in parsed:
                            charter = parsed.get("project_charter") or parsed.get("charter", {})
                        if "sipoc" in parsed or "sipoc_rows" in parsed:
                            sipoc_rows = parsed.get("sipoc") or parsed.get("sipoc_rows", [])
                        if "diagram" in parsed:
                            diagram = parsed.get("diagram", {})
                        if "process_steps" in parsed:
                            process_steps = parsed.get("process_steps", [])

                        # If JSON contains transcript_segments, convert to blocks
                        if "transcript_segments" in parsed and parsed["transcript_segments"]:
                            for s_idx, s in enumerate(parsed["transcript_segments"], start=1):
                                blocks.append(ParagraphBlock(
                                    index=s_idx,
                                    source_type="audio_transcript",
                                    timestamp_start=s.get("timestamp_start", "00:00:00"),
                                    timestamp_end=s.get("timestamp_end", ""),
                                    speaker=s.get("speaker", "Participante"),
                                    text=s.get("text", "")
                                ))
                    except Exception as j_err:
                        print(f"[DocumentParser] Error parsing JSON in ZIP {j_name}: {j_err}")

                # 3. If no blocks yet from JSON, look for Word docx in ZIP
                if not blocks:
                    docx_names = [
                        n for n in names 
                        if n.lower().endswith('.docx') and not n.startswith('~$') and not n.startswith('__MACOSX')
                    ]
                    for d_name in docx_names:
                        try:
                            docx_bytes = z.read(d_name)
                            docx_blocks = cls._extract_blocks_from_docx(docx_bytes)
                            if docx_blocks:
                                blocks = docx_blocks
                                break
                        except Exception as d_err:
                            print(f"[DocumentParser] Error parsing DOCX in ZIP {d_name}: {d_err}")

                # 4. If still no blocks, look for VTT or SRT in ZIP
                if not blocks:
                    vtt_names = [n for n in names if n.lower().endswith(('.vtt', '.srt'))]
                    for v_name in vtt_names:
                        try:
                            from backend.services.audio_transcriber import AudioTranscriber
                            v_text = z.read(v_name).decode('utf-8', errors='replace')
                            v_blocks = AudioTranscriber.parse_subtitle_file(v_text, v_name)
                            if v_blocks:
                                blocks = v_blocks
                                break
                        except Exception as v_err:
                            print(f"[DocumentParser] Error parsing VTT in ZIP {v_name}: {v_err}")

                # 5. If still no blocks, parse any plain text file in ZIP
                if not blocks:
                    txt_names = [n for n in names if n.lower().endswith(('.txt', '.md'))]
                    for t_name in txt_names:
                        try:
                            t_bytes = z.read(t_name)
                            t_blocks = cls._extract_blocks_from_plain_text(t_bytes)
                            if t_blocks:
                                blocks = t_blocks
                                break
                        except Exception as t_err:
                            print(f"[DocumentParser] Error parsing TXT in ZIP {t_name}: {t_err}")

        except Exception as e:
            print(f"[DocumentParser] Error unzipping package {filename}: {e}")

        # Link keyframe timestamps with blocks if available
        if keyframes and blocks:
            for k in keyframes:
                # Find matching block by index or timestamp
                k_idx = k.get("index", 1)
                matching_block = next((b for b in blocks if b.index == k_idx), None)
                if matching_block and matching_block.timestamp_start:
                    k["timestamp_formatted"] = f"⏱️ {matching_block.timestamp_start}"

        return {
            "is_zip": True,
            "filename": filename,
            "blocks": blocks,
            "keyframes": keyframes,
            "total_screenshots": len(keyframes),
            "charter": charter,
            "sipoc_rows": sipoc_rows,
            "diagram": diagram,
            "process_steps": process_steps
        }

    @staticmethod
    def _extract_blocks_from_json(content: bytes) -> List[ParagraphBlock]:
        """Extract indexed blocks from JSON package or transcript export"""
        try:
            data = json.loads(content.decode('utf-8', errors='replace'))
            blocks = []
            if "transcript_segments" in data:
                for idx, s in enumerate(data["transcript_segments"], start=1):
                    blocks.append(ParagraphBlock(
                        index=idx,
                        source_type="audio_transcript",
                        timestamp_start=s.get("timestamp_start", "00:00:00"),
                        timestamp_end=s.get("timestamp_end", ""),
                        speaker=s.get("speaker", "Participante"),
                        text=s.get("text", "")
                    ))
                return blocks
            elif "process_steps" in data:
                for idx, s in enumerate(data["process_steps"], start=1):
                    blocks.append(ParagraphBlock(
                        index=idx,
                        source_type="paragraph",
                        timestamp_start=s.get("timestamp", "00:00:00"),
                        speaker=s.get("actor", "Operador"),
                        text=f"{s.get('title', '')}: {s.get('description', '')}"
                    ))
                return blocks
        except Exception as e:
            print(f"[DocumentParser] JSON parse error: {e}")
        return []

    @staticmethod
    def _extract_blocks_from_docx(content: bytes) -> List[ParagraphBlock]:
        """Extract indexed blocks from DOCX paragraphs and tables"""
        from docx import Document
        doc = Document(io.BytesIO(content))
        blocks: List[ParagraphBlock] = []
        block_counter = 1

        # 1. Iterate through paragraphs
        for p_idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if text:
                # Detect heading level if applicable
                heading_level = None
                if p.style and p.style.name.startswith("Heading"):
                    try:
                        heading_level = int(p.style.name.replace("Heading", "").strip())
                    except ValueError:
                        heading_level = 1
                
                blocks.append(ParagraphBlock(
                    index=block_counter,
                    source_type="paragraph",
                    heading_level=heading_level,
                    text=text,
                    page_number=None,
                    table_index=None,
                    row_index=None
                ))
                block_counter += 1

        # 2. Iterate through tables
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                seen_cells: List[str] = []
                for cell in row.cells:
                    ctext = cell.text.strip().replace("\r", " ").replace("\n", " // ")
                    if ctext and (not seen_cells or seen_cells[-1] != ctext):
                        seen_cells.append(ctext)
                
                if seen_cells:
                    row_text = " | ".join(seen_cells)
                    blocks.append(ParagraphBlock(
                        index=block_counter,
                        source_type="table_row",
                        heading_level=None,
                        text=row_text,
                        page_number=None,
                        table_index=t_idx + 1,
                        row_index=r_idx + 1
                    ))
                    block_counter += 1

        return blocks

    @staticmethod
    def _extract_blocks_from_pdf(content: bytes) -> List[ParagraphBlock]:
        """Extract indexed blocks from PDF document with page numbers"""
        import PyPDF2
        pdf_file = io.BytesIO(content)
        reader = PyPDF2.PdfReader(pdf_file)
        blocks: List[ParagraphBlock] = []
        block_counter = 1

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not raw_paragraphs and text.strip():
                raw_paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 30]

            for p_text in raw_paragraphs:
                if len(p_text) > 5:
                    blocks.append(ParagraphBlock(
                        index=block_counter,
                        source_type="paragraph",
                        heading_level=None,
                        text=p_text,
                        page_number=page_num,
                        table_index=None,
                        row_index=None
                    ))
                    block_counter += 1

        return blocks

    @staticmethod
    def _extract_blocks_from_plain_text(content: bytes) -> List[ParagraphBlock]:
        """Extract indexed blocks from plain text or markdown"""
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1', errors='ignore')
            
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        blocks: List[ParagraphBlock] = []
        
        for idx, p in enumerate(paragraphs, start=1):
            blocks.append(ParagraphBlock(
                index=idx,
                source_type="paragraph",
                heading_level=None,
                text=p,
                page_number=None,
                table_index=None,
                row_index=None
            ))
            
        return blocks
