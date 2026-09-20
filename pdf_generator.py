"""
PDF Report Generator for AP ECET Counselling Forecasting System.
Uses ReportLab to generate official prediction reports and web option preference lists.
"""

import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def get_theme_colors():
    return {
        'primary': colors.HexColor('#0f172a'),
        'secondary': colors.HexColor('#0284c7'),
        'accent': colors.HexColor('#7c3aed'),
        'safe': colors.HexColor('#059669'),
        'moderate': colors.HexColor('#d97706'),
        'ambitious': colors.HexColor('#ea580c'),
        'dream': colors.HexColor('#dc2626'),
        'light_bg': colors.HexColor('#f8fafc'),
        'border': colors.HexColor('#cbd5e1')
    }

def generate_prediction_report_pdf(student_data, recommendations):
    """
    Generates a formal PDF report of the candidate's AP ECET admission prediction.
    Returns bytes of the generated PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    theme = get_theme_colors()
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=theme['primary'],
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=theme['secondary'],
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("ANDHRA PRADESH STATE COUNCIL OF HIGHER EDUCATION", title_style))
    elements.append(Paragraph("AP ECET COUNSELLING FORECASTING SYSTEM — ADMISSION FORECAST REPORT", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=theme['secondary'], spaceAfter=12))

    # 2. Candidate Profile Table
    elements.append(Paragraph("CANDIDATE & PREDICTION PARAMETERS", section_style))
    
    cand_data = [
        [
            Paragraph("<b>Candidate Rank:</b>", body_style), Paragraph(f"<b>{student_data.get('student_rank', 'N/A'):,}</b>", body_style),
            Paragraph("<b>Category:</b>", body_style), Paragraph(str(student_data.get('category', 'OC')), body_style)
        ],
        [
            Paragraph("<b>Gender:</b>", body_style), Paragraph(str(student_data.get('gender', 'BOYS')), body_style),
            Paragraph("<b>Region:</b>", body_style), Paragraph(str(student_data.get('region', 'AU')), body_style)
        ],
        [
            Paragraph("<b>Preferred Branch:</b>", body_style), Paragraph(str(student_data.get('branch', 'N/A')), body_style),
            Paragraph("<b>Counselling Round:</b>", body_style), Paragraph(str(student_data.get('counselling_round', 'Phase 1')), body_style)
        ],
        [
            Paragraph("<b>District Filter:</b>", body_style), Paragraph(str(student_data.get('district', 'ALL')), body_style),
            Paragraph("<b>College Type:</b>", body_style), Paragraph(str(student_data.get('college_type', 'ALL')), body_style)
        ]
    ]

    cand_table = Table(cand_data, colWidths=[110, 150, 110, 150])
    cand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), theme['light_bg']),
        ('BOX', (0, 0), (-1, -1), 0.5, theme['border']),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, theme['border']),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(cand_table)
    elements.append(Spacer(1, 14))

    # 3. Forecast Overview Summary
    safe_cnt = sum(1 for r in recommendations if r.get('classification') == 'Safe')
    mod_cnt = sum(1 for r in recommendations if r.get('classification') == 'Moderate')
    amb_cnt = sum(1 for r in recommendations if r.get('classification') == 'Ambitious')
    drm_cnt = sum(1 for r in recommendations if r.get('classification') == 'Dream')

    summary_data = [
        [
            Paragraph(f"<b>Total Eligible:</b> {len(recommendations)}", body_style),
            Paragraph(f"<font color='#059669'><b>Safe (High Prob):</b> {safe_cnt}</font>", body_style),
            Paragraph(f"<font color='#d97706'><b>Moderate:</b> {mod_cnt}</font>", body_style),
            Paragraph(f"<font color='#ea580c'><b>Ambitious:</b> {amb_cnt}</font>", body_style),
            Paragraph(f"<font color='#dc2626'><b>Dream:</b> {drm_cnt}</font>", body_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[104, 104, 104, 104, 104])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, theme['border']),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # 4. Recommendations Table
    elements.append(Paragraph("TOP RECOMMENDED COLLEGES & ADMISSION PROBABILITY", section_style))

    table_data = [[
        Paragraph("<b>Code</b>", table_header),
        Paragraph("<b>College Name & Place</b>", table_header),
        Paragraph("<b>Dist/Reg</b>", table_header),
        Paragraph("<b>Exp. Cutoff</b>", table_header),
        Paragraph("<b>Prob %</b>", table_header),
        Paragraph("<b>Category</b>", table_header),
        Paragraph("<b>Annual Fee</b>", table_header)
    ]]

    # Show top 35 recommendations in PDF to keep it practical
    for rec in recommendations[:35]:
        cls_name = rec.get('classification', 'Safe')
        cls_color = {
            'Safe': '#059669',
            'Moderate': '#d97706',
            'Ambitious': '#ea580c',
            'Dream': '#dc2626'
        }.get(cls_name, '#059669')

        table_data.append([
            Paragraph(f"<b>{rec.get('college_code')}</b>", table_text),
            Paragraph(f"<b>{rec.get('college_name')[:36]}</b><br/>{rec.get('place', '')}", table_text),
            Paragraph(f"{rec.get('district')}<br/>({rec.get('region')})", table_text),
            Paragraph(f"{rec.get('expected_cutoff', 0):,}", table_text),
            Paragraph(f"<b>{rec.get('admission_probability', 0)}%</b>", table_text),
            Paragraph(f"<font color='{cls_color}'><b>{cls_name}</b></font>", table_text),
            Paragraph(f"Rs. {rec.get('annual_fee', 0):,}", table_text)
        ])

    rec_table = Table(table_data, colWidths=[45, 185, 55, 60, 50, 65, 60])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), theme['primary']),
        ('BOX', (0, 0), (-1, -1), 0.5, theme['border']),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, theme['border']),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, theme['light_bg']])
    ]))
    elements.append(rec_table)
    elements.append(Spacer(1, 14))

    # 5. Explainable Reasoning & Viva Disclaimers
    elements.append(Paragraph("SYSTEM EXPLANATION & COUNSELLING ADVISORY", section_style))
    reasons_text = """
    • <b>Forecasting Methodology:</b> Predictions are derived from a hybrid machine learning engine combining recency-weighted historical cutoff analysis (2023-2024) with multi-model predictive trends (2025-2026).<br/>
    • <b>Recommendation Tiers:</b> <b>Safe:</b> High probability (>=75%); <b>Moderate:</b> Reasonable probability (50-74%); <b>Ambitious:</b> Low probability (25-49%); <b>Dream:</b> Highly competitive (&lt;25%).<br/>
    • <b>Important Notice:</b> Web options order should balance Safe, Moderate, and Dream choices to maximize admission prospects during official APSCHE allotment.
    """
    elements.append(Paragraph(reasons_text, body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_preference_list_pdf(user_info, preference_items):
    """
    Generates a printable AP ECET Web Options Preference List PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    theme = get_theme_colors()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'PrefTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=theme['primary'],
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'PrefSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    elements = []
    elements.append(Paragraph("AP ECET 2026 COUNSELLING — WEB OPTIONS PREFERENCE LIST", title_style))
    elements.append(Paragraph(f"Generated for Candidate: {user_info.get('username', 'Student')} | Email: {user_info.get('email', '')}", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=theme['accent'], spaceAfter=12))

    table_data = [[
        Paragraph("<b>Opt No</b>", table_header),
        Paragraph("<b>College Code</b>", table_header),
        Paragraph("<b>College Name</b>", table_header),
        Paragraph("<b>Branch Name</b>", table_header),
        Paragraph("<b>District</b>", table_header),
        Paragraph("<b>Classification</b>", table_header),
        Paragraph("<b>Chance %</b>", table_header),
        Paragraph("<b>Fee</b>", table_header)
    ]]

    for item in preference_items:
        cls_name = item.get('classification', 'Safe')
        cls_color = {
            'Safe': '#059669',
            'Moderate': '#d97706',
            'Ambitious': '#ea580c',
            'Dream': '#dc2626'
        }.get(cls_name, '#059669')

        table_data.append([
            Paragraph(f"<b>{item.get('preference_order', 1):02d}</b>", table_text),
            Paragraph(f"<b>{item.get('college_code')}</b>", table_text),
            Paragraph(f"{item.get('college_name', '')[:38]}", table_text),
            Paragraph(f"{item.get('branch_name', '')[:28]}", table_text),
            Paragraph(f"{item.get('district', '')}", table_text),
            Paragraph(f"<font color='{cls_color}'><b>{cls_name}</b></font>", table_text),
            Paragraph(f"{item.get('probability', 0)}%", table_text),
            Paragraph(f"Rs. {item.get('fees', 0):,}", table_text)
        ])

    pref_table = Table(table_data, colWidths=[40, 55, 175, 110, 45, 55, 45, 50])
    pref_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), theme['accent']),
        ('BOX', (0, 0), (-1, -1), 0.5, theme['border']),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, theme['border']),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, theme['light_bg']])
    ]))
    elements.append(pref_table)
    elements.append(Spacer(1, 18))

    # Signature Block
    sign_data = [
        [
            Paragraph("<b>Candidate Signature:</b> _______________________", body_style),
            Paragraph("<b>Verification Officer:</b> _______________________", body_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
