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
from typing import Dict, List, Optional

import anthropic
from PIL import Image

from ...config import settings
from .subjects.base import SubjectProfile

CACHE_DIR = Path.home() / ".cache" / "beyond_book_pictures_v2"   # outside git; only checked pictures
WORKERS = 4           # pictures generated at the same time
ATTEMPTS = 2          # tries per picture
MAX_WIDTH = 960       # card width is ~820px; this keeps it sharp on most screens
WEBP_QUALITY = 78

PROBLEM_KINDS = (
    "religious", "stereotype", "unsafe", "words_or_logo", "screen_on",
    "not_real_life", "wrong_or_missing_object", "busy_scene", "malformed_body",
)

# Short, positive instructions for a retry. The problem text itself is never sent to the
# image model: its own safety filter can reject prompts that describe hazards.
KIND_FIX = {
    "religious": "Keep the scene free of any religious buildings, symbols or marks.",
    "stereotype": "Show everyone equally active; a boy does any household chore; heights and sizes are mixed across boys and girls.",
    "unsafe": "Everyone keeps their hands well away from switchboards, sockets and wires; all panels are closed.",
    "words_or_logo": "No brand names or logos; keep any label simple and clean.",
    "screen_on": "Every screen is switched off.",
    "not_real_life": "Show the real everyday moment, not a drawing or diagram.",
    "wrong_or_missing_object": "Make the main object large, accurate and clearly recognisable.",
    "busy_scene": "Use a plain background with only the main object and the people.",
    "malformed_body": "Draw every hand with five natural fingers and every face and body naturally; keep hands simple and relaxed.",
}


def _fixes(problems: List[str]) -> List[str]:
    kinds = {x.split(":", 1)[0].strip() for x in problems}
    return [KIND_FIX[k] for k in PROBLEM_KINDS if k in kinds]


CHECK_TOOL = {
    "name": "check_picture",
    "description": "Report whether this picture is fit for school students.",
    "input_schema": {
        "type": "object",
        "properties": {
            "notes": {"type": "string", "description": "Your working, 1-3 short sentences."},
            "problems": {"type": "array",
                         "description": "Only problems you can see. Empty if the picture is fine.",
                         "items": {"type": "object", "properties": {
                             "kind": {"type": "string", "enum": list(PROBLEM_KINDS)},
                             "detail": {"type": "string"}},
                             "required": ["kind", "detail"]}},
        },
        "required": ["notes", "problems"],
    },
}

CHECK_PROMPT = """You are checking a picture for a lesson card shown to Tamil Nadu school students.
The picture was made from this brief: {brief}
(It belongs to a lesson card asking: {hook})

Judge the picture against the brief. Use the card only to catch a picture that would
teach something false. Give each problem the kind that fits it.

List a problem only if you can actually see it in the picture:
- any religious element: temple, gopuram, church, mosque, shrine, deity, idol, prayer lamp,
  religious symbol, or religious marks or clothing on people
- a gender or social stereotype that is clearly shown: a girl or woman doing housework
  while a boy or man watches, or a girl or woman passive while a boy or man does the
  technical work, or height, strength or size shown by gender, such as boys always taller
  or stronger (never flag a stereotype that only "could" be read into the picture; a
  boy or man doing household work is intended and is never a stereotype)
- anything unsafe, violent, frightening or unsuitable for students
- anyone touching or reaching into a switchboard, open panel, socket or wire
- a brand name, logo, flag or political symbol
- a readable brand name, a recognisable real logo, or garbled or misspelt words (colourful
  generic packaging is fine; labels, bills or markings that the brief itself mentions are
  fine, and so are meter digits and dial scales)
- a sketch, drawing, chart, diagram or lab apparatus instead of a real-life moment
- a switched-on TV, phone or computer screen showing content
- lab instruments, test meters or circuit boards when the card should show an everyday thing
- a busy scene where extra devices or objects distract from the main object
- malformed hands, fingers, limbs or faces: extra or missing fingers, twisted or fused
  hands, distorted faces (look closely at every hand)
- the brief's main object or moment is missing, wrong or unclear, or drawn in a way that
  would teach something false
Do not judge artistic style."""


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

    def _claude(self):
        if not hasattr(self, "_anthropic"):
            self._anthropic = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    def _generate(self, prompt: str, p: SubjectProfile) -> Optional[bytes]:
        try:
            r = self._openai().images.generate(
                model=p.picture_model, prompt=prompt, size=p.picture_size,
                quality=p.picture_quality, n=1)
            return _shrink(base64.b64decode(r.data[0].b64_json))
        except Exception as e:
            print(f"         ⚠️  picture generation failed: {type(e).__name__}: {str(e)[:140]}")
            time.sleep(10)
            return None

    def _check(self, webp: bytes, card: Dict) -> List[str]:
        """Claude looks at the picture. Returns problems; [] means it passed."""
        text = CHECK_PROMPT.format(
            hook=card.get("hook", ""),
            focus=card.get("where_you_see_it") or card.get("beyond_school", ""),
            brief=card.get("picture", ""))
        for _ in range(2):
            try:
                resp = self._claude().messages.create(
                    model=settings.ANTHROPIC_MODEL, max_tokens=800,
                    tools=[CHECK_TOOL], tool_choice={"type": "tool", "name": "check_picture"},
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/webp",
                                                     "data": base64.b64encode(webp).decode()}},
                        {"type": "text", "text": text}]}])
                for b in resp.content:
                    if b.type == "tool_use":
                        return [f"{x['kind']}: {x.get('detail', '')}"
                                for x in (b.input.get("problems") or [])
                                if isinstance(x, dict) and x.get("kind") in PROBLEM_KINDS]
            except Exception as e:
                print(f"         ⚠️  picture check error: {type(e).__name__}: {str(e)[:120]}")
                time.sleep(5)
        return ["picture could not be checked"]   # fail closed

    def one(self, card: Dict, p: SubjectProfile) -> Optional[bytes]:
        """Generate -> check -> regenerate once with the problems named -> else no picture."""
        prompt = _prompt(card["picture"], p)
        cached = CACHE_DIR / f"{_cache_key(prompt, p)}.webp"
        if cached.exists():
            return cached.read_bytes()
        avoid: List[str] = []
        for attempt in range(1, ATTEMPTS + 1):
            full = prompt if not avoid else f"{prompt} {' '.join(_fixes(avoid))}"
            webp = self._generate(full, p)
            if webp is None:
                continue
            problems = self._check(webp, card)
            if not problems:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(webp)
                return webp
            print(f"         🚫 day {card.get('day')} picture rejected (try {attempt}): "
                  f"{'; '.join(problems)[:220]}")
            avoid = problems
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
            futures = {ex.submit(self.one, c, p): c for c in jobs}
            for fut in as_completed(futures):
                c, webp = futures[fut], fut.result()
                if webp:
                    c["image"] = "data:image/webp;base64," + base64.b64encode(webp).decode()
                    made += 1
                else:
                    c.setdefault("warnings", []).append("no picture — failed generation or the picture check")
        print(f"   🖼  {made}/{len(jobs)} pictures ready in {time.time() - t:.0f}s")
        deck["pictures"] = {"model": p.picture_model, "made": made, "wanted": len(jobs)}
        return deck


picture_maker = PictureMaker()