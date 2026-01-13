"""
HTML Converter
Converts Markdown to beautiful HTML (Standalone or Server-Ready)
Removes raw metadata/frontmatter from the output.
"""

import markdown
import re
from typing import Optional

class HTMLConverter:
    """Converts Markdown to styled HTML"""
    
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                'extra',          # Tables, footnotes
                'codehilite',     # Code highlighting
                'toc',            # Table of contents
                'nl2br',          # Newline to <br>
                'sane_lists',     # Better lists
            ]
        )
    
    def _clean_metadata(self, text: str) -> str:
        """
        Removes YAML-style metadata or JSON blocks from the top of the file.
        Example:
        title: "Lesson"
        class: 8
        ...
        """
        # 1. Remove standard YAML frontmatter (between --- and ---)
        text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
        
        # 2. Remove raw key-value pairs at the start if AI forgot the --- dashes
        # Matches lines like "title: ...", "class: ...", "source: ..." at the start
        text = re.sub(r'^\s*(title|class|subject|unit|source|generated):\s+.*?\n', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text.strip()

    def convert_to_html(
        self, 
        markdown_content: str,
        metadata: dict,
        mode: str = "standalone"
    ) -> Optional[str]:
        """
        Convert Markdown to HTML
        """
        try:
            # Step 1: Clean the input (Remove that ugly JSON/YAML block)
            cleaned_markdown = self._clean_metadata(markdown_content)
            
            # Step 2: Convert MD to HTML body
            html_body = self.md.convert(cleaned_markdown)
            
            # Step 3: Select template
            if mode == "server":
                full_html = self._create_server_document(html_body, metadata)
            else:
                full_html = self._create_standalone_document(html_body, metadata)
            
            return full_html
            
        except Exception as e:
            print(f"❌ HTML Conversion Error: {e}")
            return None
    
    def _create_server_document(self, body: str, metadata: dict) -> str:
        """
        Creates HTML matching the module 1 server structure.
        Links to external sk.css instead of internal styles.
        """
        class_num = int(metadata.get('class', 0))
        lesson_title = metadata.get('lesson_title', 'Lesson')
        
        # Calculate Path Depth
        if class_num <= 7:
            relative_path = "../../../.." 
        else:
            relative_path = "../.."

        html = f"""<html>
  <head>
    <title>{lesson_title} - Tutorea Samacheer</title>
    <link rel="stylesheet" href="{relative_path}/css/sk.css" />
    <script src="{relative_path}/js/sk.js"></script>
  </head>
  <body>
    <h1>{lesson_title}</h1>
    <div class="content">
{body}
    </div>
  </body>
</html>"""
        return html

    def _create_standalone_document(self, body: str, metadata: dict) -> str:
        """
        Creates the beautiful, gradient-styled HTML for standalone viewing.
        """
        class_num = metadata.get('class', 'Unknown')
        unit = metadata.get('unit', '')
        lesson_title = metadata.get('lesson_title', 'Lesson')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lesson_title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.8;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        img {{ max-width: 100%; height: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; }}
        blockquote {{ border-left: 4px solid #667eea; background: #f9f9f9; padding: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{lesson_title}</h1>
        <div class="metadata">Class {class_num} | Unit {unit}</div>
        <hr>
        {body}
    </div>
</body>
</html>"""
        return html

# Create singleton instance
html_converter = HTMLConverter()