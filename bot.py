"""Hopper - ربات recon غیرفعال با منوی دکمه‌ای رنگی (aiogram 3)

اجرا:
    pip install -r requirements.txt
    export BOT_TOKEN="توکن از BotFather"
    python bot.py

نکته: رنگ دکمه‌ها (style) فقط در نسخه‌های جدید تلگرام (بعد از فوریه ۲۰۲۶) دیده می‌شود.
"""
import asyncio
import base64
import ipaddress
import json
import logging
import os
import re
import socket
import sqlite3
import ssl
import statistics
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import httpx
from cryptography import x509
from cryptography.x509.oid import NameOID
from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import EditMessageText, SendMessage, SendPhoto
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import premium
from i18n import LANG, tr

router = Router()
http = httpx.AsyncClient(timeout=15, headers={"User-Agent": "recon-bot/0.1"})
COOLDOWN = 3  # ثانیه بین دو درخواست هر کاربر
PORT_LIMIT = 15  # تعداد چک پورت مجاز برای هر کاربر در ساعت
_last: dict[int, float] = {}


class NotPublic(ValueError):
    pass


class Wait(StatesGroup):
    ip = State()
    dns = State()
    subs = State()
    hdr = State()
    whois = State()
    ssl = State()
    port_target = State()
    port_custom = State()
    ping = State()
    iran = State()
    mon_add = State()
    cping = State()
    exp_add = State()
    ss = State()
    reality = State()
    cfg = State()
    asn = State()
    email = State()
    http = State()
    dnsir = State()


SIMPLE = (Wait.ip, Wait.dns, Wait.subs, Wait.hdr, Wait.whois, Wait.ssl, Wait.ping, Wait.iran, Wait.ss,
          Wait.reality, Wait.cfg, Wait.asn, Wait.email, Wait.http, Wait.dnsir)

RLM = "\u200f"
_FA = re.compile(r"[\u0600-\u06FF]")


def rtl(text: str) -> str:
    """هر خطی که حروف فارسی داره راست‌به‌چپ می‌شه تا پرانتز و عدد و متن لاتین جا‌به‌جا نشن."""
    if LANG.get() != "fa":
        return text
    return "\n".join((RLM + ln if _FA.search(ln) else ln) for ln in text.split("\n"))


# ───────────── دکمه‌ها ─────────────
def btn(text: str, data: str | None, style: str | None = None, url: str | None = None) -> InlineKeyboardButton:
    # style: "primary" آبی | "success" سبز | "danger" قرمز | None پیش‌فرض
    icon, text = premium.split_icon(text)  # ایموجی پرمیوم به‌جای ایموجی اول دکمه
    kw = {"callback_data": data} if url is None else {"url": url}
    if icon:
        kw["icon_custom_emoji_id"] = icon
    return InlineKeyboardButton(text=text, style=style, **kw)


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn(tr("🖧 ابزارهای سرور و VPN"), "m:cat:vpn", "primary")],
        [btn(tr("🌍 ابزارهای وب و دامنه"), "m:cat:web", "success")],
        [btn(tr("ℹ️ راهنما"), "m:help"), btn("🌐 زبان / Language", "lg:ask")],  # noi18n
    ])


def cat_kb(cat: str) -> InlineKeyboardMarkup:
    if cat == "vpn":
        rows = [
            [btn(tr("🌐 اطلاعات IP"), "m:ip", "primary"), btn(tr("🔌 چک پورت"), "m:port", "success")],
            [btn(tr("🇮🇷 چک از ایران"), "m:iran", "success"), btn(tr("🏓 پینگ جهانی"), "m:cping", "success")],
            [btn(tr("⚡ تاخیر TCP"), "m:ping", "primary"), btn(tr("📡 مانیتور"), "m:mon", "success")],
            [btn(tr("🧾 تحلیل ss"), "m:ss", "primary"), btn(tr("🎭 چک Reality"), "m:reality", "primary")],
            [btn(tr("🔗 تحلیل لینک کانفیگ"), "m:cfg", "primary"), btn(tr("🕸 تحلیل ASN"), "m:asn", "primary")],
        ]
    else:
        rows = [
            [btn(tr("🔎 DNS دامنه"), "m:dns", "primary"), btn(tr("🧭 DNS از ایران"), "m:dnsir", "success")],
            [btn(tr("🧩 ساب\u200cدامین\u200cها"), "m:subs", "primary"), btn("📇 Whois", "m:whois", "primary")],
            [btn("🔐 SSL Info", "m:ssl", "primary"), btn(tr("🛡 هدرهای امنیتی"), "m:hdr", "primary")],
            [btn(tr("🧪 بازرس HTTP"), "m:http", "success"), btn(tr("✉️ چک ایمیل"), "m:email", "primary")],
            [btn(tr("⏰ هشدار انقضا"), "m:exp", "success")],
        ]
    rows.append([btn(tr("🏠 منوی اصلی"), "m:home", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def port_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn(tr("✅ پورت\u200cهای رایج تانل"), "p:common", "success"), btn(tr("🎯 پورت دلخواه"), "p:custom", "primary")],
        [btn(tr("📋 دستور چک روی سرور"), "p:cmd"), btn(tr("🔄 هدف جدید"), "m:port")],
        [btn(tr("🏠 منوی اصلی"), "m:home", "danger")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[btn(tr("✖️ انصراف"), "m:home", "danger")]])


def home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[btn(tr("🏠 منوی اصلی"), "m:home", "primary")]])


def welcome_text() -> str:
    return tr("👻 <b>Hopper</b>\nیه دسته انتخاب کن:")


def help_text() -> str:
    return (
        tr("ℹ️ <b>راهنما</b>\nبیشتر ابزارها فقط از منابع عمومی (Shodan InternetDB، Cloudflare DoH، CT logs، check-host و ...) داده می\u200cگیرن. چک پورت، تاخیر TCP و مانیتور یه اتصال TCP ساده به سرور برقرار می\u200cکنن، پس فقط روی سرور خودت ازشون استفاده کن.")
    )


def prompt_text(kind: str) -> str:
    return {
        "reality": tr("🎭 دامنه‌ای که می‌خوای توی Reality به‌عنوان <code>dest</code> استفاده کنی رو بفرست (مثلاً <code>www.microsoft.com</code>).\nTLS 1.3 و HTTP/2 و گواهی و تاخیر بررسی می‌شن."),
        "cfg": tr("🔗 لینک کانفیگ (<code>vless://</code> یا <code>vmess://</code> یا <code>trojan://</code> یا <code>ss://</code>) رو بفرست.\n<i>لینک شامل کلید شماست؛ ربات ذخیره‌ش نمی‌کنه و جایی نمی‌فرسته.</i>"),
        "asn": tr("🕸 شماره‌ی ASN (مثل <code>AS13335</code>) یا یه آی‌پی یا دامنه بفرست تا گراف همسایه‌های BGP‌ش رو بکشم."),
        "email": tr("✉️ دامنه رو بفرست تا SPF و DKIM و DMARC بررسی بشه (مثلاً <code>example.com</code>)"),
        "http": tr("🧪 آدرس سایت رو بفرست (مثلاً <code>https://example.com</code>)"),
        "dnsir": tr("🧭 دامنه رو بفرست تا جواب DNS از نودهای ایران و خارج مقایسه بشه."),
        "ip": tr("🌐 هر آی\u200cپی رو بفرست: IPv4 یا IPv6، عمومی یا خصوصی\n(مثلاً <code>8.8.8.8</code> یا <code>2606:4700:4700::1111</code>)"),
        "dns": tr("🔎 دامنه رو بفرست (مثلاً <code>example.com</code>)"),
        "subs": tr("🧩 دامنه\u200cی اصلی رو بفرست تا ساب\u200cدامین\u200cهاش پیدا بشه"),
        "hdr": tr("🛡 دامنه رو بفرست تا هدرهای امنیتی\u200cش بررسی بشه"),
        "whois": tr("📇 دامنه یا آی\u200cپی عمومی رو بفرست (مثلاً <code>example.com</code>)"),
        "ssl": tr("🔐 دامنه رو بفرست (مثلاً <code>example.com</code> یا با پورت: <code>example.com:8443</code>)"),
        "ping": (
            tr("⚡ سرور رو به شکل <code>host:port</code> بفرست. اگه پورت ننویسی 443 در نظر گرفته می\u200cشه.\nبرای مقایسه تا ۵ سرور رو با فاصله یا خط جدید بفرست.\nمثال: <code>1.2.3.4:443 5.6.7.8:8443</code>")
        ),
        "ss": (
            tr("🧾 این دستور رو روی سرورت بزن (ترجیحاً با root) و خروجی\u200cش رو همین\u200cجا paste کن:\n<pre>ss -tulpn</pre>پورت\u200cهای در حال استفاده، برنامه\u200cی پشتشون، پورت\u200cهای فقط داخلی و پورت\u200cهای آزاد پیشنهادی رو بهت می\u200cگم.")
        ),
        "iran": (
            tr("🇮🇷 آی\u200cپی یا دامنه\u200cی سرورت رو به شکل <code>host:port</code> بفرست (پیش\u200cفرض پورت 443).\nدسترسی از چند نود داخل ایران و چند نود شاهد خارج از ایران چک می\u200cشه تا بفهمی سرور فیلتر شده یا نه.")
        ),
    }[kind]


def port_prompt() -> str:
    return (
        tr("🔌 <b>چک پورت</b>\nآی\u200cپی یا دامنه\u200cی <b>سرور خودت</b> رو بفرست.\n\n<i>فقط برای بررسی سرورهای خودت استفاده کن؛ برای هر کاربر ساعتی {0} چک مجازه.</i>", PORT_LIMIT)
    )


# ───────────── اعتبارسنجی ورودی ─────────────
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$")


def clean_domain(text: str) -> str:
    d = re.sub(r"^https?://", "", text.strip().lower()).split("/")[0]
    if not DOMAIN_RE.match(d):
        raise ValueError(tr("دامنه معتبر نیست"))
    return d


async def assert_public(domain: str) -> None:
    """جلوگیری از SSRF: دامنه نباید به IP داخلی/خصوصی resolve بشه."""
    infos = await asyncio.get_running_loop().getaddrinfo(domain, 443)
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError(tr("این دامنه به آدرس غیرعمومی اشاره می\u200cکنه"))
    # توجه: DNS rebinding هنوز تئوریه؛ برای نسخه‌ی جدی‌تر به IP پین‌شده وصل شو.


# ───────────── ابزارها ─────────────
async def _doh(name: str, rtype: str) -> list[str]:
    r = await http.get(
        "https://cloudflare-dns.com/dns-query",
        params={"name": name, "type": rtype},
        headers={"accept": "application/dns-json"},
    )
    r.raise_for_status()
    return [a["data"] for a in r.json().get("Answer", [])]


CGNAT = ipaddress.ip_network("100.64.0.0/10")

def kind_info(kind: str):
    return {
        "loopback": ("Loopback", tr("آدرس خود دستگاه (localhost). از بیرون قابل دسترس نیست.")),
        "link_local": ("Link-local", tr("آدرس خودکار داخل یک شبکه\u200cی محلی؛ وقتی DHCP جواب نداده یا برای ارتباط مستقیم دو دستگاه.")),
        "multicast": ("Multicast", tr("آدرس گروهی؛ یک بسته برای چند گیرنده فرستاده می\u200cشه.")),
        "unspecified": ("Unspecified", tr("آدرس نامشخص (0.0.0.0 یا ::)؛ یعنی «همه\u200cی اینترفیس\u200cها» یا «هنوز آدرس ندارم».")),
        "cgnat": ("CGNAT (Shared)", tr("رنج 100.64.0.0/10 که اپراتورها برای NAT چندلایه استفاده می\u200cکنن؛ چند مشترک یک IP عمومی مشترک دارن.")),
        "private": ("Private", tr("آدرس شبکه\u200cی داخلی (مثل 10.x یا 192.168.x یا 172.16-31.x)؛ روی اینترنت route نمی\u200cشه.")),
        "reserved": ("Reserved", tr("رنج رزروشده؛ برای مستندات، تست یا استفاده\u200cی آینده.")),
    }[kind]


def parse_ip(text: str):
    t = text.strip()
    m = re.match(r"^\[(.+)\](?::\d+)?$", t)  # [::1]:80
    if m:
        t = m.group(1)
    elif t.count(":") == 1:  # 1.2.3.4:443
        t = t.split(":")[0]
    try:
        ip = ipaddress.ip_address(t)
    except ValueError:
        raise ValueError(tr("آی\u200cپی معتبر نیست"))
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return ip


def classify(ip) -> str | None:
    """برای آی‌پی غیرعمومی نوعش رو برمی‌گردونه، برای عمومی None."""
    if ip.is_unspecified:
        return "unspecified"
    if ip.is_loopback:
        return "loopback"
    if ip.is_link_local:
        return "link_local"
    if ip.is_multicast:
        return "multicast"
    if ip.version == 4 and ip in CGNAT:
        return "cgnat"
    if ip.is_private:
        return "private"
    if not ip.is_global:
        return "reserved"
    return None


async def _geo(ip) -> dict:
    r = await http.get(f"https://ipwho.is/{ip}")
    r.raise_for_status()
    d = r.json()
    if not d.get("success", False):
        raise ValueError(d.get("message", "lookup failed"))
    return d


async def _idb(ip) -> dict:
    r = await http.get(f"https://internetdb.shodan.io/{ip}")
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


async def _ptr(ip) -> list[str]:
    return await _doh(ip.reverse_pointer, "PTR")


async def tool_ip(text: str):
    ip = parse_ip(text)
    ver = f"IPv{ip.version}"

    kind = classify(ip)
    if kind:
        name, desc = kind_info(kind)
        return (
            tr("🌐 <b>{0}</b> · {1}\n\n📦 نوع: <b>{2}</b>\n📝 {3}\n\nℹ️ آدرس عمومی نیست، پس موقعیت جغرافیایی و ISP نداره.", escape(str(ip)), ver, name, desc)
        )

    geo, idb, ptr = await asyncio.gather(_geo(ip), _idb(ip), _ptr(ip), return_exceptions=True)
    geo = geo if isinstance(geo, dict) else {}
    idb = idb if isinstance(idb, dict) else {}
    ptr = ptr if isinstance(ptr, list) else []
    if not geo and not idb:
        raise httpx.HTTPError("no data")

    e = escape
    flag = geo.get("flag", {}).get("emoji", "")
    conn = geo.get("connection", {})
    tz = geo.get("timezone", {})
    lines = [f"🌐 <b>{e(str(ip))}</b> · {ver} · Public\n"]

    if geo:
        lines += [
            tr("{0} کشور: <b>{1}</b> · {2}", flag, e(str(geo.get('country', '—'))), e(str(geo.get('country_code', '—')))),
            tr("🗺 قاره: {0}", e(str(geo.get('continent', '—')))),
            tr("📍 منطقه: {0} / {1}", e(str(geo.get('region', '—'))), e(str(geo.get('city', '—'))))
            + (f" · {e(str(geo['postal']))}" if geo.get("postal") else ""),
            tr("🧭 مختصات: <code>{0}, {1}</code>", geo.get('latitude'), geo.get('longitude')),
            tr("🕒 زمان: {0} · UTC{1}", e(str(tz.get('id', '—'))), e(str(tz.get('utc', '')))),
            "",
            f"🏢 ISP: {e(str(conn.get('isp') or '—'))}",
            tr("🏛 سازمان: {0}", e(str(conn.get('org') or '—'))),
            f"🔢 ASN: <code>AS{conn.get('asn', '—')}</code>"
            + (f" · {e(conn['domain'])}" if conn.get("domain") else ""),
        ]
    lines.append(f"🔁 Reverse DNS: <code>{e(ptr[0].rstrip('.')) if ptr else '—'}</code>")

    if idb:
        ports = ", ".join(map(str, idb.get("ports", []))) or "—"
        vulns = idb.get("vulns", [])
        vtxt = ", ".join(e(v) for v in vulns[:10]) + (tr(" و {0} مورد دیگر", len(vulns) - 10) if len(vulns) > 10 else "")
        hosts = ", ".join(e(h) for h in idb.get("hostnames", [])[:5]) or "—"
        lines += [
            "",
            tr("🔓 پورت\u200cهای باز: <code>{0}</code>", ports),
            tr("🏷 تگ\u200cها: {0}", e(', '.join(idb.get('tags', [])) or '—')),
            tr("🖥 هاست\u200cنیم\u200cها: {0}", hosts),
            tr("⚠️ آسیب\u200cپذیری\u200cها: {0}", vtxt or '—'),
        ]
    else:
        lines += ["", tr("🔓 در Shodan InternetDB چیزی برای این آی\u200cپی ثبت نشده.")]

    lines.append(tr("\n<i>موقعیت جغرافیایی تقریبیه در حد شهر یا منطقه و ممکنه دقیق نباشه.</i>"))

    extra = []
    if geo.get("latitude") is not None:
        la, lo = geo["latitude"], geo["longitude"]
        extra.append([btn(
            tr("📍 نمایش روی نقشه"), None,
            url=f"https://www.openstreetmap.org/?mlat={la}&mlon={lo}#map=10/{la}/{lo}",
        )])
    return "\n".join(lines), extra


async def tool_dns(text: str) -> str:
    d = clean_domain(text)
    types = ["A", "AAAA", "MX", "NS", "TXT"]
    res = await asyncio.gather(*[_doh(d, t) for t in types])
    out = [f"🔎 <b>{escape(d)}</b>\n"]
    for t, rows in zip(types, res):
        body = "\n".join(f"  <code>{escape(x[:150])}</code>" for x in rows[:8]) or "  —"
        out.append(f"<b>{t}</b>\n{body}")
    return "\n".join(out)


def _clean_names(raw, d: str) -> set[str]:
    out = set()
    for n in raw:
        n = str(n).strip().lower().lstrip("*.").rstrip(".")
        if re.fullmatch(r"[a-z0-9_.-]+", n) and (n == d or n.endswith("." + d)):
            out.add(n)
    return out


async def _src_crtsh(d: str) -> set[str]:
    r = await http.get("https://crt.sh/", params={"q": f"%.{d}", "output": "json"}, timeout=25)
    r.raise_for_status()
    return _clean_names((x for row in r.json() for x in row.get("name_value", "").splitlines()), d)


async def _src_certspotter(d: str) -> set[str]:
    r = await http.get(
        "https://api.certspotter.com/v1/issuances",
        params={"domain": d, "include_subdomains": "true", "expand": "dns_names"}, timeout=25,
    )
    r.raise_for_status()
    return _clean_names((x for row in r.json() for x in row.get("dns_names", [])), d)


async def _src_anubis(d: str) -> set[str]:
    r = await http.get(f"https://jldc.me/anubis/subdomains/{d}", timeout=25)
    r.raise_for_status()
    return _clean_names(r.json(), d)


async def _src_otx(d: str) -> set[str]:
    r = await http.get(f"https://otx.alienvault.com/api/v1/indicators/domain/{d}/passive_dns", timeout=25)
    r.raise_for_status()
    return _clean_names((x.get("hostname", "") for x in r.json().get("passive_dns", [])), d)


async def _src_hackertarget(d: str) -> set[str]:
    r = await http.get("https://api.hackertarget.com/hostsearch/", params={"q": d}, timeout=25)
    r.raise_for_status()
    txt = r.text
    if txt.lower().startswith("error") or "exceeded" in txt.lower()[:100]:
        raise ValueError("quota")
    return _clean_names((ln.split(",")[0] for ln in txt.splitlines()), d)


