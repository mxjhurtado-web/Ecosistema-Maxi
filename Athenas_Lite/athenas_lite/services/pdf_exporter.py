
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger("athenas_lite")


def generate_pdf_report(txt_path, output_path, maxi_logo_path=None, athenas_logo_path=None, evaluator_comments=""):
    """
    Genera un PDF profesional a partir del contenido de un archivo TXT de análisis.
    
    Args:
        txt_path: Ruta al archivo TXT con el análisis
        output_path: Ruta donde se guardará el PDF
        maxi_logo_path: Ruta al logo de Maxi Send (opcional)
        athenas_logo_path: Ruta al logo de ATHENAS (opcional)
        evaluator_comments: Comentarios adicionales del evaluador (opcional)
    
    Returns:
        bool: True si se generó exitosamente, False en caso contrario
    """
    try:
        # Leer contenido del TXT
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.5*inch,  # Reducido para header
            bottomMargin=0.75*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para título principal (centrado)
        main_title_style = ParagraphStyle(
            'MainTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#4A5FC1'),  # Azul Maxi
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4A5FC1'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Estilo para datos importantes
        highlight_style = ParagraphStyle(
            'Highlight',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2E7D32'),  # Verde
            fontName='Helvetica-Bold'
        )
        
        # Construir contenido del PDF
        story = []
        
        # ===== HEADER CON LOGOS DUALES =====
        header_data = []
        header_widths = []
        
        # Logo ATHENAS (izquierda)
        athenas_cell = ""
        if athenas_logo_path and os.path.exists(athenas_logo_path):
            try:
                athenas_img = Image(athenas_logo_path, width=1.0*inch, height=0.4*inch)  # Reducido para mejor proporción
                athenas_cell = athenas_img
            except Exception as e:
                logger.warning(f"No se pudo cargar logo ATHENAS: {e}")
                athenas_cell = ""
        
        # Título centrado
        title_cell = Paragraph("Reporte de Análisis de Calidad", main_title_style)
        
        # Logo Maxi Send (derecha)
        maxi_cell = ""
        if maxi_logo_path and os.path.exists(maxi_logo_path):
            try:
                maxi_img = Image(maxi_logo_path, width=1.25*inch, height=0.5*inch)  # 50% del tamaño original
                maxi_cell = maxi_img
            except Exception as e:
                logger.warning(f"No se pudo cargar logo Maxi: {e}")
                maxi_cell = ""
        
        # Crear tabla de header
        header_data = [[athenas_cell, title_cell, maxi_cell]]
        header_table = Table(header_data, colWidths=[1.5*inch, 4*inch, 1.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # ATHENAS izquierda
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Título centro
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),   # Maxi derecha
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Línea separadora
        line_data = [['', '']]
        line_table = Table(line_data, colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#4A5FC1')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Parsear contenido del TXT
        lines = content.split('\n')
        
        # Extraer información clave
        asesor = ""
        evaluador = ""
        archivo = ""
        departamento = ""
        timestamp = ""
        duracion = ""
        score_bruto = ""
        score_final = ""
        
        for line in lines:
            if line.startswith("Asesor:"):
                asesor = line.replace("Asesor:", "").strip()
            elif line.startswith("Evaluador:"):
                evaluador = line.replace("Evaluador:", "").strip()
            elif line.startswith("Archivo:"):
                archivo = line.replace("Archivo:", "").strip()
            elif line.startswith("Departamento seleccionado:"):
                departamento = line.replace("Departamento seleccionado:", "").strip()
            elif line.startswith("Timestamp:"):
                timestamp = line.replace("Timestamp:", "").strip()
            elif line.startswith("Duración:"):
                duracion = line.replace("Duración:", "").strip()
            elif "Score de Atributos" in line and "Puntaje Bruto" in line:
                score_bruto = line.split(":")[-1].strip()
            elif "Score Final" in line and "Aplicando Críticos" in line:
                score_final = line.split(":")[-1].strip()
        
        # Tabla de información general
        info_data = [
            ['Asesor:', asesor],
            ['Evaluador:', evaluador],
            ['Archivo:', archivo],
            ['Departamento:', departamento],
            ['Fecha:', timestamp],
            ['Duración:', duracion]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1565C0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Calificación Final (destacada)
        score_data = [
            ['Score de Atributos (Bruto):', score_bruto],
            ['Score Final (con Críticos):', score_final]
        ]
        
        score_table = Table(score_data, colWidths=[3*inch, 3.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#C8E6C9')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1B5E20')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2E7D32')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4CAF50')),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Procesar el resto del contenido por secciones
        in_section = False
        current_section = ""
        section_content = []
        
        for line in lines:
            # Detectar secciones
            if line.startswith("---"):
                if current_section and section_content:
                    # Agregar sección anterior
                    story.append(Paragraph(current_section, subtitle_style))
                    for content_line in section_content:
                        if content_line.strip():
                            # Aplicar estilos según contenido
                            if "✅" in content_line:
                                para = Paragraph(content_line, highlight_style)
                            elif "❌" in content_line:
                                error_style = ParagraphStyle('Error', parent=normal_style, 
                                                            textColor=colors.HexColor('#C62828'))
                                para = Paragraph(content_line, error_style)
                            elif "🟡" in content_line:
                                warning_style = ParagraphStyle('Warning', parent=normal_style,
                                                              textColor=colors.HexColor('#F57C00'))
                                para = Paragraph(content_line, warning_style)
                            else:
                                para = Paragraph(content_line, normal_style)
                            story.append(para)
                    story.append(Spacer(1, 0.15*inch))
                    section_content = []
                
                # Nueva sección
                current_section = line.replace("---", "").strip()
                in_section = True
            elif in_section and line.strip():
                # Agregar contenido a la sección actual
                if not any(skip in line for skip in ["Asesor:", "Evaluador:", "Archivo:", 
                                                      "Departamento", "Timestamp:", "Duración:",
                                                      "Score de Atributos", "Score Final"]):
                    section_content.append(line)
        
        # Agregar última sección
        if current_section and section_content:
            story.append(Paragraph(current_section, subtitle_style))
            for content_line in section_content:
                if content_line.strip():
                    para = Paragraph(content_line, normal_style)
                    story.append(para)
        
        # ===== COMENTARIOS DEL EVALUADOR =====
        if evaluator_comments and evaluator_comments.strip():
            story.append(Spacer(1, 0.4*inch))
            story.append(Paragraph("Comentarios Adicionales del Evaluador", subtitle_style))
            
            # Crear caja para comentarios
            comments_style = ParagraphStyle('Comments', parent=normal_style, 
                                           fontSize=10, leftIndent=10, rightIndent=10)
            story.append(Paragraph(evaluator_comments, comments_style))
            story.append(Spacer(1, 0.3*inch))
        
        # ===== SECCIÓN DE FIRMAS =====
        story.append(Spacer(1, 0.5*inch))
        
        # Línea separadora antes de firmas
        story.append(line_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tabla de firmas
        signature_data = [
            ['', ''],  # Espacio para firmas
            ['_' * 40, '_' * 40],  # Líneas de firma
            [f'Asesor: {asesor}', f'Evaluador: {evaluador}']
        ]
        
        signature_table = Table(signature_data, colWidths=[3.25*inch, 3.25*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, 0), 20),  # Espacio para firma manuscrita
            ('BOTTOMPADDING', (0, 1), (-1, 1), 2),
            ('TOPPADDING', (0, 2), (-1, 2), 5),
        ]))
        
        story.append(signature_table)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle('Footer', parent=normal_style, 
                                     fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        story.append(Paragraph(f"Generado por ATHENAS Lite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              footer_style))
        
        # Construir PDF
        doc.build(story)
        logger.info(f"PDF generado exitosamente: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return False
