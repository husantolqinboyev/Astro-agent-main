#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Generator for Astro Agent Project Articles
This script converts Markdown articles to PDF format.
It utilizes Microsoft Edge or Google Chrome in headless mode for high-fidelity PDF rendering.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Check if required libraries are available, if not, install them
try:
    from markdown import markdown
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'markdown'])
    from markdown import markdown


def find_browser():
    """Find Google Chrome or Microsoft Edge executable on Windows."""
    # 1. Try standard Windows paths
    paths = [
        # Microsoft Edge
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Google Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\x86\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
            
    # 2. Try to find in PATH
    for cmd in ["msedge", "chrome", "google-chrome"]:
        path = shutil.which(cmd)
        if path:
            return path
            
    return None


def get_styles():
    """Return CSS styles optimized for Astro Agent technical articles."""
    return """
    @page {
        margin: 2cm;
        size: A4;
    }
    
    body {
        font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        direction: ltr;
        color: #1a202c;
        background-color: #ffffff;
    }
    
    h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 28pt;
        color: #2d3748;
        border-bottom: 4px solid #4a5568;
        padding-bottom: 12px;
        margin-top: 40px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    h2 {
        font-family: 'Outfit', sans-serif;
        font-size: 20pt;
        color: #2b6cb0;
        margin-top: 30px;
        margin-bottom: 15px;
        border-left: 5px solid #2b6cb0;
        padding-left: 15px;
    }
    
    h3 {
        font-family: 'Outfit', sans-serif;
        font-size: 16pt;
        color: #2d3748;
        margin-top: 25px;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 25px 0;
        page-break-inside: avoid;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    th, td {
        border: 1px solid #e2e8f0;
        padding: 12px 15px;
        text-align: left;
    }
    
    th {
        background-color: #2d3748;
        color: white;
        font-weight: 700;
        font-size: 10pt;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    tr:nth-child(even) {
        background-color: #f7fafc;
    }
    
    blockquote {
        border-left: 4px solid #4a5568;
        margin: 20px 0;
        padding: 15px 25px;
        background-color: #edf2f7;
        font-style: italic;
        color: #4a5568;
        border-radius: 0 8px 8px 0;
    }
    
    code {
        background-color: #f7fafc;
        padding: 2px 5px;
        border-radius: 4px;
        font-family: 'Fira Code', 'Consolas', monospace;
        font-size: 90%;
        color: #e53e3e;
        border: 1px solid #e2e8f0;
    }
    
    pre {
        background-color: #1a202c;
        color: #f7fafc;
        padding: 20px;
        border-radius: 10px;
        overflow-x: auto;
        font-family: 'Fira Code', 'Consolas', monospace;
        font-size: 9pt;
        line-height: 1.5;
        margin: 20px 0;
    }
    
    ul, ol {
        margin: 15px 0;
        padding-left: 35px;
    }
    
    li {
        margin: 8px 0;
    }
    
    strong {
        color: #2d3748;
        font-weight: 700;
    }
    
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        font-size: 9pt;
        color: #a0aec0;
        padding: 10px;
    }
    """


def convert_markdown_to_html(md_file_path):
    """Convert markdown file to HTML with proper styling."""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_body = markdown(md_content, extensions=['tables', 'fenced_code', 'codehilite'])
    
    # Create full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Astro Agent - Maqolalar</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&family=Fira+Code&display=swap" rel="stylesheet">
        <style>
            {get_styles()}
        </style>
    </head>
    <body>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            Astro Agent Loyihasi Maqolalari | Created by Husan
        </div>
    </body>
    </html>
    """
    
    return full_html


def generate_pdf(md_file_path, output_pdf_path):
    """Generate PDF from markdown file using headless Microsoft Edge or Chrome."""
    print(f"O'tkazilmoqda: {md_file_path}")
    
    browser_path = find_browser()
    if not browser_path:
        print("[XATO] Microsoft Edge yoki Google Chrome topilmadi.")
        return False
        
    html_content = convert_markdown_to_html(md_file_path)
    
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write(html_content)
        temp_html_path = temp_file.name
        
    temp_file_url = Path(temp_html_path).absolute().as_uri()
    
    success = False
    try:
        cmd = [
            browser_path,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_pdf_path}",
            temp_file_url
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[MUVAFFAQIYAT] Yaratildi: {output_pdf_path}")
        success = True
    except Exception as e:
        print(f"[XATO] PDF yaratishda xatolik: {e}")
    finally:
        if os.path.exists(temp_html_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass
                
    return success


def main():
    """Main function to process article files."""
    workspace_dir = Path(__file__).parent.absolute()
    output_dir = workspace_dir / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Target specific files or all .md files in the current directory
    article_files = sorted(workspace_dir.glob('*.md'))
    
    if not article_files:
        print("[OGOHLANTIRISH] Maqola fayllari topilmadi (.md)")
        return
        
    print("=" * 60)
    print("      ASTRO AGENT MAQOLALARI PDF GENERATOR")
    print("=" * 60)
    print("\nMavjud fayllar:")
    
    for idx, article_file in enumerate(article_files, 1):
        print(f" [{idx}] {article_file.name}")
        
    print("-" * 60)
    user_input = input("Tanlovingizni kiriting (0 - barchasi, yoki raqam): ").strip()
    
    selected_files = []
    if user_input == "0" or user_input == "":
        selected_files = article_files
    else:
        try:
            indices = [int(i.strip()) for i in user_input.split(",")]
            for idx in indices:
                if 1 <= idx <= len(article_files):
                    selected_files.append(article_files[idx - 1])
        except ValueError:
            print("[XATO] Noto'g'ri tanlov.")
            return

    if not selected_files:
        return
        
    for article_file in selected_files:
        output_pdf = output_dir / (article_file.stem + ".pdf")
        generate_pdf(str(article_file), str(output_pdf))
    
    print("\n" + "=" * 60)
    print(f"PDF fayllar saqlandi: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == '__main__':
    main()
