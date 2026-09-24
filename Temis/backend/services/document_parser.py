#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Parser Service for TEMIS
Extracts structured text, indexed paragraph blocks, and raw tables 
from DOCX and PDF documents with exact character offsets and hash tracking.
"""

from typing import Optional, List, Dict, Any, Tuple
import io
import hashlib
from backend.models.narrative_source_model import ParagraphBlock


class DocumentParser:
    """Parse documents and extract indexed text blocks for citation tracking"""
    
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
            if ext == '.docx':
                return DocumentParser._extract_blocks_from_docx(file_content)
            elif ext == '.pdf':
                return DocumentParser._extract_blocks_from_pdf(file_content)
            elif ext in ['.vtt', '.srt']:
                from backend.services.audio_transcriber import AudioTranscriber
                text_content = file_content.decode("utf-8", errors="replace")
                return AudioTranscriber.parse_subtitle_file(text_content, filename)
            elif ext in ['.mp3', '.mp4', '.m4a', '.wav', '.ogg', '.flac', '.webm', '.mov', '.avi', '.opus', '.wma', '.mkv']:
                from backend.services.media_processor import MediaProcessor
                from backend.services.audio_transcriber import AudioTranscriber
                meta = MediaProcessor.extract_metadata(file_content, filename)
                transcriber = AudioTranscriber()
                return transcriber.transcribe_media(file_content, filename, meta.get("duration_seconds"))
            elif ext in ['.txt', '.md', '.csv']:
                return DocumentParser._extract_blocks_from_plain_text(file_content)
            else:
                return DocumentParser._extract_blocks_from_plain_text(file_content)
        except Exception as e:
            print(f"[DocumentParser] Error extracting blocks: {e}")
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
                # Clean and deduplicate merged cell texts in same row
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
            # Split page text into non-empty logical paragraphs
            raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not raw_paragraphs and text.strip():
                # Split by single newlines if no double newlines
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
