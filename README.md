<div align="center">

# 👻 Hopper

**A passive-recon and server-diagnostics Telegram bot for VPN admins, sysadmins and curious security people.**
Bilingual (فارسی / English) · colorful inline menus · premium custom emoji · built on aiogram 3

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[فارسی](README.fa.md) · [English](README.md)

</div>

---

## What is Hopper?

Hopper answers the questions you keep asking when you run servers, especially in a country where connectivity is unreliable:

- *Is my server reachable from **inside Iran**, or is the IP/port filtered?*
- *Which ports are open? What is behind this IP?*
- *What does the BGP path to this prefix look like?*
- *When does my SSL certificate or domain expire?*
- *Did my server go down while I was asleep?*

Most tools use **public data sources only** (Shodan InternetDB, certificate transparency logs, RIPEstat, check-host.net, RDAP…). The only tools that open a connection to a target are the port check, TCP latency and the uptime monitor, and they make a plain TCP connect, nothing more.

## Features

### 🖧 Server & VPN tools
| Tool | What it does |
|---|---|
| 🌐 **IP info** | Geolocation, ASN, reverse DNS, open ports / services / known CVEs from Shodan InternetDB. Also describes private / reserved ranges. |
| 🔌 **Port check** | TCP connect to common or custom ports with service/banner identification. Rate-limited per user. |
| 🇮🇷 **Check from Iran** | Reachability of `host:port` from several nodes inside Iran plus control nodes abroad, with a verdict (filtered vs. down). |
| 🏓 **Global ping** | Ping from Iranian nodes or from every check-host node, sorted by latency. |
| ⚡ **TCP latency** | Connect-time measurement for up to 5 servers, handy for comparing them. |
| 📡 **Monitor** | Uptime/downtime alerts with a 24-hour chart. Optional automatic *filter watch* from Iran. |
| 🧾 **`ss -tulpn` analyzer** | Paste the output; get ports in use, the program behind each, internal-only ports, risky exposed databases and suggested free ports. |
| 🎭 **Reality checker** | Checks a candidate `dest` domain: TLS 1.3, HTTP/2, certificate and latency. |
| 🔗 **Config link analyzer** | Parses `vless://`, `vmess://`, `trojan://`, `ss://` links and flags weak settings. Keys are masked, nothing is stored. |
| 🕸 **ASN / BGP map** | AS path map in the style of bgpmap, drawn from RIPEstat data. |

### 🌍 Web & domain tools
| Tool | What it does |
|---|---|
| 🔎 **DNS** | A / AAAA / MX / NS / TXT … over DNS-over-HTTPS. |
| 🧭 **DNS from Iran** | Compares DNS answers from Iranian nodes with control nodes abroad (spot DNS poisoning and block pages). |
| 🧩 **Subdomains** | Merges 5 passive sources (crt.sh, CertSpotter, AnubisDB, OTX, HackerTarget) and reports which ones answered. |
| 📇 **Whois** | Registration / expiry dates and name servers via RDAP, with raw WHOIS (port 43) fallback. Supports `.ir`. |
| 🔐 **SSL info** | Validity, issuer, key type, SANs, protocol. Custom ports supported (`example.com:8443`). |
| 🛡 **Security headers** | HSTS, CSP and friends with a simple score. |
| 🧪 **HTTP inspector** | Redirect chain, status, headers and timing, with SSRF protection at every hop. |
| ✉️ **Email check** | SPF, DKIM and DMARC. |
| ⏰ **Expiry alerts** | Register up to 10 domains / certificates; get warned at 30, 15, 7, 3, 1 and 0 days. |

### 👥 Commands for groups
Add Hopper to a group and use these (as a command argument, or by replying to a message):

| Command | Description |
|---|---|
| `/bgp AS13335` · `/bgp 1.1.1.1` · `/bgp example.com` | ASN / AS path map |
| `/ping example.com` | Global ping (all nodes) |
| `/pingir example.com` | Ping from Iran only |
| `/ip 1.1.1.1` | IP info |

### ✨ Extras
- **Two languages**, chosen on `/start` and stored per user. All texts, errors and alerts follow it.
- **Premium custom emoji** in messages and button icons, with automatic fallback to normal emoji if Telegram rejects them.
- **Colored inline buttons** (`primary` / `success` / `danger`) on recent Telegram clients.
- Tehran-time timestamps in alerts, RTL-safe text rendering, per-user cooldown and quotas.

## Quick start