SUB_SOURCES = (
    ("crt.sh", _src_crtsh), ("CertSpotter", _src_certspotter), ("AnubisDB", _src_anubis),
    ("OTX", _src_otx), ("HackerTarget", _src_hackertarget),
)


async def tool_subs(text: str):
    d = clean_domain(text)
    results = await asyncio.gather(
        *[asyncio.wait_for(fn(d), 30) for _n, fn in SUB_SOURCES], return_exceptions=True
    )
    names: set[str] = set()
    ok, bad = [], []
    for (name, _fn), res in zip(SUB_SOURCES, results):
        if isinstance(res, Exception):
            bad.append(name)
        else:
            ok.append(name)
            names |= res
    if not ok:
        raise ValueError(tr("همه\u200cی منابع جواب ندادن؛ چند دقیقه بعد دوباره امتحان کن."))
    src = tr("منابع: {0}", ', '.join(ok)) + (tr(" · ناموفق: {0}", ', '.join(bad)) if bad else "")
    if not names:
        return tr("ℹ️ ساب\u200cدامینی برای <code>{0}</code> پیدا نشد.\n<i>{1}</i>", escape(d), src)
    ordered = sorted(names)
    lines = "\n".join(f"• <code>{escape(n)}</code>" for n in ordered[:40])
    head = tr("🧩 <b>{0}</b> ساب\u200cدامین برای <b>{1}</b>\n\n{2}", len(names), escape(d), lines)
    if len(ordered) <= 40:
        return f"{head}\n\n<i>{src}</i>"
    more = tr("\n… و {0} مورد دیگر؛ لیست کامل توی فایل پایین هست.", len(ordered) - 40)
    return f"{head}{more}\n\n<i>{src}</i>", [], ("doc", "\n".join(ordered).encode(), f"{d}-subdomains.txt")


SEC_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]


async def tool_hdr(text: str) -> str:
    d = clean_domain(text)
    await assert_public(d)
    r = await http.get(f"https://{d}", follow_redirects=False, timeout=10)
    h = {k.lower(): v for k, v in r.headers.items()}
    lines, ok = [], 0
    for name in SEC_HEADERS:
        if name in h:
            ok += 1
            lines.append(f"✅ {name}")
        else:
            lines.append(f"❌ {name}")
    server = escape(h.get("server", "—")[:80])
    return (
        f"🛡 <b>{escape(d)}</b> · HTTP {r.status_code}\n\n" + "\n".join(lines)
        + tr("\n\n📊 نمره: <b>{0}/{1}</b>\n🖥 Server: <code>{2}</code>", ok, len(SEC_HEADERS), server)
    )


# ───────────── Whois (RDAP) ─────────────
def _d(dt) -> str:
    return dt.strftime("%Y-%m-%d") if dt else "—"


def _days_left(dt) -> str:
    if not dt:
        return ""
    n = (dt - datetime.now(timezone.utc)).days
    return tr(" · {0} روز مانده", n) if n >= 0 else tr(" · ⚠️ {0} روز پیش منقضی شده", -n)


def _parse_date(v: str):
    v = (v or "").strip()
    m = re.search(r"(\d{4})[-/.](\d{2})[-/.](\d{2})", v)
    try:
        if m:
            return datetime(int(m[1]), int(m[2]), int(m[3]), tzinfo=timezone.utc)
        m = re.search(r"(\d{1,2})[- ]([A-Za-z]{3})[a-z]*[- ](\d{4})", v)
        if m:
            return datetime.strptime(f"{m[1]} {m[2].title()} {m[3]}", "%d %b %Y").replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    return None


_whois_servers: dict[str, str] = {}


async def whois_raw(server: str, query: str) -> str:
    infos = await asyncio.get_running_loop().getaddrinfo(server, 43, type=socket.SOCK_STREAM)
    ips = [i[4][0] for i in infos]
    if not ips or any(not ipaddress.ip_address(x).is_global for x in ips):
        raise ValueError("whois server is not public")
    r, w = await asyncio.wait_for(asyncio.open_connection(ips[0], 43), 8)
    data = b""
    try:
        w.write((query + "\r\n").encode())
        await w.drain()
        while len(data) < 200_000:
            chunk = await asyncio.wait_for(r.read(4096), 8)
            if not chunk:
                break
            data += chunk
    finally:
        w.close()
    return data.decode("utf-8", "replace")


async def whois_server_for(tld: str) -> str:
    if tld not in _whois_servers:
        txt = await whois_raw("whois.iana.org", tld)
        m = re.search(r"(?im)^whois:\s*(\S+)", txt) or re.search(r"(?im)^refer:\s*(\S+)", txt)
        if not m or not re.fullmatch(r"[a-zA-Z0-9.-]+", m.group(1)):
            raise ValueError("no whois server")
        _whois_servers[tld] = m.group(1).lower()
    return _whois_servers[tld]


def parse_whois(text: str) -> dict:
    out = {"created": None, "updated": None, "expires": None, "registrar": None, "ns": [], "status": []}
    for line in text.splitlines():
        if ":" not in line or line.lstrip().startswith(("%", "#", ">")):
            continue
        key, _sep, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if not val:
            continue
        if re.search(r"expir|paid-till|renewal", key):
            out["expires"] = out["expires"] or _parse_date(val)
        elif re.search(r"creat|registered on|registration date", key):
            out["created"] = out["created"] or _parse_date(val)
        elif re.search(r"updated|last-updated|last modified|changed", key):
            out["updated"] = out["updated"] or _parse_date(val)
        elif key in ("registrar", "sponsoring registrar"):
            out["registrar"] = out["registrar"] or val
        elif key in ("name server", "nserver", "nameserver"):
            out["ns"].append(val.split()[0].lower())
        elif key in ("domain status", "status"):
            out["status"].append(val.split()[0])
    return out


async def domain_data(dom: str) -> dict:
    """اول RDAP، اگه نبود یا خطا داد WHOIS مستقیم (پورت 43)."""
    try:
        r = await http.get(f"https://rdap.org/domain/{dom}", follow_redirects=True, timeout=12)
        if r.status_code == 200:
            d = r.json()
            ev = {x.get("eventAction"): x.get("eventDate") for x in d.get("events", [])}
            registrar = None
            for ent in d.get("entities", []):
                if "registrar" in ent.get("roles", []):
                    for item in (ent.get("vcardArray") or [None, []])[1]:
                        if item[0] == "fn":
                            registrar = item[3]
            return {
                "source": "RDAP", "created": _parse_date(ev.get("registration")),
                "updated": _parse_date(ev.get("last changed")), "expires": _parse_date(ev.get("expiration")),
                "registrar": registrar, "ns": [n.get("ldhName", "").lower() for n in d.get("nameservers", [])],
                "status": d.get("status", []),
            }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        pass
    try:
        server = await whois_server_for(dom.rsplit(".", 1)[1])
        data = parse_whois(await whois_raw(server, dom))
    except (OSError, asyncio.TimeoutError, ValueError, IndexError):
        data = None
    if not data or not any([data["expires"], data["created"], data["registrar"], data["ns"]]):
        raise ValueError(tr("اطلاعات Whois این دامنه از هیچ منبعی در دسترس نبود."))
    data["source"] = "WHOIS"
    return data


async def tool_whois(text: str) -> str:
    e = escape
    try:
        ip = parse_ip(text)
    except ValueError:
        ip = None

    if ip is not None:
        if classify(ip):
            raise ValueError(tr("برای آی\u200cپی غیرعمومی Whois وجود نداره"))
        r = await http.get(f"https://rdap.org/ip/{ip}", follow_redirects=True)
        if r.status_code == 404:
            raise ValueError(tr("اطلاعاتی برای این آی\u200cپی پیدا نشد"))
        r.raise_for_status()
        d = r.json()
        cidrs = ", ".join(
            f"{c.get('v4prefix') or c.get('v6prefix')}/{c.get('length')}" for c in d.get("cidr0_cidrs", [])
        ) or "—"
        return (
            tr("📇 <b>Whois {0}</b>\n\n🏷 نام شبکه: <code>{1}</code>\n🔖 Handle: <code>{2}</code>\n🌍 کشور: {3}\n📦 رنج: <code>{4} - {5}</code>\n🧱 CIDR: <code>{6}</code>\n📌 نوع: {7}", e(str(ip)), e(str(d.get('name', '—'))), e(str(d.get('handle', '—'))), e(str(d.get('country', '—'))), e(str(d.get('startAddress', '—'))), e(str(d.get('endAddress', '—'))), e(cidrs), e(str(d.get('type', '—'))))
        )

    dom = clean_domain(text)
    dd = await domain_data(dom)
    ns = ", ".join(e(n) for n in dd["ns"][:6]) or "—"
    status = ", ".join(e(s) for s in dd["status"][:5]) or "—"
    return (
        tr("📇 <b>Whois {0}</b>\n\n📅 ثبت: {1}\n🔄 آخرین تغییر: {2}\n⏰ انقضا: {3}{4}\n🏷 رجیستار: {5}\n🌐 Name Servers: {6}\n📌 وضعیت: {7}\n<i>منبع: {8}</i>", e(dom), _d(dd['created']), _d(dd['updated']), _d(dd['expires']), _days_left(dd['expires']), e(str(dd['registrar'] or '—')), ns, status, dd['source'])
    )


# ───────────── SSL Info ─────────────
async def _tls(ip: str, port: int, sni: str, verify: bool):
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    r, w = await asyncio.wait_for(
        asyncio.open_connection(ip, port, ssl=ctx, server_hostname=sni), 8
    )
    obj = w.get_extra_info("ssl_object")
    out = (obj.getpeercert(binary_form=True), obj.version(), obj.cipher(), obj.selected_alpn_protocol())
    w.close()
    try:
        await w.wait_closed()
    except Exception:
        pass
    return out


def _attr(name: x509.Name, oid) -> str:
    a = name.get_attributes_for_oid(oid)
    return a[0].value if a else "—"


async def tool_ssl(text: str) -> str:
    e = escape
    host = re.sub(r"^https?://", "", text.strip().lower()).split("/")[0]
    port = 443
    m = re.match(r"^(.+):(\d{1,5})$", host)
    if m:
        host, port = m.group(1), int(m.group(2))
    if not 1 <= port <= 65535:
        raise ValueError(tr("پورت نامعتبره"))
    dom = clean_domain(host)
    _, ip = await resolve_target(dom)

    verdict = tr("✅ گواهی معتبر و مورد اعتماده")
    try:
        try:
            der, ver, cipher, alpn = await _tls(ip, port, dom, True)
        except ssl.SSLCertVerificationError as ex:
            verdict = f"❌ {e(ex.verify_message)}"
            der, ver, cipher, alpn = await _tls(ip, port, dom, False)
    except ssl.SSLError as ex:
        raise ValueError(tr("هندشیک TLS ناموفق بود: {0}", ex.reason or 'unknown'))
    except (OSError, asyncio.TimeoutError):
        raise ValueError(tr("اتصال TLS روی این پورت برقرار نشد"))

    cert = x509.load_der_x509_certificate(der)
    na, nb = cert.not_valid_after_utc, cert.not_valid_before_utc
    days = (na - datetime.now(timezone.utc)).days
    warn = tr(" ⚠️ منقضی شده!") if days < 0 else (tr(" ⚠️ کمتر از ۱۵ روز مونده") if days < 15 else "")
    try:
        sans = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        sans = []
    sans_txt = ", ".join(e(s) for s in sans[:8]) + (tr(" و {0} مورد دیگر", len(sans) - 8) if len(sans) > 8 else "")
    pub = cert.public_key()
    key = f"{type(pub).__name__.replace('PublicKey', '')} {getattr(pub, 'key_size', '')}".strip()
    sig = cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else "—"
    self_signed = cert.issuer == cert.subject
    return (
        f"🔐 <b>{e(dom)}:{port}</b>\n\n"
        f"{verdict}\n\n"
        f"👤 Subject: <code>{e(_attr(cert.subject, NameOID.COMMON_NAME))}</code>\n"
        f"🏛 Issuer: {e(_attr(cert.issuer, NameOID.ORGANIZATION_NAME))} / {e(_attr(cert.issuer, NameOID.COMMON_NAME))}"
        + (" · Self-signed" if self_signed else "") + tr("\n📅 از: {0:%Y-%m-%d}\n⏰ تا: {1:%Y-%m-%d} · {2} روز{3}\n🔑 کلید: {4} | امضا: {5}\n🔒 پروتکل: {6} | {7}\n📡 ALPN: {8}\n🌐 SAN: {9}", nb, na, days, warn, e(key), e(sig), e(str(ver)), e(str(cipher[0])), e(str(alpn or '—')), sans_txt or '—')
    )


# ───────────── چک پورت ─────────────
PORT_NAMES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP", 993: "IMAPS",
    1080: "SOCKS", 1194: "OpenVPN", 3128: "Squid Proxy", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8000: "Web panel (e.g. Marzban)", 8080: "HTTP-alt",
    8443: "HTTPS-alt", 8880: "HTTP-alt Cloudflare", 27017: "MongoDB",
    2052: "Cloudflare HTTP", 2053: "Cloudflare HTTPS", 2082: "Cloudflare HTTP", 2083: "Cloudflare HTTPS",
    2086: "Cloudflare HTTP", 2087: "Cloudflare HTTPS", 2095: "Cloudflare HTTP", 2096: "Cloudflare HTTPS",
    62050: "Marzban Node", 62051: "Marzban Node Xray API", 51820: "WireGuard UDP",
}
# پورت‌های پرکاربرد برای تانل و پروکسی
COMMON_PORTS = [22, 80, 443, 2052, 2053, 2082, 2083, 2086, 2087, 2095, 2096,
                8000, 8080, 8443, 8880, 1080, 3128, 10000, 20000, 30000]
_quota: dict[int, deque] = {}


def port_quota(uid: int) -> None:
    q = _quota.setdefault(uid, deque())
    now = time.monotonic()
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= PORT_LIMIT:
        raise ValueError(tr("سقف {0} چک پورت در ساعت پر شده؛ بعداً دوباره امتحان کن.", PORT_LIMIT))
    q.append(now)


