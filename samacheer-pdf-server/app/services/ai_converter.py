"""
AI Markdown Converter
Converts extracted text to formatted Markdown using Kimi API
"""

from openai import OpenAI
from typing import Dict, Optional
from ..config import settings


class AIMarkdownConverter:
    """Converts text to markdown using Kimi AI"""
    
    def __init__(self):
        """Initialize Kimi client"""
        self.client = OpenAI(
            api_key=settings.KIMI_API_KEY,
            base_url=settings.KIMI_BASE_URL,
        )
        self.model = settings.KIMI_MODEL
    
    def convert_to_markdown(
        self, 
        text: str, 
        metadata: Dict
    ) -> Optional[str]:
        """
        Convert extracted text to formatted Markdown
        
        Args:
            text: Raw text extracted from PDF
            metadata: Dict with class, subject, unit, lesson info
        
        Returns:
            Formatted markdown string or None if failed
        """
        try:
            # Build prompt
            prompt = self._build_prompt(text, metadata)
            
            # Call Kimi API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at formatting educational content into clean, well-structured Markdown. You preserve all original content while improving readability."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower = more consistent formatting
            )
            
            # Extract response
            markdown_content = completion.choices[0].message.content
            
            # Add metadata header
            markdown_with_header = self._add_metadata_header(
                markdown_content, 
                metadata
            )
            
            return markdown_with_header
            
        except Exception as e:
            print(f"❌ AI Conversion Error: {e}")
            return None
    
    def _build_prompt(self, text: str, metadata: Dict) -> str:
        """Build the conversion prompt"""
        
        class_num = metadata.get('class', 'Unknown')
        subject = metadata.get('subject', 'Unknown')
        unit = metadata.get('unit', '')
        lesson_title = metadata.get('lesson_title', 'Unknown')
        
        prompt = f"""Convert the following textbook content into clean, well-formatted Markdown.

**Source Information:**
- Class: {class_num}
- Subject: {subject.title()}
- Unit: {unit}
- Lesson: {lesson_title}

**Formatting Requirements:**
1. Use proper heading hierarchy (# ## ### ####)
2. Format poetry with proper line breaks
3. Create clean paragraphs with proper spacing
4. Use **bold** for important terms
5. Use *italics* for emphasis or foreign words
6. Create bullet lists where appropriate
7. Format dialogues clearly
8. Preserve all original content - don't summarize
9. Remove page numbers and artifact text
10. Make it readable and student-friendly

**Original Text:**
---
{text}
---

**Output ONLY the formatted Markdown, no explanations.**
"""
        return prompt
    
    def _add_metadata_header(self, markdown: str, metadata: Dict) -> str:
        """Add YAML frontmatter with metadata"""
        
        class_num = metadata.get('class', 'Unknown')
        subject = metadata.get('subject', 'Unknown')
        unit = metadata.get('unit', '')
        lesson_title = metadata.get('lesson_title', 'Unknown')
        
        header = f"""---
title: "{lesson_title}"
class: {class_num}
subject: {subject.title()}
unit: {unit}
source: Samacheer Kalvi Textbook
generated: AI-Formatted Markdown
---

"""
        return header + markdown


# Create singleton instance
ai_converter = AIMarkdownConverter()