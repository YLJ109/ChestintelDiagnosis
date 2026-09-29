"""PDF报告生成服务 - 批量诊断报告"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# 注册中文字体 (使用Windows自带宋体)
def _register_chinese_font():
    font_paths = [
        'C:/Windows/Fonts/simsun.ttc',  # 宋体
        'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
        'C:/Windows/Fonts/simhei.ttf',   # 黑体
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                name = os.path.basename(fp).split('.')[0]
                pdfmetrics.registerFont(TTFont(name, fp))
                return name
            except Exception:
                continue
    return None


# 14种疾病定义
DISEASE_NAMES = {
    'Atelectasis': '肺不张', 'Cardiomegaly': '心脏肥大', 'Consolidation': '实变',
    'Edema': '水肿', 'Effusion': '胸腔积液', 'Emphysema': '肺气肿',
    'Fibrosis': '纤维化', 'Hernia': '膈疝', 'Infiltration': '浸润',
    'Mass': '肿块', 'Nodule': '结节', 'Pleural_Thickening': '胸膜增厚',
    'Pneumonia': '肺炎', 'Pneumothorax': '气胸',
}

PRIMARY_COLOR = HexColor('#10B981')
DARK_COLOR = HexColor('#1E293B')
HEADER_BG = HexColor('#0F172A')
WARNING_COLOR = HexColor('#EF4444')
TEXT_COLOR = HexColor('#1f2937')


def generate_batch_pdf(batch_no, diagnosis_results, output_dir):
    """生成批量诊断PDF报告"""
    font_name = _register_chinese_font()
    font = font_name if font_name else 'Helvetica'

    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{batch_no}.pdf")

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'CNTitle', fontName=font, fontSize=20, leading=28,
        alignment=1, textColor=DARK_COLOR, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'CNSubtitle', fontName=font, fontSize=10, leading=14,
        alignment=1, textColor=HexColor('#6B7280'), spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        'CNHeading', fontName=font, fontSize=13, leading=18,
        textColor=PRIMARY_COLOR, spaceAfter=6, spaceBefore=10,
    ))
    styles.add(ParagraphStyle(
        'CNBody', fontName=font, fontSize=10, leading=16,
        textColor=TEXT_COLOR, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        'CNSmall', fontName=font, fontSize=8, leading=12,
        textColor=HexColor('#9CA3AF'), spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        'CNWarning', fontName=font, fontSize=9, leading=13,
        textColor=WARNING_COLOR, spaceAfter=6,
    ))

    elements = []

    # ==================== 封面页 ====================
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph('胸部X光AI智能辅助诊断报告', styles['CNTitle']))
    elements.append(Paragraph('Chest X-ray AI Intelligent Diagnosis Report', styles['CNSubtitle']))
    elements.append(Spacer(1, 10*mm))

    cover_data = [
        ['批次编号', batch_no],
        ['报告日期', datetime.now().strftime('%Y年%m月%d日 %H:%M')],
        ['影像数量', str(len(diagnosis_results))],
        ['系统版本', '胸影智诊V3.0'],
    ]
    cover_table = Table(cover_data, colWidths=[50*mm, 80*mm])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#E5E7EB')),
    ]))
    elements.append(cover_table)

    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph('AI诊断结果仅供参考，最终诊断以执业医师审核为准', styles['CNWarning']))
    elements.append(PageBreak())

    # ==================== 每个诊断详情 ====================
    for idx, diag in enumerate(diagnosis_results, 1):
        patient_name = diag.get('patient_name', '未知')
        patient_no = diag.get('patient_no', '')
        is_standard = diag.get('is_standard', False)
        original_filename = diag.get('original_filename', '')

        # 患者信息头
        elements.append(Paragraph(f'第 {idx} 份诊断', styles['CNHeading']))

        if is_standard:
            info = diag.get('patient_info', {})
            gender_map = {'male': '男', 'female': '女'}
            patient_info_data = [
                ['患者姓名', patient_name, '患者编号', patient_no],
                ['性别', gender_map.get(info.get('gender', ''), info.get('gender', '')),
                 '年龄', f"{info.get('age', '')}岁"],
                ['主要发现', diag.get('finding_zh', '') or info.get('finding_zh', ''),
                 '图片ID', info.get('image_id', '')],
                ['原始文件', original_filename, '', ''],
            ]
        else:
            patient_info_data = [
                ['患者姓名', f'{patient_name} (文件名不规范)', '患者编号', patient_no or '未匹配'],
                ['原始文件', original_filename, '', ''],
            ]

        info_table = Table(patient_info_data, colWidths=[25*mm, 35*mm, 25*mm, 45*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), DARK_COLOR),
            ('TEXTCOLOR', (2, 0), (2, -1), HexColor('#6B7280')),
            ('TEXTCOLOR', (3, 0), (3, -1), DARK_COLOR),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('SPAN', (1, -1), (3, -1)),  # 合并原始文件行
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 4*mm))

        # 疾病概率表格
        elements.append(Paragraph('疾病概率分析 (14类)', styles['CNHeading']))
        probabilities = diag.get('probabilities', [])

        prob_header = ['疾病名称', '英文名称', '概率', '状态']
        prob_rows = [prob_header]
        for p in probabilities:
            prob_val = p['probability']
            pct = f"{prob_val * 100:.1f}%"
            if prob_val >= 0.7:
                status = '高危'
            elif prob_val >= 0.3:
                status = '关注'
            else:
                status = '正常'
            prob_rows.append([
                p['disease_name_zh'],
                p['disease_code'],
                pct,
                status,
            ])

        prob_table = Table(prob_rows, colWidths=[30*mm, 35*mm, 20*mm, 20*mm])
        prob_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9FAFB')]),
        ]))
        # 高危行标红
        for i, p in enumerate(probabilities, 1):
            if p['probability'] >= 0.7:
                prob_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (3, i), (3, i), WARNING_COLOR),
                    ('FONTNAME', (3, i), (3, i), font),
                ]))
            elif p['probability'] >= 0.3:
                prob_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (3, i), (3, i), HexColor('#F59E0B')),
                    ('FONTNAME', (3, i), (3, i), font),
                ]))

        elements.append(prob_table)
        elements.append(Spacer(1, 4*mm))

        # 影像图片 (原始+热力图)
        image_path = diag.get('image_path')
        heatmap_path = diag.get('heatmap_path')

        images = []
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if image_path:
            full_path = os.path.join(base_dir, 'data', image_path)
            if os.path.exists(full_path):
                images.append(('原始影像', full_path))
        if heatmap_path:
            full_path = os.path.join(base_dir, 'data', heatmap_path)
            if os.path.exists(full_path):
                images.append(('Grad-CAM热力图', full_path))

        if images:
            img_elements = []
            for label, path in images:
                try:
                    img = Image(path, width=70*mm, height=70*mm)
                    img.hAlign = 'CENTER'
                    elements.append(Paragraph(label, styles['CNSmall']))
                    elements.append(img)
                    elements.append(Spacer(1, 3*mm))
                except Exception:
                    pass

        # AI报告内容
        from xml.sax.saxutils import escape as _xml_escape
        report = diag.get('report', {})
        if report:
            elements.append(Paragraph('AI诊断报告', styles['CNHeading']))
            if report.get('findings'):
                elements.append(Paragraph(f'<b>检查所见：</b>{_xml_escape(str(report["findings"]))}', styles['CNBody']))
            if report.get('impression'):
                elements.append(Paragraph(f'<b>诊断意见：</b>{_xml_escape(str(report["impression"]))}', styles['CNBody']))
            if report.get('recommendations'):
                elements.append(Paragraph(f'<b>建议：</b>{_xml_escape(str(report["recommendations"]))}', styles['CNBody']))

        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph('─' * 60, styles['CNSmall']))

        # 每2个诊断换一页(避免页面太拥挤)
        if idx % 2 == 0 and idx < len(diagnosis_results):
            elements.append(PageBreak())

    # 生成PDF
    doc.build(elements)
    return f"{batch_no}.pdf"
