"""
Beyond the Book: one picture per card via OpenAI's image API.

Each card's `picture` description + the profile's style line -> an image,
shrunk to WebP and embedded as a data URI, so the page stays one
self-contained index.html (no Node change). Images are cached by prompt,
so rebuilding a lesson never pays twice for the same picture. A failed
picture just leaves that card without one; nothing else breaks.
"""
import base64
import hashlib
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Optional

from PIL import Image

from ...config import settings
from .subjects.base import SubjectProfile

CACHE_DIR = Path.home() / ".cache" / "beyond_book_pictures"   # outside git
WORKERS = 4           # pictures generated at the same time
ATTEMPTS = 2          # tries per picture
MAX_WIDTH = 960       # card width is ~820px; this keeps it sharp on most screens
WEBP_QUALITY = 78


def _prompt(desc: str, p: SubjectProfile) -> str:
    return f"{desc.strip()} Style: {p.picture_style}."


def _cache_key(prompt: str, p: SubjectProfile) -> str:
    raw = f"{p.picture_model}|{p.picture_size}|{p.picture_quality}|{prompt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _shrink(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
    return out.getvalue()


class PictureMaker:
    def __init__(self):
        self._client = None

    def _openai(self):
        if self._client is None:
            from openai import OpenAI
            if not settings.OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY is not set in .env")
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def one(self, desc: str, p: SubjectProfile) -> Optional[bytes]:
        prompt = _prompt(desc, p)
        cached = CACHE_DIR / f"{_cache_key(prompt, p)}.webp"
        if cached.exists():
            return cached.read_bytes()
        for attempt in range(1, ATTEMPTS + 1):
            try:
                r = self._openai().images.generate(
                    model=p.picture_model, prompt=prompt, size=p.picture_size,
                    quality=p.picture_quality, n=1)
                webp = _shrink(base64.b64decode(r.data[0].b64_json))
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(webp)
                return webp
            except Exception as e:
                print(f"         ⚠️  picture attempt {attempt} failed: {type(e).__name__}: {str(e)[:140]}")
                if attempt < ATTEMPTS:
                    time.sleep(10)
        return None

    def add_pictures(self, deck: Dict, p: SubjectProfile) -> Dict:
        """Sets card['image'] (a data URI) on every card that has a picture description."""
        if not p.pictures:
            return deck
        jobs = [c for c in deck.get("cards", []) if (c.get("picture") or "").strip()]
        if not jobs:
            return deck
        print(f"   🖼  Pictures: {len(jobs)} cards (model {p.picture_model})")
        t, made = time.time(), 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(self.one, c["picture"], p): c for c in jobs}
            for fut in as_completed(futures):
                c, webp = futures[fut], fut.result()
                if webp:
                    c["image"] = "data:image/webp;base64," + base64.b64encode(webp).decode()
                    made += 1
                else:
                    c.setdefault("warnings", []).append("picture failed — card shown without it")
        print(f"   🖼  {made}/{len(jobs)} pictures ready in {time.time() - t:.0f}s")
        deck["pictures"] = {"model": p.picture_model, "made": made, "wanted": len(jobs)}
        return deck


picture_maker = PictureMaker()