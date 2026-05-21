from weasyprint import HTML

def render_pdf(html_content, output_path):
    return HTML(string=html_content).write_pdf(output_path)