async def resolve_target(text: str) -> tuple[str, str]:
    """ورودی آی‌پی یا دامنه؛ خروجی (نمایش، IP عمومی). از SSRF جلوگیری می‌کنه."""
    try:
        ip = parse_ip(text)
        if classify(ip):
            raise NotPublic(tr("فقط آی\u200cپی عمومی قابل بررسیه"))
        return str(ip), str(ip)
    except NotPublic:
        raise
    except ValueError:
        pass
    dom = clean_domain(text)
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(dom, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError(tr("دامنه resolve نشد"))
    ips = sorted({i[4][0] for i in infos}, key=lambda x: ":" in x)  # اول IPv4
    if not ips or any(not ipaddress.ip_address(i).is_global for i in ips):
        raise ValueError(tr("این دامنه به آدرس غیرعمومی اشاره می\u200cکنه"))
    return dom, ips[0]


def parse_ports(text: str) -> list[int]:
    ports: set[int] = set()
    try:
        for part in re.split(r"[,\s\u060c]+", text.strip()):
            if not part:
                continue
            if "-" in part:
                a, b = (int(x) for x in part.split("-", 1))
                if a > b or b - a >= 20:
                    raise ValueError
                ports.update(range(a, b + 1))
            else:
                ports.add(int(part))
    except ValueError:
        raise ValueError(tr("فرمت پورت نامعتبره. مثال: 443 یا 80,443,8443 یا 8000-8005"))
    if not ports or len(ports) > 20 or any(not 1 <= p <= 65535 for p in ports):
        raise ValueError(tr("بین ۱ تا ۲۰ پورت (۱ تا ۶۵۵۳۵) وارد کن."))
    return sorted(ports)


def identify(data: bytes) -> str:
    if data.startswith(b"SSH-"):
        return "SSH · " + data.split(b"\n")[0].decode(errors="replace").strip()[:60]
    if data.startswith(b"HTTP/"):
        srv = re.search(rb"(?im)^server:\s*(.+)$", data)
        return "HTTP" + (f" · {srv.group(1).decode(errors='replace').strip()[:40]}" if srv else "")
    if data[:2] in (b"\x15\x03", b"\x16\x03"):
        return tr("TLS/SSL (احتمالاً HTTPS یا پروکسی TLS)")
    if data.startswith(b"220"):
        return "FTP/SMTP · " + data.split(b"\n")[0].decode(errors="replace").strip()[:50]
    if not data:
        return tr("ساکت؛ چیزی نفرستاد (ممکنه پروکسی/تانل مثل VLESS، VMess، Trojan، SS باشه)")
    return tr("سرویس ناشناس")


async def probe(ip: str, port: int, timeout: float = 3.0) -> tuple[str, str]:
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
    except (asyncio.TimeoutError, TimeoutError):
        return "filtered", ""
    except ConnectionRefusedError:
        return "closed", ""
    except OSError:
        return "filtered", ""
    data = b""
    try:
        try:
            data = await asyncio.wait_for(r.read(200), 1.0)
        except (asyncio.TimeoutError, TimeoutError):
            w.write(b"HEAD / HTTP/1.0\r\nHost: check\r\n\r\n")
            await w.drain()
            data = await asyncio.wait_for(r.read(300), 1.5)
    except Exception:
        pass
    finally:
        w.close()
    return "open", identify(data)


async def scan(ip: str, ports: list[int]):
    sem = asyncio.Semaphore(10)

    async def one(p: int):
        async with sem:
            st, info = await probe(ip, p)
            return p, st, info

    return sorted(await asyncio.gather(*[one(p) for p in ports]))


def fmt_scan(shown: str, ip: str, res) -> str:
    e = escape

    def label(p):
        n = PORT_NAMES.get(p)
        return f"<code>{p}</code>" + (f" · {e(n)}" if n else "")

    opened = [(p, i) for p, s_, i in res if s_ == "open"]
    closed = [p for p, s_, _ in res if s_ == "closed"]
    filt = [p for p, s_, _ in res if s_ == "filtered"]
    out = [f"🔌 <b>{e(shown)}</b>" + (f" · <code>{ip}</code>" if shown != ip else "") + tr(" · {0} پورت\n", len(res))]
    if opened:
        out.append(tr("🟢 <b>باز</b> · Open"))
        out += [f"• {label(p)}\n   ↳ {e(i)}" for p, i in opened]
    if closed:
        out.append(tr("\n🔴 <b>بسته</b> · Closed\n") + tr("، ").join(label(p) for p in closed))
    if filt:
        out.append(tr("\n🟡 <b>بدون پاسخ</b> · Filtered\nفایروال یا فیلتر؛ مشخص نیست باز یا بسته\u200cست\n") + tr("، ").join(label(p) for p in filt))
    out.append(
        tr("\n💡 باز یعنی چیزی روی پورت اتصال قبول می\u200cکنه؛ معمولاً یه سرویسه ولی ممکنه فایروال، پراکسی یا CDN باشه. بسته یعنی از بیرون چیزی جواب نمی\u200cده، اما ممکنه روی 127.0.0.1 در حال استفاده باشه. برای انتخاب پورت تانل جدید با «🧾 تحلیل ss» مطمئن شو.")
    )
    out.append(
        tr("\n<i>نتیجه از دید سرور ربات (خارج از ایران) هست و ممکنه از داخل ایران فرق کنه. پورت UDP مثل WireGuard و پورتی که فقط روی 127.0.0.1 گوش می\u200cده از بیرون دیده نمی\u200cشه.</i>")
    )
    return "\n".join(out)


def port_cmd_text() -> str:
    return (
        tr("📋 <b>دستور بررسی پورت\u200cهای در حال استفاده روی خود سرور</b>\n(داخل SSH سرور خودت بزن؛ دقیق\u200cتر از هر چک بیرونیه و نیازی نیست پسورد جایی بفرستی)\n\n<pre>ss -tulpn</pre>\nستون Local Address پورت و ستون Process اسم برنامه\u200cست.\n• <code>0.0.0.0:443</code> یعنی از بیرون در دسترسه\n• <code>127.0.0.1:8000</code> یعنی فقط داخل خود سرور\n\nچک یک پورت مشخص:\n<pre>ss -tulpn | grep :443</pre>")
    )


# ───────────── ابزارهای مشترک شبکه ─────────────
def parse_hostport(tok: str, default: int | None = 443) -> tuple[str, int]:
    t = re.sub(r"^[a-z]+://", "", tok.strip(), flags=re.I).split("/")[0]
    port = default
    m = re.match(r"^\[(.+)\](?::(\d+))?$", t)  # [::1]:443
    if m:
        host = m.group(1)
        if m.group(2):
            port = int(m.group(2))
    elif t.count(":") == 1:  # host:port
        host, p = t.split(":")
        if not p.isdigit():
            raise ValueError(tr("پورت نامعتبره"))
        port = int(p)
    else:
        host = t
    if port is None:
        raise ValueError(tr("پورت رو هم بنویس، مثل host:443"))
    if not 1 <= port <= 65535:
        raise ValueError(tr("پورت نامعتبره"))
    return host.lower(), port


async def tcp_ms(ip: str, port: int, timeout: float = 3.0) -> float | None:
    """زمان برقراری اتصال TCP به میلی‌ثانیه؛ None اگه وصل نشد."""
    t0 = time.perf_counter()
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
    except (asyncio.TimeoutError, OSError):
        return None
    ms = (time.perf_counter() - t0) * 1000
    w.close()
    return ms


# ───────────── ⚡ تاخیر TCP ─────────────
async def tcp_latency(ip: str, port: int, n: int = 5) -> list[float | None]:
    out = []
    for _ in range(n):
        out.append(await tcp_ms(ip, port, 3.0))
        await asyncio.sleep(0.15)
    return out


async def tool_ping(text: str) -> str:
    toks = [t for t in re.split(r"[,\s\u060c]+", text.strip()) if t]
    if not 1 <= len(toks) <= 5:
        raise ValueError(tr("بین ۱ تا ۵ سرور بفرست."))
    targets = []
    for t in toks:
        try:
            host, port = parse_hostport(t)
            shown, ip = await resolve_target(host)
        except ValueError as ex:
            raise ValueError(f"{t} ← {ex}")
        targets.append((f"{shown}:{port}", ip, port))
    series = await asyncio.gather(*[tcp_latency(ip, p) for _, ip, p in targets])

    rows = []
    for (label, _, _), s_ in zip(targets, series):
        ok = [x for x in s_ if x is not None]
        loss = round(100 * (len(s_) - len(ok)) / len(s_))
        if ok:
            rows.append((sum(ok) / len(ok), label, min(ok), max(ok),
                         statistics.pstdev(ok) if len(ok) > 1 else 0.0, loss))
        else:
            rows.append((None, label, 0, 0, 0, 100))
    rows.sort(key=lambda r: (r[0] is None, r[0] or 0))

    out = [tr("⚡ <b>تاخیر TCP</b> · ۵ نمونه برای هر سرور\n")]
    for avg, label, mn, mx, jit, loss in rows:
        if avg is None:
            out.append(tr("⚫ <code>{0}</code>\n   اتصال برقرار نشد؛ بسته یا فیلتره", escape(label)))
            continue
        dot = "🟢" if avg < 100 else "🟡" if avg < 250 else "🔴"
        out.append(
            tr("{0} <code>{1}</code>\n   میانگین {2:.0f}ms · کمترین {3:.0f} · بیشترین {4:.0f} · نوسان {5:.0f} · ریزش {6}%", dot, escape(label), avg, mn, mx, jit, loss)
        )
    if len(rows) > 1 and rows[0][0] is not None:
        out.append(tr("\n🏆 سریع\u200cترین: <code>{0}</code>", escape(rows[0][1])))
    out.append(tr("\n<i>تاخیر از دید سرور ربات (خارج از ایران) اندازه\u200cگیری شده. برای دید از داخل ایران از «🇮🇷 چک از ایران» استفاده کن.</i>"))
    return "\n".join(out)


# ───────────── 🇮🇷 چک دسترسی از ایران (check-host.net) ─────────────
CH = "https://check-host.net"
CH_HDR = {"Accept": "application/json"}
_nodes_cache: dict = {"t": 0.0, "nodes": {}}
CITY_FA = {"Tehran": "تهران", "Shiraz": "شیراز", "Qom": "قم", "Tabriz": "تبریز",
           "Mashhad": "مشهد", "Isfahan": "اصفهان"}
def city_name(city: str) -> str:
    return CITY_FA.get(city, city) if LANG.get() == "fa" else city


CONTROL_PREF = ("de4.node.check-host.net", "nl1.node.check-host.net", "tr1.node.check-host.net")


async def ch_nodes() -> dict:
    if not _nodes_cache["nodes"] or time.monotonic() - _nodes_cache["t"] > 3600:
        r = await http.get(f"{CH}/nodes/hosts", headers=CH_HDR)
        r.raise_for_status()
        _nodes_cache.update(t=time.monotonic(), nodes=r.json().get("nodes", {}))
    return _nodes_cache["nodes"]


def _flag(cc: str) -> str:
    cc = (cc or "").upper()
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc) if len(cc) == 2 and cc.isalpha() else "🌐"


def _parse_tcp(v):
    ent = v[0] if isinstance(v, list) and v else v
    if ent is None:
        return "pending", None
    if isinstance(ent, dict):
        if "time" in ent:
            return "ok", int(float(ent["time"]) * 1000)
        if "error" in ent:
            err = str(ent["error"])
            low = err.lower()
            if "timed out" in low or "timeout" in low:
                return "fail", tr("تایم\u200cاوت؛ احتمالاً فیلتر یا دراپ")
            if "refused" in low:
                return "fail", tr("رد شد؛ پورت بسته\u200cست")
            return "fail", err[:40]
    return "fail", tr("نامشخص")


async def tool_iran(text: str):
    host, port = parse_hostport(text)
    shown, ip = await resolve_target(host)
    nodes = await ch_nodes()
    ir = [n for n, v in nodes.items() if v.get("location", [""])[0] == "ir"]
    if not ir:
        raise ValueError(tr("الان هیچ نود ایرانی در check-host فعال نیست."))
    control = [n for n in CONTROL_PREF if n in nodes][:2] or \
              [n for n, v in nodes.items() if v.get("location", [""])[0] != "ir"][:2]
    target = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
    params = [("host", target)] + [("node", n) for n in ir + control]
    r = await http.get(f"{CH}/check-tcp", params=params, headers=CH_HDR)
    r.raise_for_status()
    j = r.json()
    if j.get("ok") != 1 or "request_id" not in j:
        raise ValueError(tr("check-host درخواست رو قبول نکرد (احتمالاً محدودیت نرخ). کمی بعد دوباره امتحان کن."))
    info, rid = j.get("nodes", {}), j["request_id"]

    res: dict = {}
    for _ in range(12):
        await asyncio.sleep(2.5)
        rr = await http.get(f"{CH}/check-result/{rid}", headers=CH_HDR)
        rr.raise_for_status()
        res = rr.json()
        if all(res.get(n) is not None for n in info):
            break

    st = {n: _parse_tcp(res.get(n)) for n in info}
    e = escape

    def line(n):
        cc, country, city, _ip, asn = (list(info[n]) + [""] * 5)[:5]
        name = city_name(city) if cc == "ir" else f"{country} {city}"
        s_, v = st[n]
        mark = f"✅ {v}ms" if s_ == "ok" else f"❌ {e(str(v))}" if s_ == "fail" else tr("⏳ بدون نتیجه")
        return f"{_flag(cc)} {e(name)} · {e(asn)} — {mark}"

    ir_in = [n for n in info if n in ir]
    ct_in = [n for n in info if n in control]
    ir_done = sum(1 for n in ir_in if st[n][0] != "pending")
    ir_ok = sum(1 for n in ir_in if st[n][0] == "ok")
    c_done = sum(1 for n in ct_in if st[n][0] != "pending")
    c_ok = sum(1 for n in ct_in if st[n][0] == "ok")

    if ir_done == 0:
        verdict = tr("⏳ نودهای ایران جواب ندادن؛ چند دقیقه بعد دوباره امتحان کن.")
    elif c_done > 0 and c_ok == 0 and ir_ok == 0:
        verdict = tr("⚠️ از ایران و از خارج هر دو بسته\u200cست. مشکل از خود سرور یا پورته (سرویس خاموشه یا فایروال سرور)، نه فیلترینگ.")
    elif ir_ok == 0:
        verdict = tr("🚫 از ایران بسته ولی از خارج بازه. احتمالاً IP یا پورت فیلتر شده.")
    elif ir_ok < ir_done:
        verdict = tr("⚠️ فقط از بعضی نودهای ایران بازه. ممکنه روی بعضی ISPها فیلتر باشه.")
    else:
        verdict = tr("✅ از همه\u200cی نودهای ایران باز.")

    body = [tr("🇮🇷 <b>چک دسترسی از ایران</b>"), f"<code>{e(shown)}:{port}</code>\n", tr("<b>نودهای ایران</b>")]
    body += [line(n) for n in ir_in] or ["—"]
    if ct_in:
        body += [tr("\n<b>نودهای شاهد (خارج از ایران)</b>")] + [line(n) for n in ct_in]
    body += [
        f"\n{verdict}",
        tr("\n<i>نودهای check-host روی دیتاسنترهای ایران هستن، نه اینترنت خونگی یا موبایل؛ پس نتیجه برای همراه اول و ایرانسل ممکنه فرق کنه.</i>"),
    ]
    extra = []
    if j.get("permanent_link", "").startswith("https://check-host.net/"):
        extra.append([btn(tr("🔗 گزارش کامل check-host"), None, url=j["permanent_link"])])
    return "\n".join(body), extra


# ───────────── 📡 مانیتور آپ/داون ─────────────
log = logging.getLogger("recon-bot")
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor.db"))
CHECK_EVERY = 300  # ثانیه
MAX_MON = 5        # تعداد سرور مجاز برای هر کاربر
TEHRAN = timezone(timedelta(hours=3, minutes=30))
_db_lock = threading.Lock()


_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS monitors ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER NOT NULL, host TEXT NOT NULL, "
    "port INTEGER NOT NULL, state INTEGER, since REAL, last_check REAL, last_ms REAL, "
    "created REAL, UNIQUE(uid, host, port))",
    "CREATE INDEX IF NOT EXISTS ix_monitors_uid ON monitors(uid)",
    "CREATE TABLE IF NOT EXISTS expiry ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER NOT NULL, kind TEXT NOT NULL, host TEXT NOT NULL, "
    "port INTEGER NOT NULL, last_days INTEGER, last_th INTEGER, last_check REAL, created REAL, "
    "UNIQUE(uid, kind, host, port))",
    "CREATE INDEX IF NOT EXISTS ix_expiry_uid ON expiry(uid)",
    "CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, lang TEXT NOT NULL, created REAL)",
    "CREATE TABLE IF NOT EXISTS samples (mid INTEGER NOT NULL, ts REAL NOT NULL, up INTEGER NOT NULL, ms REAL)",
    "CREATE INDEX IF NOT EXISTS ix_samples ON samples(mid, ts)",
)

_MON_COLS = {"iran_watch": "INTEGER DEFAULT 0", "iran_state": "INTEGER", "iran_fail": "INTEGER DEFAULT 0", "iran_check": "REAL"}


def _ensure_schema(con: sqlite3.Connection) -> None:
    for stmt in _SCHEMA:
        con.execute(stmt)
    have = {r[1] for r in con.execute("PRAGMA table_info(monitors)")}
    for col, typ in _MON_COLS.items():  # مهاجرت: ستون‌های جدید برای دیتابیس‌های قدیمی
        if col not in have:
            con.execute(f"ALTER TABLE monitors ADD COLUMN {col} {typ}")
    con.commit()


def _db_exec(sql: str, args: tuple = ()):
    with _db_lock:
        con = sqlite3.connect(DB_PATH)
        try:
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(sql, args)
            except sqlite3.OperationalError as e:
                # اگه جدول‌ها وجود نداشتن (فایل دیتابیس خالی/پاک‌شده)، می‌سازیم و یه بار دوباره امتحان می‌کنیم
                if "no such table" not in str(e) and "no such column" not in str(e):
                    raise
                _ensure_schema(con)
                cur = con.execute(sql, args)
            rows = cur.fetchall()
            con.commit()
            return rows, cur.lastrowid, cur.rowcount
        finally:
            con.close()


async def db(sql: str, args: tuple = ()):
    return await asyncio.to_thread(_db_exec, sql, args)


def init_db() -> None:
    with _db_lock:
        con = sqlite3.connect(DB_PATH)
        try:
            _ensure_schema(con)
        finally:
            con.close()


