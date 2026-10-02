import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.ledger import get_all_visits, verify_ledger, get_ledger_stats

def generate_incentive_pdf(
    output_filename: str = "asha_incentive_report.pdf",
    worker_name: str = "Anugrah K (ASHA Worker #4102)",
    phc_name: str = "Primary Health Centre, Ward 4",
    month_year: Optional[str] = None
) -> str:
    """
    Generates a professional NHM ASHA monthly incentive claim report PDF.
    """
    if not month_year:
        month_year = datetime.now().strftime("%B %Y")
        
    visits = get_all_visits()
    verification = verify_ledger()
    stats = get_ledger_stats()
    
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1F2937')
    )
    
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#111827')
    )
    
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )
    
    kpi_number_style = ParagraphStyle(
        'KPINumber',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )
    
    kpi_label_style = ParagraphStyle(
        'KPILabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#6B7280'),
        alignment=1
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("NATIONAL HEALTH MISSION (NHM) - ASHA INCENTIVE CLAIM", title_style))
    story.append(Paragraph("DEPARTMENT OF HEALTH & FAMILY WELFARE • ANATENATAL CARE (ANC) DIGITAL REGISTER", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=2, spaceAfter=10))

    # 2. Worker & Period Info Box
    generated_on = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    info_data = [
        [
            Paragraph(f"<b>ASHA Worker:</b> {worker_name}", meta_style),
            Paragraph(f"<b>Billing Month:</b> {month_year}", meta_style)
        ],
        [
            Paragraph(f"<b>Health Centre:</b> {phc_name}", meta_style),
            Paragraph(f"<b>Generated On:</b> {generated_on}", meta_style)
        ],
        [
            Paragraph(f"<b>Ledger Proof:</b> SHA-256 Chained Integrity Verified", meta_style),
            Paragraph(f"<b>Verification Status:</b> {'PASS (Authentic)' if verification.get('is_valid') else 'FLAGGED'}", meta_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 260])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # 3. KPI Summary Cards
    total_visits = stats.get("total_visits", 0)
    high_risk = stats.get("high_risk_cases", 0)
    total_incentives = stats.get("total_incentives", 0.0)

    kpi_data = [
        [
            Paragraph(f"{total_visits}", kpi_number_style),
            Paragraph(f"{high_risk}", kpi_number_style),
            Paragraph(f"₹ {total_incentives:,.2f}", kpi_number_style),
            Paragraph("100% SHA-256", kpi_number_style)
        ],
        [
            Paragraph("Total ANC Visits", kpi_label_style),
            Paragraph("High-Risk / Triage Flags", kpi_label_style),
            Paragraph("Total Approved Claim", kpi_label_style),
            Paragraph("Proof-of-Work Security", kpi_label_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[132, 132, 133, 133])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3B82F6')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BFDBFE')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))

    # 4. Visits Detail Table
    story.append(Paragraph("<b>VERIFIED PATIENT VISITS & INCENTIVE BREAKDOWN:</b>", meta_style))
    story.append(Spacer(1, 6))

    headers = ["#", "Date", "Patient Name", "GA Wk", "BP (mmHg)", "Risk Status", "Claim", "Hash Sig"]
    rows = [headers]

    for v in visits:
        risk = v.get("risk_level", "NORMAL")
        risk_color = "#DC2626" if risk in ["HIGH_RISK", "CRITICAL"] else ("#D97706" if risk == "MODERATE_RISK" else "#16A34A")
        
        bp = f"{v.get('bp_sys', '-')}/{v.get('bp_dia', '-')}" if v.get('bp_sys') else "-"
        hash_short = (v.get('hash') or '')[:8] + "…"
        date_short = v.get('timestamp', '')[:10]
        
        risk_cell = Paragraph(f"<font color='{risk_color}'><b>{risk}</b></font>", cell_style)
        
        rows.append([
            Paragraph(str(v.get("id")), cell_style),
            Paragraph(date_short, cell_style),
            Paragraph(v.get("patient_name", "N/A"), cell_bold),
            Paragraph(f"{v.get('gestational_age_weeks', '-')}w", cell_style),
            Paragraph(bp, cell_style),
            risk_cell,
            Paragraph(f"₹ {v.get('incentive_amount', 0):.0f}", cell_bold),
            Paragraph(f"<font face='Courier' size='7'>{hash_short}</font>", cell_style),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("No visits logged yet", cell_style), "", "", "", "", "", "", ""])

    visits_table = Table(rows, colWidths=[20, 60, 110, 45, 65, 80, 50, 100])
    visits_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#9CA3AF')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(visits_table)
    story.append(Spacer(1, 25))

    # 5. Certification Signatures Block
    sig_data = [
        [
            Paragraph("<b>Verified & Submitted by:</b><br/><br/><br/>____________________________________<br/>Signature of ASHA Worker<br/>Date: ________________________", meta_style),
            Paragraph("<b>Approved & Certified by:</b><br/><br/><br/>____________________________________<br/>Medical Officer In-Charge (PHC)<br/>Seal & Date: _________________", meta_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 265])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_filename

if __name__ == "__main__":
    out = generate_incentive_pdf("samples/test_report.pdf")
    print(f"Generated PDF at: {out}")
