"""Translations for Hopper.

Farsi is the source language: every string in bot.py is written in Farsi and passed through tr().
EN maps each Farsi template to its English version. To add a language, add another dict and a
button in lang_kb() (bot.py). Placeholders like {0} and HTML tags must stay the same.
"""
import contextvars

# زبان کاربر فعلی؛ توسط LangMiddleware برای هر آپدیت مقداردهی می‌شه
LANG: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default="fa")

EN = {
    "🌐 اطلاعات IP":
        "🌐 IP info",
    "🔎 DNS دامنه":
        "🔎 Domain DNS",
    "🔌 چک پورت":
        "🔌 Port check",
    "🇮🇷 چک از ایران":
        "🇮🇷 Check from Iran",
    "🏓 پینگ جهانی":
        "🏓 Global ping",
    "⚡ تاخیر TCP":
        "⚡ TCP latency",
    "📡 مانیتور":
        "📡 Monitor",
    "⏰ هشدار انقضا":
        "⏰ Expiry alerts",
    "🧾 تحلیل ss":
        "🧾 ss analyzer",
    "🧩 ساب\u200cدامین\u200cها":
        "🧩 Subdomains",
    "🛡 هدرهای امنیتی":
        "🛡 Security headers",
    "ℹ️ راهنما":
        "ℹ️ Help",
    "✅ پورت\u200cهای رایج تانل":
        "✅ Common tunnel ports",
    "🎯 پورت دلخواه":
        "🎯 Custom port",
    "📋 دستور چک روی سرور":
        "📋 Server-side command",
    "🔄 هدف جدید":
        "🔄 New target",
    "🏠 منوی اصلی":
        "🏠 Main menu",
    "✖️ انصراف":
        "✖️ Cancel",
    "👻 <b>Hopper</b>\nیکی از ابزارها رو انتخاب کن:":
        "👻 <b>Hopper</b>\nPick a tool:",
    "ℹ️ <b>راهنما</b>\nبیشتر ابزارها فقط از منابع عمومی (Shodan InternetDB، Cloudflare DoH، CT logs، check-host و ...) داده می\u200cگیرن. چک پورت، تاخیر TCP و مانیتور یه اتصال TCP ساده به سرور برقرار می\u200cکنن، پس فقط روی سرور خودت ازشون استفاده کن.":
        "ℹ️ <b>Help</b>\nMost tools only read public sources (Shodan InternetDB, Cloudflare DoH, CT logs, check-host and others). Port check, TCP latency and the monitor open a simple TCP connection to your server, so use them only on servers you own.",
    "🌐 هر آی\u200cپی رو بفرست: IPv4 یا IPv6، عمومی یا خصوصی\n(مثلاً <code>8.8.8.8</code> یا <code>2606:4700:4700::1111</code>)":
        "🌐 Send any IP: IPv4 or IPv6, public or private\n(e.g. <code>8.8.8.8</code> or <code>2606:4700:4700::1111</code>)",
    "🔎 دامنه رو بفرست (مثلاً <code>example.com</code>)":
        "🔎 Send a domain (e.g. <code>example.com</code>)",
    "🧩 دامنه\u200cی اصلی رو بفرست تا ساب\u200cدامین\u200cهاش پیدا بشه":
        "🧩 Send the root domain to find its subdomains",
    "🛡 دامنه رو بفرست تا هدرهای امنیتی\u200cش بررسی بشه":
        "🛡 Send a domain to check its security headers",
    "📇 دامنه یا آی\u200cپی عمومی رو بفرست (مثلاً <code>example.com</code>)":
        "📇 Send a domain or a public IP (e.g. <code>example.com</code>)",
    "🔐 دامنه رو بفرست (مثلاً <code>example.com</code> یا با پورت: <code>example.com:8443</code>)":
        "🔐 Send a domain (e.g. <code>example.com</code> or with a port: <code>example.com:8443</code>)",
    "⚡ سرور رو به شکل <code>host:port</code> بفرست. اگه پورت ننویسی 443 در نظر گرفته می\u200cشه.\nبرای مقایسه تا ۵ سرور رو با فاصله یا خط جدید بفرست.\nمثال: <code>1.2.3.4:443 5.6.7.8:8443</code>":
        "⚡ Send a server as <code>host:port</code>. The port defaults to 443.\nTo compare, send up to 5 servers separated by spaces or new lines.\nExample: <code>1.2.3.4:443 5.6.7.8:8443</code>",
    "🧾 این دستور رو روی سرورت بزن (ترجیحاً با root) و خروجی\u200cش رو همین\u200cجا paste کن:\n<pre>ss -tulpn</pre>پورت\u200cهای در حال استفاده، برنامه\u200cی پشتشون، پورت\u200cهای فقط داخلی و پورت\u200cهای آزاد پیشنهادی رو بهت می\u200cگم.":
        "🧾 Run this on your server (preferably as root) and paste the output here:\n<pre>ss -tulpn</pre>I will show the ports in use, the program behind each one, internal-only ports and suggested free ports.",
    "🇮🇷 آی\u200cپی یا دامنه\u200cی سرورت رو به شکل <code>host:port</code> بفرست (پیش\u200cفرض پورت 443).\nدسترسی از چند نود داخل ایران و چند نود شاهد خارج از ایران چک می\u200cشه تا بفهمی سرور فیلتر شده یا نه.":
        "🇮🇷 Send your server's IP or domain as <code>host:port</code> (default port 443).\nReachability is checked from several nodes inside Iran and a few control nodes outside, so you can tell whether the server is filtered.",
    "🔌 <b>چک پورت</b>\nآی\u200cپی یا دامنه\u200cی <b>سرور خودت</b> رو بفرست.\n\n<i>فقط برای بررسی سرورهای خودت استفاده کن؛ برای هر کاربر ساعتی {0} چک مجازه.</i>":
        "🔌 <b>Port check</b>\nSend the IP or domain of <b>your own server</b>.\n\n<i>Only use this on servers you own; each user gets {0} checks per hour.</i>",
    "دامنه معتبر نیست":
        "Invalid domain",
    "این دامنه به آدرس غیرعمومی اشاره می\u200cکنه":
        "This domain points to a non-public address",
    "آدرس خود دستگاه (localhost). از بیرون قابل دسترس نیست.":
        "Address of the device itself (localhost). Not reachable from outside.",
    "آدرس خودکار داخل یک شبکه\u200cی محلی؛ وقتی DHCP جواب نداده یا برای ارتباط مستقیم دو دستگاه.":
        "Automatic address inside a local network; used when DHCP did not answer or for direct links between two devices.",
    "آدرس گروهی؛ یک بسته برای چند گیرنده فرستاده می\u200cشه.":
        "Multicast address; one packet is delivered to several receivers.",
    "آدرس نامشخص (0.0.0.0 یا ::)؛ یعنی «همه\u200cی اینترفیس\u200cها» یا «هنوز آدرس ندارم».":
        "Unspecified address (0.0.0.0 or ::); it means “all interfaces” or “I have no address yet”.",
    "رنج 100.64.0.0/10 که اپراتورها برای NAT چندلایه استفاده می\u200cکنن؛ چند مشترک یک IP عمومی مشترک دارن.":
        "Range 100.64.0.0/10 used by ISPs for carrier-grade NAT; several subscribers share one public IP.",
    "آدرس شبکه\u200cی داخلی (مثل 10.x یا 192.168.x یا 172.16-31.x)؛ روی اینترنت route نمی\u200cشه.":
        "Private network address (such as 10.x, 192.168.x or 172.16-31.x); it is not routed on the internet.",
    "رنج رزروشده؛ برای مستندات، تست یا استفاده\u200cی آینده.":
        "Reserved range; used for documentation, testing or future use.",
    "آی\u200cپی معتبر نیست":
        "Invalid IP address",
    "🌐 <b>{0}</b> · {1}\n\n📦 نوع: <b>{2}</b>\n📝 {3}\n\nℹ️ آدرس عمومی نیست، پس موقعیت جغرافیایی و ISP نداره.":
        "🌐 <b>{0}</b> · {1}\n\n📦 Type: <b>{2}</b>\n📝 {3}\n\nℹ️ This is not a public address, so it has no geolocation or ISP.",
    "{0} کشور: <b>{1}</b> · {2}":
        "{0} Country: <b>{1}</b> · {2}",
    "🗺 قاره: {0}":
        "🗺 Continent: {0}",
    "📍 منطقه: {0} / {1}":
        "📍 Region: {0} / {1}",
    "🧭 مختصات: <code>{0}, {1}</code>":
        "🧭 Coordinates: <code>{0}, {1}</code>",
    "🕒 زمان: {0} · UTC{1}":
        "🕒 Time zone: {0} · UTC{1}",
    "🏛 سازمان: {0}":
        "🏛 Organization: {0}",
    " و {0} مورد دیگر":
        " and {0} more",
    "🔓 پورت\u200cهای باز: <code>{0}</code>":
        "🔓 Open ports: <code>{0}</code>",
    "🏷 تگ\u200cها: {0}":
        "🏷 Tags: {0}",
    "🖥 هاست\u200cنیم\u200cها: {0}":
        "🖥 Hostnames: {0}",
    "⚠️ آسیب\u200cپذیری\u200cها: {0}":
        "⚠️ Vulnerabilities: {0}",
    "🔓 در Shodan InternetDB چیزی برای این آی\u200cپی ثبت نشده.":
        "🔓 Shodan InternetDB has nothing recorded for this IP.",
    "\n<i>موقعیت جغرافیایی تقریبیه در حد شهر یا منطقه و ممکنه دقیق نباشه.</i>":
        "\n<i>Geolocation is approximate (city or region level) and may be inaccurate.</i>",
    "📍 نمایش روی نقشه":
        "📍 Show on map",
    "همه\u200cی منابع جواب ندادن؛ چند دقیقه بعد دوباره امتحان کن.":
        "All sources failed to respond; try again in a few minutes.",
    "منابع: {0}":
        "Sources: {0}",
    " · ناموفق: {0}":
        " · failed: {0}",
    "ℹ️ ساب\u200cدامینی برای <code>{0}</code> پیدا نشد.\n<i>{1}</i>":
        "ℹ️ No subdomains found for <code>{0}</code>.\n<i>{1}</i>",
    "🧩 <b>{0}</b> ساب\u200cدامین برای <b>{1}</b>\n\n{2}":
        "🧩 <b>{0}</b> subdomains for <b>{1}</b>\n\n{2}",
    "\n… و {0} مورد دیگر؛ لیست کامل توی فایل پایین هست.":
        "\n… and {0} more; the full list is in the file below.",
    "\n\n📊 نمره: <b>{0}/{1}</b>\n🖥 Server: <code>{2}</code>":
        "\n\n📊 Score: <b>{0}/{1}</b>\n🖥 Server: <code>{2}</code>",
    " · {0} روز مانده":
        " · {0} days left",
    " · ⚠️ {0} روز پیش منقضی شده":
        " · ⚠️ expired {0} days ago",
    "اطلاعات Whois این دامنه از هیچ منبعی در دسترس نبود.":
        "Whois data for this domain was not available from any source.",
    "برای آی\u200cپی غیرعمومی Whois وجود نداره":
        "Whois is not available for non-public IPs",
    "اطلاعاتی برای این آی\u200cپی پیدا نشد":
        "No information found for this IP",
    "📇 <b>Whois {0}</b>\n\n🏷 نام شبکه: <code>{1}</code>\n🔖 Handle: <code>{2}</code>\n🌍 کشور: {3}\n📦 رنج: <code>{4} - {5}</code>\n🧱 CIDR: <code>{6}</code>\n📌 نوع: {7}":
        "📇 <b>Whois {0}</b>\n\n🏷 Network name: <code>{1}</code>\n🔖 Handle: <code>{2}</code>\n🌍 Country: {3}\n📦 Range: <code>{4} - {5}</code>\n🧱 CIDR: <code>{6}</code>\n📌 Type: {7}",
    "📇 <b>Whois {0}</b>\n\n📅 ثبت: {1}\n🔄 آخرین تغییر: {2}\n⏰ انقضا: {3}{4}\n🏷 رجیستار: {5}\n🌐 Name Servers: {6}\n📌 وضعیت: {7}\n<i>منبع: {8}</i>":
        "📇 <b>Whois {0}</b>\n\n📅 Registered: {1}\n🔄 Last changed: {2}\n⏰ Expires: {3}{4}\n🏷 Registrar: {5}\n🌐 Name Servers: {6}\n📌 Status: {7}\n<i>Source: {8}</i>",
    "پورت نامعتبره":
        "Invalid port",
    "✅ گواهی معتبر و مورد اعتماده":
        "✅ The certificate is valid and trusted",
    "هندشیک TLS ناموفق بود: {0}":
        "TLS handshake failed: {0}",
    "اتصال TLS روی این پورت برقرار نشد":
        "Could not establish a TLS connection on this port",
    " ⚠️ منقضی شده!":
        " ⚠️ Expired!",
    " ⚠️ کمتر از ۱۵ روز مونده":
        " ⚠️ Less than 15 days left",
    "\n📅 از: {0:%Y-%m-%d}\n⏰ تا: {1:%Y-%m-%d} · {2} روز{3}\n🔑 کلید: {4} | امضا: {5}\n🔒 پروتکل: {6} | {7}\n📡 ALPN: {8}\n🌐 SAN: {9}":
        "\n📅 From: {0:%Y-%m-%d}\n⏰ To: {1:%Y-%m-%d} · {2} days{3}\n🔑 Key: {4} | Signature: {5}\n🔒 Protocol: {6} | {7}\n📡 ALPN: {8}\n🌐 SAN: {9}",
    "سقف {0} چک پورت در ساعت پر شده؛ بعداً دوباره امتحان کن.":
        "The limit of {0} port checks per hour has been reached; try again later.",
    "فقط آی\u200cپی عمومی قابل بررسیه":
        "Only public IPs can be checked",
    "دامنه resolve نشد":
        "Could not resolve the domain",
    "فرمت پورت نامعتبره. مثال: 443 یا 80,443,8443 یا 8000-8005":
        "Invalid port format. Examples: 443 or 80,443,8443 or 8000-8005",
    "بین ۱ تا ۲۰ پورت (۱ تا ۶۵۵۳۵) وارد کن.":
        "Enter between 1 and 20 ports (1 to 65535).",
    "TLS/SSL (احتمالاً HTTPS یا پروکسی TLS)":
        "TLS/SSL (probably HTTPS or a TLS proxy)",
    "ساکت؛ چیزی نفرستاد (ممکنه پروکسی/تانل مثل VLESS، VMess، Trojan، SS باشه)":
        "Silent; it sent nothing (could be a proxy or tunnel such as VLESS, VMess, Trojan or SS)",
    "سرویس ناشناس":
        "Unknown service",
    " · {0} پورت\n":
        " · {0} ports\n",
    "🟢 <b>باز</b> · Open":
        "🟢 <b>Open</b>",
    "\n🔴 <b>بسته</b> · Closed\n":
        "\n🔴 <b>Closed</b>\n",
    "، ":
        ", ",
    "\n🟡 <b>بدون پاسخ</b> · Filtered\nفایروال یا فیلتر؛ مشخص نیست باز یا بسته\u200cست\n":
        "\n🟡 <b>No response</b> · Filtered\nFirewall or filtering; it is unclear whether the port is open or closed\n",
    "\n💡 باز یعنی چیزی روی پورت اتصال قبول می\u200cکنه؛ معمولاً یه سرویسه ولی ممکنه فایروال، پراکسی یا CDN باشه. بسته یعنی از بیرون چیزی جواب نمی\u200cده، اما ممکنه روی 127.0.0.1 در حال استفاده باشه. برای انتخاب پورت تانل جدید با «🧾 تحلیل ss» مطمئن شو.":
        "\n💡 Open means something accepts connections on the port; usually a service, but it can be a firewall, proxy or CDN. Closed means nothing answers from outside, but the port may still be in use on 127.0.0.1. To pick a port for a new tunnel, confirm with “🧾 ss analyzer”.",
    "\n<i>نتیجه از دید سرور ربات (خارج از ایران) هست و ممکنه از داخل ایران فرق کنه. پورت UDP مثل WireGuard و پورتی که فقط روی 127.0.0.1 گوش می\u200cده از بیرون دیده نمی\u200cشه.</i>":
        "\n<i>The result is from the bot server's point of view (outside Iran) and may differ from inside Iran. UDP ports such as WireGuard, and ports listening only on 127.0.0.1, are not visible from outside.</i>",
    "📋 <b>دستور بررسی پورت\u200cهای در حال استفاده روی خود سرور</b>\n(داخل SSH سرور خودت بزن؛ دقیق\u200cتر از هر چک بیرونیه و نیازی نیست پسورد جایی بفرستی)\n\n<pre>ss -tulpn</pre>\nستون Local Address پورت و ستون Process اسم برنامه\u200cست.\n• <code>0.0.0.0:443</code> یعنی از بیرون در دسترسه\n• <code>127.0.0.1:8000</code> یعنی فقط داخل خود سرور\n\nچک یک پورت مشخص:\n<pre>ss -tulpn | grep :443</pre>":
        "📋 <b>Command to see the ports in use on the server itself</b>\n(Run it inside SSH on your own server; it is more accurate than any external check and you never have to share a password)\n\n<pre>ss -tulpn</pre>\nThe Local Address column shows the port and the Process column shows the program.\n• <code>0.0.0.0:443</code> means reachable from outside\n• <code>127.0.0.1:8000</code> means only inside the server\n\nTo check one specific port:\n<pre>ss -tulpn | grep :443</pre>",
    "پورت رو هم بنویس، مثل host:443":
        "Please include the port too, e.g. host:443",
    "بین ۱ تا ۵ سرور بفرست.":
        "Send between 1 and 5 servers.",
    "⚡ <b>تاخیر TCP</b> · ۵ نمونه برای هر سرور\n":
        "⚡ <b>TCP latency</b> · 5 samples per server\n",
    "⚫ <code>{0}</code>\n   اتصال برقرار نشد؛ بسته یا فیلتره":
        "⚫ <code>{0}</code>\n   Connection failed; closed or filtered",
    "{0} <code>{1}</code>\n   میانگین {2:.0f}ms · کمترین {3:.0f} · بیشترین {4:.0f} · نوسان {5:.0f} · ریزش {6}%":
        "{0} <code>{1}</code>\n   avg {2:.0f}ms · min {3:.0f} · max {4:.0f} · jitter {5:.0f} · loss {6}%",
    "\n🏆 سریع\u200cترین: <code>{0}</code>":
        "\n🏆 Fastest: <code>{0}</code>",
    "\n<i>تاخیر از دید سرور ربات (خارج از ایران) اندازه\u200cگیری شده. برای دید از داخل ایران از «🇮🇷 چک از ایران» استفاده کن.</i>":
        "\n<i>Latency is measured from the bot server (outside Iran). For the view from inside Iran use “🇮🇷 Check from Iran”.</i>",
    "تایم\u200cاوت؛ احتمالاً فیلتر یا دراپ":
        "Timed out; probably filtered or dropped",
    "رد شد؛ پورت بسته\u200cست":
        "Refused; the port is closed",
    "نامشخص":
        "Unknown",
    "الان هیچ نود ایرانی در check-host فعال نیست.":
        "There are no active Iranian nodes on check-host right now.",
    "check-host درخواست رو قبول نکرد (احتمالاً محدودیت نرخ). کمی بعد دوباره امتحان کن.":
        "check-host did not accept the request (probably rate limited). Try again shortly.",
    "⏳ بدون نتیجه":
        "⏳ No result",
    "⏳ نودهای ایران جواب ندادن؛ چند دقیقه بعد دوباره امتحان کن.":
        "⏳ The Iranian nodes did not answer; try again in a few minutes.",
    "⚠️ از ایران و از خارج هر دو بسته\u200cست. مشکل از خود سرور یا پورته (سرویس خاموشه یا فایروال سرور)، نه فیلترینگ.":
        "⚠️ Closed from both Iran and abroad. The problem is the server or the port itself (the service is down or the server firewall blocks it), not filtering.",
    "🚫 از ایران بسته ولی از خارج بازه. احتمالاً IP یا پورت فیلتر شده.":
        "🚫 Closed from Iran but open from abroad. The IP or port is probably filtered.",
    "⚠️ فقط از بعضی نودهای ایران بازه. ممکنه روی بعضی ISPها فیلتر باشه.":
        "⚠️ Open only from some Iranian nodes. It may be filtered on some ISPs.",
    "✅ پورت از همه\u200cی نودهای ایران باز است.":
        "✅ The port is open from all Iranian nodes.",
    "🇮🇷 <b>چک دسترسی از ایران</b>":
        "🇮🇷 <b>Reachability check from Iran</b>",
    "<b>نودهای ایران</b>":
        "<b>Iranian nodes</b>",
    "\n<b>نودهای شاهد (خارج از ایران)</b>":
        "\n<b>Control nodes (outside Iran)</b>",
    "\n<i>نودهای check-host روی دیتاسنترهای ایران هستن، نه اینترنت خونگی یا موبایل؛ پس نتیجه برای همراه اول و ایرانسل ممکنه فرق کنه.</i>":
        "\n<i>check-host nodes sit in Iranian data centers, not on home or mobile internet; results for MCI and Irancell may differ.</i>",
    "\n<i>⚠️ این چک فقط اتصال TCP به آی\u200cپیِ دامنه رو بررسی می\u200cکنه و فیلتر DNS یا SNI/HTTP رو نشون نمی\u200cده؛ پس «باز» بودن اینجا لزوماً به معنی در دسترس بودن سایت در ایران نیست. برای دامنه از «🧭 DNS از ایران» و «🧪 بازرس HTTP» استفاده کن.</i>":
        "\n<i>⚠️ This only checks the TCP connection to the domain's IP. It does not detect DNS or SNI/HTTP filtering, so “open” here does not necessarily mean the site is reachable in Iran. For domains, use “DNS from Iran” and “HTTP inspector”.</i>",
    "🔗 گزارش کامل check-host":
        "🔗 Full check-host report",
    "{0} ثانیه":
        "{0} s",
    "{0} دقیقه":
        "{0} min",
    "{0} ساعت":
        "{0} h",
    "{0} روز":
        "{0} d",
    "📡 <b>مانیتور سرورها</b>":
        "📡 <b>Server monitor</b>",
    "\nهنوز سروری اضافه نکردی.":
        "\nYou have not added any server yet.",
    "هنوز چک نشده":
        "Not checked yet",
    "بالا":
        "Up",
    "قطع":
        "Down",
    "\n<i>هر {0} دقیقه چک می\u200cشه و اگه قطع یا وصل شد پیام می\u200cگیری. روی اسم سرور بزنی همین الان چک می\u200cشه.</i>":
        "\n<i>Servers are checked every {0} minutes and you get a message when one goes down or comes back. Tap a server to check it right now.</i>",
    "➕ افزودن سرور":
        "➕ Add server",
    "🟢 <b>وصل شد</b>\n<code>{0}</code>\nمدت قطعی: {1}\nساعت {2} به وقت تهران":
        "🟢 <b>Back online</b>\n<code>{0}</code>\nDowntime: {1}\nAt {2} Tehran time",
    "🔴 <b>قطع شد</b>\n<code>{0}</code>\nساعت {1} به وقت تهران":
        "🔴 <b>Went down</b>\n<code>{0}</code>\nAt {1} Tehran time",
    "🔄 چک دوباره":
        "🔄 Check again",
    "❌ جواب نداد":
        "❌ No answer",
    "\n<i>ستون\u200cها: پینگ موفق از کل · کمترین/میانگین/بیشترین</i>":
        "\n<i>Columns: successful pings out of total · min/avg/max</i>",
    "\n🏆 بهترین: {0} {1:.0f}ms\n🐢 ضعیف\u200cترین: {2} {3:.0f}ms":
        "\n🏆 Best: {0} {1:.0f}ms\n🐢 Weakest: {2} {3:.0f}ms",
    "🌍 <b>پینگ از همه\u200cی نودها</b>\n{0}\n\n":
        "🌍 <b>Ping from all nodes</b>\n{0}\n\n",
    "🚫 از ایران پینگ جواب نمی\u200cگیره ولی از خارج می\u200cگیره؛ ممکنه IP فیلتر شده باشه. برای اطمینان «🇮🇷 چک از ایران» رو روی پورت سرویس بزن.":
        "🚫 No ping replies from Iran, but there are replies from abroad; the IP may be filtered. To be sure, run “🇮🇷 Check from Iran” on the service port.",
    "⚠️ از هیچ\u200cجا پینگ جواب نمی\u200cگیره. ممکنه سرور ICMP رو بسته باشه، که لزوماً به معنی خاموش بودن نیست. پورت سرویس رو با «🔌 چک پورت» بررسی کن.":
        "⚠️ No ping replies from anywhere. The server may block ICMP, which does not necessarily mean it is down. Check the service port with “🔌 Port check”.",
    "⚠️ بعضی نودهای ایران ریزش دارن؛ مسیر ناپایداره.":
        "⚠️ Some Iranian nodes show packet loss; the route is unstable.",
    "✅ پینگ از همه\u200cی نودهای ایران سالمه.":
        "✅ Ping from all Iranian nodes is healthy.",
    "🏓 <b>پینگ از ایران</b>\n{0}\n":
        "🏓 <b>Ping from Iran</b>\n{0}\n",
    "🌍 همه\u200cی نودها":
        "🌍 All nodes",
    "🇮🇷 فقط ایران":
        "🇮🇷 Iran only",
    "🔄 دوباره":
        "🔄 Again",
    "خروجی ss شناسایی نشد. دستور ss -tulpn رو بزن و کامل paste کن.":
        "Could not recognize the ss output. Run ss -tulpn and paste the full output.",
    "🧾 <b>تحلیل پورت\u200cهای سرور</b> · {0} پورت\n":
        "🧾 <b>Server port analysis</b> · {0} ports\n",
    "🌍 <b>در دسترس از بیرون</b>":
        "🌍 <b>Reachable from outside</b>",
    "\n🔒 <b>فقط داخلی</b> · روی 127.0.0.1":
        "\n🔒 <b>Internal only</b> · on 127.0.0.1",
    "⚠️ {0} روی پورت {1} از بیرون باز است. اگه لازم نیست ببندش یا فقط به 127.0.0.1 محدودش کن.":
        "⚠️ {0} is open to the outside on port {1}. If you do not need that, close it or bind it to 127.0.0.1 only.",
    "\n🟢 <b>پورت\u200cهای آزاد پیشنهادی برای تانل جدید</b>\n":
        "\n🟢 <b>Suggested free ports for a new tunnel</b>\n",
    "\n<i>اسم برنامه\u200cها پیدا نشد؛ دستور رو با root (یا sudo) بزن.</i>":
        "\n<i>Program names were not found; run the command as root (or with sudo).</i>",
    "\n<i>این لیست فقط پورت\u200cهای TCP/UDP در حال گوش دادن روی خود سرور رو نشون می\u200cده. بازبودن از بیرون به فایروال هم بستگی داره.</i>":
        "\n<i>This list only shows the TCP/UDP ports listening on the server itself. Whether they are reachable from outside also depends on the firewall.</i>",
    "📇 دامنه":
        "📇 Domain",
    "⏰ <b>هشدار انقضا</b>":
        "⏰ <b>Expiry alerts</b>",
    "\nهنوز چیزی اضافه نکردی.":
        "\nYou have not added anything yet.",
    "هنوز چک نشده یا برای این پسوند در دسترس نیست":
        "Not checked yet, or not available for this TLD",
    "⚠️ {0} روز پیش منقضی شده":
        "⚠️ expired {0} days ago",
    "{0} روز مانده":
        "{0} days left",
    "\n<i>۳۰ و ۱۵ و ۷ و ۳ و ۱ روز مونده و روز انقضا بهت پیام می\u200cدم. روی هر مورد بزنی همین الان چک می\u200cشه.</i>":
        "\n<i>I will message you 30, 15, 7, 3 and 1 days before expiry and on the expiry day. Tap an item to check it right now.</i>",
    "➕ افزودن":
        "➕ Add",
    "{0} روز دیگه منقضی می\u200cشه":
        "expires in {0} days",
    "{0} روز پیش منقضی شده":
        "expired {0} days ago",
    "⏰ <b>هشدار انقضا</b>\n{0} · <code>{1}</code>\n{2}":
        "⏰ <b>Expiry alert</b>\n{0} · <code>{1}</code>\n{2}",
    "🎯 هدف: <code>{0}</code>":
        "🎯 Target: <code>{0}</code>",
    "\n\nچی بررسی کنم؟":
        "\n\nWhat should I check?",
    "🎯 هدف: <code>{0}</code>\n\nچی بررسی کنم؟":
        "🎯 Target: <code>{0}</code>\n\nWhat should I check?",
    "↩️ برگشت":
        "↩️ Back",
    "نشست منقضی شد، دوباره هدف رو بفرست.":
        "Session expired; please send the target again.",
    "⏳ در حال چک {0} پورت...":
        "⏳ Checking {0} ports...",
    "🎯 پورت (یا چند پورت) رو بفرست:\n<code>443</code>\n<code>80,443,8443</code>\n<code>8000-8005</code>\n(حداکثر ۲۰ پورت)":
        "🎯 Send a port (or several ports):\n<code>443</code>\n<code>80,443,8443</code>\n<code>8000-8005</code>\n(max 20 ports)",
    "نشست منقضی شد.":
        "Session expired.",
    "⏳ در حال چک...":
        "⏳ Checking...",
    "حداکثر {0} سرور می\u200cتونی اضافه کنی.":
        "You can add at most {0} servers.",
    "📡 سرور رو به شکل <code>host:port</code> بفرست.\nمثال: <code>1.2.3.4:443</code> یا <code>example.com:8443</code>\n\n<i>فقط سرور خودت رو اضافه کن.</i>":
        "📡 Send the server as <code>host:port</code>.\nExample: <code>1.2.3.4:443</code> or <code>example.com:8443</code>\n\n<i>Only add your own servers.</i>",
    "⚠️ حداکثر {0} سرور می\u200cتونی اضافه کنی.":
        "⚠️ You can add at most {0} servers.",
    "⚠️ این سرور قبلاً اضافه شده.":
        "⚠️ This server has already been added.",
    "این مورد دیگه وجود نداره.":
        "This item no longer exists.",
    "🗑 حذف شد":
        "🗑 Deleted",
    "✅ الان بالاست · {0}ms":
        "✅ Up right now · {0}ms",
    "❌ هنوز قطعه":
        "❌ Still down",
    "⏳ در حال چک از نودهای ایران...":
        "⏳ Checking from the Iranian nodes...",
    "❌ سرویس check-host جواب نداد، بعداً امتحان کن.":
        "❌ The check-host service did not respond; try again later.",
    "🏓 آی\u200cپی یا دامنه\u200cی سرورت رو بفرست (پورت لازم نیست).\nپینگ از نودهای ایران و چند نود شاهد خارج از ایران گرفته می\u200cشه.":
        "🏓 Send your server's IP or domain (no port needed).\nPing is taken from Iranian nodes and a few control nodes outside Iran.",
    "نشست منقضی شد، دوباره از منو شروع کن.":
        "Session expired; please start again from the menu.",
    "⏳ در حال پینگ از نودها؛ حدود ۱۰ تا ۳۰ ثانیه طول می\u200cکشه...":
        "⏳ Pinging from the nodes; this takes about 10 to 30 seconds...",
    "⏳ کمی صبر کن و دوباره بفرست.":
        "⏳ Please wait a moment and send again.",
    "حداکثر {0} مورد می\u200cتونی اضافه کنی.":
        "You can add at most {0} items.",
    "⏰ دامنه رو بفرست. برای SSL می\u200cتونی پورت هم بنویسی.\nمثال: <code>example.com</code> یا <code>example.com:8443</code>":
        "⏰ Send a domain. For SSL you can also add a port.\nExample: <code>example.com</code> or <code>example.com:8443</code>",
    "🔐 گواهی SSL":
        "🔐 SSL certificate",
    "📇 انقضای دامنه":
        "📇 Domain expiry",
    "کدوم رو برای <code>{0}</code> پایش کنم؟":
        "Which one should I monitor for <code>{0}</code>?",
    "این مورد قبلاً اضافه شده.":
        "This item has already been added.",
    "⚠️ تاریخ انقضا همین الان از هیچ منبعی گرفته نشد. هر ۶ ساعت دوباره تلاش می\u200cکنم.":
        "⚠️ The expiry date could not be fetched from any source right now. I will try again every 6 hours.",
    "⏳ در حال بررسی...":
        "⏳ Working on it...",
    "❌ سرویس منبع جواب نداد، بعداً امتحان کن.":
        "❌ The source service did not respond; try again later.",
    "👻 <b>Hopper</b>\nیه دسته انتخاب کن:":
        "👻 <b>Hopper</b>\nPick a category:",
    "هندشیک TLS با این دامنه ناموفق بود.":
        "TLS handshake with this domain failed.",
    "<i>🇮🇷 (سبز = روشن) هر ۳۰ دقیقه از نودهای ایران چک می\u200cکنه و اگه IP فیلتر بشه خبر می\u200cده. 📈 نمودار ۲۴ ساعت اخیر رو می\u200cفرسته.</i>":
        "<i>🇮🇷 (green = on) checks every 30 minutes from Iranian nodes and warns you if the IP gets filtered. 📈 sends the chart of the last 24 hours.</i>",
    "✅ برای dest و serverNames توی Reality مناسبه.":
        "✅ Suitable as dest and serverNames in Reality.",
    "\n<i>تاخیر از دید سرور ربات اندازه\u200cگیری شده و پشتیبانی X25519 قابل بررسی نیست. برای نتیجه\u200cی دقیق\u200cتر همین چک رو روی خود سرور VPN هم بزن.</i>":
        "\n<i>Latency was measured from the bot server, and X25519 support cannot be checked. For a more accurate result, run this same check on your VPN server itself.</i>",
    "لینک کانفیگ معتبر نیست. باید با vless:// یا vmess:// یا trojan:// یا ss:// شروع بشه.":
        "Invalid config link. It must start with vless://, vmess://, trojan:// or ss://.",
    "این نوع لینک پشتیبانی نمی\u200cشه.":
        "This link type is not supported.",
    "\n<i>لینک ذخیره نمی\u200cشه. بهتره پیام حاوی کلیدت رو از چت پاک کنی.</i>":
        "\n<i>The link is not stored. It is better to delete the message containing your key from the chat.</i>",
    "\n<i>همسایه\u200cها از مسیرهای BGP دیده\u200cشده توسط RIPE RIS استخراج شدن و تقریبی هستن. چپ یعنی سمت بالادستی/پیرها و راست یعنی مشتری\u200cها.</i>":
        "\n<i>Neighbours are derived from BGP paths seen by RIPE RIS and are approximate. Left means the upstream/peer side and right means customers.</i>",
    "\n📊 نمره: <b>{0}/5</b>":
        "\n📊 Score: <b>{0}/5</b>",
    "🚫 از ایران باز نمی\u200cشه ولی از خارج باز می\u200cشه؛ احتمالاً فیلتر شده.":
        "🚫 Does not open from Iran but opens from abroad; it is probably filtered.",
    "🚫 آی\u200cپی صفحه\u200cی مسدودسازی (10.10.34.x) برگشته؛ این دامنه توی ایران با DNS فیلتر شده.":
        "🚫 A block-page IP (10.10.34.x) was returned; this domain is DNS-filtered in Iran.",
    "🚫 <b>احتمالاً فیلتر شد</b>\n<code>{0}</code>\nاز خارج ایران بازه ولی از نودهای ایران جواب نمی\u200cگیره. بهتره IP یا پورت رو عوض کنی.\nساعت {1} به وقت تهران":
        "🚫 <b>Probably filtered</b>\n<code>{0}</code>\nIt is open from outside Iran but does not answer from the Iranian nodes. Better change the IP or port.\nAt {1} Tehran time",
    "✅ <b>دوباره از ایران در دسترسه</b>\n<code>{0}</code>\nساعت {1} به وقت تهران":
        "✅ <b>Reachable from Iran again</b>\n<code>{0}</code>\nAt {1} Tehran time",
    "🖧 <b>ابزارهای سرور و VPN</b>\nیکی از ابزارها رو انتخاب کن:":
        "🖧 <b>Server & VPN tools</b>\nPick a tool:",
    "🌍 <b>ابزارهای وب و دامنه</b>\nیکی از ابزارها رو انتخاب کن:":
        "🌍 <b>Web & domain tools</b>\nPick a tool:",
    "🎭 دامنه\u200cای که می\u200cخوای توی Reality به\u200cعنوان <code>dest</code> استفاده کنی رو بفرست (مثلاً <code>www.microsoft.com</code>).\nTLS 1.3 و HTTP/2 و گواهی و تاخیر بررسی می\u200cشن.":
        "🎭 Send the domain you want to use as <code>dest</code> in Reality (e.g. <code>www.microsoft.com</code>).\nTLS 1.3, HTTP/2, the certificate and latency are checked.",
    "🔗 لینک کانفیگ (<code>vless://</code> یا <code>vmess://</code> یا <code>trojan://</code> یا <code>ss://</code>) رو بفرست.\n<i>لینک شامل کلید شماست؛ ربات ذخیره\u200cش نمی\u200cکنه و جایی نمی\u200cفرسته.</i>":
        "🔗 Send the config link (<code>vless://</code>, <code>vmess://</code>, <code>trojan://</code> or <code>ss://</code>).\n<i>The link contains your key; the bot does not store it or send it anywhere.</i>",
    "🕸 شماره\u200cی ASN (مثل <code>AS13335</code>) یا یه آی\u200cپی یا دامنه بفرست تا گراف همسایه\u200cهای BGP\u200cش رو بکشم.":
        "🕸 Send an ASN (like <code>AS13335</code>) or an IP or domain and I will draw its BGP neighbour graph.",
    "✉️ دامنه رو بفرست تا SPF و DKIM و DMARC بررسی بشه (مثلاً <code>example.com</code>)":
        "✉️ Send a domain to check its SPF, DKIM and DMARC (e.g. <code>example.com</code>)",
    "🧪 آدرس سایت رو بفرست (مثلاً <code>https://example.com</code>)":
        "🧪 Send the website address (e.g. <code>https://example.com</code>)",
    "🧭 دامنه رو بفرست تا جواب DNS از نودهای ایران و خارج مقایسه بشه.":
        "🧭 Send a domain to compare its DNS answers from Iranian nodes and from abroad.",
    "اتصال TCP به این دامنه روی پورت {0} برقرار نشد.":
        "Could not establish a TCP connection to this domain on port {0}.",
    "⚠️ TLS 1.3 و HTTP/2 داره ولی گواهیش با این دامنه نمی\u200cخونه.":
        "⚠️ It has TLS 1.3 and HTTP/2 but its certificate does not match this domain.",
    "آدرس یا پورت سرور توی لینک پیدا نشد.":
        "Could not find the server address or port in the link.",
    "این ASN پیدا نشد.":
        "This ASN was not found.",
    "\n⚠️ سرور کد خطای {0} برگردونده.":
        "\n⚠️ The server returned error code {0}.",
    "⚠️ از هیچ\u200cجا باز نمی\u200cشه؛ مشکل از خود سایته.":
        "⚠️ It does not open from anywhere; the problem is the website itself.",
    "✅ از نودهای ایران باز می\u200cشه.":
        "✅ It opens from the Iranian nodes.",
    "🚫 از ایران آی\u200cپی خصوصی برگشته؛ احتمالاً DNS دستکاری شده.":
        "🚫 A private IP was returned from Iran; DNS has probably been tampered with.",
    "⏳ در حال ساخت نمودار...":
        "⏳ Building the chart...",
    "\n↪️ این دامنه به <code>{0}</code> ریدایرکت می\u200cکنه؛ بهتره خود اون دامنه رو تست کنی.":
        "\n↪️ This domain redirects to <code>{0}</code>; better test that domain itself.",
    "⚠️ TLS 1.3 داره ولی HTTP/2 نداره؛ برای Reality توصیه نمی\u200cشه.":
        "⚠️ It has TLS 1.3 but no HTTP/2; not recommended for Reality.",
    "❌ TLS 1.3 نداره؛ برای Reality مناسب نیست.":
        "❌ No TLS 1.3; not suitable for Reality.",
    "⚠️ متد {0} قدیمی یا ضعیفه؛ از 2022-blake3-*، aes-256-gcm یا chacha20-ietf-poly1305 استفاده کن.":
        "⚠️ Method {0} is old or weak; use 2022-blake3-*, aes-256-gcm or chacha20-ietf-poly1305.",
    "⚠️ allowInsecure روشنه؛ گواهی چک نمی\u200cشه و ارتباط در معرض MITM هست.":
        "⚠️ allowInsecure is on; the certificate is not verified and the connection is exposed to MITM.",
    "⚠️ alterId غیر صفره؛ این روش قدیمیه و استاندارد جدید 0 هست.":
        "⚠️ alterId is non-zero; this is the old way and the current standard is 0.",
    "⚠️ آدرس سرور عمومی نیست.":
        "⚠️ The server address is not public.",
    "\n✅ مشکل واضحی توی تنظیمات پیدا نشد.":
        "\n✅ No obvious problem found in the settings.",
    "ASN این آدرس پیدا نشد.":
        "The ASN of this address was not found.",
    "رکوردی پیدا نشد":
        "No record found",
    "با سلکتورهای رایج پیدا نشد (ممکنه سلکتور اختصاصی داشته باشی)":
        "Not found with the common selectors (you may have a custom selector)",
    "آدرس نامعتبره.":
        "Invalid address.",
    "⚠️ نودهای ایران جوابی ندادن.":
        "⚠️ The Iranian nodes did not answer.",
    "پایش فیلتر خاموش شد.":
        "Filter watch turned off.",
    "🇮🇷 پایش فیلتر روشن شد. هر ۳۰ دقیقه از نودهای ایران چک می\u200cشه و اگه IP یا پورت فیلتر بشه بهت خبر می\u200cدم.":
        "🇮🇷 Filter watch turned on. It checks from Iranian nodes every 30 minutes and I will tell you if the IP or port gets filtered.",
    "هنوز داده\u200cی کافی نیست؛ بعد از چند چک دوباره امتحان کن.":
        "Not enough data yet; try again after a few checks.",
    "🎭 چک Reality":
        "🎭 Reality check",
    "🔗 تحلیل لینک کانفیگ":
        "🔗 Config link analyzer",
    "🕸 تحلیل ASN":
        "🕸 BGP MAP",
    "🧭 DNS از ایران":
        "🧭 DNS from Iran",
    "🧪 بازرس HTTP":
        "🧪 HTTP inspector",
    "✉️ چک ایمیل":
        "✉️ Email check",
    "سالم":
        "healthy",
    "⚠️ بدون TLS یا Reality؛ ترافیک راحت شناسایی و مسدود می\u200cشه.":
        "⚠️ No TLS or Reality; the traffic is easily detected and blocked.",
    "⚠️ Trojan بدون TLS معنی نداره.":
        "⚠️ Trojan without TLS makes no sense.",
    "❌ کلید عمومی (pbk) نداره؛ لینک ناقصه.":
        "❌ It has no public key (pbk); the link is incomplete.",
    "⚠️ SNI (دامنه\u200cی dest) مشخص نشده.":
        "⚠️ SNI (the dest domain) is not set.",
    "ℹ️ fingerprint (fp) تنظیم نشده؛ chrome پیشنهاد می\u200cشه.":
        "ℹ️ fingerprint (fp) is not set; chrome is recommended.",
    "ℹ️ برای Reality روی TCP معمولاً flow=xtls-rprx-vision توصیه می\u200cشه.":
        "ℹ️ For Reality over TCP, flow=xtls-rprx-vision is usually recommended.",
    "بیشتر از یک رکورد SPF داری؛ این نامعتبره":
        "You have more than one SPF record; this is invalid",
    "فقط مانیتورینگه؛ quarantine یا reject بذار":
        "monitoring only; set quarantine or reject",
    "اتصال به {0} ناموفق بود.":
        "Connection to {0} failed.",
    "⚠️ جواب DNS توی ایران با خارج فرق داره. اگه دامنه پشت CDN باشه عادیه، وگرنه ممکنه دستکاری شده باشه.":
        "⚠️ The DNS answer in Iran differs from abroad. That is normal if the domain is behind a CDN, otherwise it may have been tampered with.",
    "✅ جواب DNS از ایران با خارج هم\u200cخونی داره.":
        "✅ The DNS answer from Iran matches abroad.",
    "حداکثر {0} سرور رو می\u200cتونی با پایش فیلتر بذاری.":
        "You can put at most {0} servers on filter watch.",
    "🖧 ابزارهای سرور و VPN":
        "🖧 Server & VPN tools",
    "🌍 ابزارهای وب و دامنه":
        "🌍 Web & domain tools",
    "مسدود":
        "blocked",
    "در حال بررسی":
        "checking",
    "⚠️ سرور با آی\u200cپی و بدون SNI تنظیم شده؛ احتمالاً با TLS درست کار نمی\u200cکنه.":
        "⚠️ The server is set up with an IP and no SNI; it probably will not work properly with TLS.",
    "⚠️ دامنه\u200cی سرور resolve نشد.":
        "⚠️ The server domain could not be resolved.",
    "بیش از ۱۰ جستجوی DNS (حد مجاز SPF)":
        "more than 10 DNS lookups (the SPF limit)",
    "ندارد":
        "none",
    "جواب نداد":
        "no answer",
    "نرم؛ -all امن\u200cتره":
        "soft; -all is safer",
    "بدون -all یا ~all؛ ضعیفه":
        "no -all or ~all; weak",
    "🇮🇷 چک کامل":
        "🇮🇷 Full check",
    "<i>عدد روی هر خط = تعداد مسیرهای RIPE RIS؛ خط قرمز = مسیر اصلی.</i>":
        "<i>Number on each line = RIPE RIS path count; red line = main path.</i>",
}


def tr(msg: str, *args) -> str:
    """متن فارسی (یا قالبش) رو بر اساس زبان کاربر برمی‌گردونه و آرگومان‌ها رو جایگذاری می‌کنه."""
    if LANG.get() == "en":
        msg = EN.get(msg, msg)
    return msg.format(*args) if args else msg