def fmt_dur(sec: float) -> str:
    sec = max(int(sec), 0)
    if sec < 60:
        return tr("{0} ثانیه", sec)
    if sec < 3600:
        return tr("{0} دقیقه", sec // 60)
    if sec < 86400:
        return tr("{0} ساعت", sec // 3600)
    return tr("{0} روز", sec // 86400)


async def check_up(host: str, port: int, attempts: int = 1) -> tuple[bool, float | None]:
    for i in range(attempts):
        try:
            _, ip = await resolve_target(host)
            ms = await tcp_ms(ip, port, 5.0)
            if ms is not None:
                return True, ms
        except ValueError:
            pass
        if i < attempts - 1:
            await asyncio.sleep(5)
    return False, None


async def get_mon(mid: int, uid: int):
    rows, _, _ = await db("SELECT * FROM monitors WHERE id=? AND uid=?", (mid, uid))
    return rows[0] if rows else None


async def set_state(row, up: bool, ms: float | None) -> bool:
    """وضعیت رو ذخیره می‌کنه؛ اگه وضعیت عوض شده باشه True برمی‌گردونه."""
    now, new = time.time(), int(up)
    changed = row["state"] is None or row["state"] != new
    if changed:
        _, _, n = await db(
            "UPDATE monitors SET state=?, since=?, last_check=?, last_ms=? WHERE id=?",
            (new, now, now, ms, row["id"]),
        )
    else:
        _, _, n = await db("UPDATE monitors SET last_check=?, last_ms=? WHERE id=?", (now, ms, row["id"]))
    return changed and n > 0


async def render_monitors(uid: int):
    rows, _, _ = await db("SELECT * FROM monitors WHERE uid=? ORDER BY id", (uid,))
    now = time.time()
    lines = [tr("📡 <b>مانیتور سرورها</b>")]
    kb = []
    if not rows:
        lines.append(tr("\nهنوز سروری اضافه نکردی."))
    for r in rows:
        st = r["state"]
        emoji = "🟢" if st == 1 else "🔴" if st == 0 else "⚪"
        label = f"{r['host']}:{r['port']}"
        if st is None:
            desc = tr("هنوز چک نشده")
        else:
            desc = (tr("بالا") if st == 1 else tr("قطع")) + f" · {fmt_dur(now - (r['since'] or now))}"
            if st == 1 and r["last_ms"]:
                desc += f" · {int(r['last_ms'])}ms"
        iw, ist = r["iran_watch"], r["iran_state"]
        if iw:
            desc += " · 🇮🇷 " + (tr("سالم") if ist == 1 else tr("مسدود") if ist == 0 else tr("در حال بررسی"))
        lines.append(f"\n{emoji} <code>{escape(label)}</code>\n   {desc}")
        kb.append([
            btn(f"{emoji} {label}", f"mon:chk:{r['id']}", "success" if st == 1 else "danger" if st == 0 else None),
            btn("🇮🇷", f"mon:wf:{r['id']}", "danger" if iw and ist == 0 else "success" if iw else None),
            btn("📈", f"mon:ch:{r['id']}", "primary"),
            btn("🗑", f"mon:del:{r['id']}", "danger"),
        ])
    lines.append(
        tr("\n<i>هر {0} دقیقه چک می\u200cشه و اگه قطع یا وصل شد پیام می\u200cگیری. روی اسم سرور بزنی همین الان چک می\u200cشه.</i>", CHECK_EVERY // 60)
    )
    lines.append(tr("<i>🇮🇷 (سبز = روشن) هر ۳۰ دقیقه از نودهای ایران چک می\u200cکنه و اگه IP فیلتر بشه خبر می\u200cده. 📈 نمودار ۲۴ ساعت اخیر رو می\u200cفرسته.</i>"))
    if len(rows) < MAX_MON:
        kb.append([btn(tr("➕ افزودن سرور"), "mon:add", "success")])
    kb.append([btn(tr("🏠 منوی اصلی"), "m:home", "primary")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb)


async def safe_edit(msg, text: str, kb=None) -> None:
    try:
        await msg.edit_text(rtl(text), reply_markup=kb, disable_web_page_preview=True)
    except TelegramBadRequest as ex:
        if "not modified" not in str(ex):
            raise


async def handle_result(bot, row, up: bool, ms: float | None) -> None:
    await db("INSERT INTO samples(mid, ts, up, ms) VALUES (?,?,?,?)", (row["id"], time.time(), int(up), ms))
    old = row["state"]
    changed = await set_state(row, up, ms)
    if not changed or old is None:
        return  # اولین چک یا بدون تغییر: پیامی لازم نیست
    LANG.set(await get_lang(row["uid"]) or "fa")
    label = f"{row['host']}:{row['port']}"
    when = datetime.now(TEHRAN).strftime("%H:%M")
    if up:
        text = (tr("🟢 <b>وصل شد</b>\n<code>{0}</code>\nمدت قطعی: {1}\nساعت {2} به وقت تهران", escape(label), fmt_dur(time.time() - (row['since'] or time.time())), when))
        kb = None
    else:
        text = tr("🔴 <b>قطع شد</b>\n<code>{0}</code>\nساعت {1} به وقت تهران", escape(label), when)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            btn(tr("🔄 چک دوباره"), f"mon:re:{row['id']}", "primary"),
            btn(tr("🇮🇷 چک از ایران"), f"mon:ir:{row['id']}", "success"),
        ]])
    try:
        await bot.send_message(row["uid"], rtl(text), reply_markup=kb)
    except TelegramForbiddenError:
        await db("DELETE FROM monitors WHERE uid=?", (row["uid"],))  # کاربر ربات رو بلاک کرده
    except Exception:
        log.exception("alert failed for uid=%s", row["uid"])


async def monitor_cycle(bot) -> None:
    rows, _, _ = await db("SELECT * FROM monitors")
    sem = asyncio.Semaphore(20)

    async def one(r):
        async with sem:
            up, ms = await check_up(r["host"], r["port"], attempts=3)  # سه بار تلاش تا اشتباهی هشدار نده
            await handle_result(bot, r, up, ms)

    await asyncio.gather(*[one(r) for r in rows], return_exceptions=True)
    await db("DELETE FROM samples WHERE ts < ? OR mid NOT IN (SELECT id FROM monitors)", (time.time() - 7 * 86400,))
    try:
        await iran_cycle(bot)
    except Exception:
        log.exception("iran watch cycle failed")


async def monitor_loop(bot) -> None:
    await asyncio.sleep(10)
    while True:
        try:
            await monitor_cycle(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("monitor cycle failed")
        await asyncio.sleep(CHECK_EVERY)


# ───────────── 🏓 پینگ از ایران و جهان (check-host.net) ─────────────
def cooldown_ok(uid: int) -> bool:
    now = time.monotonic()
    if now - _last.get(uid, 0) < COOLDOWN:
        return False
    _last[uid] = now
    return True


def clip(text: str, limit: int = 3900) -> str:
    return text if len(text) <= limit else text[:limit].rsplit("\n", 1)[0] + "\n…"


def _parse_ping(v):
    """-> (state, (ok, total, min, avg, max)) ؛ state: pending | ok | fail"""
    if v is None:
        return "pending", None
    inner = v[0] if isinstance(v, list) and v else None
    tries = [t for t in (inner if isinstance(inner, list) else []) if isinstance(t, list) and t]
    oks = [float(t[1]) * 1000 for t in tries if t[0] == "OK" and len(t) > 1]
    if not oks:
        return "fail", (0, len(tries), 0, 0, 0)
    return "ok", (len(oks), len(tries), min(oks), sum(oks) / len(oks), max(oks))


async def ch_run(kind: str, host: str, node_names: list[str], polls: int = 14):
    params = [("host", host)] + [("node", n) for n in node_names]
    r = await http.get(f"{CH}/check-{kind}", params=params, headers=CH_HDR)
    r.raise_for_status()
    j = r.json()
    if j.get("ok") != 1 or "request_id" not in j:
        raise ValueError(tr("check-host درخواست رو قبول نکرد (احتمالاً محدودیت نرخ). کمی بعد دوباره امتحان کن."))
    res: dict = {}
    for _ in range(polls):
        await asyncio.sleep(2.5)
        rr = await http.get(f"{CH}/check-result/{j['request_id']}", headers=CH_HDR)
        rr.raise_for_status()
        res = rr.json()
        if all(res.get(n) is not None for n in j.get("nodes", {})):
            break
    return j, res


async def ping_check(shown: str, ip: str, mode: str):
    nodes = await ch_nodes()
    ir = [n for n, v in nodes.items() if v.get("location", [""])[0] == "ir"]
    if not ir:
        raise ValueError(tr("الان هیچ نود ایرانی در check-host فعال نیست."))
    if mode == "all":
        names = list(nodes)
    else:
        control = [n for n in CONTROL_PREF if n in nodes][:2]
        names = ir + control
    j, res = await ch_run("ping", ip, names)
    info = j.get("nodes", {})
    st = {n: _parse_ping(res.get(n)) for n in info}
    e = escape

    def meta(n):
        cc, _country, city, _ip, asn = (list(info[n]) + [""] * 5)[:5]
        return cc, (city_name(city) if cc == "ir" else city), asn

    def stat(n):
        s_, v = st[n]
        if s_ == "pending":
            return tr("⏳ بدون نتیجه")
        ok, tot, mn, avg, mx = v
        if ok == 0:
            return tr("❌ جواب نداد")
        return f"{'✅' if ok == tot else '⚠️'} {ok}/{tot} · {mn:.0f}/{avg:.0f}/{mx:.0f}ms"

    legend = tr("\n<i>ستون\u200cها: پینگ موفق از کل · کمترین/میانگین/بیشترین</i>")
    head = f"<code>{e(shown)}</code>" + (f" · <code>{ip}</code>" if shown != ip else "")

    if mode == "all":
        def key(n):
            s_, v = st[n]
            return (0, v[3]) if s_ == "ok" else (1, 0)
        order = sorted(info, key=key)
        lines = []
        for n in order:
            cc, city, _ = meta(n)
            lines.append(f"{_flag(cc)} {e(city)} · {stat(n).partition(' ')[2]}")
        okn = [n for n in order if st[n][0] == "ok"]
        summary = ""
        if okn:
            b, w = okn[0], okn[-1]
            summary = (tr("\n🏆 بهترین: {0} {1:.0f}ms\n🐢 ضعیف\u200cترین: {2} {3:.0f}ms", e(meta(b)[1]), st[b][1][3], e(meta(w)[1]), st[w][1][3]))
        text = tr("🌍 <b>پینگ از همه\u200cی نودها</b>\n{0}\n\n", head) + "\n".join(lines) + summary + legend
        return clip(text)

    ir_in = [n for n in info if n in ir]
    ct_in = [n for n in info if n not in ir]
    ir_done = sum(1 for n in ir_in if st[n][0] != "pending")
    ir_ok = sum(1 for n in ir_in if st[n][0] == "ok")
    ir_loss = sum(1 for n in ir_in if st[n][0] == "ok" and st[n][1][0] < st[n][1][1])
    c_ok = sum(1 for n in ct_in if st[n][0] == "ok")
    if ir_done == 0:
        verdict = tr("⏳ نودهای ایران جواب ندادن؛ چند دقیقه بعد دوباره امتحان کن.")
    elif ir_ok == 0 and c_ok > 0:
        verdict = (tr("🚫 از ایران پینگ جواب نمی\u200cگیره ولی از خارج می\u200cگیره؛ ممکنه IP فیلتر شده باشه. برای اطمینان «🇮🇷 چک از ایران» رو روی پورت سرویس بزن."))
    elif ir_ok == 0:
        verdict = (tr("⚠️ از هیچ\u200cجا پینگ جواب نمی\u200cگیره. ممکنه سرور ICMP رو بسته باشه، که لزوماً به معنی خاموش بودن نیست. پورت سرویس رو با «🔌 چک پورت» بررسی کن."))
    elif ir_loss:
        verdict = tr("⚠️ بعضی نودهای ایران ریزش دارن؛ مسیر ناپایداره.")
    else:
        verdict = tr("✅ پینگ از همه\u200cی نودهای ایران سالمه.")
    body = [tr("🏓 <b>پینگ از ایران</b>\n{0}\n", head), tr("<b>نودهای ایران</b>")]
    for n in ir_in:
        cc, city, asn = meta(n)
        body.append(f"{_flag(cc)} {e(city)} · {e(asn)} — {stat(n)}")
    if ct_in:
        body.append(tr("\n<b>نودهای شاهد (خارج از ایران)</b>"))
        for n in ct_in:
            cc, city, _ = meta(n)
            body.append(f"{_flag(cc)} {e(city)} — {stat(n)}")
    body += [f"\n{verdict}", legend.strip()]
    return clip("\n".join(body))


def ping_kb(mode: str) -> InlineKeyboardMarkup:
    first = btn(tr("🌍 همه\u200cی نودها"), "pg:all", "primary") if mode == "ir" else btn(tr("🇮🇷 فقط ایران"), "pg:ir", "success")
    return InlineKeyboardMarkup(inline_keyboard=[
        [first, btn(tr("🔄 دوباره"), f"pg:{mode}")],
        [btn(tr("🏠 منوی اصلی"), "m:home", "danger")],
    ])


# ───────────── 🧾 تحلیل خروجی ss ─────────────
SS_RE = re.compile(r"^(?:(tcp|udp)\d*\s+)?(LISTEN|UNCONN)\s+\d+\s+\d+\s+(\S+)\s+\S+\s*(.*)$", re.I)
DANGEROUS = {3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB",
             11211: "Memcached", 9200: "Elasticsearch", 23: "Telnet"}
FREE_CANDIDATES = [443, 8443, 2053, 2083, 2087, 2096, 8880, 2052, 2082, 2086, 2095, 8080, 9443, 10443]


def tool_ss(text: str) -> str:
    entries: dict[tuple[str, int], dict] = {}
    for raw in text.splitlines():
        m = SS_RE.match(raw.strip())
        if not m:
            continue
        proto = (m.group(1) or ("tcp" if m.group(2).upper() == "LISTEN" else "udp")).lower()
        local = m.group(3)
        if ":" not in local:
            continue
        addr, port_s = local.rsplit(":", 1)
        if not port_s.isdigit():
            continue
        addr = addr.strip("[]").split("%")[0]
        try:
            loopback = ipaddress.ip_address(addr).is_loopback
        except ValueError:
            loopback = False  # مثل * یا 0.0.0.0 که از بیرون هم دیده می‌شه
        procs = re.findall(r'\("([^"]+)",pid=(\d+)', m.group(4))
        ent = entries.setdefault((proto, int(port_s)), {"public": False, "procs": set()})
        ent["public"] |= not loopback
        ent["procs"].update(n for n, _ in procs)
    if not entries:
        raise ValueError(tr("خروجی ss شناسایی نشد. دستور ss -tulpn رو بزن و کامل paste کن."))

    e = escape

    def fmt(items):
        return [f"• <code>{p}</code> {pr} · {e(', '.join(sorted(v['procs'])) or tr("نامشخص"))}" for (pr, p), v in items]

    items = sorted(entries.items(), key=lambda kv: (kv[0][1], kv[0][0]))
    pub = [kv for kv in items if kv[1]["public"]]
    loc = [kv for kv in items if not kv[1]["public"]]
    out = [tr("🧾 <b>تحلیل پورت\u200cهای سرور</b> · {0} پورت\n", len(entries))]
    if pub:
        out += [tr("🌍 <b>در دسترس از بیرون</b>")] + fmt(pub)
    if loc:
        out += [tr("\n🔒 <b>فقط داخلی</b> · روی 127.0.0.1")] + fmt(loc)
    warns = [tr("⚠️ {0} روی پورت {1} از بیرون باز است. اگه لازم نیست ببندش یا فقط به 127.0.0.1 محدودش کن.", name, p)
             for (pr, p), v in pub if p in DANGEROUS and pr == "tcp" for name in [DANGEROUS[p]]]
    if warns:
        out += [""] + warns
    used_tcp = {p for (pr, p) in entries if pr == "tcp"}
    free = [str(p) for p in FREE_CANDIDATES if p not in used_tcp][:8]
    if free:
        out.append(tr("\n🟢 <b>پورت\u200cهای آزاد پیشنهادی برای تانل جدید</b>\n") + tr("، ").join(f"<code>{p}</code>" for p in free))
    if not any(v["procs"] for v in entries.values()):
        out.append(tr("\n<i>اسم برنامه\u200cها پیدا نشد؛ دستور رو با root (یا sudo) بزن.</i>"))
    out.append(tr("\n<i>این لیست فقط پورت\u200cهای TCP/UDP در حال گوش دادن روی خود سرور رو نشون می\u200cده. بازبودن از بیرون به فایروال هم بستگی داره.</i>"))
    return "\n".join(out)


# ───────────── ⏰ هشدار انقضای SSL و دامنه ─────────────
EXPIRY_TH = (30, 15, 7, 3, 1, 0)  # روزهای مانده که هشدار می‌ده
EXPIRY_EVERY = 6 * 3600
MAX_EXP = 10


def _due_threshold(days: int) -> int | None:
    c = [t for t in EXPIRY_TH if days <= t]
    return min(c) if c else None


async def expiry_days(kind: str, host: str, port: int) -> int | None:
    if kind == "ssl":
        _, ip = await resolve_target(host)
        der, *_ = await _tls(ip, port, host, False)
        cert = x509.load_der_x509_certificate(der)
        return (cert.not_valid_after_utc - datetime.now(timezone.utc)).days
    dd = await domain_data(host)
    return (dd["expires"] - datetime.now(timezone.utc)).days if dd["expires"] else None


def exp_label(r) -> str:
    base = ("🔐 SSL" if r["kind"] == "ssl" else tr("📇 دامنه"))
    host = r["host"] + (f":{r['port']}" if r["kind"] == "ssl" and r["port"] != 443 else "")
    return base, host


async def render_expiry(uid: int):
    rows, _, _ = await db("SELECT * FROM expiry WHERE uid=? ORDER BY id", (uid,))
    lines = [tr("⏰ <b>هشدار انقضا</b>")]
    kb = []
    if not rows:
        lines.append(tr("\nهنوز چیزی اضافه نکردی."))
    for r in rows:
        base, host = exp_label(r)
        d = r["last_days"]
        if d is None:
            emoji, desc, style = "⚪", tr("هنوز چک نشده یا برای این پسوند در دسترس نیست"), None
        elif d < 0:
            emoji, desc, style = "🔴", tr("⚠️ {0} روز پیش منقضی شده", -d), "danger"
        else:
            emoji = "🔴" if d < 7 else "🟡" if d < 30 else "🟢"
            desc, style = tr("{0} روز مانده", d), ("danger" if d < 7 else "success" if d >= 30 else None)
        lines.append(f"\n{emoji} {base} · <code>{escape(host)}</code>\n   {desc}")
        kb.append([btn(f"{emoji} {base.partition(' ')[2]} {host}", f"ex:chk:{r['id']}", style), btn("🗑", f"ex:del:{r['id']}", "danger")])
    lines.append(tr("\n<i>۳۰ و ۱۵ و ۷ و ۳ و ۱ روز مونده و روز انقضا بهت پیام می\u200cدم. روی هر مورد بزنی همین الان چک می\u200cشه.</i>"))
    if len(rows) < MAX_EXP:
        kb.append([btn(tr("➕ افزودن"), "ex:add", "success")])
    kb.append([btn(tr("🏠 منوی اصلی"), "m:home", "primary")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb)


async def expiry_cycle(bot) -> None:
    rows, _, _ = await db("SELECT * FROM expiry")
    sem = asyncio.Semaphore(5)

    async def one(r):
        async with sem:
            try:
                days = await expiry_days(r["kind"], r["host"], r["port"])
            except Exception:
                log.info("expiry check failed for %s", r["host"])
                return
            if days is None:
                return
            th, last = _due_threshold(days), r["last_th"]
            notify = th is not None and (last is None or th < last)
            new_last = th if notify else (None if th is None else last)
            await db("UPDATE expiry SET last_days=?, last_check=?, last_th=? WHERE id=?",
                     (days, time.time(), new_last, r["id"]))
            if not notify:
                return
            LANG.set(await get_lang(r["uid"]) or "fa")
            base, host = exp_label(r)
            when = tr("{0} روز دیگه منقضی می\u200cشه", days) if days >= 0 else tr("{0} روز پیش منقضی شده", -days)
            text = tr("⏰ <b>هشدار انقضا</b>\n{0} · <code>{1}</code>\n{2}", base, escape(host), when)
            try:
                await bot.send_message(r["uid"], rtl(text))
            except TelegramForbiddenError:
                await db("DELETE FROM expiry WHERE uid=?", (r["uid"],))
            except Exception:
                log.exception("expiry alert failed")

    await asyncio.gather(*[one(r) for r in rows], return_exceptions=True)


async def expiry_loop(bot) -> None:
    await asyncio.sleep(30)
    while True:
        try:
            await expiry_cycle(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("expiry cycle failed")
        await asyncio.sleep(EXPIRY_EVERY)


UA = "Mozilla/5.0 (compatible; recon-bot/0.1)"


# ───────────── ابزارهای TLS مشترک ─────────────
async def tls_probe(ip: str, port: int, sni: str, tls13: bool = False, alpn=("h2", "http/1.1")) -> dict:
    """هندشیک TLS بدون بررسی گواهی؛ نسخه، cipher، ALPN و زمان رو برمی‌گردونه."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    if tls13:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.set_alpn_protocols(list(alpn))
    t0 = time.perf_counter()
    _r, w = await asyncio.wait_for(asyncio.open_connection(ip, port, ssl=ctx, server_hostname=sni), 8)
    ms = (time.perf_counter() - t0) * 1000
    obj = w.get_extra_info("ssl_object")
    out = {"version": obj.version(), "cipher": obj.cipher()[0], "alpn": obj.selected_alpn_protocol(),
           "ms": ms, "der": obj.getpeercert(binary_form=True)}
    w.close()
    try:
        await w.wait_closed()
    except Exception:
        pass
    return out


def cert_dns_names(cert) -> list[str]:
    try:
        return cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return []


def name_matches(dom: str, names: list[str]) -> bool:
    dom = dom.lower()
    for n in (x.lower() for x in names):
        if n == dom or (n.startswith("*.") and "." in dom and dom.split(".", 1)[1] == n[2:]):
            return True
    return False


CDN_SIGS = (
    ("Cloudflare", ("cf-ray", "cf-cache-status"), "cloudflare"),
    ("CloudFront", ("x-amz-cf-id", "x-amz-cf-pop"), "cloudfront"),
    ("Fastly", ("fastly-debug-digest", "x-fastly-request-id"), "fastly"),
    ("Akamai", ("x-akamai-transformed", "akamai-grn"), "akamaighost"),
    ("Vercel", ("x-vercel-id",), "vercel"),
    ("Netlify", ("x-nf-request-id",), "netlify"),
    ("Azure Front Door", ("x-azure-ref",), ""),
    ("Google Cloud", ("x-goog-generation", "x-guploader-uploadid"), "gws"),
)


def detect_cdn(h: dict) -> str | None:
    server = h.get("server", "").lower()
    for name, heads, srv in CDN_SIGS:
        if any(x in h for x in heads) or (srv and srv in server):
            return name
    return None


async def _tls_head(ip: str, port: int, dom: str):
    """یه HEAD / ساده روی TLS (HTTP/1.1)؛ (status، headers) یا None."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_alpn_protocols(["http/1.1"])
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(ip, port, ssl=ctx, server_hostname=dom), 8)
        w.write(f"HEAD / HTTP/1.1\r\nHost: {dom}\r\nUser-Agent: recon-bot\r\nAccept: */*\r\nConnection: close\r\n\r\n".encode())
        await w.drain()
        data = await asyncio.wait_for(r.read(8192), 6)
        w.close()
        lines = data.decode("latin-1", "replace").split("\r\n\r\n")[0].split("\r\n")
        status = int(lines[0].split()[1])
        hdrs = {}
        for ln in lines[1:]:
            k, _s, v = ln.partition(":")
            hdrs[k.strip().lower()] = v.strip()
        return status, hdrs
    except (OSError, asyncio.TimeoutError, ssl.SSLError, ValueError, IndexError):
        return None


# ───────────── 🎭 چک Reality ─────────────
async def tool_reality(text: str) -> str:
    host, port = parse_hostport(text)
    dom = clean_domain(host)
    _shown, ip = await resolve_target(dom)
    e = escape
    tcp = await tcp_ms(ip, port, 5.0)
    if tcp is None:
        raise ValueError(tr("اتصال TCP به این دامنه روی پورت {0} برقرار نشد.", port))
    fail = tr("هندشیک TLS با این دامنه ناموفق بود.")
    try:
        info, tls13 = await tls_probe(ip, port, dom, tls13=True), True
    except (ssl.SSLError, OSError, asyncio.TimeoutError):
        # بعضی سرورها وقتی TLS 1.3 ندارن اتصال رو reset می‌کنن؛ پس با نسخه‌ی پایین‌تر دوباره امتحان می‌کنیم
        tls13 = False
        try:
            info = await tls_probe(ip, port, dom)
        except (ssl.SSLError, OSError, asyncio.TimeoutError):
            raise ValueError(fail)
    h2 = info["alpn"] == "h2"
    cert = x509.load_der_x509_certificate(info["der"])
    days = (cert.not_valid_after_utc - datetime.now(timezone.utc)).days
    pub = cert.public_key()
    key = f"{type(pub).__name__.replace('PublicKey', '')} {getattr(pub, 'key_size', '')}".strip()
    match = name_matches(dom, cert_dns_names(cert))
    head = await _tls_head(ip, port, dom)
    out = [
        f"🎭 <b>Reality check</b> · <code>{e(dom)}:{port}</code>", f"<code>{ip}</code>\n",
        f"TLS 1.3: {'✅' if tls13 else '❌'} ({e(str(info['version']))})",
        f"HTTP/2: {'✅' if h2 else '❌'} (ALPN: {e(str(info['alpn'] or '-'))})",
        f"Handshake: {info['ms']:.0f}ms · TCP: {tcp:.0f}ms",
        f"Cipher: {e(info['cipher'])}",
        f"Cert: {e(_attr(cert.issuer, NameOID.ORGANIZATION_NAME))} · {days}d · {e(key)}",
        f"SAN match: {'✅' if match else '❌'}",
    ]
    note = ""
    if head:
        status, hdrs = head
        out.append(f"HTTP: {status}" + (f" · server: {e(hdrs['server'][:40])}" if hdrs.get("server") else ""))
        cdn = detect_cdn(hdrs)
        if cdn:
            out.append(f"CDN: {cdn}")
        loc = hdrs.get("location", "")
        if 300 <= status < 400 and loc:
            lh = urlsplit(urljoin(f"https://{dom}/", loc)).hostname or ""
            if lh and lh != dom:
                note = tr("\n↪️ این دامنه به <code>{0}</code> ریدایرکت می‌کنه؛ بهتره خود اون دامنه رو تست کنی.", e(lh))
    if tls13 and h2 and match:
        verdict = tr("✅ برای dest و serverNames توی Reality مناسبه.")
    elif tls13 and h2:
        verdict = tr("⚠️ TLS 1.3 و HTTP/2 داره ولی گواهیش با این دامنه نمی‌خونه.")
    elif tls13:
        verdict = tr("⚠️ TLS 1.3 داره ولی HTTP/2 نداره؛ برای Reality توصیه نمی‌شه.")
    else:
        verdict = tr("❌ TLS 1.3 نداره؛ برای Reality مناسب نیست.")
    out += [f"\n{verdict}{note}", tr("\n<i>تاخیر از دید سرور ربات اندازه‌گیری شده و پشتیبانی X25519 قابل بررسی نیست. برای نتیجه‌ی دقیق‌تر همین چک رو روی خود سرور VPN هم بزن.</i>")]
    return "\n".join(out)


# ───────────── 🔗 تحلیل لینک کانفیگ ─────────────
WEAK_SS = re.compile(r"^(rc4|bf-|des|aes-\d+-(cfb|ctr)|camellia|salsa20|chacha20$|none|plain)", re.I)


def _b64d(s: str) -> str:
    s = s.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", "replace")


def _mask(s: str, keep: int = 6) -> str:
    return s if len(s) <= keep else s[:keep] + "…"


def parse_config(link: str) -> dict:
    link = link.strip()
    m = re.match(r"^([a-z0-9]+)://(.+)$", link, re.I | re.S)
    bad = ValueError(tr("لینک کانفیگ معتبر نیست. باید با vless:// یا vmess:// یا trojan:// یا ss:// شروع بشه."))
    if not m:
        raise bad
    proto = m.group(1).lower()
    try:
        if proto == "vmess":
            j = json.loads(_b64d(m.group(2).split("#")[0]))
            return {"proto": "vmess", "host": str(j.get("add", "")).strip(), "port": int(j.get("port") or 0),
                    "name": str(j.get("ps", "")), "id": str(j.get("id", "")), "net": j.get("net") or "tcp",
                    "sec": "tls" if j.get("tls") == "tls" else "none", "sni": j.get("sni") or "",
                    "fp": j.get("fp") or "", "aid": int(j.get("aid") or 0), "scy": j.get("scy") or "auto",
                    "path": j.get("path") or "", "hosthdr": j.get("host") or "", "alpn": j.get("alpn") or ""}
        if proto in ("vless", "trojan"):
            u = urlsplit(link)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return {"proto": proto, "host": u.hostname or "", "port": u.port or 0, "name": unquote(u.fragment),
                    "id": unquote(u.username or ""), "net": q.get("type", "tcp"),
                    "sec": q.get("security", "tls" if proto == "trojan" else "none"),
                    "sni": q.get("sni") or q.get("peer") or "", "fp": q.get("fp", ""), "flow": q.get("flow", ""),
                    "pbk": q.get("pbk", ""), "sid": q.get("sid", ""), "alpn": q.get("alpn", ""),
                    "path": q.get("path", ""), "hosthdr": q.get("host", ""), "enc": q.get("encryption", ""),
                    "insecure": q.get("allowInsecure", q.get("insecure", "0")) in ("1", "true")}
        if proto == "ss":
            body = m.group(2).split("#")[0].split("?")[0]
            name = unquote(m.group(2).split("#", 1)[1]) if "#" in m.group(2) else ""
            if "@" in body:
                userinfo, hostport = body.rsplit("@", 1)
                try:
                    cred = _b64d(userinfo)
                    if ":" not in cred:
                        raise ValueError
                except Exception:
                    cred = unquote(userinfo)
            else:
                cred_host = _b64d(body)
                cred, hostport = cred_host.rsplit("@", 1)
            method, _s, pw = cred.partition(":")
            host, _s, port = hostport.rpartition(":")
            return {"proto": "ss", "host": host.strip("[]"), "port": int(port), "name": name, "method": method, "id": pw}
    except (ValueError, KeyError, IndexError, json.JSONDecodeError, TypeError):
        raise bad
    raise ValueError(tr("این نوع لینک پشتیبانی نمی‌شه."))


async def tool_cfg(text: str):
    c = parse_config(text)
    e = escape
    host, port = c["host"], c["port"]
    if not host or not 1 <= port <= 65535:
        raise ValueError(tr("آدرس یا پورت سرور توی لینک پیدا نشد."))
    warns: list[str] = []
    out = [f"🔗 <b>{c['proto'].upper()}</b> · <code>{e(host)}:{port}</code>"]
    if c["name"]:
        out.append(f"📛 {e(c['name'][:60])}")
    if c["proto"] == "ss":
        out.append(f"Method: {e(c['method'])} · Password: {_mask(c['id'], 2)}***")
        if WEAK_SS.match(c["method"]):
            warns.append(tr("⚠️ متد {0} قدیمی یا ضعیفه؛ از 2022-blake3-*، aes-256-gcm یا chacha20-ietf-poly1305 استفاده کن.", e(c["method"])))
    else:
        out.append(f"Transport: {e(str(c['net']))} · Security: {e(c['sec'])}")
        out.append(f"ID: {e(_mask(c['id'], 8))}")
        if c["sni"] or c["fp"] or c.get("flow"):
            out.append(f"SNI: {e(c['sni'] or '-')} · FP: {e(c['fp'] or '-')}" + (f" · Flow: {e(c['flow'])}" if c.get("flow") else ""))
        if c["path"] or c["hosthdr"]:
            out.append(f"Path: {e(c['path'] or '-')} · Host: {e(c['hosthdr'] or '-')}")
        if c["sec"] == "none":
            warns.append(tr("⚠️ بدون TLS یا Reality؛ ترافیک راحت شناسایی و مسدود می‌شه.") if c["proto"] != "trojan"
                         else tr("⚠️ Trojan بدون TLS معنی نداره."))
        if c.get("insecure"):
            warns.append(tr("⚠️ allowInsecure روشنه؛ گواهی چک نمی‌شه و ارتباط در معرض MITM هست."))
        if c["proto"] == "vmess" and c["aid"] > 0:
            warns.append(tr("⚠️ alterId غیر صفره؛ این روش قدیمیه و استاندارد جدید 0 هست."))
        if c["sec"] == "reality":
            if not c.get("pbk"):
                warns.append(tr("❌ کلید عمومی (pbk) نداره؛ لینک ناقصه."))
            else:
                out.append(f"PBK: {e(_mask(c['pbk']))} · SID: {e(c.get('sid') or '-')}")
            if not c["sni"]:
                warns.append(tr("⚠️ SNI (دامنه‌ی dest) مشخص نشده."))
            if not c["fp"]:
                warns.append(tr("ℹ️ fingerprint (fp) تنظیم نشده؛ chrome پیشنهاد می‌شه."))
            if c["net"] == "tcp" and not c.get("flow"):
                warns.append(tr("ℹ️ برای Reality روی TCP معمولاً flow=xtls-rprx-vision توصیه می‌شه."))
        elif c["sec"] == "tls" and not c["sni"]:
            if re.fullmatch(r"[\d.:]+", host):
                warns.append(tr("⚠️ سرور با آی‌پی و بدون SNI تنظیم شده؛ احتمالاً با TLS درست کار نمی‌کنه."))
    extra = []
    try:
        ip_lit = ipaddress.ip_address(host)
        if classify(ip_lit):
            warns.append(tr("⚠️ آدرس سرور عمومی نیست."))
            ip = None
        else:
            ip = str(ip_lit)
    except ValueError:
        try:
            _s, ip = await resolve_target(host)
        except ValueError:
            ip = None
            warns.append(tr("⚠️ دامنه‌ی سرور resolve نشد."))
    if ip:
        ms = await tcp_ms(ip, port, 4.0)
        out.append(f"\nServer: {'🟢 open · %.0fms' % ms if ms is not None else '🔴 closed / filtered'}")
        target = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
        if len(f"ir:{target}".encode()) <= 64:
            extra.append([btn(tr("🇮🇷 چک از ایران"), f"ir:{target}", "success")])
    if warns:
        out += [""] + warns
    elif c["proto"] != "ss":
        out.append(tr("\n✅ مشکل واضحی توی تنظیمات پیدا نشد."))
    out.append(tr("\n<i>لینک ذخیره نمی‌شه. بهتره پیام حاوی کلیدت رو از چت پاک کنی.</i>"))
    return "\n".join(out), extra


# ───────────── 🕸 تحلیل ASN (RIPEstat) ─────────────
RIPE = "https://stat.ripe.net/data"
_asn_names: dict[int, str] = {}
_ripe_sem = asyncio.Semaphore(6)  # RIPEstat فقط 8 درخواست هم‌زمان از هر آی‌پی قبول می‌کنه


async def ripe(endpoint: str, resource: str, timeout: float = 20) -> dict:
    async with _ripe_sem:
        r = await http.get(f"{RIPE}/{endpoint}/data.json", params={"resource": resource}, timeout=timeout)
    r.raise_for_status()
    return r.json().get("data") or {}


async def asn_name(n: int) -> str:
    if n not in _asn_names:
        try:
            _asn_names[n] = str((await ripe("as-overview", f"AS{n}", 12)).get("holder") or "")
        except Exception:
            return ""
    return _asn_names[n]


def short_holder(h: str, n: int = 28) -> str:
    h = h.split(" - ", 1)[-1] if " - " in h else h
    return h if len(h) <= n else h[: n - 1] + "…"


def draw_asn_graph(asn: int, holder: str, left, right, lt: int, rt: int, v4: int, v6: int) -> bytes:
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = max(len(left), len(right), 1)
    fig, ax = plt.subplots(figsize=(10, max(4.4, 0.66 * n + 2.4)), dpi=140)
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.0, n + 0.4)
    ax.axis("off")
    cy = (n - 1) / 2
    maxp = max([p for _a, _n, p in left + right] or [1])

    def ypos(i: int, cnt: int) -> float:
        return cy + ((cnt - 1) / 2 - i)

    for items, x, color in ((left, -1.2, "#3b82f6"), (right, 1.2, "#10b981")):
        for i, (a, nm, p) in enumerate(items):
            y = ypos(i, len(items))
            ax.plot([x, 0], [y, cy], color=color, alpha=0.45, lw=0.8 + 3.4 * p / maxp, zorder=1)
            ax.text(x, y, f"AS{a}\n{short_holder(nm, 24)}", ha="center", va="center", fontsize=7.5, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, lw=1.4))
    ax.text(0, cy, f"AS{asn}\n{short_holder(holder, 26)}", ha="center", va="center", fontsize=9, fontweight="bold",
            zorder=4, bbox=dict(boxstyle="round,pad=0.5", fc="#fde68a", ec="#f59e0b", lw=2))
    ax.text(-1.2, n + 0.05, f"Upstream / peers ({lt})", ha="center", fontsize=9, color="#1d4ed8", fontweight="bold")
    ax.text(1.2, n + 0.05, f"Downstream ({rt})", ha="center", fontsize=9, color="#047857", fontweight="bold")
    fig.suptitle(f"AS{asn} · {short_holder(holder, 50)}", fontsize=12, fontweight="bold")
    ax.text(0, -0.85, f"IPv4 prefixes: {v4} · IPv6 prefixes: {v6} · line width = path count · source: RIPEstat",
            ha="center", fontsize=7.5, color="#6b7280")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


# ───────────── 🗺 نقشه‌ی مسیر BGP (شبیه bgpmap) ─────────────
async def fetch_as_paths(prefix: str) -> list[list[int]]:
    """مسیرهای AS دیده‌شده توسط RIPE RIS برای یک prefix؛ هر مسیر از peer تا origin."""
    d = await ripe("looking-glass", prefix, 25)
    paths: list[list[int]] = []
    for rrc in d.get("rrcs", []):
        for peer in rrc.get("peers", []):
            raw = str(peer.get("as_path") or "")
            if "{" in raw:
                continue
            seq: list[int] = []
            for tok in raw.split():
                if tok.isdigit() and (not seq or seq[-1] != int(tok)):  # prepend حذف می‌شه
                    seq.append(int(tok))
            if len(seq) >= 2:
                paths.append(seq)
    return paths


def build_path_graph(paths: list[list[int]], max_nodes: int = 15):
    """مسیرها رو هرس می‌کنه: پرتکرارترین مسیرها اول، تا سقف تعداد نود. خروجی: (مسیرها با تعداد، مسیر اصلی)."""
    from collections import Counter
    cnt = Counter(tuple(p) for p in paths)
    origin = Counter(p[-1] for p in paths).most_common(1)[0][0]
    cnt = Counter({p: c for p, c in cnt.items() if p[-1] == origin})
    ranked = [p for p, _c in cnt.most_common()]
    main = ranked[0]
    nodes: set[int] = set(main)
    chosen = [main]
    for p in ranked[1:]:
        extra = set(p) - nodes
        if len(nodes) + len(extra) <= max_nodes:
            nodes |= extra
            chosen.append(p)
    return [(p, cnt[p]) for p in chosen], main


def draw_bgp_map(prefix: str, target: int, items, main, names: dict[int, str]) -> bytes:
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch
    from matplotlib.path import Path as MPath

    origin = main[-1]
    dist: dict[int, int] = {origin: 0}
    for p, _c in items:
        for i, a in enumerate(reversed(p)):
            dist[a] = min(dist.get(a, 99), i)
    edges: dict[tuple[int, int], int] = {}
    for p, c in items:
        for u, v in zip(p, p[1:]):  # u (دورتر) → v (نزدیک‌تر به origin)
            if dist[u] > dist[v]:
                edges[(u, v)] = edges.get((u, v), 0) + c
    main_edges = {(u, v) for u, v in zip(main, main[1:])}
    top = max(dist.values())
    layers: dict[int, list[int]] = {}
    for a, d in dist.items():
        layers.setdefault(d, []).append(a)

    # چینش افقی: از origin به بالا، با میانگین موقعیت فرزندها
    xs: dict[int, float] = {origin: 0.0}
    for d in range(1, top + 1):
        row = layers.get(d, [])
        def bary(a):
            ch = [xs[v] for (u, v) in edges if u == a and v in xs]
            return sum(ch) / len(ch) if ch else 0.0
        row.sort(key=lambda a: (bary(a), a))
        gap = 3.1
        for i, a in enumerate(row):
            xs[a] = (i - (len(row) - 1) / 2) * gap
    # مسیر اصلی وسط و عمودی
    for a in main:
        if len(layers[dist[a]]) == 1:
            xs[a] = 0.0

    W = max(max((abs(x) for x in xs.values()), default=0) * 2 + 4.2, 6)
    H = (top + 2) * 2.4
    fig, ax = plt.subplots(figsize=(W * 0.62, H * 0.62), dpi=150)
    fig.patch.set_facecolor("#fdfcfa")
    ax.set_facecolor("#fdfcfa")
    ax.set_xlim(-W / 2, W / 2)
    ax.set_ylim(-1.5, top * 2.4 + 2.6)
    ax.axis("off")
    ypos = lambda a: dist[a] * 2.4 + 1.9

    def short(s, n=24):
        s = s.split(" - ", 1)[-1] if " - " in s else s
        return s if len(s) <= n else s[: n - 1] + "…"

    # prefix box
    ax.add_patch(FancyBboxPatch((-1.7, -1.0), 3.4, 0.8, boxstyle="round,pad=0.05,rounding_size=0.18",
                                fc="#fdf3e3", ec="#b7791f", lw=2, zorder=3))
    ax.text(0, -0.6, prefix, ha="center", va="center", family="monospace", fontsize=10, color="#9c5a12", zorder=4)

    def curve(p0, p1, col, lw, z, arrow=False):
        (x0, y0), (x1, y1) = p0, p1
        my = (y0 + y1) / 2
        path = MPath([(x0, y0), (x0, my), (x1, my), (x1, y1)],
                     [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4])
        if arrow:
            ax.add_patch(FancyArrowPatch(path=path, arrowstyle="-|>", mutation_scale=14, color=col, lw=lw, zorder=z))
        else:
            ax.add_patch(PathPatch(path, fc="none", ec=col, lw=lw, zorder=z))
        t = 0.5
        return (x0 * (1 - t) ** 3 + 3 * x0 * t * (1 - t) ** 2 + 3 * x1 * t ** 2 * (1 - t) + x1 * t ** 3,
                my)

    bw, bh = 2.8, 0.9
    for (u, v), c in sorted(edges.items(), key=lambda kv: (kv[0] in main_edges)):
        isr = (u, v) in main_edges
        col, lw = ("#c0392b", 2.6) if isr else ("#d6d1c7", 1.6)
        mid = curve((xs[u], ypos(u) - bh / 2), (xs[v], ypos(v) + bh / 2), col, lw, 5 if isr else 2, arrow=isr)
        ax.text(mid[0], mid[1], str(c), ha="center", va="center", fontsize=7.5, zorder=6,
                color="#c0392b" if isr else "#666",
                bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.8", fc="white", ec=col, lw=1))
    curve((0, ypos(origin) - bh / 2), (0, -0.2), "#c0392b", 2.6, 5, arrow=True)
    ax.text(0, (ypos(origin) - bh / 2 - 0.2) / 2, str(sum(c for p, c in items)), ha="center", va="center", fontsize=7.5,
            color="#c0392b", zorder=6, bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.8", fc="white", ec="#c0392b", lw=1))

    for a in dist:
        me = a == origin
        ax.add_patch(FancyBboxPatch((xs[a] - bw / 2, ypos(a) - bh / 2), bw, bh, boxstyle="round,pad=0.03,rounding_size=0.16",
                                    fc="#eef3fb" if me else "white", ec="#2b5797" if me else "#d6d1c7", lw=2.4 if me else 1.4, zorder=4))
        ax.text(xs[a], ypos(a) + 0.15, f"AS{a}", ha="center", va="center", fontsize=9.5,
                color="#2b5797" if me else "#222", zorder=5)
        ax.text(xs[a], ypos(a) - 0.2, short(names.get(a, "")), ha="center", va="center", fontsize=7, color="#6b6558", zorder=5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


async def bgp_map(prefix: str):
    """نقشه‌ی مسیر برای prefix؛ اگه داده نبود None."""
    paths = await fetch_as_paths(prefix)
    if not paths:
        return None
    items, main = build_path_graph(paths)
    asns = sorted({a for p, _c in items for a in p})
    nm = await asyncio.gather(*[asn_name(a) for a in asns])
    names = dict(zip(asns, nm))
    png = await asyncio.to_thread(draw_bgp_map, prefix, main[-1], items, main, names)
    return png, len(paths), main


async def tool_asn(text: str):
    t = text.strip()
    m = re.fullmatch(r"(?i)(?:as)?\s*(\d{1,10})", t)
    prefix = None
    if m:
        asn = int(m.group(1))
    else:
        host, _p = parse_hostport(t)
        _shown, ip = await resolve_target(host)
        d = await ripe("network-info", ip)
        if not d.get("asns"):
            raise ValueError(tr("ASN این آدرس پیدا نشد."))
        asn, prefix = int(d["asns"][0]), d.get("prefix")
    ov, pf, nb = await asyncio.gather(
        ripe("as-overview", f"AS{asn}"), ripe("announced-prefixes", f"AS{asn}", 25),
        ripe("asn-neighbours", f"AS{asn}"), return_exceptions=True,
    )
    if isinstance(ov, Exception) and isinstance(nb, Exception):
        raise ov
    ov = ov if isinstance(ov, dict) else {}
    pf = pf if isinstance(pf, dict) else {}
    nb = nb if isinstance(nb, dict) else {}
    holder = str(ov.get("holder") or "")
    prefixes = [p.get("prefix", "") for p in pf.get("prefixes", [])]
    v4, v6 = sum(1 for p in prefixes if ":" not in p), sum(1 for p in prefixes if ":" in p)
    nbs = nb.get("neighbours", [])
    if not holder and not nbs and not prefixes:
        raise ValueError(tr("این ASN پیدا نشد."))
    cnt = nb.get("neighbour_counts", {})
    top = lambda kind: sorted((x for x in nbs if x.get("type") == kind), key=lambda x: -x.get("power", 0))[:8]
    lraw, rraw = top("left"), top("right")
    names = await asyncio.gather(*[asn_name(int(x["asn"])) for x in lraw + rraw])
    nmap = {int(x["asn"]): nm for x, nm in zip(lraw + rraw, names)}
    left = [(int(x["asn"]), nmap[int(x["asn"])], x.get("power", 1)) for x in lraw]
    right = [(int(x["asn"]), nmap[int(x["asn"])], x.get("power", 1)) for x in rraw]
    e = escape
    out = [f"🕸 <b>AS{asn}</b>" + (f" · {e(holder)}" if holder else "")]
    if prefix:
        out.append(f"Prefix: <code>{e(str(prefix))}</code>")
    out.append(f"Announced: {'✅' if ov.get('announced') else '❌'} · IPv4: {v4} · IPv6: {v6}")
    out.append(f"Upstream/peers: {cnt.get('left', len(left))} · Downstream: {cnt.get('right', len(right))}")
    if left:
        out += ["\n<b>Top upstream</b>"] + [f"• AS{a} · {e(short_holder(nm, 32))}" for a, nm, _p in left[:5]]
    if right:
        out += ["\n<b>Top downstream</b>"] + [f"• AS{a} · {e(short_holder(nm, 32))}" for a, nm, _p in right[:5]]
    out.append(tr("\n<i>همسایه‌ها از مسیرهای BGP دیده‌شده توسط RIPE RIS استخراج شدن و تقریبی هستن. چپ یعنی سمت بالادستی/پیرها و راست یعنی مشتری‌ها.</i>"))
    if not prefix:
        prefix = next((x for x in prefixes if ":" not in x), None) or (prefixes[0] if prefixes else None)
    nm_ = lambda x: e(short_holder(x, 22))
    short_cap = [f"🕸 <b>AS{asn}</b>" + (f" · {nm_(holder)}" if holder else "")]
    short_cap.append("")
    if prefix:
        short_cap.append(f"📍 Prefix: <code>{e(str(prefix))}</code>")
    short_cap.append(f"📡 Announced: {'✅' if ov.get('announced') else '❌'}")
    short_cap.append(f"🔢 IPv4: <b>{v4}</b> · IPv6: <b>{v6}</b>")
    if left:
        short_cap += ["", f"⬆️ <b>Upstream</b> ({cnt.get('left', len(left))})"]
        short_cap += [f"  • <code>AS{a}</code> {nm_(n)}" for a, n, _p in left[:4]]
    if right:
        short_cap += ["", f"⬇️ <b>Downstream</b> ({cnt.get('right', len(right))})"]
        short_cap += [f"  • <code>AS{a}</code> {nm_(n)}" for a, n, _p in right[:4]]
    short_cap += ["", tr("<i>عدد روی هر خط = تعداد مسیرهای RIPE RIS؛ خط قرمز = مسیر اصلی.</i>")]
    try:
        m = await bgp_map(str(prefix)) if prefix else None
    except Exception:
        log.exception("bgp map failed")
        m = None
    if m:
        return "\n".join(out), [], ("photo", m[0], f"AS{asn}.png", "\n".join(short_cap))
    png = await asyncio.to_thread(draw_asn_graph, asn, holder, left, right,
                                  cnt.get("left", len(left)), cnt.get("right", len(right)), v4, v6)
    return "\n".join(out), [], ("photo", png, f"AS{asn}.png", "\n".join(short_cap))


# ───────────── ✉️ چک ایمیل (SPF / DKIM / DMARC) ─────────────
DKIM_SELECTORS = ("default", "google", "selector1", "selector2", "k1", "k2", "s1", "s2", "mail", "dkim",
                  "smtp", "mandrill", "zoho", "protonmail", "protonmail2", "protonmail3", "cm", "mxvault")


def _txt(vals: list[str]) -> list[str]:
    return [re.sub(r'"\s*"', "", v).strip().strip('"') for v in vals]


async def _safe_doh(name: str, rtype: str) -> list[str]:
    try:
        return await _doh(name, rtype)
    except (httpx.HTTPError, ValueError):
        return []


async def tool_email(text: str) -> str:
    dom = clean_domain(text)
    sem = asyncio.Semaphore(8)

    async def q(name, t):
        async with sem:
            return await _safe_doh(name, t)

    txt, dmarc, mx, mta, *dk = await asyncio.gather(
        q(dom, "TXT"), q(f"_dmarc.{dom}", "TXT"), q(dom, "MX"), q(f"_mta-sts.{dom}", "TXT"),
        *[q(f"{s}._domainkey.{dom}", "TXT") for s in DKIM_SELECTORS],
    )
    e = escape
    score, lines = 0, [f"✉️ <b>Email check</b> · <code>{e(dom)}</code>\n"]

    spf = [v for v in _txt(txt) if v.lower().startswith("v=spf1")]
    if not spf:
        lines.append("SPF: ❌ " + tr("رکوردی پیدا نشد"))
    elif len(spf) > 1:
        lines.append("SPF: ❌ " + tr("بیشتر از یک رکورد SPF داری؛ این نامعتبره"))
    else:
        s = spf[0].lower()
        lookups = len(re.findall(r"\b(include:|a\b|mx\b|ptr\b|exists:|redirect=)", s))
        score += 1
        if s.endswith("-all"):
            score += 1
            lines.append("SPF: ✅ -all")
        elif s.endswith("~all"):
            lines.append("SPF: ⚠️ ~all · " + tr("نرم؛ -all امن‌تره"))
        else:
            lines.append("SPF: ⚠️ " + tr("بدون -all یا ~all؛ ضعیفه"))
        if lookups > 10:
            lines.append("   ⚠️ " + tr("بیش از ۱۰ جستجوی DNS (حد مجاز SPF)"))
        lines.append(f"   <code>{e(spf[0][:110])}</code>")

    dm = [v for v in _txt(dmarc) if v.lower().startswith("v=dmarc1")]
    if not dm:
        lines.append("DMARC: ❌ " + tr("رکوردی پیدا نشد"))
    else:
        score += 1
        pol = (re.search(r"\bp=(\w+)", dm[0], re.I) or [None, "?"])[1].lower()
        if pol in ("quarantine", "reject"):
            score += 1
            lines.append(f"DMARC: ✅ p={pol}")
        else:
            lines.append(f"DMARC: ⚠️ p={pol} · " + tr("فقط مانیتورینگه؛ quarantine یا reject بذار"))
        lines.append(f"   <code>{e(dm[0][:110])}</code>")

    found = [s for s, v in zip(DKIM_SELECTORS, dk) if any("p=" in x for x in _txt(v))]
    if found:
        score += 1
        lines.append(f"DKIM: ✅ selector: {', '.join(found)}")
    else:
        lines.append("DKIM: ⚠️ " + tr("با سلکتورهای رایج پیدا نشد (ممکنه سلکتور اختصاصی داشته باشی)"))

    lines.append(f"MX: {'✅ ' + ', '.join(e(m.split()[-1].rstrip('.')) for m in mx[:3]) if mx else '⚠️ ' + tr('ندارد')}")
    lines.append(f"MTA-STS: {'✅' if any('v=sts' in x.lower() for x in _txt(mta)) else '—'}")
    lines.append(tr("\n📊 نمره: <b>{0}/5</b>", score))
    return "\n".join(lines)


# ───────────── 🧪 بازرس HTTP ─────────────
async def tool_http(text: str):
    url = text.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    e = escape
    chain, cur, hdrs, status = [], url, {}, 0
    for _ in range(8):
        u = urlsplit(cur)
        if u.scheme not in ("http", "https") or not u.hostname:
            raise ValueError(tr("آدرس نامعتبره."))
        _shown, ip = await resolve_target(u.hostname)
        t0 = time.perf_counter()
        try:
            async with http.stream("GET", cur, headers={"User-Agent": UA, "Accept-Encoding": "gzip, br"}, timeout=15) as r:
                ms = (time.perf_counter() - t0) * 1000
                status, hdrs = r.status_code, {k.lower(): v for k, v in r.headers.items()}
        except httpx.HTTPError:
            raise ValueError(tr("اتصال به {0} ناموفق بود.", u.hostname))
        chain.append((status, cur, ms))
        loc = hdrs.get("location")
        if status in (301, 302, 303, 307, 308) and loc:
            cur = urljoin(cur, loc)
            continue
        break
    u = urlsplit(cur)
    host, https_ = u.hostname, u.scheme == "https"
    port = u.port or (443 if https_ else 80)
    loop = asyncio.get_running_loop()
    t0 = time.perf_counter()
    await loop.getaddrinfo(host, port)
    dns_ms = (time.perf_counter() - t0) * 1000
    tcp = await tcp_ms(ip, port, 5.0)
    tls = None
    if https_:
        try:
            tls = await tls_probe(ip, port, host)
        except (ssl.SSLError, OSError, asyncio.TimeoutError):
            tls = None
    out = ["🧪 <b>HTTP inspector</b>", f"<code>{e(url[:80])}</code>\n"]
    out += [f"{'↪️' if 300 <= s < 400 else '•'} {s} · <code>{e(c[:70])}</code> · {m:.0f}ms" for s, c, m in chain]
    timing = f"DNS: {dns_ms:.0f}ms · TCP: {tcp:.0f}ms" if tcp is not None else f"DNS: {dns_ms:.0f}ms"
    if tls:
        timing += f" · TLS: {tls['ms']:.0f}ms"
    out += ["", timing]
    if tls:
        out.append(f"TLS: {e(str(tls['version']))} · ALPN: {e(str(tls['alpn'] or '-'))}")
    out.append(f"HTTP/3: {'✅' if 'h3' in hdrs.get('alt-svc', '') else '—'} · HSTS: {'✅' if 'strict-transport-security' in hdrs else '❌'}")
    out.append(f"Compression: {e(hdrs.get('content-encoding', '-'))} · Type: {e(hdrs.get('content-type', '-')[:40])}")
    for k in ("server", "x-powered-by", "via"):
        if hdrs.get(k):
            out.append(f"{k}: {e(hdrs[k][:50])}")
    cdn = detect_cdn(hdrs)
    if cdn:
        out.append(f"CDN: {cdn}")
    if status >= 400:
        out.append(tr("\n⚠️ سرور کد خطای {0} برگردونده.", status))
    extra = []
    if len(f"hi:{host}".encode()) <= 64:
        extra.append([btn(tr("🇮🇷 چک از ایران"), f"hi:{host}", "success")])
    return "\n".join(out), extra


def _parse_http(v):
    ent = v[0] if isinstance(v, list) and v else None
    if v is None:
        return "pending", None
    if isinstance(ent, list) and len(ent) >= 4:
        if ent[0] == 1:
            return "ok", f"{ent[3]} · {float(ent[1]) * 1000:.0f}ms"
        return "fail", str(ent[2] or ent[3] or "error")[:40]
    return "fail", "error"


async def tool_http_iran(host: str):
    nodes = await ch_nodes()
    ir = [n for n, v in nodes.items() if v.get("location", [""])[0] == "ir"]
    if not ir:
        raise ValueError(tr("الان هیچ نود ایرانی در check-host فعال نیست."))
    control = [n for n in CONTROL_PREF if n in nodes][:2]
    j, res = await ch_run("http", f"https://{host}", ir + control)
    info = j.get("nodes", {})
    st = {n: _parse_http(res.get(n)) for n in info}
    e = escape
    lines = []
    for n in info:
        cc, _c, city, _ip, asn = (list(info[n]) + [""] * 5)[:5]
        s_, v = st[n]
        mark = f"✅ {v}" if s_ == "ok" else f"❌ {e(str(v))}" if s_ == "fail" else tr("⏳ بدون نتیجه")
        lines.append(f"{_flag(cc)} {e(city_name(city) if cc == 'ir' else city)} · {e(asn)} — {mark}")
    ir_ok = sum(1 for n in info if n in ir and st[n][0] == "ok")
    c_ok = sum(1 for n in info if n not in ir and st[n][0] == "ok")
    if ir_ok == 0 and c_ok > 0:
        verdict = tr("🚫 از ایران باز نمی‌شه ولی از خارج باز می‌شه؛ احتمالاً فیلتر شده.")
    elif ir_ok == 0:
        verdict = tr("⚠️ از هیچ‌جا باز نمی‌شه؛ مشکل از خود سایته.")
    else:
        verdict = tr("✅ از نودهای ایران باز می‌شه.")
    return f"🇮🇷 <b>HTTP</b> · <code>{e(host)}</code>\n\n" + "\n".join(lines) + f"\n\n{verdict}", []


# ───────────── 🧭 DNS از نودهای ایران ─────────────
async def tool_dnsir(text: str) -> str:
    dom = clean_domain(text)
    nodes = await ch_nodes()
    ir = [n for n, v in nodes.items() if v.get("location", [""])[0] == "ir"]
    if not ir:
        raise ValueError(tr("الان هیچ نود ایرانی در check-host فعال نیست."))
    control = [n for n in CONTROL_PREF if n in nodes][:2]
    j, res = await ch_run("dns", dom, ir + control)
    info = j.get("nodes", {})
    e = escape
    answers: dict[str, set[str]] = {}
    lines, blockpage, private = [], False, False
    for n in info:
        v = res.get(n)
        cc, _c, city, _ip, asn = (list(info[n]) + [""] * 5)[:5]
        label = f"{_flag(cc)} {e(city_name(city) if cc == 'ir' else city)} · {e(asn)}"
        ent = v[0] if isinstance(v, list) and v else None
        if not isinstance(ent, dict):
            lines.append(f"{label} — " + tr("⏳ بدون نتیجه"))
            continue
        ips = list(ent.get("A") or []) + list(ent.get("AAAA") or [])
        answers[n] = set(ips)
        if cc == "ir":
            blockpage |= any(a.startswith("10.10.34.") for a in ips)
            private |= any(ipaddress.ip_address(a).is_private for a in ips if re.fullmatch(r"[\d.:a-f]+", a))
        shown = ", ".join(e(a) for a in ips[:3]) + (f" +{len(ips) - 3}" if len(ips) > 3 else "")
        lines.append(f"{label} — " + (f"<code>{shown}</code>" if ips else "❌ " + tr("جواب نداد")))
    ir_sets = [s for n, s in answers.items() if n in ir]
    ct_union = set().union(*[s for n, s in answers.items() if n not in ir]) if any(n not in ir for n in answers) else set()
    ir_union = set().union(*ir_sets) if ir_sets else set()
    if blockpage:
        verdict = tr("🚫 آی‌پی صفحه‌ی مسدودسازی (10.10.34.x) برگشته؛ این دامنه توی ایران با DNS فیلتر شده.")
    elif private:
        verdict = tr("🚫 از ایران آی‌پی خصوصی برگشته؛ احتمالاً DNS دستکاری شده.")
    elif not ir_union:
        verdict = tr("⚠️ نودهای ایران جوابی ندادن.")
    elif ct_union and not (ir_union & ct_union):
        verdict = tr("⚠️ جواب DNS توی ایران با خارج فرق داره. اگه دامنه پشت CDN باشه عادیه، وگرنه ممکنه دستکاری شده باشه.")
    else:
        verdict = tr("✅ جواب DNS از ایران با خارج هم‌خونی داره.")
    return f"🧭 <b>DNS</b> · <code>{e(dom)}</code>\n\n" + "\n".join(lines) + f"\n\n{verdict}"


# ───────────── 🇮🇷 پایش خودکار فیلتر (برای مانیتور) ─────────────
IRAN_EVERY = 1800     # هر ۳۰ دقیقه
IRAN_RECHECK = 300    # اگه مشکوک شد، ۵ دقیقه بعد دوباره
IRAN_BATCH = 8        # حداکثر چک از ایران در هر دور (برای رعایت محدودیت check-host)
IRAN_WATCH_MAX = 3    # هر کاربر حداکثر ۳ سرور


async def iran_reach(host: str, port: int):
    _s, ip = await resolve_target(host)
    nodes = await ch_nodes()
    ir = [n for n, v in nodes.items() if v.get("location", [""])[0] == "ir"]
    control = [n for n in CONTROL_PREF if n in nodes][:2]
    target = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
    j, res = await ch_run("tcp", target, ir + control, polls=10)
    st = {n: _parse_tcp(res.get(n))[0] for n in j.get("nodes", {})}
    ir_done = sum(1 for n in st if n in ir and st[n] != "pending")
    ir_ok = sum(1 for n in st if n in ir and st[n] == "ok")
    c_ok = sum(1 for n in st if n not in ir and st[n] == "ok")
    return ir_ok, ir_done, c_ok


async def iran_alert(bot, row, blocked: bool) -> None:
    LANG.set(await get_lang(row["uid"]) or "fa")
    label = f"{row['host']}:{row['port']}"
    when = datetime.now(TEHRAN).strftime("%H:%M")
    if blocked:
        text = tr("🚫 <b>احتمالاً فیلتر شد</b>\n<code>{0}</code>\nاز خارج ایران بازه ولی از نودهای ایران جواب نمی‌گیره. بهتره IP یا پورت رو عوض کنی.\nساعت {1} به وقت تهران", escape(label), when)
    else:
        text = tr("✅ <b>دوباره از ایران در دسترسه</b>\n<code>{0}</code>\nساعت {1} به وقت تهران", escape(label), when)
    target = f"[{row['host']}]:{row['port']}" if ":" in row["host"] else f"{row['host']}:{row['port']}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn(tr("🇮🇷 چک کامل"), f"ir:{target}", "primary")]]) if len(f"ir:{target}".encode()) <= 64 else None
    try:
        await bot.send_message(row["uid"], rtl(text), reply_markup=kb)
    except TelegramForbiddenError:
        await db("DELETE FROM monitors WHERE uid=?", (row["uid"],))
    except Exception:
        log.exception("iran alert failed")


async def iran_cycle(bot) -> None:
    now = time.time()
    rows, _, _ = await db("SELECT * FROM monitors WHERE iran_watch=1 AND state=1")
    due = [r for r in rows if (r["iran_check"] or 0) + (IRAN_RECHECK if r["iran_fail"] else IRAN_EVERY) <= now]
    due.sort(key=lambda r: r["iran_check"] or 0)
    for r in due[:IRAN_BATCH]:
        st, fail = r["iran_state"], r["iran_fail"] or 0
        try:
            ir_ok, ir_done, c_ok = await iran_reach(r["host"], r["port"])
        except Exception:
            log.info("iran check failed for %s", r["host"])
            await db("UPDATE monitors SET iran_check=? WHERE id=?", (time.time(), r["id"]))
            continue
        alert = None
        if ir_done >= 3 and ir_ok == 0 and c_ok > 0:      # از خارج باز، از ایران بسته
            fail += 1
            if fail >= 2 and st != 0:                       # دو بار پشت‌سرهم تایید شد
                st, alert = 0, True
        elif ir_done >= 3 and ir_ok >= max(1, ir_done // 2):
            fail = 0
            if st == 0:
                alert = False
            st = 1
        await db("UPDATE monitors SET iran_state=?, iran_fail=?, iran_check=? WHERE id=?", (st, fail, time.time(), r["id"]))
        if alert is not None:
            await iran_alert(bot, r, alert)
        await asyncio.sleep(1)


# ───────────── 📈 نمودار مانیتور ─────────────
def render_chart(points, title: str) -> bytes:
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    fig, ax = plt.subplots(figsize=(10, 4), dpi=140)
    half = timedelta(seconds=CHECK_EVERY / 2)
    xs = [datetime.fromtimestamp(t, TEHRAN) for t, _u, _m in points]
    for x, (_t, up, _m) in zip(xs, points):
        if not up:
            ax.axvspan(x - half, x + half, color="#ef4444", alpha=0.28, lw=0)
    ux = [x for x, (_t, up, m) in zip(xs, points) if up and m is not None]
    uy = [m for _t, up, m in points if up and m is not None]
    if uy:
        ax.plot(ux, uy, color="#2563eb", lw=1.4, marker="o", ms=2)
    else:
        ax.set_ylim(0, 1)
    ax.set_ylabel("TCP connect (ms)")
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M", tz=TEHRAN))
    fig.autofmt_xdate()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


TOOLS = {"ip": tool_ip, "dns": tool_dns, "subs": tool_subs, "hdr": tool_hdr, "whois": tool_whois, "ssl": tool_ssl, "ping": tool_ping, "iran": tool_iran, "ss": tool_ss,
         "reality": tool_reality, "cfg": tool_cfg, "asn": tool_asn, "email": tool_email, "http": tool_http, "dnsir": tool_dnsir}


# ───────────── ایموجی پرمیوم ─────────────
ADMINS = {int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()}


def _icons_in(markup) -> bool:
    return isinstance(markup, InlineKeyboardMarkup) and any(
        getattr(b, "icon_custom_emoji_id", None) for row in markup.inline_keyboard for b in row
    )


def _strip_icons(markup):
    """اگه تلگرام آیکن پرمیوم رو قبول نکرد، ایموجی معمولی رو برمی‌گردونیم."""
    rows = []
    for row in markup.inline_keyboard:
        new_row = []
        for b in row:
            if getattr(b, "icon_custom_emoji_id", None):
                text = f"{premium.emoji_of(b.icon_custom_emoji_id)} {b.text}".strip()
                b = b.model_copy(update={"icon_custom_emoji_id": None, "text": text})
            new_row.append(b)
        rows.append(new_row)
    return markup.model_copy(update={"inline_keyboard": rows})


class PremiumMiddleware(BaseRequestMiddleware):
    """هر پیام خروجی رو قبل از ارسال premium می‌کنه؛ اگه تلگرام رد کرد، بدون پرمیوم دوباره می‌فرسته."""

    async def __call__(self, make_request, bot, method):
        new, premium_used = method, False
        if premium.ENABLED:
            if isinstance(method, (SendMessage, EditMessageText)) and isinstance(method.text, str):
                text, n = premium.premiumize(method.text)
                if n:
                    new, premium_used = method.model_copy(update={"text": text}), True
            elif isinstance(method, SendPhoto) and isinstance(method.caption, str):
                cap, n = premium.premiumize(method.caption)
                if n:
                    new, premium_used = method.model_copy(update={"caption": cap}), True
            premium_used = premium_used or _icons_in(getattr(method, "reply_markup", None))
        try:
            return await make_request(bot, new)
        except TelegramBadRequest as ex:
            if not premium_used or "not modified" in str(ex):
                raise
            log.warning("premium emoji rejected by Telegram, resending plain: %s", ex)
            plain = method
            if _icons_in(getattr(method, "reply_markup", None)):
                plain = method.model_copy(update={"reply_markup": _strip_icons(method.reply_markup)})
            return await make_request(bot, plain)


def _is_admin(msg: Message) -> bool:
    return bool(msg.from_user and msg.from_user.id in ADMINS)


# ───────────── 👥 دستورهای گروه: /asn /ping /ip ─────────────
async def _grp_arg(msg: Message, command, usage: str) -> str | None:
    arg = (command.args or "").strip()
    if not arg and msg.reply_to_message and msg.reply_to_message.text:
        arg = msg.reply_to_message.text.split()[0]
    if not arg:
        await msg.reply(usage)
        return None
    if not cooldown_ok(msg.from_user.id):
        await msg.reply(tr("⏳ کمی صبر کن و دوباره بفرست."))
        return None
    return arg


@router.message(Command("bgp"))
async def grp_asn(msg: Message, command: CommandObject):
    arg = await _grp_arg(msg, command, "/bgp <code>AS13335</code> | <code>1.1.1.1</code> | <code>example.com</code>")
    if not arg:
        return
    wait = await msg.reply(tr("⏳ در حال بررسی..."))
    try:
        text, _extra, attach = await tool_asn(arg)
    except ValueError as ex:
        await wait.edit_text(f"⚠️ {escape(str(ex))}")
        return
    except httpx.HTTPError:
        await wait.edit_text(tr("❌ سرویس منبع جواب نداد، بعداً امتحان کن."))
        return
    await wait.delete()
    await msg.reply_photo(BufferedInputFile(attach[1], filename=attach[2]), caption=rtl(attach[3])[:1020])


async def _grp_ping(msg: Message, command: CommandObject, mode: str, cmd: str):
    arg = await _grp_arg(msg, command, f"/{cmd} <code>1.2.3.4</code> | <code>example.com</code>")
    if not arg:
        return
    wait = await msg.reply(tr("⏳ در حال پینگ از نودها؛ حدود ۱۰ تا ۳۰ ثانیه طول می\u200cکشه..."))
    try:
        port_quota(msg.from_user.id)
        host, _ = parse_hostport(arg.split()[0])
        shown, ip = await resolve_target(host)
        text = await ping_check(shown, ip, mode)
    except ValueError as ex:
        text = f"⚠️ {escape(str(ex))}"
    except httpx.HTTPError:
        text = tr("❌ سرویس check-host جواب نداد، بعداً امتحان کن.")
    await safe_edit(wait, text)


@router.message(Command("ping"))
async def grp_ping(msg: Message, command: CommandObject):
    await _grp_ping(msg, command, "all", "ping")  # پینگ جهانی: مستقیم همه‌ی نودها


@router.message(Command("pingir"))
async def grp_pingir(msg: Message, command: CommandObject):
    await _grp_ping(msg, command, "ir", "pingir")  # فقط ایران + دو نود شاهد


@router.message(Command("ip"))
async def grp_ip(msg: Message, command: CommandObject):
    arg = await _grp_arg(msg, command, "/ip <code>8.8.8.8</code>")
    if not arg:
        return
    try:
        res = await tool_ip(arg)
    except ValueError as ex:
        await msg.reply(f"⚠️ {escape(str(ex))}")
        return
    except httpx.HTTPError:
        await msg.reply(tr("❌ سرویس منبع جواب نداد، بعداً امتحان کن."))
        return
    text = res[0] if isinstance(res, tuple) else res
    await msg.reply(rtl(text), disable_web_page_preview=True)


@router.message(Command("id"))
async def cmd_id(msg: Message):
    await msg.answer(f"<code>{msg.from_user.id}</code>")


EMOJI_PACKS = [p.strip() for p in os.environ.get("EMOJI_PACKS", "CenterOfEmoji27799750,FluentEmojiSet5").split(",") if p.strip()]


async def import_pack(bot: Bot, name: str):
    """همه‌ی ایموجی‌های یک پک رو توی نقشه می‌ریزه؛ (عنوان، تعداد ایموجی، تعداد جدید) برمی‌گردونه."""
    sset = await bot.get_sticker_set(name)
    pairs = {}
    for st in sset.stickers:
        if st.custom_emoji_id and st.emoji:
            pairs.setdefault(st.emoji, st.custom_emoji_id)  # اگه چند استیکر یک ایموجی داشتن، اولی
    return sset.title, len(pairs), premium.set_many(pairs)


async def sync_packs(bot: Bot) -> int:
    total = 0
    for name in EMOJI_PACKS:
        try:
            _title, _n, added = await import_pack(bot, name)
            total += added
        except Exception:
            log.exception("could not import emoji pack %s", name)
    return total


@router.message(Command("pack"))
async def cmd_pack(msg: Message):
    """/pack <لینک یا اسم پک ایموجی> ؛ همه‌ی ایموجی‌های پک رو یک‌جا به نقشه اضافه می‌کنه."""
    if not _is_admin(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Usage: <code>/pack https://t.me/addemoji/PackName</code>")
        return
    name = re.search(r"addemoji/([A-Za-z0-9_]+)", parts[1]) or re.search(r"([A-Za-z0-9_]+)\s*$", parts[1])
    try:
        title, n, added = await import_pack(msg.bot, name.group(1))
    except TelegramBadRequest as ex:
        await msg.answer(f"❌ {escape(str(ex))}")
        return
    await msg.answer(f"✅ <b>{escape(title)}</b>: {n} emoji in pack, {added} added.\nTotal mapped: {premium.count()}")


@router.message(Command("sync"))
async def cmd_sync(msg: Message):
    """/sync ؛ پک‌های EMOJI_PACKS رو دوباره می‌خونه."""
    if _is_admin(msg):
        added = await sync_packs(msg.bot)
        await msg.answer(f"✅ {added} new. Total mapped: {premium.count()} ({', '.join(EMOJI_PACKS)})")


@router.message(Command("map"))
async def cmd_map(msg: Message):
    """/map 🌐 <ایموجی پرمیوم> ؛ یه ایموجی معمولی رو به یه ایموجی پرمیوم مشخص وصل می‌کنه."""
    if not _is_admin(msg):
        return
    parts = (msg.text or "").split(maxsplit=2)
    ce = [e for e in (msg.entities or []) if e.type == "custom_emoji"]
    if len(parts) < 3 or not ce:
        await msg.answer("Usage: <code>/map 🌐</code> followed by a premium emoji, e.g. /map 🌐 + [premium emoji]")
        return
    premium.set_many({parts[1]: ce[0].custom_emoji_id}, overwrite=True)
    await msg.answer(f"✅ {escape(parts[1])} → <code>{ce[0].custom_emoji_id}</code>")


@router.message(Command("emojis"))
async def cmd_emojis(msg: Message):
    if not _is_admin(msg):
        return
    miss = premium.missing()
    await msg.answer(
        f"Mapped from packs/manual: <b>{premium.count()}</b> · effective: <b>{premium.effective_count()}</b>\n"
        f"Enabled: <b>{premium.ENABLED}</b>\n\n"
        + (f"Still plain (no premium version): {' '.join(miss)}\n\nFix with <code>/map 🟢</code> + a premium emoji, or <code>/pack</code> another pack."
           if miss else "All emoji used by the bot have a premium version ✅")
    )


@router.message(lambda m: _is_admin(m) and any(e.type == "custom_emoji" for e in (m.entities or [])))
async def show_custom_ids(msg: Message):
    """ادمین یه ایموجی پرمیوم می‌فرسته؛ ربات id‌ش رو برمی‌گردونه."""
    ids = [e.custom_emoji_id for e in msg.entities if e.type == "custom_emoji"]
    await msg.answer("\n".join(f"<code>{i}</code>" for i in ids))


# ───────────── زبان ─────────────
_lang_cache: dict[int, str] = {}
LANG_PICK = "🌐 زبانت رو انتخاب کن\nChoose your language"  # noi18n


async def get_lang(uid: int) -> str | None:
    """زبان ذخیره‌شده‌ی کاربر؛ اگه هنوز انتخاب نکرده None."""
    if uid not in _lang_cache:
        rows, _, _ = await db("SELECT lang FROM users WHERE uid=?", (uid,))
        if not rows:
            return None
        _lang_cache[uid] = rows[0]["lang"]
    return _lang_cache[uid]


async def set_lang(uid: int, lang: str) -> None:
    await db("INSERT OR REPLACE INTO users(uid, lang, created) VALUES (?,?,?)", (uid, lang, time.time()))
    _lang_cache[uid] = lang


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        btn("🇮🇷 فارسی", "lg:fa", "primary"),  # noi18n
        btn("🇬🇧 English", "lg:en", "primary"),
    ]])


class LangMiddleware(BaseMiddleware):
    """زبان کاربر رو برای هر آپدیت توی LANG می‌ذاره تا همه‌ی متن‌ها با همون زبان ساخته بشن."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user:
            LANG.set(await get_lang(user.id) or "fa")
        return await handler(event, data)


# ───────────── هندلرها ─────────────
@router.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    if await get_lang(msg.from_user.id) is None:
        await msg.answer(LANG_PICK, reply_markup=lang_kb())
        return
    await msg.answer(welcome_text(), reply_markup=menu_kb())


@router.callback_query(F.data.in_({"lg:ask", "lg:fa", "lg:en"}))
async def lang_choice(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if cb.data == "lg:ask":
        await cb.message.edit_text(LANG_PICK, reply_markup=lang_kb())
    else:
        lang = cb.data[3:]
        await set_lang(cb.from_user.id, lang)
        LANG.set(lang)
        await cb.message.edit_text(welcome_text(), reply_markup=menu_kb())
    await cb.answer()


@router.callback_query(F.data == "m:home")
async def home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if cb.message.photo:
        # پیام عکس‌دار (مثل BGP MAP) متن نداره که ادیت بشه؛ دکمه‌ش رو برمی‌داریم و منو رو پیام جدید می‌فرستیم
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await cb.message.answer(welcome_text(), reply_markup=menu_kb())
    else:
        await cb.message.edit_text(welcome_text(), reply_markup=menu_kb())
    await cb.answer()


@router.callback_query(F.data == "m:help")
async def help_(cb: CallbackQuery):
    await cb.message.edit_text(rtl(help_text()), reply_markup=home_kb())
    await cb.answer()


@router.callback_query(F.data.in_({"m:ip", "m:dns", "m:subs", "m:hdr", "m:whois", "m:ssl", "m:ping", "m:iran", "m:ss",
                                    "m:reality", "m:cfg", "m:asn", "m:email", "m:http", "m:dnsir"}))
async def pick(cb: CallbackQuery, state: FSMContext):
    kind = cb.data[2:]
    await state.set_state(getattr(Wait, kind))
    await cb.message.edit_text(rtl(prompt_text(kind)), reply_markup=cancel_kb())
    await cb.answer()


# ── چک پورت ──
@router.callback_query(F.data == "m:port")
async def port_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Wait.port_target)
    await cb.message.edit_text(rtl(port_prompt()), reply_markup=cancel_kb())
    await cb.answer()


@router.message(F.text, StateFilter(Wait.port_target))
async def port_target(msg: Message, state: FSMContext):
    try:
        shown, ip = await resolve_target(msg.text)
    except ValueError as ex:
        await msg.answer(f"⚠️ {escape(str(ex))}", reply_markup=cancel_kb())
        return
    await state.update_data(shown=shown, ip=ip)
    await state.set_state(None)
    await msg.answer(
        tr("🎯 هدف: <code>{0}</code>", escape(shown)) + (f" → <code>{ip}</code>" if shown != ip else "")
        + tr("\n\nچی بررسی کنم؟"),
        reply_markup=port_menu_kb(),
    )


async def _port_target_of(state: FSMContext):
    d = await state.get_data()
    return d.get("shown"), d.get("ip")


@router.callback_query(F.data == "p:back")
async def port_back(cb: CallbackQuery, state: FSMContext):
    shown, ip = await _port_target_of(state)
    await state.set_state(None)
    await cb.message.edit_text(tr("🎯 هدف: <code>{0}</code>\n\nچی بررسی کنم؟", escape(str(shown))), reply_markup=port_menu_kb())
    await cb.answer()


@router.callback_query(F.data == "p:cmd")
async def port_cmd(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn(tr("↩️ برگشت"), "p:back", "primary")]])
    await cb.message.edit_text(rtl(port_cmd_text()), reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "p:common")
async def port_common(cb: CallbackQuery, state: FSMContext):
    shown, ip = await _port_target_of(state)
    if not ip:
        await cb.answer(tr("نشست منقضی شد، دوباره هدف رو بفرست."), show_alert=True)
        return
    try:
        port_quota(cb.from_user.id)
    except ValueError as ex:
        await cb.answer(str(ex), show_alert=True)
        return
    await cb.answer()
    await cb.message.edit_text(tr("⏳ در حال چک {0} پورت...", len(COMMON_PORTS)))
    res = await scan(ip, COMMON_PORTS)
    await cb.message.edit_text(rtl(fmt_scan(shown, ip, res)), reply_markup=port_menu_kb())


@router.callback_query(F.data == "p:custom")
async def port_custom_ask(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Wait.port_custom)
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn(tr("↩️ برگشت"), "p:back", "danger")]])
    await cb.message.edit_text(
        tr("🎯 پورت (یا چند پورت) رو بفرست:\n<code>443</code>\n<code>80,443,8443</code>\n<code>8000-8005</code>\n(حداکثر ۲۰ پورت)"),
        reply_markup=kb,
    )
    await cb.answer()


@router.message(F.text, StateFilter(Wait.port_custom))
async def port_custom(msg: Message, state: FSMContext):
    shown, ip = await _port_target_of(state)
    if not ip:
        await state.clear()
        await msg.answer(tr("نشست منقضی شد."), reply_markup=menu_kb())
        return
    try:
        ports = parse_ports(msg.text)
        port_quota(msg.from_user.id)
    except ValueError as ex:
        await msg.answer(f"⚠️ {escape(str(ex))}")
        return
    wait = await msg.answer(tr("⏳ در حال چک..."))
    res = await scan(ip, ports)
    await state.set_state(None)
    await wait.edit_text(rtl(fmt_scan(shown, ip, res)), reply_markup=port_menu_kb())


# ── مانیتور ──
@router.callback_query(F.data == "m:mon")
async def mon_home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    text, kb = await render_monitors(cb.from_user.id)
    await safe_edit(cb.message, text, kb)
    await cb.answer()


@router.callback_query(F.data == "mon:add")
async def mon_add_ask(cb: CallbackQuery, state: FSMContext):
    rows, _, _ = await db("SELECT 1 FROM monitors WHERE uid=?", (cb.from_user.id,))
    if len(rows) >= MAX_MON:
        await cb.answer(tr("حداکثر {0} سرور می\u200cتونی اضافه کنی.", MAX_MON), show_alert=True)
        return
    await state.set_state(Wait.mon_add)
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn(tr("↩️ برگشت"), "m:mon", "danger")]])
    await safe_edit(
        cb.message,
        tr("📡 سرور رو به شکل <code>host:port</code> بفرست.\nمثال: <code>1.2.3.4:443</code> یا <code>example.com:8443</code>\n\n<i>فقط سرور خودت رو اضافه کن.</i>"),
        kb,
    )
    await cb.answer()


@router.message(F.text, StateFilter(Wait.mon_add))
async def mon_add(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    try:
        host, port = parse_hostport(msg.text)
        shown, _ = await resolve_target(host)
    except ValueError as ex:
        await msg.answer(f"⚠️ {escape(str(ex))}")
        return
    rows, _, _ = await db("SELECT 1 FROM monitors WHERE uid=?", (uid,))
    if len(rows) >= MAX_MON:
        await msg.answer(tr("⚠️ حداکثر {0} سرور می\u200cتونی اضافه کنی.", MAX_MON))
        return
    try:
        _, mid, _ = await db(
            "INSERT INTO monitors(uid, host, port, created) VALUES (?,?,?,?)", (uid, shown, port, time.time())
        )
    except sqlite3.IntegrityError:
        await msg.answer(tr("⚠️ این سرور قبلاً اضافه شده."))
        return
    up, ms = await check_up(shown, port)
    await set_state(await get_mon(mid, uid), up, ms)
    await state.clear()
    text, kb = await render_monitors(uid)
    await msg.answer(rtl(text), reply_markup=kb)


@router.callback_query(F.data.startswith("mon:chk:"))
async def mon_check(cb: CallbackQuery):
    row = await get_mon(int(cb.data.split(":")[2]), cb.from_user.id)
    if not row:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    await cb.answer(tr("⏳ در حال چک..."))
    up, ms = await check_up(row["host"], row["port"])
    await set_state(row, up, ms)  # کاربر خودش نتیجه رو می‌بینه، پس هشدار جدا نمی‌ره
    text, kb = await render_monitors(cb.from_user.id)
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("mon:del:"))
async def mon_delete(cb: CallbackQuery):
    await db("DELETE FROM monitors WHERE id=? AND uid=?", (int(cb.data.split(":")[2]), cb.from_user.id))
    text, kb = await render_monitors(cb.from_user.id)
    await safe_edit(cb.message, text, kb)
    await cb.answer(tr("🗑 حذف شد"))


@router.callback_query(F.data.startswith("mon:re:"))
async def mon_recheck(cb: CallbackQuery):
    row = await get_mon(int(cb.data.split(":")[2]), cb.from_user.id)
    if not row:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    await cb.answer(tr("⏳ در حال چک..."))
    up, ms = await check_up(row["host"], row["port"])
    await cb.message.answer(
        rtl(tr("✅ الان بالاست · {0}ms", int(ms)) if up else tr("❌ هنوز قطعه"))
    )


@router.callback_query(F.data.startswith("mon:ir:"))
async def mon_iran(cb: CallbackQuery):
    row = await get_mon(int(cb.data.split(":")[2]), cb.from_user.id)
    if not row:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    try:
        port_quota(cb.from_user.id)
    except ValueError as ex:
        await cb.answer(str(ex), show_alert=True)
        return
    await cb.answer()
    wait = await cb.message.answer(tr("⏳ در حال چک از نودهای ایران..."))
    try:
        text, extra = await tool_iran(f"{row['host']}:{row['port']}")
    except ValueError as ex:
        text, extra = f"⚠️ {escape(str(ex))}", []
    except httpx.HTTPError:
        text, extra = tr("❌ سرویس check-host جواب نداد، بعداً امتحان کن."), []
    await wait.edit_text(rtl(text), reply_markup=InlineKeyboardMarkup(inline_keyboard=extra), disable_web_page_preview=True)


# ── پینگ از ایران و جهان ──
@router.callback_query(F.data == "m:cping")
async def cping_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Wait.cping)
    await safe_edit(
        cb.message,
        tr("🏓 آی\u200cپی یا دامنه\u200cی سرورت رو بفرست (پورت لازم نیست).\nپینگ از نودهای ایران و چند نود شاهد خارج از ایران گرفته می\u200cشه."),
        cancel_kb(),
    )
    await cb.answer()


async def _run_ping(target_msg, state: FSMContext, uid: int, mode: str, edit: bool):
    d = await state.get_data()
    shown, ip = d.get("pshown"), d.get("pip")
    if not ip:
        await target_msg.answer(tr("نشست منقضی شد، دوباره از منو شروع کن."), reply_markup=menu_kb())
        return
    try:
        port_quota(uid)
    except ValueError as ex:
        await target_msg.answer(f"⚠️ {escape(str(ex))}")
        return
    wait = target_msg if edit else await target_msg.answer("⏳")
    await safe_edit(wait, tr("⏳ در حال پینگ از نودها؛ حدود ۱۰ تا ۳۰ ثانیه طول می\u200cکشه..."))
    try:
        text = await ping_check(shown, ip, mode)
    except ValueError as ex:
        text = f"⚠️ {escape(str(ex))}"
    except httpx.HTTPError:
        text = tr("❌ سرویس check-host جواب نداد، بعداً امتحان کن.")
    await safe_edit(wait, text, ping_kb(mode))


@router.message(F.text, StateFilter(Wait.cping))
async def cping_target(msg: Message, state: FSMContext):
    if not cooldown_ok(msg.from_user.id):
        await msg.answer(tr("⏳ کمی صبر کن و دوباره بفرست."))
        return
    try:
        host, _ = parse_hostport(msg.text)
        shown, ip = await resolve_target(host)
    except ValueError as ex:
        await msg.answer(f"⚠️ {escape(str(ex))}", reply_markup=cancel_kb())
        return
    await state.update_data(pshown=shown, pip=ip)
    await state.set_state(None)
    await _run_ping(msg, state, msg.from_user.id, "all", edit=False)


@router.callback_query(F.data.in_({"pg:ir", "pg:all"}))
async def cping_again(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await _run_ping(cb.message, state, cb.from_user.id, cb.data[3:], edit=True)


# ── هشدار انقضا ──
@router.callback_query(F.data == "m:exp")
async def exp_home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    text, kb = await render_expiry(cb.from_user.id)
    await safe_edit(cb.message, text, kb)
    await cb.answer()


@router.callback_query(F.data == "ex:add")
async def exp_add_ask(cb: CallbackQuery, state: FSMContext):
    rows, _, _ = await db("SELECT 1 FROM expiry WHERE uid=?", (cb.from_user.id,))
    if len(rows) >= MAX_EXP:
        await cb.answer(tr("حداکثر {0} مورد می\u200cتونی اضافه کنی.", MAX_EXP), show_alert=True)
        return
    await state.set_state(Wait.exp_add)
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn(tr("↩️ برگشت"), "m:exp", "danger")]])
    await safe_edit(
        cb.message,
        tr("⏰ دامنه رو بفرست. برای SSL می\u200cتونی پورت هم بنویسی.\nمثال: <code>example.com</code> یا <code>example.com:8443</code>"),
        kb,
    )
    await cb.answer()


@router.message(F.text, StateFilter(Wait.exp_add))
async def exp_add_target(msg: Message, state: FSMContext):
    try:
        host, port = parse_hostport(msg.text)
        host = clean_domain(host)
        await resolve_target(host)
    except ValueError as ex:
        await msg.answer(f"⚠️ {escape(str(ex))}")
        return
    await state.update_data(exh=host, exp=port)
    await state.set_state(None)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn(tr("🔐 گواهی SSL"), "ex:k:ssl", "primary"), btn(tr("📇 انقضای دامنه"), "ex:k:dom", "primary")],
        [btn(tr("↩️ برگشت"), "m:exp", "danger")],
    ])
    await msg.answer(rtl(tr("کدوم رو برای <code>{0}</code> پایش کنم؟", escape(host))), reply_markup=kb)


@router.callback_query(F.data.in_({"ex:k:ssl", "ex:k:dom"}))
async def exp_add_kind(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    host, port = d.get("exh"), d.get("exp")
    if not host:
        await cb.answer(tr("نشست منقضی شد."), show_alert=True)
        return
    kind = "ssl" if cb.data == "ex:k:ssl" else "dom"
    port = port if kind == "ssl" else 0
    try:
        _, rid, _ = await db(
            "INSERT INTO expiry(uid, kind, host, port, created) VALUES (?,?,?,?,?)",
            (cb.from_user.id, kind, host, port, time.time()),
        )
    except sqlite3.IntegrityError:
        await cb.answer(tr("این مورد قبلاً اضافه شده."), show_alert=True)
        return
    await cb.answer(tr("⏳ در حال چک..."))
    try:
        days = await expiry_days(kind, host, port)
    except Exception:
        days = None
    if days is not None:  # اگه همین الان نزدیک انقضاست، هشدار تکراری ندیم
        await db("UPDATE expiry SET last_days=?, last_check=?, last_th=? WHERE id=?",
                 (days, time.time(), _due_threshold(days), rid))
    text, kb = await render_expiry(cb.from_user.id)
    await safe_edit(cb.message, text, kb)
    if days is None:
        await cb.message.answer(rtl(tr("⚠️ تاریخ انقضا همین الان از هیچ منبعی گرفته نشد. هر ۶ ساعت دوباره تلاش می\u200cکنم.")))


@router.callback_query(F.data.startswith("ex:chk:"))
async def exp_check(cb: CallbackQuery):
    rows, _, _ = await db("SELECT * FROM expiry WHERE id=? AND uid=?", (int(cb.data.split(":")[2]), cb.from_user.id))
    if not rows:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    r = rows[0]
    await cb.answer(tr("⏳ در حال چک..."))
    try:
        days = await expiry_days(r["kind"], r["host"], r["port"])
    except Exception:
        days = None
    if days is not None:
        await db("UPDATE expiry SET last_days=?, last_check=? WHERE id=?", (days, time.time(), r["id"]))
    text, kb = await render_expiry(cb.from_user.id)
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("ex:del:"))
async def exp_delete(cb: CallbackQuery):
    await db("DELETE FROM expiry WHERE id=? AND uid=?", (int(cb.data.split(":")[2]), cb.from_user.id))
    text, kb = await render_expiry(cb.from_user.id)
    await safe_edit(cb.message, text, kb)
    await cb.answer(tr("🗑 حذف شد"))


# ── دسته‌بندی منو و دکمه‌های مشترک ──
@router.callback_query(F.data.in_({"m:cat:vpn", "m:cat:web"}))
async def show_category(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    vpn = cb.data.endswith("vpn")
    text = (tr("🖧 <b>ابزارهای سرور و VPN</b>\nیکی از ابزارها رو انتخاب کن:") if vpn
            else tr("🌍 <b>ابزارهای وب و دامنه</b>\nیکی از ابزارها رو انتخاب کن:"))
    await safe_edit(cb.message, text, cat_kb("vpn" if vpn else "web"))
    await cb.answer()


@router.callback_query(F.data.startswith("ir:"))
async def ir_callback(cb: CallbackQuery):
    """دکمه‌ی «چک از ایران» که زیر نتیجه‌ی ابزارها و هشدارها میاد."""
    try:
        port_quota(cb.from_user.id)
    except ValueError as ex:
        await cb.answer(str(ex), show_alert=True)
        return
    await cb.answer()
    wait = await cb.message.answer(tr("⏳ در حال چک از نودهای ایران..."))
    try:
        text, extra = await tool_iran(cb.data[3:])
    except ValueError as ex:
        text, extra = f"⚠️ {escape(str(ex))}", []
    except httpx.HTTPError:
        text, extra = tr("❌ سرویس check-host جواب نداد، بعداً امتحان کن."), []
    await safe_edit(wait, text, InlineKeyboardMarkup(inline_keyboard=extra))


@router.callback_query(F.data.startswith("hi:"))
async def http_iran_callback(cb: CallbackQuery):
    try:
        port_quota(cb.from_user.id)
    except ValueError as ex:
        await cb.answer(str(ex), show_alert=True)
        return
    await cb.answer()
    wait = await cb.message.answer(tr("⏳ در حال چک از نودهای ایران..."))
    try:
        text, extra = await tool_http_iran(cb.data[3:])
    except ValueError as ex:
        text, extra = f"⚠️ {escape(str(ex))}", []
    except httpx.HTTPError:
        text, extra = tr("❌ سرویس check-host جواب نداد، بعداً امتحان کن."), []
    await safe_edit(wait, text, InlineKeyboardMarkup(inline_keyboard=extra))


# ── مانیتور: پایش فیلتر و نمودار ──
@router.callback_query(F.data.startswith("mon:wf:"))
async def mon_watch(cb: CallbackQuery):
    row = await get_mon(int(cb.data.split(":")[2]), cb.from_user.id)
    if not row:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    if row["iran_watch"]:
        await db("UPDATE monitors SET iran_watch=0, iran_state=NULL, iran_fail=0, iran_check=NULL WHERE id=?", (row["id"],))
        await cb.answer(tr("پایش فیلتر خاموش شد."))
    else:
        rows, _, _ = await db("SELECT 1 FROM monitors WHERE uid=? AND iran_watch=1", (cb.from_user.id,))
        if len(rows) >= IRAN_WATCH_MAX:
            await cb.answer(tr("حداکثر {0} سرور رو می‌تونی با پایش فیلتر بذاری.", IRAN_WATCH_MAX), show_alert=True)
            return
        await db("UPDATE monitors SET iran_watch=1, iran_state=NULL, iran_fail=0, iran_check=NULL WHERE id=?", (row["id"],))
        await cb.answer(tr("🇮🇷 پایش فیلتر روشن شد. هر ۳۰ دقیقه از نودهای ایران چک می‌شه و اگه IP یا پورت فیلتر بشه بهت خبر می‌دم."), show_alert=True)
    text, kb = await render_monitors(cb.from_user.id)
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("mon:ch:"))
async def mon_chart(cb: CallbackQuery):
    row = await get_mon(int(cb.data.split(":")[2]), cb.from_user.id)
    if not row:
        await cb.answer(tr("این مورد دیگه وجود نداره."), show_alert=True)
        return
    rows, _, _ = await db("SELECT ts, up, ms FROM samples WHERE mid=? AND ts>=? ORDER BY ts", (row["id"], time.time() - 86400))
    if len(rows) < 3:
        await cb.answer(tr("هنوز داده‌ی کافی نیست؛ بعد از چند چک دوباره امتحان کن."), show_alert=True)
        return
    await cb.answer(tr("⏳ در حال ساخت نمودار..."))
    pts = [(r["ts"], r["up"], r["ms"]) for r in rows]
    ups = [p for p in pts if p[1]]
    uptime = 100 * len(ups) / len(pts)
    ms = [p[2] for p in ups if p[2] is not None]
    outages = sum(1 for i, p in enumerate(pts) if not p[1] and (i == 0 or pts[i - 1][1]))
    label = f"{row['host']}:{row['port']}"
    png = await asyncio.to_thread(render_chart, pts, f"{label} · last 24h · uptime {uptime:.2f}%")
    cap = f"📈 {label} · 24h\nUptime: {uptime:.2f}% · Outages: {outages}"
    if ms:
        cap += f"\navg {sum(ms) / len(ms):.0f}ms · min {min(ms):.0f} · max {max(ms):.0f}"
    await cb.message.answer_photo(BufferedInputFile(png, filename="chart.png"), caption=cap)


@router.message(F.text, StateFilter(*SIMPLE))
async def run_tool(msg: Message, state: FSMContext):
    now = time.monotonic()
    if now - _last.get(msg.from_user.id, 0) < COOLDOWN:
        await msg.answer(tr("⏳ کمی صبر کن و دوباره بفرست."))
        return
    _last[msg.from_user.id] = now

    kind = (await state.get_state()).split(":")[1]
    wait = await msg.answer(tr("⏳ در حال بررسی..."))
    try:
        if kind in ("ping", "iran", "reality", "http", "dnsir"):
            port_quota(msg.from_user.id)
        res = TOOLS[kind](msg.text)
        if asyncio.iscoroutine(res):
            res = await res
    except ValueError as e:
        res = f"⚠️ {escape(str(e))}"
    except httpx.HTTPError:
        res = tr("❌ سرویس منبع جواب نداد، بعداً امتحان کن.")
    text, extra, attach = (list(res) + [[], None])[:3] if isinstance(res, tuple) else (res, [], None)
    kb = InlineKeyboardMarkup(inline_keyboard=[*extra, [btn(tr("🏠 منوی اصلی"), "m:home", "primary")]])
    await state.clear()
    if attach and attach[0] == "photo" and len(attach) > 3:
        # عکس و متن توی یک پیام (کپشن)
        await wait.delete()
        await msg.answer_photo(BufferedInputFile(attach[1], filename=attach[2]),
                               caption=rtl(attach[3])[:1020], reply_markup=kb)
        return
    await wait.edit_text(rtl(text), reply_markup=kb, disable_web_page_preview=True)
    if attach:
        kind_, data_, fname = attach[:3]
        if kind_ == "photo":
            await msg.answer_photo(BufferedInputFile(data_, filename=fname))
        else:
            await msg.answer_document(BufferedInputFile(data_, filename=fname))


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    bot.session.middleware(PremiumMiddleware())
    try:
        await bot.set_my_commands(
            [BotCommand(command="bgp", description="ASN / AS path map"),
             BotCommand(command="ping", description="Global ping (all nodes)"),
             BotCommand(command="pingir", description="Ping from Iran only"),
             BotCommand(command="ip", description="IP info")],
            scope=BotCommandScopeAllGroupChats(),
        )
    except Exception:
        log.warning("could not set group commands")
    added = await sync_packs(bot)
    log.info("premium emoji: %s from packs/manual (+%s new), enabled=%s, still plain: %s", premium.count(), added, premium.ENABLED, " ".join(premium.missing()))
    router.message.outer_middleware(LangMiddleware())
    router.callback_query.outer_middleware(LangMiddleware())
    dp.include_router(router)
    tasks = [asyncio.create_task(monitor_loop(bot)), asyncio.create_task(expiry_loop(bot))]
    try:
        await dp.start_polling(bot)
    finally:
        for t in tasks:
            t.cancel()
        await http.aclose()


if __name__ == "__main__":
    asyncio.run(main())