**Requirements:** Python 3.10+ and a bot token from [@BotFather](https://t.me/BotFather).

> Telegram is blocked in Iran, so run the bot on a server **outside** Iran.

```bash
git clone https://github.com/YASIN0ASADI/HOPPER.git
cd HOPPER

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN="123456:ABC-your-token"
python bot.py
```

Send `/start` to your bot, pick a language, and you are in.

## Configuration

All settings are environment variables.

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Token from BotFather. **Never commit it.** |
| `ADMIN_IDS` | – | Comma-separated Telegram user IDs allowed to use the admin commands. Get yours with `/id`. |
| `DB_PATH` | – | SQLite file for monitors, expiry alerts and user languages. Default: `monitor.db` next to `bot.py`. |
| `EMOJI_PACKS` | – | Comma-separated custom-emoji pack names to import at startup. |
| `EMOJI_MAP` | – | Path of the emoji mapping file. Default: `emoji_map.json` next to `bot.py`. |
| `PREMIUM_EMOJI` | – | Set to `0` to disable premium emoji entirely. |

A template is provided in [`.env.example`](.env.example).

## Deploy with systemd

The included unit file runs the bot as an unprivileged user with a hardened sandbox. It expects the project in `/bot`.

```bash
# 1. Get the code
git clone https://github.com/YASIN0ASADI/HOPPER.git /bot
cd /bot

# 2. Python environment
apt update && apt install -y python3-venv python3-pip
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 3. Dedicated user
useradd -r -s /usr/sbin/nologin reconbot
chown -R reconbot:reconbot /bot

# 4. Secrets (readable by root only)
install -m 600 /dev/null /etc/recon-bot.env
nano /etc/recon-bot.env          # add:  BOT_TOKEN=your-token   (and optionally ADMIN_IDS=123456789)

# 5. Service
cp recon-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now recon-bot
```

Everyday commands:

```bash
journalctl -u recon-bot -f                                    # live logs
systemctl restart recon-bot                                   # after updating files
git pull && chown -R reconbot:reconbot /bot && systemctl restart recon-bot   # update
```

## Premium custom emoji

Custom emoji in bot messages need the **bot owner's account to have Telegram Premium** (or the bot to own an extra username from Fragment). Without it the bot still works; Telegram rejects the emoji and Hopper silently resends the plain version.

Admin-only commands (set `ADMIN_IDS` first):

| Command | Description |
|---|---|
| `/id` | Show your Telegram user ID (available to everyone). |
| `/pack <link or name>` | Import every emoji of a custom-emoji pack. |
| `/sync` | Re-read the packs listed in `EMOJI_PACKS`. |
| `/map 🌐 <premium emoji>` | Map a regular emoji to a specific premium emoji. |
| `/emojis` | Show which emoji in the UI are still plain. |
| *(send a premium emoji)* | The bot replies with its custom emoji ID. |

Mappings are saved in `emoji_map.json` (ignored by git).

## Project layout

```
HOPPER/
├── bot.py               # handlers, tools, monitors, premium middleware
├── i18n.py              # English translations (Farsi is the source language)
├── premium.py           # custom-emoji mapping and HTML rewriting
├── requirements.txt
├── recon-bot.service    # hardened systemd unit
├── .env.example
├── LICENSE
└── README.md / README.fa.md
```

### Adding a language

Every user-facing string in `bot.py` is written in Farsi and wrapped in `tr()`. `i18n.py` maps each Farsi template to its translation, keeping `{0}`-style placeholders and HTML tags unchanged. To add a language, add another dictionary, extend `tr()`, and add a button in `lang_kb()`. Pull requests with new translations are very welcome.

## Data sources

Hopper relies on free public services. Please respect their terms and rate limits:
[Shodan InternetDB](https://internetdb.shodan.io/) · [ipwho.is](https://ipwho.is/) · [Cloudflare DNS-over-HTTPS](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/) · [crt.sh](https://crt.sh/) · [CertSpotter](https://sslmate.com/certspotter/) · [AnubisDB](https://jldc.me/) · [AlienVault OTX](https://otx.alienvault.com/) · [HackerTarget](https://hackertarget.com/) · [RDAP](https://rdap.org/) · [check-host.net](https://check-host.net/) · [RIPEstat](https://stat.ripe.net/)

## Security & responsible use

- Hopper is built for **checking servers you own or administer**. Port check, TCP latency and the monitor connect directly to the target, so do not point them at systems you have no permission to test.
- Targets that resolve to private, loopback or otherwise non-public addresses are refused (SSRF protection).
- Port checks are limited to 15 per user per hour, with a short per-user cooldown on every request.
- Config links you send are analyzed in memory; keys are masked in the output and never stored or forwarded.
- The bot never asks for SSH access or passwords. Run the "ss" analyzer yourself and paste the output.
- **Never commit your bot token or `monitor.db`.** If a token leaks, revoke it in BotFather with `/revoke`.

You are responsible for how you use this software. See the [license](LICENSE) for the warranty disclaimer.

## Contributing

Issues and pull requests are welcome: new tools, translations, bug reports, ideas. Please keep tools passive by default and keep every user-facing string translatable.

## License

Released under the [MIT License](LICENSE). © 2026 invincible.
