"""ایموجی پرمیوم (custom emoji) برای Hopper.

ایموجی معمولی → custom_emoji_id. سه منبع داره (به ترتیب اولویت):
  1) نقشه‌ی دستی `emoji_map.json` (با /pack و /map ساخته می‌شه)
  2) SEED: چند id ثابت که توی کد هست (مثل ❌)
  3) ALIASES: برای ایموجی‌هایی که توی پک نیستن، یه ایموجی مشابه از پک جایگزین می‌شه

- متن پیام‌ها: هر ایموجی که معادل پرمیوم داشته باشه خودکار با <tg-emoji> عوض می‌شه.
- دکمه‌ها: اولین کلمه‌ی متن دکمه اگه ایموجی باشه، به آیکن پرمیوم دکمه تبدیل می‌شه.

طبق مستندات تلگرام، صاحب ربات باید Premium داشته باشه (یا ربات یوزرنیم اضافه از Fragment خریده باشه).
"""
import json
import logging
import os
import re
from pathlib import Path

log = logging.getLogger("recon-bot.premium")
PATH = os.environ.get("EMOJI_MAP", str(Path(__file__).with_name("emoji_map.json")))
MAX_ENTITIES = 90  # تلگرام حداکثر ~100 entity برای هر پیام قبول می‌کنه

# id هایی که مطمئنیم؛ کمترین اولویت بعد از نقشه‌ی دستی
SEED = {
    "❌": "5019523782004441717",
}

# اجباری: بالاتر از نقشه‌ی دستی و همه‌ی منابع دیگه
FORCE = {
    "\U0001F1EE\U0001F1F7": "4911689862010111583",  # پرچم ایران 🇮🇷 → 👑
}

# ایموجی رابط ← ایموجی مشابه که توی پک‌های Fluent هست (فقط وقتی خودش توی نقشه نباشه)
ALIASES = {
    "🌐": "📍", "🌍": "🔭", "🔌": "🔧", "⚡": "📈", "⏰": "📅", "🧾": "📋", "🧩": "🗂", "ℹ": "📖",
    "🎯": "🏹", "🔄": "⚙", "🔁": "🪃", "↩": "🪃", "🏠": "🚪", "✖": "❌", "🚫": "❌", "👻": "🔬",
    "🕒": "📆", "🧭": "📐", "🗺": "📌", "🏛": "💼", "🏢": "💼", "🔢": "🏷", "🖥": "🗄", "🧱": "🧰",
    "⚠": "🪧", "⏳": "⚙", "➕": "✨", "📇": "📁", "👤": "🎫", "🐢": "📉", "⚫": "❌", "⚪": "⚙",
}

_map: dict[str, str] = {}   # فقط موارد دستی/پک (روی دیسک ذخیره می‌شه)
_eff: dict[str, str] = {}   # نقشه‌ی نهایی = دستی + SEED + ALIASES
_rev: dict[str, str] = {}
_re: re.Pattern | None = None
_TAG = re.compile(r"(<[^>]*>)")
_EMO = re.compile(
    "[\U0001F1E6-\U0001F1FF]{2}|[\U0001F300-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF\u2139\u21A9\u203C\u2049]\ufe0f?"
)
ENABLED = False


def _norm(e: str) -> str:
    return e.replace("\ufe0f", "")


def _rebuild() -> None:
    global _re, _rev, _eff, ENABLED
    _eff = dict(_map)
    for k, v in SEED.items():
        _eff.setdefault(_norm(k), v)
    for ui, src in ALIASES.items():
        ui, src = _norm(ui), _norm(src)
        if ui not in _eff and src in _eff:
            _eff[ui] = _eff[src]
    _eff.update({_norm(k): v for k, v in FORCE.items()})
    _rev = {}
    for k, v in _eff.items():
        _rev.setdefault(v, k)
    keys = sorted(_eff, key=len, reverse=True)
    _re = re.compile("(?:" + "|".join(re.escape(k) for k in keys) + ")\ufe0f?") if keys else None
    ENABLED = bool(_eff) and os.environ.get("PREMIUM_EMOJI", "1") != "0"


def load() -> int:
    global _map
    try:
        with open(PATH, encoding="utf-8") as f:
            _map = {_norm(k): str(v) for k, v in json.load(f).items()}
    except FileNotFoundError:
        _map = {}
    except (OSError, ValueError, AttributeError):
        log.exception("could not read %s", PATH)
        _map = {}
    _rebuild()
    return len(_map)


def _save() -> None:
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_map, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PATH)


def set_many(pairs: dict[str, str], overwrite: bool = False) -> int:
    """جفت‌های ایموجی→id رو اضافه می‌کنه؛ تعداد موارد جدید یا تغییرکرده رو برمی‌گردونه."""
    changed = 0
    for k, v in pairs.items():
        k, v = _norm(k or ""), str(v or "")
        if not k or k.isascii() or not v.isdigit():
            continue
        if k in _map and not overwrite:
            continue
        if _map.get(k) != v:
            changed += 1
        _map[k] = v
    _rebuild()
    _save()
    return changed


def count() -> int:
    return len(_map)


def effective_count() -> int:
    return len(_eff)


def emoji_of(custom_id: str) -> str:
    return _rev.get(custom_id, "")


def ui_emojis() -> set[str]:
    """همه‌ی ایموجی‌هایی که خود ربات توی کدش (bot.py و i18n.py) استفاده می‌کنه."""
    found: set[str] = set()
    for name in ("bot.py", "i18n.py"):
        try:
            text = Path(__file__).with_name(name).read_text(encoding="utf-8")
        except OSError:
            continue
        found |= {_norm(m.group(0)) for m in _EMO.finditer(text)}
    return found


def missing() -> list[str]:
    """ایموجی‌های رابط که هنوز معادل پرمیوم ندارن (هنوز معمولی نشون داده می‌شن)."""
    return sorted(e for e in ui_emojis() if e not in _eff)


def split_icon(text: str):
    """اگه اولین کلمه‌ی متن دکمه ایموجی بود -> (id, باقی متن) وگرنه (None, text)."""
    if not ENABLED:
        return None, text
    first, _sep, rest = text.partition(" ")
    cid = _eff.get(_norm(first))
    return (cid, rest) if cid and rest else (None, text)


def premiumize(html: str) -> tuple[str, int]:
    """ایموجی‌های متن HTML رو با <tg-emoji> عوض می‌کنه (بیرون از code/pre)."""
    if not ENABLED or _re is None or "<tg-emoji" in html:
        return html, 0
    budget = MAX_ENTITIES - len(re.findall(r"<(?!/)[a-zA-Z]", html))
    if budget <= 0:
        return html, 0
    used = 0
    in_code = 0
    out = []

    def sub(m):
        nonlocal used
        cid = _eff.get(_norm(m.group(0)))
        if not cid or used >= budget:
            return m.group(0)
        used += 1
        return f'<tg-emoji emoji-id="{cid}">{m.group(0)}</tg-emoji>'

    for part in _TAG.split(html):
        if part.startswith("<"):
            low = part.lower()
            if low.startswith(("<code", "<pre")):
                in_code += 1
            elif low.startswith(("</code", "</pre")):
                in_code = max(0, in_code - 1)
            out.append(part)
        else:
            out.append(part if in_code else _re.sub(sub, part))
    return "".join(out), used


load()
