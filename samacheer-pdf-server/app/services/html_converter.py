"""
HTML Converter
Converts Markdown to beautifully formatted HTML
"""

import markdown
from typing import Optional


class HTMLConverter:
    """Converts Markdown to styled HTML"""
    
    def __init__(self):
        """Initialize Markdown converter with extensions"""
        self.md = markdown.Markdown(
            extensions=[
                'extra',          # Tables, footnotes, etc.
                'codehilite',     # Code syntax highlighting
                'toc',            # Table of contents
                'nl2br',          # Newline to <br>
                'sane_lists',     # Better list handling
            ]
        )
    
    def convert_to_html(
        self, 
        markdown_content: str,
        metadata: dict
    ) -> Optional[str]:
        """
        Convert Markdown to styled HTML
        
        Args:
            markdown_content: Markdown text
            metadata: Dict with class, subject, unit info
        
        Returns:
            Complete HTML document with CSS styling
        """
        try:
            # Convert MD to HTML body
            html_body = self.md.convert(markdown_content)
            
            # Wrap in complete HTML document with styling
            full_html = self._create_html_document(html_body, metadata)
            
            return full_html
            
        except Exception as e:
            print(f"❌ HTML Conversion Error: {e}")
            return None
    
    def _create_html_document(self, body: str, metadata: dict) -> str:
        """Create complete HTML document with CSS"""
        
        class_num = metadata.get('class', 'Unknown')
        subject = metadata.get('subject', 'Unknown')
        unit = metadata.get('unit', '')
        lesson_title = metadata.get('lesson_title', 'Lesson')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lesson_title} - Class {class_num} {subject.title()}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
        
        .header {{
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .metadata {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 10px;
            font-size: 14px;
            color: #666;
        }}
        
        .metadata span {{
            background: #f0f0f0;
            padding: 5px 12px;
            border-radius: 5px;
        }}
        
        h1 {{
            color: #667eea;
            font-size: 32px;
            margin-top: 10px;
        }}
        
        h2 {{
            color: #764ba2;
            font-size: 24px;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        
        h3 {{
            color: #555;
            font-size: 20px;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        
        h4 {{
            color: #666;
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        strong {{
            color: #667eea;
            font-weight: 600;
        }}
        
        em {{
            color: #764ba2;
            font-style: italic;
        }}
        
        ul, ol {{
            margin: 15px 0 15px 30px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
            background: #f9f9f9;
            padding: 15px 20px;
            border-radius: 5px;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        .poetry {{
            font-family: Georgia, serif;
            font-style: italic;
            line-height: 2;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="metadata">
                <span>📚 Class {class_num}</span>
                <span>📖 {subject.title()}</span>
                <span>📝 Unit {unit}</span>
                <span>🎓 Samacheer Kalvi</span>
            </div>
            <h1>{lesson_title}</h1>
        </div>
        
        <div class="content">
            {body}
        </div>
        
        <div class="footer">
            <p>Generated by Samacheer Kalvi PDF Extractor | AI-Powered Formatting</p>
            <p>Source: Tamil Nadu State Board Textbook</p>
        </div>
    </div>
</body>
</html>
"""
        return html


# Create singleton instance
html_converter = HTMLConverter()