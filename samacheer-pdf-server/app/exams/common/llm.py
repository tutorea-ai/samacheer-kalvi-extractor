"""Shared Claude call helper for the exams module (retry with 30s backoff, JSON parsing)."""
import json
import re
import time

import anthropic

from app.config import settings

RETRY_STATUS = {429, 500, 502, 503, 529}
_client = None


class RefusalError(RuntimeError):
    """The model declined the request (stop_reason == 'refusal'). Never retried or worked around."""


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    return json.loads(text[start:end + 1])


def call_json(content, model: str, max_tokens: int = 8000, max_retries: int = 5) -> dict:
    """Send content (a string or a list of content blocks) and return the parsed JSON reply."""
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    for attempt in range(1, max_retries + 1):
        try:
            with client().messages.stream(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": content}],
            ) as stream:
                resp = stream.get_final_message()
            if resp.stop_reason == "max_tokens":
                raise RuntimeError(f"Response hit max_tokens ({max_tokens}); increase it")
            if resp.stop_reason == "refusal":
                raise RefusalError("Model declined this request (stop_reason=refusal)")
            text = "".join(b.text for b in resp.content if b.type == "text")
            if not text.strip():
                raise RuntimeError(f"Empty reply from model (stop_reason={resp.stop_reason}, "
                                   f"blocks={[b.type for b in resp.content]})")
            return parse_json(text)
        except anthropic.APIStatusError as e:
            if e.status_code in RETRY_STATUS and attempt < max_retries:
                time.sleep(30)
                continue
            raise
        except anthropic.APIConnectionError:
            if attempt < max_retries:
                time.sleep(30)
                continue
            raise
        except json.JSONDecodeError:
            if attempt < max_retries:
                continue
            raise