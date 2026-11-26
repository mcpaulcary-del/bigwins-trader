"""The phone app's shared look (BF-D37, BF-D39..BF-D43): CSS, the page shell with the
bottom tab bar, the small self-contained script and the service worker.

Both the read-only dashboard (viewing pages) and the trader's control server (action
pages) render through ``page``. No external file, CDN or font: everything is served by
the app itself. Pages work without JavaScript (server-rendered, plain links and forms);
the script only adds smooth tab switching, refresh, chart interaction, unread badges and
the "Turn on alerts" button.
"""

from __future__ import annotations

import html
from collections.abc import Sequence

THEME = "#0f172a"  # BF-D73: icon navy (the light theme colour is the page background)

TABS: tuple[tuple[str, str, str], ...] = (
    ("home", "/", "Home"),
    ("holdings", "/holdings", "Holdings"),
    ("news", "/news", "News"),  # BF-D92
    ("orders", "/orders", "Orders"),
    ("inbox", "/inbox", "Inbox"),
    ("server", "/server", "Server"),
)
ICONS = {
    "home": '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "holdings": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "orders": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"/>',
    "news": '<path d="M4 5h13v14a1 1 0 0 0 2 0V9h2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM8 9h5M8 13h5M8 17h5"/>',
    "inbox": '<path d="M3 13l3-9h12l3 9v7H3zM3 13h5l1 3h6l1-3h5"/>',
    "server": '<path d="M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1'
    'M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-5-5"/>',
    # BF-D73: one line-icon set (24 grid, 1.75 stroke) replaces every emoji
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "pause": '<path d="M9 5v14M15 5v14"/>',
    "stop-octagon": '<path d="M7.9 2h8.2L22 7.9v8.2L16.1 22H7.9L2 16.1V7.9z"/><path d="M15 9l-6 6M9 9l6 6"/>',
    "minus-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "alert-triangle": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'
    '<path d="M12 9v4M12 17h.01"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "chevron-right": '<path d="M9 6l6 6-6 6"/>',
    "chevron-left": '<path d="M15 6l-6 6 6 6"/>',
    "sliders": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/>'
    '<circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "arrow-up-right": '<path d="M7 17L17 7M8 7h9v9"/>',
    "arrow-down-right": '<path d="M7 7l10 10M17 8v9H8"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8M10 20a2 2 0 0 0 4 0"/>',
    "archive": '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9M10 13h4"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M15 8l2 2"/>',
    "list-check": '<path d="M11 6h9M11 12h9M11 18h9M3 6l1.5 1.5L7 5M3 12l1.5 1.5L7 11M3 18l1.5 1.5L7 17"/>',
    "upload": '<path d="M12 21V9M7 14l5-5 5 5M5 3h14"/>',
    "undo": '<path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',
    "terminal": '<path d="M4 17l6-6-6-6M12 19h8"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-5M12 8h.01"/>',
    "beaker": '<path d="M9 3h6M10 3v6L4 19a1 1 0 0 0 .9 1.5h14.2A1 1 0 0 0 20 19l-6-10V3"/>',
    "activity": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    "swap": '<path d="M7 4L3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
    # BF-D82 / BF-D83: Lock actions, I'm here
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "user-check": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M16 11l2 2 4-4"/>',
}

CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    # BF-D55: "same-origin", not "no-referrer": with no-referrer Chromium sends
    # `Origin: null` on the app's own form POSTs, which the CSRF check refused
    "Referrer-Policy": "same-origin",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}


def mode_label(demo: bool = False, live: bool = False) -> str:
    """BF-D50: the badge from the broker mode in the config (never hard-coded)."""
    return "DEMO" if demo else ("LIVE" if live else "PAPER")


def e(x: object) -> str:
    return html.escape(str(x), quote=True)


def icon(name: str, cls: str = "ic") -> str:
    return (
        f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def plural(n: int, one: str, many: str = "") -> str:
    """BF-D73: real plurals ("1 order", "2 orders"), never "order(s)"."""
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def chev() -> str:
    return f'<span class="chev" aria-hidden="true">{icon("chevron-right")}</span>'


def backlink(href: str, label: str) -> str:
    """The pushed-page back row ("< Holdings"); hidden inside a sheet."""
    return f'<a class="back" href="{e(href)}" data-nav>{icon("chevron-left")}{e(label)}</a>'


def mode_badge(demo: bool = False, live: bool = False) -> str:
    """The one persistent mode label (BF-D73): DEMO amber, PAPER neutral, LIVE solid red."""
    lab = mode_label(demo, live)
    return f'<span class="badge {lab.lower()}">{lab}</span>'


def page(
    title: str,
    body: str,
    active: str = "",
    *,
    demo: bool = False,
    subtitle: str = "",
    notes: Sequence[str] = (),
    latest_inbox: int = 0,
    refresh: bool = True,
    inbox_ids: Sequence[int] = (),
    live: bool = False,
    confirm: bool = False,
    waiting: int = 0,
    latest_news: int = 0,
) -> str:
    """One whole page: header (icon, name, the DEMO / PAPER / LIVE chip, search, settings),
    the body in ``<main>`` (a footer line with the book, the time and a refresh link) and
    the bottom tab bar. ``active`` = the tab to highlight. ``confirm``: a commit screen
    (BF-D73): no tab bar, a Cancel control in the bar, the title in the middle."""
    tabs = "".join(
        f'<a href="{href}" class="tab{" on" if key == active else ""}" data-nav data-tab="{key}"'
        + (' aria-current="page"' if key == active else "")
        + ">"
        f"{icon(key)}<span>{e(label)}</span>"
        + ('<b class="dot" hidden></b>' if key in ("inbox", "news") else "")
        + (
            f'<b class="dot n" aria-label="{plural(waiting, "order")} waiting">{waiting}</b>'
            if key == "orders" and waiting > 0
            else ""
        )
        + "</a>"
        for key, href, label in TABS
    )
    badge = mode_badge(demo, live)
    if confirm:
        head = (
            f'<header class="top ctop"><a class="iconbtn" href="/act" aria-label="Cancel">'
            f'{icon("x")}</a><span class="ctitle">{e(title)}</span>{badge}</header>'
        )
    else:
        head = (
            '<header class="top"><a class="brand" href="/" data-nav>'
            '<img class="logo" src="/icon.svg" alt="" width="28" height="28">'
            f"Big Wins</a>{badge}"
            '<span class="sp"></span>'
            f'<button class="iconbtn" id="searchbtn" type="button" aria-label="Search">{icon("search")}'
            f'</button><a class="iconbtn" href="/settings" data-nav aria-label="Settings">'
            f"{icon('gear')}</a></header>"
        )
    strip = (
        '<div class="demostrip" role="note">Demo data: simulated prices, not your book</div>'
        if demo and not confirm else ""
    )  # fmt: skip
    shown = [n for n in notes if not (demo and n.startswith("DEMO:"))]
    note = "".join(f'<p class="note">{e(n)}</p>' for n in shown)
    foot = ""
    if subtitle or refresh:
        foot = (
            '<p class="foot" id="sub">' + (e(subtitle) if subtitle else "")
            + (f'{" · " if subtitle else ""}<a href="" id="refresh">Refresh</a>' if refresh else "")
            + "</p>"
        )  # fmt: skip
    noscript = '<noscript><meta http-equiv="refresh" content="60"></noscript>' if refresh else ""
    nav = (
        "" if confirm else
        f'<nav class="tabs" aria-label="Sections"><div class="tabin">{tabs}</div></nav>'
    )  # fmt: skip
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#f4f6f9" media="(prefers-color-scheme: light)">'
        '<meta name="theme-color" content="#0b1220" media="(prefers-color-scheme: dark)">'
        '<meta name="color-scheme" content="light dark">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="Big Wins">'
        '<link rel="manifest" href="/manifest.webmanifest">'
        '<link rel="icon" href="/icon.svg" type="image/svg+xml">'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
        f"{noscript}<title>{e(title)} · Big Wins</title>"
        f'<link rel="stylesheet" href="/app.css"></head>'
        f'<body data-tab="{e(active)}" data-latest-inbox="{latest_inbox}"'
        f' data-inbox-ids="{",".join(str(int(i)) for i in inbox_ids)}"'
        f' data-waiting="{int(waiting)}" data-latest-news="{int(latest_news)}"'
        f' data-refresh="{1 if refresh else 0}"{" class=notabs" if confirm else ""}>'
        f'{head}{strip}<div id="ptr" class="ptr" aria-hidden="true"><svg viewBox="0 0 24 24"><circle '
        'cx="12" cy="12" r="9" stroke-dasharray="0 63" transform="rotate(-90 12 12)"/></svg></div>'
        f'<main id="main" data-title="{e(title)}">{note}{body}{foot}</main>'
        f"{nav}"
        '<div id="toast" role="status" aria-live="polite"></div>'
        '<script src="/app.js" defer></script></body></html>'
    )


def section(title: str, body: str, cls: str = "", aside: str = "", card: str = "") -> str:
    """A card; ``card`` names it for the customisable Home (order / hide, BF-D68)."""
    head = f"<h2>{e(title)}{aside}</h2>" if title else ""
    dc = f' data-card="{e(card)}"' if card else ""
    return f'<section class="{cls}"{dc}>{head}{body}</section>'


def tile(label: str, value: str, sub: str = "", tone: str = "") -> str:
    """A small figure; a gain / loss also carries ▲ / ▼ (never colour alone, BF-D62)."""
    mark = {"up": '<span class="arr">▲</span>', "down": '<span class="arr">▼</span>'}.get(tone, "")
    return (
        f'<div class="tile"><div class="tl">{e(label)}</div>'
        f'<div class="tv {tone}">{mark}{e(value)}</div>'
        + (f'<div class="ts">{e(sub)}</div>' if sub else "")
        + "</div>"
    )


def stat(label: str, value: str, sub: str = "", tone: str = "") -> str:
    """An unboxed figure for a ``<dl class="stats">`` (BF-D73); gains carry ▲ / ▼ too."""
    mark = {"up": '<span class="arr">▲</span>', "down": '<span class="arr">▼</span>'}.get(tone, "")
    return (
        f'<div><dt>{e(label)}</dt><dd class="{tone}">{mark}{e(value)}'
        + (f"<small>{e(sub)}</small>" if sub else "")
        + "</dd></div>"
    )


CSS = """
:root{color-scheme:light;
--bg:#f4f6f9;--surface:#ffffff;--surface-2:#f1f5f9;--line:#e2e8f0;--line-strong:#94a3b8;
--ink:#0f172a;--ink-2:#475569;--ink-3:#5b6b82;
--brand:#0f172a;--brand-ink:#ffffff;--mint:#34d399;--focus:#059669;--link:#0f172a;
--up:#047857;--up-soft:#e6f6ef;--down:#be123c;--down-soft:#fdecef;--warn:#92400e;--warn-soft:#fef3c7;
--danger:#b91c1c;--danger-ink:#ffffff;
--c-index:#64748b;--c-grid:#e2e8f0;--c-axis:#5b6b82;--c-band:#0f172a;
--c0:#0f172a;--c1:#1d4ed8;--c2:#7c3aed;--c3:#c2410c;
--tabbar:rgba(255,255,255,.94);--on-up:#ffffff;--on-down:#ffffff;--hatch:rgba(15,23,42,.35);--shadow-sheet:0 -8px 32px rgba(15,23,42,.16);
--shadow-pop:0 8px 28px rgba(15,23,42,.14);
--r-sm:8px;--r-md:12px;--r-lg:20px;--ease:cubic-bezier(.2,.8,.2,1);
--font:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
--card:var(--surface);--card2:var(--surface-2);--ink2:var(--ink-2);--acc:var(--ink);--amber:var(--warn);
--amber-soft:var(--warn-soft);--s1:var(--up);--s2:var(--c-index);--s3:var(--ink-2)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;
--bg:#0b1220;--surface:#131c2e;--surface-2:#1a2538;--line:#243049;--line-strong:#55637d;
--ink:#f1f5f9;--ink-2:#a8b3c7;--ink-3:#8493ab;
--brand:#34d399;--brand-ink:#06281e;--mint:#34d399;--focus:#34d399;--link:#f1f5f9;
--up:#34d399;--up-soft:#0f2e2a;--down:#fb7185;--down-soft:#3a1524;--warn:#fbbf24;--warn-soft:#33270b;
--danger:#dc2626;--danger-ink:#ffffff;
--c-index:#8493ab;--c-grid:#243049;--c-axis:#8493ab;--c-band:#f1f5f9;
--c0:#f1f5f9;--c1:#60a5fa;--c2:#a78bfa;--c3:#fb923c;
--tabbar:rgba(11,18,32,.92);--on-up:#06281e;--on-down:#3a1524;--hatch:rgba(241,245,249,.45);--shadow-sheet:0 -8px 32px rgba(0,0,0,.5);--shadow-pop:0 8px 28px rgba(0,0,0,.5)}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0 auto;background:var(--bg);color:var(--ink);font:400 16px/24px var(--font);
font-variant-numeric:tabular-nums lining-nums;padding:0 16px calc(84px + env(safe-area-inset-bottom));
max-width:640px;-webkit-font-smoothing:antialiased;-webkit-tap-highlight-color:transparent}
body.notabs{padding-bottom:calc(32px + env(safe-area-inset-bottom))}
a{color:var(--link);text-underline-offset:3px;text-decoration-thickness:1px}
b,strong{font-weight:600}
code{font:13px/18px var(--mono)}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.ic{width:20px;height:20px;flex:none}
/* top bar */
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;min-height:52px;
padding:env(safe-area-inset-top) 0 0;margin:0 -16px;padding-left:16px;padding-right:8px;background:var(--bg);
box-shadow:0 1px 0 var(--line)}
.js .top{box-shadow:none}.js .top.scrolled{box-shadow:0 1px 0 var(--line)}
.brand{font:600 17px/24px var(--font);display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none}
.logo{width:28px;height:28px;border-radius:7px;display:block}
.badge{display:inline-flex;align-items:center;height:22px;border-radius:6px;font:600 12px/16px var(--font);
padding:0 7px;letter-spacing:.04em;background:var(--surface-2);color:var(--ink-2)}
.badge.demo{background:var(--warn-soft);color:var(--warn)}.badge.live{background:var(--danger);color:var(--danger-ink)}
.sp{flex:1}
.iconbtn{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:var(--r-md);
border:0;background:none;color:var(--ink);cursor:pointer;padding:0;text-decoration:none}
.iconbtn:active{background:var(--surface-2)}.iconbtn .ic{width:24px;height:24px}
.demostrip{margin:0 -16px;padding:4px 16px;background:var(--warn-soft);color:var(--warn);font:500 13px/20px var(--font)}
.ptr{height:0;overflow:hidden;display:flex;align-items:center;justify-content:center;color:var(--ink-3);transition:height .12s var(--ease)}
.ptr svg{width:24px;height:24px}.ptr circle{fill:none;stroke:var(--ink-3);stroke-width:2.5;stroke-linecap:round}
.ptr.show{height:44px}.ptr.go svg{animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
main{display:block;padding-top:8px;transition:opacity .2s var(--ease)}main.fade{opacity:.4}
/* tab bar */
.tabs{position:fixed;left:0;right:0;bottom:0;z-index:6;display:flex;justify-content:center;
background:var(--tabbar);backdrop-filter:saturate(1.4) blur(14px);-webkit-backdrop-filter:blur(14px);
border-top:1px solid var(--line);padding:4px 4px env(safe-area-inset-bottom)}
.tabs .tabin{position:relative;display:flex;width:100%;max-width:640px}
.tab{position:relative;flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-height:52px;
font:500 11px/14px var(--font);color:var(--ink-3);text-decoration:none;border-radius:var(--r-md)}
.tab.on{color:var(--ink);font-weight:600}.tab .ic{width:24px;height:24px}.tab.on .ic{stroke-width:2.25}
.dot{position:absolute;top:5px;left:calc(50% + 7px);width:8px;height:8px;border-radius:4px;background:var(--down);
font-size:0;padding:0;font-style:normal}
.dot.n{width:auto;min-width:18px;height:18px;top:2px;border-radius:9px;background:var(--warn);color:var(--bg);
font:600 11px/18px var(--font);text-align:center;padding:0 5px}
/* type */
h1{font:600 24px/30px var(--font);letter-spacing:-.01em;margin:8px 0 12px}
h2{font:600 12px/16px var(--font);margin:0 0 12px;color:var(--ink-3);display:flex;align-items:center;gap:8px;
text-transform:uppercase;letter-spacing:.06em}
h2 .sp+a,h2>a{font:500 13px/18px var(--font);letter-spacing:0;text-transform:none;color:var(--ink)}
.h3{font:600 16px/24px var(--font);margin:16px 0 4px}
.muted{color:var(--ink-2)}.small,.sub{font-size:13px;line-height:18px}.sub{color:var(--ink-3)}
.caption{font:400 13px/18px var(--font);color:var(--ink-3)}
.mono{font:13px/18px var(--mono);color:var(--ink-3);word-break:break-all}
.up,.sub.up{color:var(--up)}.down,.sub.down{color:var(--down)}.warn{color:var(--warn)}
.arr{font-size:.7em;vertical-align:.12em;margin-right:3px}
.num,.tv,.r,td,.hv,.money{font-variant-numeric:tabular-nums lining-nums}
/* cards */
section{background:var(--surface);border:0;border-radius:var(--r-md);padding:16px;margin:12px 0;box-shadow:none}
.back{display:inline-flex;align-items:center;gap:2px;margin:4px 0 0 -6px;padding:6px 8px 6px 2px;color:var(--ink-2);
font:500 15px/20px var(--font);text-decoration:none;border-radius:var(--r-sm)}.back .ic{width:20px;height:20px}
.sheet .back,.pane .back{display:none}
.hpx{margin:-4px 0 4px;font:500 15px/22px var(--font)}.hpx b{font:700 28px/34px var(--font);margin-right:6px}
h2 .pill{text-transform:none;letter-spacing:0}
.coname{margin:-8px 0 12px;font-size:15px;color:var(--ink-2)}
/* hero */
.hero{padding:8px 0 4px}.hl{font:400 13px/18px var(--font);color:var(--ink-3)}
.hv{font:700 40px/44px var(--font);letter-spacing:-.02em;margin:4px 0}
.hc{font:500 15px/20px var(--font)}.hero .spk{width:100%;height:46px;margin-top:8px;display:block}
.spk.wide path{vector-effect:non-scaling-stroke}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.vs{display:inline-flex;align-items:center;gap:4px;border-radius:999px;height:24px;padding:0 10px;
font:500 13px/18px var(--font);background:var(--surface-2);color:var(--ink-2)}
.vs.up{background:var(--up-soft);color:var(--up)}.vs.down{background:var(--down-soft);color:var(--down)}
.vs.mile{background:var(--surface-2);color:var(--ink-2)}
/* stats (replaces boxed tiles) */
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 12px;margin:0}
.stats.two{grid-template-columns:repeat(2,minmax(0,1fr))}.stats.four{grid-template-columns:repeat(2,minmax(0,1fr))}
.stats dt{font:400 13px/18px var(--font);color:var(--ink-3)}
.stats dd{margin:2px 0 0;font:600 16px/22px var(--font);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stats small{display:block;font:400 13px/18px var(--font);color:inherit;opacity:1}
.stats dd small.sub{color:var(--ink-3)}
.homestats{padding:4px 0 8px}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:16px 12px;margin-bottom:12px}
.tile{background:none;border:0;border-radius:0;padding:0;min-width:0}
.tl{font:400 13px/18px var(--font);color:var(--ink-3)}
.tv{font:600 18px/24px var(--font);white-space:nowrap}
.ts{font:400 13px/18px var(--font);color:var(--ink-3)}
/* status rows (Home) */
.srows{list-style:none;margin:0;padding:0}
.srows>li{border-top:1px solid var(--line)}.srows>li:first-child{border-top:0}
.srow>summary,.srows a.sr,.srows div.sr{display:flex;align-items:center;gap:12px;min-height:52px;padding:8px 0;cursor:pointer;list-style:none;
color:var(--ink);text-decoration:none}
.srow>summary::-webkit-details-marker{display:none}
.srl{flex:none;width:92px;font:500 14px/20px var(--font);color:var(--ink-2)}
.srv{flex:1;min-width:0;font:400 15px/20px var(--font)}
.srv .sub{display:block}
.srow>summary .chev,.srows a.sr .chev{color:var(--ink-3);transition:transform .2s var(--ease)}
.srow[open]>summary .chev{transform:rotate(90deg)}
.srow .srbody{padding:4px 0 16px}
.srow .srbody>section{margin:0;padding:0;background:none}
.srow .srbody>section>h2{display:none}
.sd{display:inline-block;width:8px;height:8px;border-radius:4px;background:var(--ink-3);margin-right:6px;vertical-align:1px}
.sd.ok{background:var(--up)}.sd.wait{background:var(--warn)}.sd.bad{background:var(--down)}
/* charts */
.chartbox{position:relative}
.chart{width:100%;height:auto;display:block;touch-action:pan-y;overflow:visible}
.grid{stroke:var(--c-grid);stroke-width:1}.base{stroke:var(--line-strong);stroke-width:1;stroke-dasharray:2 4}
.ax{fill:var(--c-axis);font-size:12px;paint-order:stroke;stroke:var(--surface);stroke-width:3px;stroke-linejoin:round}
.home .ax{stroke:var(--bg)}
.s1{fill:none;stroke:var(--up);stroke-width:2;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke}
.tdown .s1,.s1.down{stroke:var(--down)}
.s2{fill:none;stroke:var(--c-index);stroke-width:1.5;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.s3{fill:none;stroke:var(--ink-2);stroke-width:2;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.area{fill:url(#gA);stroke:none}.gA0{stop-color:var(--up);stop-opacity:.12}.gA1{stop-color:var(--up);stop-opacity:0}
.tdown .gA0,.tdown .gA1{stop-color:var(--down)}
.dd{fill:var(--down);fill-opacity:.12;stroke:var(--down);stroke-width:1.5;vector-effect:non-scaling-stroke}
.bar{fill:var(--line-strong);fill-opacity:.4}.bar.me{fill:var(--ink);stroke:none}
.d1{fill:var(--up);stroke:var(--surface);stroke-width:2}.tdown .d1{fill:var(--down)}
.buyd{fill:var(--surface);stroke:var(--ink);stroke-width:1.5}.selld{fill:var(--ink);stroke:var(--surface);stroke-width:1.5}
.xh{stroke:var(--ink-3);stroke-width:1}.xd{fill:var(--surface);stroke:var(--up);stroke-width:2}.tdown .xd{stroke:var(--down)}.xd.xi{stroke:var(--c-index)}
.tip{font-size:11px;fill:var(--ink-2)}.tipbox{fill:var(--surface);stroke:var(--line)}
.readout{display:flex;justify-content:space-between;gap:8px;min-height:20px;font:400 13px/20px var(--font);color:var(--ink-3);margin:0 0 4px}
.readout b{color:var(--ink);font-weight:600}
.ctip{position:absolute;top:4px;pointer-events:none;background:var(--surface);border:1px solid var(--line);
border-radius:var(--r-sm);box-shadow:var(--shadow-pop);padding:6px 10px;font-size:13px;line-height:18px;
min-width:150px;opacity:0;transition:opacity .12s var(--ease)}
.ctip.on{opacity:1}.ctip b{font-size:14px;font-weight:600}
.legend{font:400 13px/18px var(--font);color:var(--ink-3);margin:8px 0;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center}
.legend b{color:var(--ink);font-weight:600}.legend>span{white-space:nowrap;display:inline-flex;align-items:center}
.kh{background:none;box-shadow:inset 0 0 0 1.5px var(--ink-2)}
.key{display:inline-block;width:8px;height:8px;border-radius:4px;vertical-align:middle;margin:0 6px 0 0}
.k1{background:var(--up)}.tdown .k1,.k1.down{background:var(--down)}.k2{background:var(--c-index)}.kb{background:none;box-shadow:inset 0 0 0 1.5px var(--ink)}.ks{background:var(--ink)}.k3{background:var(--ink-2)}
/* segmented (underline) control and filter chips */
.seg{display:flex;gap:24px;border-bottom:1px solid var(--line);margin:0 0 12px;overflow-x:auto;scrollbar-width:none}
.seg::-webkit-scrollbar,.chips::-webkit-scrollbar{display:none}
.seg a,.seg button{flex:none;padding:10px 0;font:500 15px/20px var(--font);color:var(--ink-3);background:none;border:0;
border-bottom:2px solid transparent;margin-bottom:-1px;text-decoration:none;cursor:pointer;border-radius:0}
.seg .on{color:var(--ink);font-weight:600;border-bottom-color:var(--ink)}
.seg .chip{height:auto;background:none;border-radius:0;padding:10px 0;color:var(--ink-3)}.seg .chip.on{background:none;color:var(--ink)}
.seg.sm{justify-content:center;gap:20px;border-bottom:0;margin:8px 0 0}
.seg.sm a,.seg.sm button{font-size:13px;line-height:18px;padding:6px 2px}
.chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin:0 0 12px;padding:2px 0}
.chip{flex:none;display:inline-flex;align-items:center;gap:6px;height:32px;border:0;background:var(--surface-2);color:var(--ink);
border-radius:var(--r-sm);padding:0 12px;font:500 14px/20px var(--font);text-decoration:none;cursor:pointer;
transition:background .12s var(--ease),color .12s var(--ease)}
.chip.on{background:var(--ink);color:var(--bg)}
/* tables, lists */
table{width:100%;border-collapse:collapse}td,th{padding:8px 4px;border-top:1px solid var(--line);vertical-align:top;text-align:left}
th{font:500 12px/16px var(--font);color:var(--ink-3);border-top:0}
.r{text-align:right}.buy,.sell{color:inherit}
.side{display:inline-block;font:600 12px/20px var(--font);padding:0 7px;border-radius:6px;background:var(--surface-2);color:var(--ink-2)}
.list{list-style:none;padding:0;margin:0}.list li{padding:12px 0;border-top:1px solid var(--line)}
.list li:first-child{border-top:0}
.rowlink{display:flex;align-items:center;gap:12px;color:var(--ink);text-decoration:none;min-height:36px}
.rowlink:active{background:var(--surface-2)}
.rowlink .grow{flex:1;min-width:0}.chev{color:var(--ink-3);display:inline-flex}.chev .ic{width:18px;height:18px}
.hold li{padding:10px 0}
.hrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:0 12px;width:100%;align-items:center}
.hrow .hc1{font:600 16px/22px var(--font)}.hrow .hc2{font:400 13px/18px var(--font);color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hrow .hr1{font:600 16px/22px var(--font);text-align:right}.hrow .hr2{font:500 13px/18px var(--font);text-align:right;white-space:nowrap}
.hrow .spk{display:none}
@media (min-width:430px){.hrow{grid-template-columns:minmax(0,1fr) 56px auto}.hrow .spk{display:block;grid-row:1/3;grid-column:2;width:56px;height:20px}
.hrow .hr1,.hrow .hr2{grid-column:3}}
.hold .spk{width:56px;height:20px;flex:none}
.bars{display:none}
.hold li.hl{background:var(--surface-2);border-radius:var(--r-sm);margin:0 -8px;padding:10px 8px}
.investbar{height:6px;border-radius:3px;background:var(--surface-2);overflow:hidden;margin:12px 0 4px}
.investbar b{display:block;height:100%;background:var(--ink)}
.tools{display:flex;align-items:center;gap:12px;justify-content:space-between;margin:16px 0 4px}
.selwrap{display:inline-flex;align-items:center;gap:6px;font:500 14px/20px var(--font);color:var(--ink-3)}
.sel{appearance:none;-webkit-appearance:none;border:0;background:var(--surface-2);color:var(--ink);font:500 14px/20px var(--font);
height:32px;border-radius:var(--r-sm);padding:0 28px 0 10px;cursor:pointer;
background-image:linear-gradient(45deg,transparent 50%,currentColor 50%),linear-gradient(135deg,currentColor 50%,transparent 50%);
background-position:calc(100% - 14px) 14px,calc(100% - 10px) 14px;background-size:4px 4px;background-repeat:no-repeat}
.viewsw{display:inline-flex;background:var(--surface-2);border-radius:var(--r-sm);padding:2px}
.viewsw a,.viewsw button{border:0;background:none;color:var(--ink-2);font:500 13px/18px var(--font);padding:5px 10px;border-radius:6px;text-decoration:none;cursor:pointer}
.viewsw .on{background:var(--surface);color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(15,23,42,.12)}
.hview{display:none}.hview.on,.hview:target{display:block}
/* donut (behind the Heatmap toggle) */
.donutrow{display:flex;gap:16px;align-items:center}
.donut{position:relative;margin:0;width:120px;flex:none}.donut svg{width:120px;height:120px}
.donut figcaption{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none}
.donut figcaption b{font-size:15px;font-weight:600}
.donut figcaption span,.ring figcaption span{font-size:12px;color:var(--ink-3)}
.ds{fill:none;stroke-width:14;cursor:pointer;transition:stroke-width .12s var(--ease),opacity .12s var(--ease)}
.ds.dim{opacity:.3}.ds.hl{stroke-width:18}
.legend2{list-style:none;margin:0;padding:0;font-size:13px;flex:1;columns:2;column-gap:16px}.legend2 li{display:flex;gap:6px;
align-items:center;padding:1px 0;break-inside:avoid}.legend2 i{width:8px;height:8px;border-radius:2px;display:inline-block}
.sheet #sub{display:none}
.spk{overflow:visible}.spl{fill:none;stroke:var(--ink-3);stroke-width:1.5;stroke-linejoin:round;stroke-linecap:round}
.spa{display:none}.spk.up .spl{stroke:var(--up)}.spk.down .spl{stroke:var(--down)}.spd{display:none}
.hero .spa{display:block;fill:var(--up);opacity:.1}.hero .spk.down .spa{fill:var(--down)}
/* rings, gauge, meters */
.rings{display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.ring{position:relative;margin:0;width:84px}.ring svg{width:84px;height:84px}
.ring figcaption{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring figcaption b{font-size:16px;font-weight:600}.rt{fill:none;stroke:var(--surface-2);stroke-width:6}
.rv{fill:none;stroke:var(--ink);stroke-width:6;stroke-linecap:round}
.ring.good .rv{stroke:var(--up)}.ring.warnr .rv{stroke:var(--warn)}
.gauge{width:100%;max-width:220px;display:block;margin:0 auto}.gt{fill:none;stroke:var(--surface-2);stroke-width:12;stroke-linecap:butt}
.gv{fill:none;stroke:var(--up);stroke-width:12;stroke-linecap:butt}.gauge.bad .gv{stroke:var(--down)}
.gm{fill:var(--ink)}.gbig{font-size:28px;font-weight:700;fill:var(--ink)}
.tmeter{margin:8px 0 24px}.tbar{position:relative;height:8px;border-radius:4px;background:var(--surface-2)}
.tbar b{display:block;height:100%;border-radius:4px;background:var(--up)}.tmeter.bad .tbar b{background:var(--down)}
.tk{position:absolute;top:-3px;width:2px;height:14px;background:var(--ink-3);transform:translateX(-1px)}
.tl3{position:absolute;top:14px;font-size:11px;color:var(--ink-3);transform:translateX(-50%);white-space:nowrap}
.meter{height:6px;border-radius:2px;background:var(--surface-2);overflow:hidden;margin:6px 0}
.meter b{display:block;height:100%;background:var(--ink)}.meter.hi b{background:var(--warn)}.meter.crit b{background:var(--down)}
/* status chips */
.pill{display:inline-flex;align-items:center;gap:5px;height:22px;font:600 12px/16px var(--font);border-radius:999px;padding:0 9px;
white-space:nowrap;background:var(--surface-2);color:var(--ink-2);border:0;vertical-align:1px}
.pill:before{content:"";width:6px;height:6px;border-radius:3px;background:currentColor;flex:none}
.pill.nodot:before{display:none}
.ok{background:var(--up-soft);color:var(--up)}.amber{background:var(--warn-soft);color:var(--warn)}
.bad{background:var(--down-soft);color:var(--down)}
.st-holding{background:var(--up-soft);color:var(--up)}.st-sold{background:var(--surface-2);color:var(--ink-2)}
.st-proposed{background:var(--warn-soft);color:var(--warn)}.st-passed{background:var(--surface-2);color:var(--ink-2)}
.ckrow{display:flex;gap:12px;align-items:flex-start;justify-content:space-between;font-size:14px;line-height:20px}
.ckrow .pill{flex:none;min-width:64px;justify-content:center}
.reld{margin:8px 0 0}.reld dt{font:600 12px/16px var(--font);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);margin-top:10px}
.reld dd{margin:2px 0 0;font-size:14px;line-height:20px}
/* banners */
.note{background:var(--warn-soft);color:var(--ink);border-left:3px solid var(--warn);border-radius:var(--r-sm);
padding:10px 12px;font:400 14px/20px var(--font);margin:12px 0}
.note.info{background:var(--surface-2);border-left-color:var(--line-strong)}
.note.bad{background:var(--down-soft);border-left-color:var(--down);color:var(--ink)}
/* buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:var(--r-md);
padding:0 18px;font:600 16px/20px var(--font);cursor:pointer;text-decoration:none;
background:var(--brand);color:var(--brand-ink);min-height:48px;box-shadow:none;transition:filter .12s var(--ease),background .12s var(--ease)}
.btn:active{filter:brightness(.92)}.btn .ic{width:18px;height:18px}
.btn.wide{width:100%}.btn.sec{background:var(--surface-2);color:var(--ink);border:0}
section .btn.sec{background:var(--surface-2)}
.btn.ter{background:none;color:var(--ink);padding:0 4px;min-height:40px;text-decoration:underline;text-underline-offset:3px}
.btn.sm{min-height:40px;font-size:14px;padding:0 14px}
.btn.danger{background:var(--danger);color:var(--danger-ink);border:0;letter-spacing:0}
.btn.dangerline{background:none;color:var(--down);border:1px solid var(--danger)}
.btn.warnb,.btn.caution{background:var(--warn-soft);color:var(--warn);border:1px solid var(--warn)}
.btn.big{min-height:52px}
.btn[disabled]{opacity:.4;pointer-events:none}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}
/* one-time code */
.code{font:600 28px/1 var(--mono);letter-spacing:.4em;text-indent:.4em;text-align:center;width:100%;height:56px;padding:0 12px;
border-radius:var(--r-md);border:1px solid var(--line-strong);background:var(--surface);color:var(--ink)}
.code:focus{border:2px solid var(--focus);outline:none}
.code::placeholder{color:var(--line-strong);letter-spacing:.3em}
.field{font:400 16px/24px var(--font);width:100%;height:48px;padding:0 12px;border-radius:var(--r-md);border:1px solid var(--line-strong);
background:var(--surface);color:var(--ink)}.field:focus{border:2px solid var(--focus);outline:none;padding:0 11px}
.flabel{display:block;font:500 14px/20px var(--font);color:var(--ink-2);margin:16px 0 6px}
.summary{font:600 18px/24px var(--font);margin:4px 0 8px}
/* approval card */
.waitcard{border:0;border-left:3px solid var(--warn);background:var(--surface)}
.waitcard>h2{color:var(--warn)}.waitcard .btns{grid-template-columns:3fr 2fr}
.otable .tot td{font-size:14px}
.cd{display:inline-flex;gap:6px;align-items:center;font:500 14px/20px var(--font);color:var(--warn);margin:0 0 4px}.cd .ic{width:16px;height:16px}
/* inbox */
.msg{position:relative;padding:12px 0 12px 18px!important;transition:transform .2s var(--ease)}
.msg .mh{display:flex;align-items:baseline;gap:8px}.msg .mk{flex:1;min-width:0;font:400 16px/22px var(--font)}
.msg.unread .mk{font-weight:600}.msg .mt{font:400 13px/18px var(--font);color:var(--ink-3);white-space:nowrap}
.msg .t{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font:400 14px/20px var(--font);color:var(--ink-2)}
.msg.unread:before{content:"";position:absolute;left:2px;top:19px;width:8px;height:8px;border-radius:4px;background:var(--ink)}
.msg .mic{position:absolute;left:-2px;top:15px;color:var(--down)}.msg .mic .ic{width:16px;height:16px}
.msg.page.unread:before{display:none}
.msg pre{white-space:pre-wrap;font:13px/18px var(--mono);margin:8px 0 0;color:var(--ink-2);max-height:16em;overflow:auto;
background:var(--surface-2);border-radius:var(--r-sm);padding:10px}
.msg.swiping{transition:none}
.msg>details>summary{list-style:none;display:flex;align-items:center;gap:8px;cursor:pointer;margin:0;font:inherit;color:inherit}
.msg>details>summary .grow{flex:1;min-width:0}.msg>details>summary::-webkit-details-marker{display:none}.msg>details[open]>summary .chev{transform:rotate(90deg)}
.msg.grp{padding-left:0!important}.msg.grp .mk{display:block}.msg.grp .list{margin-top:8px}
.msg .meta{font-size:12px;color:var(--ink-3);margin-top:6px}
.day{font:600 12px/16px var(--font);color:var(--ink-3);text-transform:uppercase;letter-spacing:.06em;
margin:16px 0 0;border-top:0!important;padding:0 0 4px!important}
.list li.day:first-child{margin-top:0}
/* order progress */
.steps{display:flex;align-items:center;gap:0;margin:10px 0 4px}.steps i{flex:none;width:10px;height:10px;
border-radius:5px;background:var(--surface-2);border:2px solid var(--line-strong)}.steps i.on{background:var(--ink);border-color:var(--ink)}
.steps i.bad{background:var(--down);border-color:var(--down)}.steps em{flex:1;height:2px;background:var(--line)}.steps em.on{background:var(--ink)}
.stepl{display:flex;justify-content:space-between;font-size:12px;color:var(--ink-3)}
.tl2{list-style:none;margin:8px 0 0;padding:0 0 0 14px;border-left:2px solid var(--line)}
.tl2 li{position:relative;padding:3px 0 3px 6px;font-size:13px;border-top:0!important}
.tl2 li:before{content:"";position:absolute;left:-20px;top:9px;width:10px;height:10px;border-radius:5px;background:var(--line-strong)}
.tl2 li.done:before{background:var(--ink)}.tl2 li.badst:before{background:var(--down)}
.ord>summary{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:center}
.ord>summary::-webkit-details-marker{display:none}.ord>summary .grow{flex:1;min-width:0}
.ord[open]>summary .chev{transform:rotate(90deg)}
/* BF-D75..BF-D80: scoreboard, research, health, costs, announcements */
.scorecard{border-left:3px solid var(--line-strong)}
.verdict{display:flex;align-items:center;gap:8px;font:600 18px/24px var(--font);margin:0 0 12px}
.verdict .ic{width:20px;height:20px;flex:none}.verdict.up{color:var(--up)}.verdict.down{color:var(--down)}
.verdict2{font:400 15px/22px var(--font);margin:4px 0 12px}
.gaprow{display:flex;align-items:center;gap:12px;margin:12px 0 0}.gaprow .spk{flex:1;height:28px}
.notelink{display:flex;gap:8px;align-items:center;text-decoration:none}.notelink .ic{width:18px;height:18px;flex:none;color:var(--down)}
.rline,.frow{display:flex;align-items:center;gap:12px}.rline .grow,.frow .grow{flex:1;min-width:0}
.rline b,.frow b{display:block;font-weight:600}.rline .sub,.frow .sub{display:block}
/* BF-D94: the paper record, the nightly report and Big movers */
.frow .rcol{text-align:right;white-space:nowrap}.frow .rcol b,.frow .rcol .sub{display:block}
.frow .why{display:block;margin:2px 0}.frow .why a{margin-left:4px}
.fold{border-top:1px solid var(--line);padding:10px 0}.fold>summary{cursor:pointer}
.fold>summary b,.fold>summary .sub{display:inline}
.prose{overflow-wrap:anywhere}.prose h2{margin-top:16px}.srcs{padding-left:22px}.srcs li{padding:4px 0}
a.nrow.card{display:flex;align-items:center;gap:12px;padding:12px 0;text-decoration:none;color:inherit}
.rr{text-align:right;white-space:nowrap}.rr .rv{display:block;font:600 15px/20px var(--font)}
.rsec{margin-top:8px}.rsec>summary{cursor:pointer;font:500 14px/20px var(--font);color:var(--ink-2);padding:8px 0}
.ann .pills{margin-top:4px}.ann div{font:400 15px/21px var(--font)}
.home .o0{order:0}
/* server */
.htiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.ht{border:0;padding:0;background:none;min-width:0}
.ht .tl{display:flex;justify-content:space-between}.ht .tv{font-size:18px}
.logs{white-space:pre-wrap;font:12px/17px var(--mono);max-height:20em;overflow:auto;background:var(--surface-2);border-radius:var(--r-sm);padding:10px;color:var(--ink-2)}
.menu{list-style:none;margin:0;padding:0}.menu li{border-top:1px solid var(--line)}.menu li:first-child{border-top:0}
.mrow{display:flex;align-items:center;gap:12px;min-height:56px;padding:8px 0;color:var(--ink);text-decoration:none;width:100%;
background:none;border:0;font:inherit;text-align:left;cursor:pointer}
.mrow:active{background:var(--surface-2)}
.mrow>.ic,.mrow>.mi{flex:none;width:22px;height:22px;color:var(--ink-2)}
.mrow .mt{flex:1;min-width:0}.mrow .ml{display:block;font:500 16px/22px var(--font)}.mrow .md{display:block;font:400 13px/18px var(--font);color:var(--ink-3)}
.mrow .mv{font:400 14px/20px var(--font);color:var(--ink-3);white-space:nowrap}
.mrow.dangerrow .ml,.mrow.dangerrow>.ic{color:var(--down)}
.mrow form{margin:0}
.statusline{display:flex;align-items:center;gap:8px;font:600 18px/24px var(--font);margin:0}
label.chk{display:flex;gap:10px;align-items:center;margin:12px 0;font-size:15px}
label.chk input{width:20px;height:20px;accent-color:var(--ink)}
footer,.foot{font:400 13px/18px var(--font);color:var(--ink-3);text-align:center;margin:24px 0 8px}
.foot a{color:var(--ink-2)}
/* skeleton */
.skel{border-radius:var(--r-md);background:var(--surface-2);animation:pulse 1.2s ease-in-out infinite alternate;height:120px;margin:12px 0}
.skel.s{height:60px}@keyframes pulse{from{opacity:.6}to{opacity:1}}
/* toast */
#toast{position:fixed;left:50%;bottom:calc(80px + env(safe-area-inset-bottom));transform:translate(-50%,12px);
background:var(--ink);color:var(--bg);padding:10px 16px;border-radius:var(--r-md);font:500 14px/20px var(--font);
opacity:0;pointer-events:none;transition:opacity .2s var(--ease),transform .2s var(--ease);z-index:9;max-width:90vw}
#toast.on{opacity:1;transform:translate(-50%,0)}
/* sheet */
.sheetbg{position:fixed;inset:0;background:rgba(2,6,23,.5);z-index:7;opacity:0;transition:opacity .24s var(--ease)}
.sheetbg.on{opacity:1}.sheet{position:fixed;left:0;right:0;bottom:0;z-index:8;max-height:92vh;overflow:auto;
background:var(--surface);border-radius:var(--r-lg) var(--r-lg) 0 0;padding:0 16px calc(24px + env(safe-area-inset-bottom));
transform:translateY(100%);transition:transform .24s var(--ease),max-height .24s var(--ease),border-radius .24s var(--ease);
max-width:640px;margin:0 auto;box-shadow:var(--shadow-sheet)}
.sheet.on{transform:translateY(0)}.sheet.full{max-height:100vh;border-radius:0;top:0}.sheet.dragging{transition:none}
.sheethead{position:sticky;top:0;z-index:1;background:var(--surface);margin:0 -16px;padding:6px 8px 4px 16px}
.grab{width:36px;height:4px;border-radius:2px;background:var(--line-strong);margin:4px auto 6px}
.shrow{display:flex;align-items:center;gap:6px}
.sheetx{flex:none}
.sheet section{background:none;padding:0;margin:20px 0}
.sheet h1{margin-top:4px}
.ghost{display:none}
.sitem.done b{color:var(--up)}.setup .btn{margin-top:8px}
[hidden]{display:none!important}
/* Home: one column on a phone (cards ordered by urgency), two panes from 860px */
@media (max-width:859px){.home{display:flex;flex-direction:column}.home>.col-a,.home>.col-b{display:contents}
.home .o1{order:1}.home .o2{order:2}.home .o3{order:3}.home .o4{order:4}.home .o5{order:5}.home .o6{order:6}.home .o7{order:7}}
.home .perf{margin:4px 0 8px}
/* layout: Fold inner screen and tablets */
@media (min-width:860px){body{max-width:1040px;padding:0 24px calc(84px + env(safe-area-inset-bottom))}
.top,.demostrip{margin:0 -24px;padding-left:24px;padding-right:16px}
main{display:grid;grid-template-columns:minmax(0,720px);justify-content:center;align-content:start}
main:has(>.home),main:has(>.twopane){display:block}
.chart{max-width:560px}.home .chart,.pane .chart{max-width:none}
main>section .chart .ax,main>section .chart .tip{font-size:8px}main>section [data-chart] .ax{font-size:12px}
.home{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:0 24px;align-items:start}
.home>.col-b{position:sticky;top:64px}.home .o3{margin-top:4px}
.twopane{display:grid;grid-template-columns:minmax(0,520px) minmax(0,1fr);gap:0 24px;align-items:start}
.twopane>.pane{position:sticky;top:64px;max-height:calc(100vh - 160px);overflow:auto;background:var(--surface);border-radius:var(--r-md);padding:0 16px 16px}
.twopane>.pane section{background:none;padding:0;margin:20px 0}
.tabs .tabin{max-width:720px}.sheet{max-width:760px}}
.pane:empty{display:none}
.panehint{color:var(--ink-3);font-size:14px;padding:24px 0;text-align:center}
@media (max-width:859px){.twopane>.pane{display:none}}
.hit{fill:transparent;cursor:crosshair}.hit.on{fill:var(--ink);fill-opacity:.06}
.ctip{white-space:pre-line}
[data-tips] .ctip{position:static;margin-top:8px;box-shadow:none;display:none;left:auto!important;opacity:1}
[data-tips] .ctip.on{display:block}
.cut{stroke-width:1;stroke-dasharray:4 3}.cut.c20{stroke:var(--up)}.cut.c40{stroke:var(--warn)}
.rk{fill:var(--surface);stroke:var(--ink);stroke-width:1.5}.rk.top{fill:var(--up);stroke:var(--up)}.rk.keep{fill:var(--warn);stroke:var(--warn)}
.out{fill:var(--line)}.fan1{fill:var(--c-band);fill-opacity:.06}.fan2{fill:var(--c-band);fill-opacity:.12}
.med{fill:none;stroke:var(--ink-3);stroke-width:1.5}.meanl{fill:none;stroke:var(--warn);stroke-width:1.5;stroke-dasharray:6 3}
.meand{fill:var(--warn)}.act{fill:none;stroke:var(--up);stroke-width:2.25;stroke-linejoin:round}.act.down{stroke:var(--down)}
.actd{fill:var(--ink);stroke:var(--surface);stroke-width:1.5}.hypd{fill:var(--surface);stroke:var(--ink-2);stroke-width:1.5}
.hi52{fill:none;stroke:var(--ink-3);stroke-width:1.2;stroke-dasharray:2 3}
.fk1{background:var(--c-band);opacity:.12;height:8px;border-radius:2px}.fk2{background:var(--c-band);opacity:.25;height:8px;border-radius:2px}
.km{background:var(--warn)}.ka{background:var(--up)}.khi{background:var(--ink-3)}
.lead2{font-size:16px}.bul{margin:4px 0;padding-left:20px}.bul li{margin:4px 0}
.about summary,details summary{cursor:pointer;font:500 14px/20px var(--font);color:var(--ink);margin:8px 0}
.doc h1{font-size:22px;line-height:28px}.doc h2{font:600 17px/24px var(--font);text-transform:none;letter-spacing:0;color:var(--ink);margin-top:20px}
.doc p,.doc li{font-size:15px;line-height:23px}
.tscroll{overflow-x:auto}.doc table{font-size:13px}
.tmap{position:relative;width:100%;aspect-ratio:100/62;margin:8px 0}
.tm{position:absolute;padding:1.5px;box-sizing:border-box;text-decoration:none}
.tmi{display:block;width:100%;height:100%;box-sizing:border-box;border-radius:6px;padding:5px 6px;font:500 12px/16px var(--font);
overflow:hidden;transition:background .2s var(--ease)}
.tm0{background:var(--surface-2);color:var(--ink-2)}
.tmu1{background:var(--up-soft);background:color-mix(in srgb,var(--up) 18%,var(--surface));color:var(--ink)}
.tmu2{background:var(--up-soft);background:color-mix(in srgb,var(--up) 45%,var(--surface));color:var(--ink)}
.tmu3{background:var(--up);color:var(--on-up)}
.tmd1,.tmd2,.tmd3{background-image:repeating-linear-gradient(135deg,var(--hatch) 0 2px,transparent 2px 5px);background-size:100% 6px;background-repeat:no-repeat;background-position:0 100%}
.tm.sm .tmi{white-space:nowrap;font-size:11px;line-height:14px;padding:3px 4px}
.tmd1{background-color:var(--down-soft);background-color:color-mix(in srgb,var(--down) 18%,var(--surface));color:var(--ink)}
.tmd2{background-color:var(--down-soft);background-color:color-mix(in srgb,var(--down) 45%,var(--surface));color:var(--ink)}
.tmd3{background-color:var(--down);color:var(--on-down)}
.whatif label{display:block;font-weight:500}input[type=range]{width:100%;accent-color:var(--ink);height:34px;margin:4px 0 0}
.wscale{display:flex;justify-content:space-between;font-size:12px;color:var(--ink-3)}.wv b{font-size:22px;font-weight:700}
.wbar{position:relative;height:8px;border-radius:4px;background:var(--surface-2);margin:16px 0 28px}
.wbar>b{display:block;height:100%;border-radius:4px;background:var(--ink);transition:width .2s var(--ease)}
.wbar.bad>b{background:var(--down)}.wbar.mid>b{background:var(--warn)}
.wk{position:absolute;top:-4px;width:2px;height:16px;background:var(--ink-3)}
.wkl{position:absolute;top:14px;font-size:11px;transform:translateX(-50%);color:var(--ink-3);white-space:nowrap}
.calnav{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.calnav .iconbtn{text-decoration:none}
.calt{margin:0;font:600 18px/24px var(--font);text-transform:none;letter-spacing:0;color:var(--ink)}
.cwk,.cgrid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:2px;text-align:center}
.cwk span{font-size:12px;color:var(--ink-3);font-weight:500}
.cday{min-height:44px;border:0;background:none;border-radius:var(--r-sm);color:var(--ink);
font:400 15px/20px var(--font);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;padding:4px 0;min-width:0}
.cday.out{opacity:.45;color:var(--ink-3)}.cday.today{box-shadow:inset 0 0 0 1.5px var(--ink);font-weight:600}
.cday.sel{background:var(--ink);color:var(--bg)}.cday.sel .cdots i{background:var(--bg)!important}
.cdots{display:flex;gap:3px;height:6px}.cdots i,.cl i,.cdk{width:6px;height:6px;border-radius:3px;display:inline-block;flex:none}
.cd-decision{background:var(--ink)}.cd-cutoff{background:var(--warn)}.cd-exdiv{background:var(--c1)}.cd-pay{background:none;box-shadow:inset 0 0 0 1.5px var(--c1)}
.cd-c6{background:var(--c2)}.cd-cgt{background:var(--c3)}.cd-eofy{background:none;box-shadow:inset 0 0 0 1.5px var(--ink-3)}
.cevs li>a{margin-left:auto;flex:none}
.clegend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:var(--ink-3);margin:12px 0 4px}
.cl{display:inline-flex;align-items:center;gap:5px}.cevs li{display:flex;gap:10px;align-items:flex-start}
.cevs .cdk{margin-top:8px}
.cmpout{position:static;opacity:1;margin-top:8px;box-shadow:none;min-height:2.6em}
.k-c0{background:var(--c0)}.k-c1{background:var(--c1)}.k-c2{background:var(--c2)}.k-c3{background:var(--c3)}
.rprog{display:flex;align-items:center;gap:12px;margin:0 0 12px}.rprog span{font:500 13px/18px var(--font);color:var(--ink-3);white-space:nowrap}
.rdots{display:flex;gap:4px;flex:1;margin:0}
.rdot{flex:1;height:4px;border-radius:2px;border:0;background:var(--surface-2);padding:0;cursor:pointer;min-height:0}
.rdot.on{background:var(--ink)}
.replay.js .rpane{display:none}.replay.js .rpane.on{display:block}
.replay:not(.js) .rbtn,.replay:not(.js) [data-rplay],.replay:not(.js) .rdots,.replay:not(.js) .rprog{display:none}
.replay.js .rbtn{position:sticky;bottom:calc(56px + env(safe-area-inset-bottom));background:var(--bg);padding:8px 0 12px;margin:0;z-index:2;box-shadow:0 -1px 0 var(--line)}
.rbars{list-style:none;padding:0;margin:6px 0}.rb{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;
align-items:center;font-size:13px;padding:4px 0!important;border-top:1px solid var(--line)!important}
.rb:first-child{border-top:0!important}.rbn{font-weight:600}
.rbb{display:none}.rbv{color:var(--ink-3);text-align:right}
.rb.pick b{color:var(--ink)}.rb.pick .rbv{color:var(--ink);font-weight:600}
li.rbuy b,li.rsell b{color:inherit}
#srch{position:fixed;inset:0;z-index:10;background:var(--bg);padding:calc(12px + env(safe-area-inset-top)) 16px 16px;
overflow:auto;display:none}#srch.on{display:block}
.sbar{display:flex;gap:8px;align-items:center;max-width:720px;margin:0 auto}.sbar input{flex:1;font:400 17px/24px var(--font);
height:48px;padding:0 14px;border-radius:var(--r-md);border:1px solid var(--line-strong);background:var(--surface);color:var(--ink)}
.sbar input:focus{border:2px solid var(--focus);outline:none;padding:0 13px}#sres{max-width:720px;margin:8px auto}
#sres h3{font:600 12px/16px var(--font);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);margin:16px 0 4px}
#sres a{display:block;padding:10px 4px;border-top:1px solid var(--line);color:var(--ink);text-decoration:none}
#sres a .sub{display:block}#sres mark{background:var(--warn-soft);color:inherit;border-radius:3px}
.tourbg{position:fixed;inset:0;z-index:11;background:rgba(2,6,23,.55)}
.tourring{position:fixed;z-index:12;border:2px solid #fff;border-radius:var(--r-md);box-shadow:0 0 0 3px var(--focus);
pointer-events:none;transition:all .24s var(--ease)}
.tourtip{position:fixed;z-index:12;left:16px;right:16px;max-width:360px;margin:0 auto;background:var(--surface);
color:var(--ink);border-radius:var(--r-md);padding:16px;box-shadow:var(--shadow-pop);transition:bottom .24s var(--ease)}
.tourtip .btns{margin:12px 0 0}.tourtip p{margin:4px 0}
body.editing section[data-card]{outline:2px dashed var(--line-strong);outline-offset:2px}
.cardbar{display:none;gap:6px;justify-content:flex-end;margin:-4px 0 8px}body.editing .cardbar{display:flex}
.cardbar button{min-width:44px}section.hiddencard{display:none}
body.editing section.hiddencard{display:block;opacity:.45}#editdone{position:fixed;left:50%;transform:translateX(-50%);
bottom:calc(80px + env(safe-area-inset-bottom));z-index:9;display:none}body.editing #editdone{display:inline-flex}
.homehint{text-align:center}
body.compact section{padding:12px;margin:8px 0}body.compact .hv{font-size:34px;line-height:40px}
body.compact .list li{padding:8px 0}
.sheetsk{padding:8px 0}.sheetsk .skel{margin:10px 0}
/* confirm screens */
.confirm{max-width:480px;margin:0 auto}
.ctop{display:flex;align-items:center;gap:8px}.ctop .ctitle{flex:1;text-align:center;font:600 16px/22px var(--font)}
.cbody section{background:var(--surface)}
.otable th.r,.otable td.r{text-align:right}.otable td{vertical-align:middle}
.otable .tot td{border-top:1px solid var(--line-strong);font-weight:600}
.stop{color:var(--danger);display:block;margin:8px 0}.stop .ic{width:40px;height:40px}
.okmark{display:block;margin:8px 0}.okmark .ic{width:44px;height:44px}.okmark.up{color:var(--up)}.okmark.down{color:var(--down)}
.cons h3{font:600 12px/16px var(--font);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);margin:16px 0 4px}
.cons ul{margin:0;padding-left:20px}.cons li{margin:4px 0}
/* research (BF-D89): verdict chips (label + dot, never colour alone), highlights, library, timeline */
.rchip{display:inline-flex;align-items:center;gap:5px;min-height:22px;font:600 12px/16px var(--font);border-radius:999px;
padding:2px 9px;white-space:nowrap;vertical-align:1px;border:1px solid transparent;background:var(--surface-2);color:var(--ink-2)}
.rchip:before{content:"";width:6px;height:6px;border-radius:3px;background:currentColor;flex:none}
.rc-works{background:var(--up-soft);color:var(--up)}.rc-doesnt{background:var(--down-soft);color:var(--down)}
.rc-mixed,.rc-info{background:var(--surface-2);color:var(--ink-2)}.rc-closed{background:var(--surface-2);color:var(--ink-3)}
.rc-testing{background:none;color:var(--ink);border-color:var(--ink)}
.rc-proposed{background:none;color:var(--ink-2);border:1px dashed var(--ink-2)}
.rc-date{background:var(--warn-soft);color:var(--warn)}
.rnote{font:400 13px/18px var(--font);color:var(--ink-3)}
.rseg{margin-bottom:8px}
.rhl p{margin:0}.rhl .hline{font:600 17px/24px var(--font);margin:8px 0 0}
.rhl details.why>summary,.rsure>summary,.pres>summary{color:var(--ink-2)}
.rhl details.why p{margin:8px 0 0}.rhl .h3{margin:12px 0 0}
.rdue{font:400 13px/18px var(--font);color:var(--warn);margin:4px 0 0!important}
a.gl{color:inherit;text-decoration:underline dotted;text-decoration-color:var(--ink-3);text-underline-offset:3px}
.rmore{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:44px;margin:4px 0 -8px;
color:var(--ink);text-decoration:none;font:500 15px/20px var(--font);border-top:1px solid var(--line)}
.know li{padding:10px 0}
.rcard{display:flex;align-items:center;gap:12px;color:var(--ink);text-decoration:none}
.rcard .grow{flex:1;min-width:0;display:flex;flex-direction:column;align-items:flex-start;gap:2px}
.rcard b{font-weight:600}.rcard .ans{font:400 14px/20px var(--font);color:var(--ink-2);margin:2px 0 4px}
.rbad{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.rans{font:400 17px/24px var(--font);margin:8px 0 4px}
.bul{margin:0;padding-left:20px}.bul li{margin:6px 0}
.rnum td{padding:8px 0}.rnum td.r{text-align:right;padding-left:12px;white-space:normal;font-weight:600}
section.rmeans{background:var(--surface-2);border-left:3px solid var(--ink)}
section.rmeans p{margin:0}
.rsure{margin:12px 0}.rsure>summary b{font-weight:600;color:var(--ink)}.rsure p{margin:8px 0}
.tline p{margin:0 0 4px}.tline .tname{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.pres{margin:4px 0 0}.pres p{margin:6px 0 0}
.tlist{list-style:none;margin:0 0 0 6px;padding:0;border-left:2px solid var(--line)}
.tlist li{position:relative;padding:0 0 16px 18px}.tlist li:last-child{padding-bottom:0}
.tlist li:before{content:"";position:absolute;left:-7px;top:6px;width:12px;height:12px;border-radius:6px;background:var(--ink)}
.tlist.done li:before{background:var(--surface);box-shadow:inset 0 0 0 2px var(--ink-3)}
.tlist p{margin:0 0 4px}.tlist .h3{margin:2px 0}.tday{font:500 14px/20px var(--font);color:var(--ink-2)}
.you{color:var(--warn);font-weight:500}
.rfoot{font:400 13px/18px var(--font);color:var(--ink-3);margin:16px 0}
.gloss{margin:0}.gloss dt{font-weight:600;margin-top:16px;scroll-margin-top:64px}.gloss dt:first-child{margin-top:0}
.gloss dd{margin:2px 0 0;color:var(--ink-2)}
@media (max-width:859px){.rtwo>.rside{display:none}}
@media (min-width:860px){main:has(>.rtwo){display:block}
.rtwo{display:grid;grid-template-columns:minmax(0,400px) minmax(0,1fr);gap:0 24px;align-items:start}
.rtwo>.rside{position:sticky;top:64px;max-height:calc(100vh - 160px);overflow:auto}.rtwo>.rside .ans{display:none}}
/* report display (BF-D91): one headline per screen, action before detail, pictures for comparisons */
.scorecard{border-left:0;padding-top:18px}
.verdict{font:600 20px/26px var(--font);letter-spacing:-.01em;align-items:flex-start;margin:0 0 16px}
.verdict .ic{width:22px;height:22px;margin-top:2px}
.cmp{display:grid;gap:14px;margin:0}
.cmph{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.cmpl{font:400 13px/18px var(--font);color:var(--ink-2);min-width:0}
.cmpv{flex:none;white-space:nowrap;font:500 13px/20px var(--font);display:inline-flex;align-items:baseline;gap:8px}
.cmpv b{font:700 20px/24px var(--font);color:var(--ink);letter-spacing:-.01em}
.cmpt{position:relative;height:10px;border-radius:5px;background:var(--surface-2);margin-top:6px}
.cmpt i{position:absolute;top:0;bottom:0;border-radius:5px;background:var(--ink)}
.cmpt i.ix{background:var(--c-index)}
.cmpt u{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;background:var(--ink-3);border-radius:1px}
.cmpn{margin:8px 0 0}
.gapc{margin:18px 0 0;padding-top:14px;border-top:1px solid var(--line)}
.gaph{display:flex;align-items:baseline;justify-content:space-between;gap:12px;font:400 13px/18px var(--font);color:var(--ink-2)}
.gaph b{font:600 15px/20px var(--font);white-space:nowrap}
.gapsvg{display:block;width:100%;height:56px;margin:8px 0 4px;overflow:visible}
.gapl{fill:none;stroke:var(--ink);stroke-width:2;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke}
.gapz{stroke:var(--line-strong);stroke-width:1;stroke-dasharray:3 3;vector-effect:non-scaling-stroke}
.gapa{stroke:none}.gapa.au{fill:var(--up);fill-opacity:.16}.gapa.ad{fill:var(--down);fill-opacity:.16}
.gapx{display:flex;justify-content:space-between;gap:8px;font:400 12px/16px var(--font);color:var(--ink-3)}
.luck{display:flex;gap:8px;align-items:flex-start;margin:14px 0 0;padding:10px 12px;border-radius:var(--r-sm);
background:var(--surface-2);font:400 14px/20px var(--font);color:var(--ink-2)}
.luck .ic{width:18px;height:18px;margin-top:1px;color:var(--ink-3)}.luck b{color:var(--ink)}
.scorecard .about{margin-top:6px}
.todo>section{margin:12px 0}
.needs>h2{color:var(--warn)}
.nlist li{padding:0}
.nrow{display:flex;align-items:center;gap:10px;min-height:56px;padding:8px 0;color:var(--ink);text-decoration:none}
.nrow .grow{flex:1;min-width:0}.nrow b{display:block;font:600 15px/20px var(--font)}.nrow .sub{display:block}
.nrow .sd{flex:none;margin:0}
.needs.calm{padding:12px 16px}
.allok{display:flex;gap:10px;align-items:flex-start;margin:0;font:400 15px/22px var(--font)}
.allok .ic{flex:none;width:20px;height:20px;margin-top:1px;color:var(--up)}.allok .sub{display:inline}
.home .hv{font-size:30px;line-height:36px}
.home .hero{padding-top:12px}
.bigrow{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.bignum{font:700 32px/38px var(--font);letter-spacing:-.02em}
.bigsub{font:400 14px/20px var(--font);color:var(--ink-2);margin:2px 0 0}
.ylead{font:400 15px/22px var(--font);margin:16px 0 8px;padding-top:14px;border-top:1px solid var(--line)}
.split{display:flex;gap:2px;height:12px;margin:10px 0 8px;border-radius:6px;overflow:hidden}
.split i{display:block;min-width:3px}
.sg0{background:var(--ink)}.sg1{background:var(--c-index)}.sg2{background:var(--c1)}
.splitk{list-style:none;margin:0 0 4px;padding:0;font:400 14px/20px var(--font)}
.splitk li{display:flex;align-items:center;gap:8px;padding:3px 0}
.splitk i{flex:none;width:10px;height:10px;border-radius:3px}.splitk .grow{flex:1;min-width:0;color:var(--ink-2)}
.splitk b{font-weight:600;white-space:nowrap}
.costhero .bul{margin-top:8px}
.rtab th,.rtab td{padding:8px 0 8px 10px}.rtab th:first-child,.rtab td:first-child{padding-left:0}
.rtab td.r,.rtab th.r{white-space:nowrap}.rtab td{font:400 15px/20px var(--font)}
.dlist li{font:400 15px/22px var(--font)}
.needs .dlist li{display:flex;gap:10px;align-items:flex-start}.needs .dlist .sd{flex:none;margin:7px 0 0}
.attn li{display:flex;gap:10px;align-items:flex-start;padding:10px 0}.attn .sd{flex:none;margin:7px 0 0}
.attn .grow{flex:1;min-width:0}.attn b{display:block;font:600 15px/20px var(--font)}.attn .sub{display:block}
/* a message opened as a report */
.rep{margin:10px 0 0;padding:14px;border-radius:var(--r-md);background:var(--surface-2)}
.rep.txt{font:400 15px/22px var(--font);color:var(--ink)}
.rep.txt p{margin:0 0 8px}.rep.txt p:last-child{margin-bottom:0}.rep.txt .h3{margin:12px 0 2px;font-size:15px}
.rep.txt .bul{margin:0 0 8px}.rep.txt .bul li{margin:3px 0}
.reph{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px}
.rep .stats{margin:14px 0 4px}.rep .stats dd{white-space:normal}
.kv{list-style:none;margin:12px 0 0;padding:0}
.kv li,.repline{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:0;padding:9px 0;
border-top:1px solid var(--line);font:400 14px/20px var(--font)}
.kv li>span,.repline>span{flex:1;min-width:0;color:var(--ink-2)}
.kv li>b,.repline>b{flex:none;max-width:62%;font-weight:600;text-align:right}
.kv small{display:block;font:400 13px/18px var(--font);color:var(--ink-3)}
.rep .fold{border-top:1px solid var(--line);margin:0}.rep .fold>summary{margin:0;padding:9px 0;color:var(--ink-2);font:400 14px/20px var(--font)}
.rep .fold>.rtab{margin-bottom:8px}.rep .fold>.rtab td{font-size:14px}
.rep .note{margin:10px 0}.rep>.caption{margin:10px 0 0}
.rep .olist li{display:flex;align-items:baseline;gap:8px;padding:9px 0;font:400 15px/20px var(--font)}
.rep .olist .rr{margin-left:auto}
.orig{margin:6px 0 0}.orig>summary{color:var(--ink-3);font:400 13px/18px var(--font);margin:6px 0 0}
.msg .rep pre{background:var(--surface);max-height:20em}
/* research pages: what to do on the card, the grade as a meter, numbers that do not break */
.hdo{margin:10px 0 0!important;padding:10px 12px;border-radius:var(--r-sm);background:var(--surface-2);font:400 15px/22px var(--font)}
.hdo>span{display:block;font:600 12px/16px var(--font);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);margin-bottom:2px}
.rhl details.why{margin-top:4px}.rhl>.caption{margin-top:8px}
.rans{font:500 18px/26px var(--font);margin:10px 0 4px}
section.rmeans{border-left:0;border-radius:var(--r-md);background:var(--surface);box-shadow:inset 3px 0 0 var(--ink)}
section.rmeans p{font:400 16px/24px var(--font)}
.rsure{background:var(--surface);border-radius:var(--r-md);padding:4px 16px;margin:12px 0}
.rsure>summary,.rsure.nofold{display:flex;align-items:center;gap:10px;min-height:44px;margin:0;font:500 15px/20px var(--font);color:var(--ink-2)}
.rsure.nofold{padding:4px 16px}.rsure>summary::-webkit-details-marker{display:none}.rsure>summary{list-style:none}
.rsure>summary .chev{transition:transform .2s var(--ease)}.rsure[open]>summary .chev{transform:rotate(90deg)}
.rsure>p{margin:4px 0 12px;font:400 15px/22px var(--font)}.rep .stats small{color:var(--ink-3)}
.conf{display:inline-flex;gap:3px;flex:none}.conf span{width:14px;height:6px;border-radius:3px;background:var(--line)}
.conf.c1 span:nth-child(-n+1),.conf.c2 span:nth-child(-n+2),.conf.c3 span:nth-child(-n+3){background:var(--ink)}
.rnum td{font:400 15px/21px var(--font)}.rnum td.r.nw{white-space:nowrap}
.rnum tr:first-child td{border-top:0}
.rjump{margin:12px 0 4px}.rjump .chip{height:30px;font-size:13px;padding:0 10px}
section[id]{scroll-margin-top:64px}
.tline{padding:14px 0!important}.tline .tname{justify-content:space-between;margin-bottom:6px}
.tline .tname b{font:600 16px/22px var(--font)}.tread{margin-top:6px!important}
.pres>summary{margin:6px 0 0;font:400 13px/18px var(--font);color:var(--ink-3)}
/* News (BF-D92): six tabs still fit at 360 px; the feed of announcements on held shares */
.tab{min-width:0}.tab span{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.newshead .verdict{margin:0 0 4px}.newshead .bigsub{margin:0}
.mkt{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 16px;margin:14px 0 0;padding-top:12px;
border-top:1px solid var(--line);font:400 15px/22px var(--font)}
.mkt .mk1{white-space:nowrap}.mkt .mk1>span{font-weight:600;font-variant-numeric:tabular-nums}
.mkt .sub{flex-basis:100%}
.ncode{font:500 12px/16px var(--font);color:var(--ink-3);letter-spacing:.02em;white-space:nowrap}
.nmv{flex:none;font:600 15px/20px var(--font);white-space:nowrap}
.moves .nrow .pill{flex:none}.moves .nrow .sub{overflow-wrap:anywhere}
.nws .nwho{font:600 14px/20px var(--font);color:var(--ink);text-decoration:none}
.nws div{overflow-wrap:anywhere}.nws .pills{align-items:center;margin-top:6px}
.pdfl{display:inline-flex;align-items:center;gap:4px;min-height:32px;padding:0 10px;margin:-5px 0;border-radius:999px;
border:1px solid var(--line-strong);font:600 12px/16px var(--font);color:var(--ink);text-decoration:none}
.pdfl .ic{width:14px;height:14px}
.newsfeed .chips{margin-bottom:4px}.newsfeed .list li.day:first-child{margin-top:8px}
@media (prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
'use strict';
var main=document.getElementById('main');
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
function store(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v);}catch(x){return null;}}
function toast(t){var el=document.getElementById('toast');if(!el)return;el.textContent=t;el.classList.add('on');
 clearTimeout(el._t);el._t=setTimeout(function(){el.classList.remove('on');},2600);}
function buzz(){try{if(navigator.vibrate)navigator.vibrate(10);}catch(x){}}
function setTab(t){document.body.dataset.tab=t;var i=-1;$$('.tab').forEach(function(a,k){var on=a.dataset.tab===t;
 a.classList.toggle('on',on);if(on){i=k;a.setAttribute('aria-current','page');}else a.removeAttribute('aria-current');});}
function readSet(){var r=store('bw.read');try{return r?JSON.parse(r):[];}catch(x){return [];}}
function badge(){
 var latest=+(document.body.dataset.latestInbox||0),seen=+(store('bw.seen')||0),read=readSet();
 var ids=(document.body.dataset.inboxIds||'').split(',').filter(Boolean).map(Number);
 if(document.body.dataset.tab==='inbox'&&latest){store('bw.seen',latest);}
 $$('[data-inbox-id]').forEach(function(m){var id=+m.dataset.inboxId;m.classList.toggle('unread',id>seen&&read.indexOf(id)<0);});
 var nl=+(document.body.dataset.latestNews||0),nd=document.querySelector('.tab[data-tab=news] .dot');
 if(document.body.dataset.tab==='news'&&nl)store('bw.newsSeen',nl);
 if(nd){if(nl>+(store('bw.newsSeen')||0)){nd.hidden=false;nd.setAttribute('aria-label','New price-sensitive announcement');}else nd.hidden=true;}
 var d=document.querySelector('.tab[data-tab=inbox] .dot');if(!d)return;
 var n=ids.length?ids.filter(function(i){return i>seen&&read.indexOf(i)<0;}).length:Math.max(latest-seen,0);
 if(document.body.dataset.tab==='inbox')n=0;
 if(n>0){d.hidden=false;d.textContent='';d.setAttribute('aria-label',n+' unread');}else{d.hidden=true;}
 var w=+(document.body.dataset.waiting||0),o=document.querySelector('.tab[data-tab=orders]');if(o){var od=o.querySelector('.dot.n');
  if(w>0){if(!od){od=document.createElement('b');od.className='dot n';o.appendChild(od);}od.textContent=w;od.setAttribute('aria-label',w+(w===1?' order':' orders')+' waiting');}else if(od)od.remove();}
 try{if(navigator.setAppBadge){if(n>0)navigator.setAppBadge(n);else navigator.clearAppBadge();}}catch(x){}
}
function markRead(m){var id=+m.dataset.inboxId,r=readSet();if(r.indexOf(id)<0){r.push(id);store('bw.read',JSON.stringify(r.slice(-500)));}
 m.classList.remove('unread');}
function inbox(){$$('.msg[data-inbox-id]').forEach(function(m){if(m.dataset.sw)return;m.dataset.sw='1';var x0=null,dx=0;
 m.addEventListener('touchstart',function(ev){x0=ev.touches[0].clientX;dx=0;m.classList.add('swiping');},{passive:true});
 m.addEventListener('touchmove',function(ev){if(x0===null)return;dx=ev.touches[0].clientX-x0;if(dx<0)m.style.transform='translateX('+Math.max(dx,-90)+'px)';},{passive:true});
 m.addEventListener('touchend',function(){m.classList.remove('swiping');m.style.transform='';if(dx<-60){markRead(m);toast('Marked as read');}x0=null;});
 var d=m.querySelector('details');if(d)d.addEventListener('toggle',function(){if(d.open)markRead(m);});});}
function markAll(){var b=document.querySelector('[data-markall]');if(!b||b.dataset.b)return;b.dataset.b='1';b.hidden=false;
 b.addEventListener('click',function(){$$('.msg[data-inbox-id]').forEach(markRead);badge();toast('All marked as read');});}
function filters(){$$('[data-filter]').forEach(function(c){if(c.dataset.b)return;c.dataset.b='1';
 c.addEventListener('click',function(ev){ev.preventDefault();var k=c.dataset.filter;
  $$('[data-filter]').forEach(function(x){x.classList.toggle('on',x===c);});
  $$('[data-kind]').forEach(function(m){m.hidden=!(k==='all'||m.dataset.kind===k||(k==='alerts'&&m.dataset.kind==='page'));});
  $$('.day').forEach(function(h){var n=h.nextElementSibling,any=false;while(n&&!n.classList.contains('day')){if(!n.hidden)any=true;n=n.nextElementSibling;}h.hidden=!any;});});});}
function countup(){}
function rings(){}
function countdown(){$$('[data-deadline]').forEach(function(el){var off=el.dataset.now?Date.parse(el.dataset.now)-Date.now():0;
 function u(){var ms=Date.parse(el.dataset.deadline)-(Date.now()+off);
 if(!(ms>0)){el.textContent='deadline passed';return;}var h=Math.floor(ms/36e5),m=Math.floor(ms%36e5/6e4);
 el.textContent=(h?h+' h ':'')+m+' min left';}u();if(!el.dataset.t){el.dataset.t='1';setInterval(u,30000);}});}
function sorter(){var sel=document.querySelector('[data-sortsel]');if(!sel||sel.dataset.b)return;sel.dataset.b='1';
 function apply(k){var ul=document.getElementById('hlist');if(!ul)return;var li=$$('li[data-code]',ul);
  li.sort(function(a,b){if(k==='name')return a.dataset.code<b.dataset.code?-1:1;return (+b.dataset[k])-(+a.dataset[k]);});
  li.forEach(function(x){ul.appendChild(x);});}
 sel.addEventListener('change',function(){apply(sel.value);store('bw.sort',sel.value);buzz();});
 var k=store('bw.sort');if(k&&sel.querySelector('option[value="'+k+'"]')){sel.value=k;apply(k);}}
function views(){$$('[data-view]').forEach(function(a){if(a.dataset.b)return;a.dataset.b='1';a.addEventListener('click',function(ev){ev.preventDefault();
 $$('[data-view]').forEach(function(x){var on=x===a;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on?'true':'false');
  var p=document.getElementById(x.dataset.view);if(p)p.classList.toggle('on',on);});store('bw.hview',a.dataset.view);buzz();});});
 var v=store('bw.hview'),a=v&&document.querySelector('[data-view="'+v+'"]');if(a&&!a.classList.contains('on'))a.click();}
function strip(m){var f=m.querySelector('.foot');if(f)f.parentNode.removeChild(f);$$('.note',m).forEach(function(n){n.parentNode.removeChild(n);});}
function paneLoad(a){var pane=document.getElementById('pane');if(!pane)return false;if(window.innerWidth<860)return false;
 $$('#hlist li.hl').forEach(function(li){li.classList.toggle('hl',false);});var li=a.closest('li');if(li)li.classList.add('hl');
 pane.innerHTML='<div class="sheetsk"><div class="skel s"></div><div class="skel"></div></div>';
 fetch(a.href,{credentials:'same-origin'}).then(function(r){return r.text();}).then(function(t){
  var doc=new DOMParser().parseFromString(t,'text/html'),m=doc.getElementById('main');if(!m){location.href=a.href;return;}
  strip(m);pane.innerHTML=m.innerHTML;pane.scrollTop=0;charts(pane);tips(pane);bench(pane);}).catch(function(){location.href=a.href;});return true;}
function donut(){$$('.ds[data-code]').forEach(function(s){if(s.dataset.b)return;s.dataset.b='1';s.addEventListener('click',function(){
 var code=s.dataset.code,on=!s.classList.contains('hl');$$('.ds').forEach(function(x){x.classList.toggle('hl',on&&x===s);x.classList.toggle('dim',on&&x!==s);});
 $$('#hlist li[data-code]').forEach(function(li){li.classList.toggle('hl',on&&li.dataset.code===code);if(on&&li.dataset.code===code)li.scrollIntoView({block:'nearest',behavior:RM?'auto':'smooth'});});
 buzz();});});}
function dropSheet(){var s=document.querySelector('.sheet'),b=document.querySelector('.sheetbg');if(!s)return false;
 s.classList.remove('on');if(b)b.classList.remove('on');setTimeout(function(){s.remove();if(b)b.remove();},RM?0:280);return true;}
function closeSheet(){if(!document.querySelector('.sheet'))return;
 if(history.state&&history.state.bwSheet){history.back();}else{dropSheet();}}
function sheet(){$$('a[data-sheet]').forEach(function(a){if(a.dataset.b)return;a.dataset.b='1';a.addEventListener('click',function(ev){
 if(ev.metaKey||ev.ctrlKey)return;ev.preventDefault();buzz();if(paneLoad(a))return;dropSheet();
 if(!(history.state&&history.state.bwSheet))history.pushState({bwSheet:1},'',location.href);
 var b=document.createElement('div');b.className='sheetbg';var s=document.createElement('div');s.className='sheet';
 s.setAttribute('role','dialog');s.setAttribute('aria-modal','true');s.setAttribute('aria-label','Detail');
 var top='<div class="sheethead"><div class="grab"></div><div class="shrow"><span class="sp"></span>'+
  '<a class="btn ter sm" href="'+a.getAttribute('href')+'">Open page</a><button class="iconbtn sheetx" type="button" aria-label="Close">'+XI+'</button></div></div>';
 s.innerHTML=top+'<div class="sheetsk"><div class="skel s"></div><div class="skel"></div><div class="skel"></div></div>';
 document.body.appendChild(b);document.body.appendChild(s);b.addEventListener('click',closeSheet);
 function bindX(){s.querySelector('.sheetx').addEventListener('click',closeSheet);}bindX();
 var y0=null,dy=0;s.addEventListener('touchstart',function(e){y0=s.scrollTop===0?e.touches[0].clientY:null;dy=0;},{passive:true});
 s.addEventListener('touchmove',function(e){if(y0===null)return;dy=e.touches[0].clientY-y0;if(dy>0){s.classList.add('dragging');s.style.transform='translateY('+dy+'px)';}},{passive:true});
 s.addEventListener('touchend',function(){s.classList.remove('dragging');s.style.transform='';if(y0!==null){if(dy>90)closeSheet();else if(dy<-50){s.classList.add('full');buzz();}}y0=null;});
 requestAnimationFrame(function(){b.classList.add('on');s.classList.add('on');});
 fetch(a.href,{credentials:'same-origin'}).then(function(r){return r.text();}).then(function(t){
  var doc=new DOMParser().parseFromString(t,'text/html'),m=doc.getElementById('main');if(!m){location.href=a.href;return;}
  if(!s.parentNode)return;strip(m);s.innerHTML=top+m.innerHTML;bindX();charts(s);rings();tips(s);bench(s);
 }).catch(function(){location.href=a.href;});});});}
// smooth path (monotone cubic) for the chart line and area
function smooth(P){if(P.length<3)return P.map(function(p,i){return (i?'L':'M')+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
 var d='M'+P[0][0].toFixed(1)+','+P[0][1].toFixed(1);for(var i=0;i<P.length-1;i++){var p0=P[i>0?i-1:i],p1=P[i],p2=P[i+1],p3=P[i+2<P.length?i+2:i+1];
  var c1x=p1[0]+(p2[0]-p0[0])/6,c1y=p1[1]+(p2[1]-p0[1])/6,c2x=p2[0]-(p3[0]-p1[0])/6,c2y=p2[1]-(p3[1]-p1[1])/6;
  d+=' C'+c1x.toFixed(1)+','+c1y.toFixed(1)+' '+c2x.toFixed(1)+','+c2y.toFixed(1)+' '+p2[0].toFixed(1)+','+p2[1].toFixed(1);}return d;}
function fd(t){return new Date(t*864e5).toLocaleDateString('en-AU',{day:'2-digit',month:'short',year:'2-digit',timeZone:'UTC'});}
function fdm(t){return new Date(t*864e5).toLocaleDateString('en-AU',{day:'numeric',month:'short',timeZone:'UTC'});}
function sp(v,dp){return (v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(dp)+'%';}
function money(v){return '$'+v.toLocaleString('en-AU',{minimumFractionDigits:2,maximumFractionDigits:2});}
// BF-D73: one chart dialect: % from the range start, labels inside the right edge, a read-out row
function charts(root){
 $$('[data-chart]',root).forEach(function(box){
  if(box.dataset.b)return;box.dataset.b='1';
  var el=document.getElementById(box.dataset.chart)||(root&&root.querySelector('#'+box.dataset.chart));if(!el)return;
  var d;try{d=JSON.parse(el.textContent);}catch(x){return;}
  var svg=box.querySelector('svg'),ranges=$$('[data-range]',box),ro=box.querySelector('.readout');
  var hv=box.closest('.home')?document.querySelector('.hero .hv'):null,hv0=hv?hv.textContent:'';
  var H=200,pl=4,pr=44,pt=12,pb=22,cur=null,idle='';
  function W(){return Math.max(300,Math.round(svg.getBoundingClientRect().width||340));}
  function view(days){var pts=d.book,last=pts[pts.length-1][0],from=days?last-days:pts[0][0];
   var b=pts.filter(function(p){return p[0]>=from;});if(b.length<2)b=pts.slice(-2);
   var b0=b[0][1],idx=(d.index||[]).filter(function(p){return p[0]>=b[0][0];}),i0=idx.length?idx[0][1]:1;
   return {bk:b.map(function(p){return [p[0],(p[1]/b0-1)*100,p[1]];}),ix:idx.map(function(p){return [p[0],(p[1]/i0-1)*100];})};}
  function ticks(lo,hi){var span=Math.max(hi-lo,.5),st=[.5,1,2,2.5,5,10,20,25,50,100,200].filter(function(s){return span/s<=3.5;})[0]||500,o=[];
   for(var v=Math.ceil(lo/st)*st;v<=hi+1e-9&&o.length<4;v+=st)o.push(Math.round(v*1e6)/1e6);return o;}
  function render(v){var w=W();svg.setAttribute('viewBox','0 0 '+w+' '+H);
   var all=v.bk.map(function(p){return p[1];}).concat(v.ix.map(function(p){return p[1];}),[0]);
   var lo=Math.min.apply(0,all),hi=Math.max.apply(0,all),pad=Math.max((hi-lo)*.12,.4);lo-=pad;hi+=pad;
   var x0=v.bk[0][0],x1=v.bk[v.bk.length-1][0],spn=Math.max(x1-x0,1);
   function X(t){return pl+(t-x0)/spn*(w-pl-pr);}function Y(y){return pt+(hi-y)/(hi-lo)*(H-pt-pb);}
   var tk=ticks(lo,hi),dp=tk.some(function(t){return Math.abs(t-Math.round(t))>0;})?1:0;
   var g='<defs><linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="gA0"/><stop offset="1" class="gA1"/></linearGradient></defs>';
   tk.forEach(function(t){if(Math.abs(t)<1e-9)return;g+='<line x1="'+pl+'" x2="'+(w-2)+'" y1="'+Y(t).toFixed(1)+'" y2="'+Y(t).toFixed(1)+'" class="grid"/><text x="'+(w-2)+'" y="'+(Y(t)+4).toFixed(1)+'" class="ax" text-anchor="end">'+sp(t,dp)+'</text>';});
   g+='<line x1="'+pl+'" x2="'+(w-pr)+'" y1="'+Y(0).toFixed(1)+'" y2="'+Y(0).toFixed(1)+'" class="base"/>';
   var P=v.bk.map(function(p){return [X(p[0]),Y(p[1])];}),line=smooth(P);
   var area=line+' L'+P[P.length-1][0].toFixed(1)+','+(H-pb)+' L'+P[0][0].toFixed(1)+','+(H-pb)+' Z';
   var tr='';(d.trades||[]).forEach(function(t){if(t[0]<x0||t[0]>x1)return;var near=v.bk[0];v.bk.forEach(function(p){if(Math.abs(p[0]-t[0])<Math.abs(near[0]-t[0]))near=p;});
    tr+='<circle cx="'+X(near[0]).toFixed(1)+'" cy="'+Y(near[1]).toFixed(1)+'" r="3.5" class="'+(t[1]==='b'?'buyd':'selld')+'"><title>'+(t[1]==='b'?'Buy':'Sell')+' '+fdm(t[0])+'</title></circle>';});
   var xt='';[[x0,'start'],[x0+spn/3,'middle'],[x0+2*spn/3,'middle'],[x1,'end']].forEach(function(q){xt+='<text x="'+X(q[0]).toFixed(1)+'" y="'+(H-6)+'" class="ax" text-anchor="'+q[1]+'">'+fdm(Math.round(q[0]))+'</text>';});
   var e=v.bk[v.bk.length-1];
   svg.innerHTML=g+'<path d="'+area+'" class="area"/>'+(v.ix.length?'<path d="'+smooth(v.ix.map(function(p){return [X(p[0]),Y(p[1])];}))+'" class="s2"/>':'')+
    '<path d="'+line+'" class="s1"/>'+tr+'<circle cx="'+X(e[0]).toFixed(1)+'" cy="'+Y(e[1]).toFixed(1)+'" r="3.5" class="d1"/>'+xt+
    '<g id="xh" style="display:none"><line class="xh" y1="'+pt+'" y2="'+(H-pb)+'"/><circle class="xd" r="5"/><circle class="xd xi" r="4"/></g>';
   box.classList.toggle('tdown',e[1]<0);box.classList.toggle('tup',e[1]>=0);
   var ie=v.ix.length?v.ix[v.ix.length-1][1]:null;
   idle='<span>'+fdm(x0)+' to '+fdm(x1)+'</span><span>Book <b>'+sp(e[1],1)+'</b>'+(ie!==null?' · '+d.label+' <b>'+sp(ie,1)+'</b>':'')+'</span>';
   if(ro)ro.innerHTML=idle;cur={v:v,X:X,Y:Y,x0:x0,x1:x1,w:w};}
  function at(ev){if(!cur)return;var r=svg.getBoundingClientRect(),cx=((ev.touches?ev.touches[0].clientX:ev.clientX)-r.left)/r.width*cur.w;
   var v=cur.v,t=cur.x0+(cx-pl)/(cur.w-pl-pr)*Math.max(cur.x1-cur.x0,1),best=v.bk[0];
   v.bk.forEach(function(p){if(Math.abs(p[0]-t)<Math.abs(best[0]-t))best=p;});var ib=null;v.ix.forEach(function(p){if(p[0]<=best[0])ib=p;});
   var g=svg.querySelector('#xh');g.style.display='';var xx=cur.X(best[0]);
   var ln=g.querySelector('line');ln.setAttribute('x1',xx);ln.setAttribute('x2',xx);var cs=g.querySelectorAll('circle');
   cs[0].setAttribute('cx',xx);cs[0].setAttribute('cy',cur.Y(best[1]));
   if(ib){cs[1].style.display='';cs[1].setAttribute('cx',xx);cs[1].setAttribute('cy',cur.Y(ib[1]));}else cs[1].style.display='none';
   if(ro){var gap=ib?best[1]-ib[1]:null;
    ro.innerHTML='<span>'+fd(best[0])+'</span><span><b>'+money(best[2])+'</b> '+(best[1]>=0?'▲ ':'▼ ')+sp(best[1],1)+
     (ib?' · '+d.label+' '+sp(ib[1],1)+' · gap '+(gap>=0?'+':'−')+Math.abs(gap).toFixed(1)+' pts':'')+'</span>';}
   if(hv)hv.textContent=money(best[2]);
   if(ev.cancelable&&ev.touches)ev.preventDefault();}
  function off(){var g=svg.querySelector('#xh');if(g)g.style.display='none';if(ro)ro.innerHTML=idle;if(hv)hv.textContent=hv0;}
  svg.addEventListener('mousemove',at);svg.addEventListener('touchstart',at,{passive:false});svg.addEventListener('touchmove',at,{passive:false});
  svg.addEventListener('mouseleave',off);svg.addEventListener('touchend',function(){setTimeout(off,1200);});
  var days=0;ranges.forEach(function(r){r.addEventListener('click',function(ev){ev.preventDefault();buzz();
   ranges.forEach(function(x){x.classList.toggle('on',x===r);x.setAttribute('aria-pressed',x===r?'true':'false');});days=+r.dataset.range;render(view(days));});});
  render(view(0));var rt=null;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){if(box.isConnected)render(view(days));},150);});});}
function resultToast(){}
function setup(){var box=document.getElementById('setup-ring');if(!box)return;
 var items=document.querySelectorAll('.sitem');
 function recount(){var n=0;items.forEach(function(li){var cb=li.querySelectorAll('input[data-setup-id]');
  var done=li.classList.contains('auto')?li.classList.contains('done'):(cb.length>0&&Array.prototype.every.call(cb,function(c){return c.checked;}));
  if(!li.classList.contains('auto'))li.classList.toggle('done',done);if(done)n++;});
  var t=+box.dataset.total,c=document.getElementById('setup-count');if(c)c.textContent=n+' of '+t+' done';
  var mb=box.querySelector('.meter b');if(mb)mb.style.width=(n/t*100).toFixed(0)+'%';var rv=box.querySelector('.rv'),b=box.querySelector('figcaption b');if(b)b.textContent=n+'/'+t;
  if(rv){var full=rv.getAttribute('stroke-dasharray').split(' ')[1];rv.setAttribute('stroke-dasharray',(full*n/t).toFixed(1)+' '+full);}}
 document.querySelectorAll('input[data-setup-id]').forEach(function(c){var k='bw.setup.'+c.dataset.setupId;
  c.checked=store(k)==='1';if(c.dataset.b)return;c.dataset.b='1';
  c.addEventListener('change',function(){store(k,c.checked?'1':'0');recount();if(c.checked){buzz();toast('Saved on this phone');}});});
 recount();}
function reminders(){document.querySelectorAll('input[data-remind]').forEach(function(i){var k='bw.remind.'+i.dataset.remind,
 out=document.querySelector('[data-remind-out="'+i.dataset.remind+'"]');function show(){if(!out)return;if(!i.value){out.textContent='';return;}
 var d=Math.ceil((Date.parse(i.value)-Date.now())/864e5);out.textContent=d<0?'Date passed '+(-d)+' days ago':d+' days to go'+(d<=14?' - soon':'');}
 i.value=store(k)||'';show();if(i.dataset.b)return;i.dataset.b='1';i.addEventListener('change',function(){store(k,i.value);show();toast('Saved on this phone');});});}
// BF-D66: tap read-outs on the share charts, and the benchmark toggle
function tips(root){$$('[data-tips]',root).forEach(function(box){if(box.dataset.tb)return;box.dataset.tb='1';
 var tip=box.querySelector('.ctip'),last=null;function show(z,ev){if(!tip)return;if(last)last.classList.remove('on');last=z;z.classList.add('on');
  tip.textContent=z.getAttribute('data-tip');tip.classList.add('on');var r=box.getBoundingClientRect(),zr=z.getBoundingClientRect(),cx=zr.left+zr.width/2-r.left;
  tip.style.left=(cx>r.width/2?Math.max(4,cx-tip.offsetWidth-12):Math.min(r.width-tip.offsetWidth-4,cx+12))+'px';}
 function pick(ev){var p=ev.touches?ev.touches[0]:ev,el=document.elementFromPoint(p.clientX,p.clientY);var z=el&&el.closest?el.closest('.hit'):null;if(z&&box.contains(z))show(z,ev);}
 box.addEventListener('click',pick);box.addEventListener('mousemove',pick);box.addEventListener('touchmove',pick,{passive:true});
 box.addEventListener('mouseleave',function(){if(tip)tip.classList.remove('on');if(last)last.classList.remove('on');});});}
function bench(root){$$('[data-benchseg]',root).forEach(function(seg){if(seg.dataset.b)return;seg.dataset.b='1';
 var sec=seg.parentNode;$$('[data-bench]',seg).forEach(function(b){b.addEventListener('click',function(){
  $$('[data-bench]',seg).forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});
  $$('[data-bench-pane]',sec).forEach(function(p){p.hidden=p.dataset.benchPane!==b.dataset.bench;});buzz();});});});}
// BF-D68: the second interactive pass (presentation only; preferences in localStorage)
function tabList(){return $$('.tabs .tab').map(function(a){return a.getAttribute('href');});}
function swipeTabs(){if(document.body.dataset.sw)return;document.body.dataset.sw='1';var sx=null,sy=0,t0=0;
 main.addEventListener('touchstart',function(ev){var t=ev.target;if(ev.touches.length!==1||document.querySelector('.sheet,#srch.on,.tourbg')||
  (t.closest&&t.closest('.chart,svg,[data-tips],.tmap,input,textarea,select,.seg,.chips,.msg,.cal,.tiles,table,.tscroll,[data-compare]'))){sx=null;return;}
  sx=ev.touches[0].clientX;sy=ev.touches[0].clientY;t0=Date.now();},{passive:true});
 main.addEventListener('touchend',function(ev){if(sx===null)return;var dx=ev.changedTouches[0].clientX-sx,dy=ev.changedTouches[0].clientY-sy;sx=null;
  if(Math.abs(dx)<70||Math.abs(dx)<1.6*Math.abs(dy)||Date.now()-t0>700)return;var tabs=tabList(),cur=document.body.dataset.tab,
  names=$$('.tabs .tab').map(function(a){return a.dataset.tab;}),i=names.indexOf(cur);if(i<0)return;var j=dx<0?i+1:i-1;if(j<0||j>=tabs.length)return;
  buzz();setTab(names[j]);go(tabs[j],true);},{passive:true});}
function tmap(){$$('[data-tmseg]').forEach(function(seg){if(seg.dataset.b)return;seg.dataset.b='1';var box=seg.parentNode.querySelector('[data-tmap]');
 $$('[data-tm]',seg).forEach(function(b){b.addEventListener('click',function(){var m=b.dataset.tm;
  $$('[data-tm]',seg).forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});
  $$('.tm',box).forEach(function(a){var i=a.querySelector('.tmi'),l=a.querySelector('.tml');i.className='tmi '+(m==='t'?a.dataset.ct:a.dataset.cs);
   if(l)l.textContent=m==='t'?a.dataset.lt:a.dataset.ls;});buzz();});});});}
function whatif(){$$('[data-whatif]').forEach(function(w){if(w.dataset.b)return;w.dataset.b='1';var d;
 try{d=JSON.parse(w.querySelector('[data-wi-data]').textContent);}catch(x){return;}
 var r=w.querySelector('input[type=range]'),lo=+w.dataset.lo,hi=+w.dataset.hi,bar=w.querySelector('[data-wi-bar]');
 function fmt(n){return '$'+Math.round(n).toLocaleString('en-AU');}
 function upd(){var m=+r.value/100,v=d.cash;d.h.forEach(function(h){v+=h[1]*(1+(h[2]===null?1:h[2])*m);});
  w.querySelector('[data-wi-m]').textContent=(m>0?'+':m<0?'−':'')+Math.abs(+r.value)+'%';
  w.querySelector('[data-wi-v]').textContent=fmt(v);var ch=v-d.now;
  w.querySelector('[data-wi-d]').textContent=(ch>=0?'▲ +':'▼ −')+fmt(Math.abs(ch));
  bar.style.width=Math.max(0,Math.min(100,(v-lo)/(hi-lo)*100)).toFixed(1)+'%';
  var L=d.lines,s;if(v>=L[0][0])s='Above the $'+(L[0][0]/1000).toFixed(0)+'k check: the loss rule stays normal.';
  else if(v>=L[1][0])s='Below the $'+(L[0][0]/1000).toFixed(0)+'k check: the trader would ask you to review.';
  else if(v>=L[2][0])s='Below $'+(L[1][0]/1000).toFixed(0)+'k: new buys would pause (loss rule L11).';
  else s='Below $'+(L[2][0]/1000).toFixed(0)+'k: the loss rule would stop the line.';
  w.querySelector('[data-wi-s]').textContent=s;bar.parentNode.classList.toggle('bad',v<L[1][0]);bar.parentNode.classList.toggle('mid',v<L[0][0]&&v>=L[1][0]);
  var t=w.querySelector('[data-wi-t]');if(d.trend){var lv=d.trend[0]*(1+m),above=lv>=d.trend[1];
   t.textContent='Trend shield (L15): if band C moved the same, its index would be '+(above?'above':'below')+' its 10-month average'+
    (above?' (shares stay).':' (at the next month-end it would switch to the A200 fund).');}else t.textContent='Trend shield (L15): not decided yet.';}
 r.addEventListener('input',upd);r.addEventListener('change',function(){buzz();});upd();});}
function cal(){$$('[data-cal]').forEach(function(c){if(c.dataset.b)return;c.dataset.b='1';var list=c.parentNode.querySelector('[data-cevs]'),
 hint=c.parentNode.querySelector('[data-cal-hint]');
 function pick(day){$$('.cday',c).forEach(function(b){b.classList.toggle('sel',b.dataset.cday===day);});
  if(list)$$('[data-cev]',list).forEach(function(li){li.hidden=!!day&&li.dataset.cev!==day;});
  if(hint){var n=list?$$('[data-cev]:not([hidden])',list).length:0;hint.textContent=day?(n?n+' on '+new Date(day+'T00:00:00Z').toLocaleDateString('en-AU',{weekday:'long',day:'numeric',month:'long',timeZone:'UTC'})+' · tap again for the whole month':'Nothing on this day · tap again for the whole month'):'Tap a day for its details.';}}
 var cur=null;$$('.cday',c).forEach(function(b){b.addEventListener('click',function(){cur=cur===b.dataset.cday?null:b.dataset.cday;pick(cur);buzz();});});});}
function cmp(){$$('[data-compare]').forEach(function(box){if(box.dataset.b)return;box.dataset.b='1';var d;
 try{d=JSON.parse(box.parentNode.querySelector('[data-compare-data]').textContent);}catch(x){return;}
 var svg=box.querySelector('svg'),out=box.querySelector('.cmpout'),leg=box.parentNode.querySelector('[data-compare-legend]'),
  chips=$$('[data-cmp]',box.parentNode),W=340,H=200,pl=34,pr=8,pt=10,pb=22,cur=null;
 function sel(){return chips.filter(function(c){return c.classList.contains('on');}).map(function(c){return c.dataset.cmp;});}
 function draw(){var ks=sel(),ser=[];ks.forEach(function(k,i){var s=k==='__idx'?d.idx:d.s[k];if(s&&s.length>1)ser.push({k:k==='__idx'?d.label:k,p:s,c:'c'+(k==='__idx'?3:i%3)});});
  if(!ser.length){svg.innerHTML='';out.textContent='Pick a line.';return;}
  var t0=Math.max.apply(0,ser.map(function(s){return s.p[0][0];})),t1=Math.min.apply(0,ser.map(function(s){return s.p[s.p.length-1][0];}));
  ser.forEach(function(s){var b=null;s.p.forEach(function(p){if(b===null&&p[0]>=t0)b=p[1];});s.r=s.p.filter(function(p){return p[0]>=t0&&p[0]<=t1;}).map(function(p){return [p[0],p[1]/b*100];});});
  var all=[];ser.forEach(function(s){s.r.forEach(function(p){all.push(p[1]);});});var lo=Math.min.apply(0,all),hi=Math.max.apply(0,all),pad=Math.max((hi-lo)*.1,1);lo-=pad;hi+=pad;
  function X(t){return pl+(t-t0)/Math.max(t1-t0,1)*(W-pl-pr);}function Y(v){return pt+(hi-v)/(hi-lo)*(H-pt-pb);}
  var g='<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(100).toFixed(1)+'" y2="'+Y(100).toFixed(1)+'" class="base"/>';
  [lo+(hi-lo)*.15,hi-(hi-lo)*.15].forEach(function(v){g+='<text x="'+(pl-4)+'" y="'+(Y(v)+3).toFixed(1)+'" class="ax" text-anchor="end">'+v.toFixed(0)+'</text>';});
  ser.forEach(function(s){g+='<path d="'+smooth(s.r.map(function(p){return [X(p[0]),Y(p[1])];}))+'" class="s1 '+s.c+'" style="stroke:var(--'+s.c+')"/>';});
  g+='<text x="'+pl+'" y="'+(H-6)+'" class="ax">'+fd(t0)+'</text><text x="'+(W-pr)+'" y="'+(H-6)+'" class="ax" text-anchor="end">'+fd(t1)+'</text>'+
   '<g id="cx" style="display:none"><line class="xh" y1="'+pt+'" y2="'+(H-pb)+'"/></g>';svg.innerHTML=g;cur={ser:ser,X:X,Y:Y,t0:t0,t1:t1};
  if(leg){leg.textContent='';ser.forEach(function(s){var w=document.createElement('span'),k=document.createElement('span');k.className='key k-'+s.c;w.appendChild(k);w.appendChild(document.createTextNode(s.k));leg.appendChild(w);});
   var z=document.createElement('span');z.textContent='100 = '+fd(t0);leg.appendChild(z);}  // security review L5: names as text
  out.textContent='Drag across the chart to read each line.';}
 function at(ev){if(!cur)return;var p=ev.touches?ev.touches[0]:ev,r=svg.getBoundingClientRect(),cx=(p.clientX-r.left)/r.width*W,
  t=cur.t0+(cx-pl)/(W-pl-pr)*(cur.t1-cur.t0);var g=svg.querySelector('#cx');if(!g)return;g.style.display='';var ln=g.querySelector('line');
  var lines=[fd(Math.round(t))];cur.ser.forEach(function(s){var b=s.r[0];s.r.forEach(function(q){if(Math.abs(q[0]-t)<Math.abs(b[0]-t))b=q;});
   lines.push(s.k+': '+b[1].toFixed(1)+' ('+(b[1]>=100?'▲ +':'▼ −')+Math.abs(b[1]-100).toFixed(1)+'%)');});
  ln.setAttribute('x1',cur.X(t));ln.setAttribute('x2',cur.X(t));out.textContent=lines.join('\n');}
 svg.addEventListener('mousemove',at);svg.addEventListener('touchmove',at,{passive:true});svg.addEventListener('click',at);
 chips.forEach(function(c){c.addEventListener('click',function(){var on=!c.classList.contains('on');
  if(on&&c.dataset.cmp!=='__idx'&&sel().filter(function(k){return k!=='__idx';}).length>=3){toast('Up to 3 holdings');return;}
  c.classList.toggle('on',on);c.setAttribute('aria-pressed',on?'true':'false');buzz();draw();});});draw();});}
function replay(){$$('[data-replay]').forEach(function(r){if(r.dataset.b)return;r.dataset.b='1';r.classList.add('js');
 var panes=$$('.rpane',r),dots=$$('.rdot',r),k=0,timer=null,play=r.querySelector('[data-rplay]');
 function show(n){k=Math.max(0,Math.min(panes.length-1,n));panes.forEach(function(p,i){p.classList.toggle('on',i===k);});
  dots.forEach(function(d,i){d.classList.toggle('on',i<=k);d.setAttribute('aria-current',i===k?'step':'false');});
  r.querySelector('[data-rprev]').disabled=k===0;r.querySelector('[data-rnext]').textContent=k===panes.length-1?'Start again':'Next';var st=r.querySelector('[data-rstep]');if(st)st.textContent='Step '+(k+1)+' of '+panes.length;}
 function stop(){if(timer){clearInterval(timer);timer=null;play.textContent='Play';}}
 r.querySelector('[data-rprev]').addEventListener('click',function(){stop();show(k-1);buzz();});
 r.querySelector('[data-rnext]').addEventListener('click',function(){stop();show(k===panes.length-1?0:k+1);buzz();});
 dots.forEach(function(d){d.addEventListener('click',function(){stop();show(+d.dataset.rgo);});});
 play.addEventListener('click',function(){if(timer){stop();return;}if(k===panes.length-1)show(0);play.textContent='Pause';
  timer=setInterval(function(){if(k>=panes.length-1){stop();return;}show(k+1);},RM?4000:2600);});show(0);});}
function homeCards(){var cards=$$('section[data-card]');if(!cards.length||document.body.dataset.tab!=='home')return;
 var st={};try{st=JSON.parse(store('bw.home')||'{}');}catch(x){st={};}var order=st.order||[],hid=st.hidden||[];
 var parent=cards[0].parentNode,anchor=cards[cards.length-1].nextSibling;
 if(order.length){var by={};cards.forEach(function(c){by[c.dataset.card]=c;});
  order.forEach(function(n){if(by[n]){parent.insertBefore(by[n],anchor);delete by[n];}});
  Object.keys(by).forEach(function(n){parent.insertBefore(by[n],anchor);});}
 $$('section[data-card]').forEach(function(c){c.classList.toggle('hiddencard',hid.indexOf(c.dataset.card)>=0);
  if(c.dataset.eb)return;c.dataset.eb='1';
  var bar=document.createElement('div');bar.className='cardbar';
  bar.innerHTML='<button type="button" class="chip" data-mv="-1" aria-label="Move up">↑</button><button type="button" class="chip" data-mv="1" aria-label="Move down">↓</button><button type="button" class="chip" data-hide>'+(c.classList.contains('hiddencard')?'Show':'Hide')+'</button>';
  c.insertBefore(bar,c.firstChild);
  bar.addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b)return;var all=$$('section[data-card]'),i=all.indexOf(c);
   if(b.dataset.mv){var j=i+(+b.dataset.mv);if(j<0||j>=all.length)return;if(+b.dataset.mv<0)parent.insertBefore(c,all[j]);else parent.insertBefore(c,all[j].nextSibling);
   }
   else{c.classList.toggle('hiddencard');b.textContent=c.classList.contains('hiddencard')?'Show':'Hide';}buzz();saveCards();});
  var h=c.querySelector('h2')||c,lt=null;function start(){lt=setTimeout(function(){document.body.classList.add('editing');buzz();toast('Move or hide cards, then Done');},550);}
  function cancel(){clearTimeout(lt);}
  h.addEventListener('touchstart',start,{passive:true});h.addEventListener('touchend',cancel);h.addEventListener('touchmove',cancel,{passive:true});
  h.addEventListener('mousedown',start);h.addEventListener('mouseup',cancel);h.addEventListener('mouseleave',cancel);
  h.addEventListener('contextmenu',function(ev){ev.preventDefault();});});
 var done=document.getElementById('editdone');if(!done){done=document.createElement('button');done.id='editdone';done.type='button';done.className='btn';
  done.textContent='Done';document.body.appendChild(done);done.addEventListener('click',function(){document.body.classList.remove('editing');saveCards();toast('Saved on this phone');});}}
function saveCards(){var all=$$('section[data-card]');store('bw.home',JSON.stringify({order:all.map(function(c){return c.dataset.card;}),
 hidden:all.filter(function(c){return c.classList.contains('hiddencard');}).map(function(c){return c.dataset.card;})}));}
function prefs(){var dn=store('bw.density')||'comfortable';document.body.classList.toggle('compact',dn==='compact');
 $$('[data-density]').forEach(function(b){b.classList.toggle('on',b.dataset.density===dn);b.setAttribute('aria-pressed',b.dataset.density===dn?'true':'false');
  if(b.dataset.b)return;b.dataset.b='1';b.addEventListener('click',function(){store('bw.density',b.dataset.density);prefs();buzz();});});
 var tr=document.querySelector('[data-tour-replay]');if(tr&&!tr.dataset.b){tr.dataset.b='1';tr.addEventListener('click',function(){store('bw.tour','0');tour(true);});}
 var hr=document.querySelector('[data-home-reset]');if(hr&&!hr.dataset.b){hr.dataset.b='1';hr.addEventListener('click',function(){store('bw.home','{}');toast('Home cards reset');});}}
var SIDX=null,XI='<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>';
function search(){var b=document.getElementById('searchbtn');if(!b||b.dataset.b)return;b.dataset.b='1';
 var o=document.createElement('div');o.id='srch';o.setAttribute('role','dialog');o.setAttribute('aria-modal','true');o.setAttribute('aria-label','Search');
 o.innerHTML='<div class="sbar"><input id="sq" type="search" placeholder="Shares, orders, messages, tax" aria-label="Search shares, orders, messages and tax rows" autocomplete="off"><button type="button" class="btn sec" id="sx">Close</button></div><div id="sres"><div class="skel s"></div><div class="skel s"></div></div>';
 document.body.appendChild(o);var q=o.querySelector('#sq'),res=o.querySelector('#sres');
 function close(){o.classList.remove('on');}o.querySelector('#sx').addEventListener('click',close);
 document.addEventListener('keydown',function(ev){if(ev.key==='Escape')close();if(ev.key==='/'&&!o.classList.contains('on')&&!/INPUT|TEXTAREA/.test((ev.target||{}).tagName||'')){ev.preventDefault();open();}});
 function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function hl(s,t){s=String(s);if(!t)return esc(s);var i=s.toLowerCase().indexOf(t.toLowerCase());return i<0?esc(s):esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+t.length))+'</mark>'+esc(s.slice(i+t.length));}
 function render(){if(!SIDX)return;var t=q.value.trim().toLowerCase(),groups={};
  SIDX.forEach(function(r){if(t&&(r.t+' '+r.s+' '+r.g).toLowerCase().indexOf(t)<0)return;(groups[r.g]=groups[r.g]||[]).push(r);});
  var h='';['Shares','Orders','Inbox','Tax'].forEach(function(g){var rs=groups[g];if(!rs)return;h+='<h3>'+g+' ('+rs.length+')</h3>'+rs.slice(0,t?20:5).map(function(r){
   return '<a href="'+esc(r.u)+'" data-nav>'+hl(r.t,t)+'<span class="sub">'+hl(r.s,t)+'</span></a>';}).join('');});
  res.innerHTML=h||'<p class="muted">Nothing found.</p>';}
 function open(){o.classList.add('on');q.value='';setTimeout(function(){q.focus();},50);buzz();
  if(SIDX)render();else fetch('/search.json',{credentials:'same-origin'}).then(function(r){return r.json();}).then(function(d){SIDX=d;render();}).catch(function(){res.innerHTML='<p class="muted">Search is not available.</p>';});}
 q.addEventListener('input',render);res.addEventListener('click',function(ev){if(ev.target.closest('a'))close();});b.addEventListener('click',open);}
var TOUR=[['home','Home','Your account value, today\'s change and how the book compares with the index. Batches waiting for your approval show up here first.'],
 ['holdings','Holdings','What you hold: the heatmap, each share\'s detail, the Shares list with the historical range of similar picks, and Tax.'],
 ['news','News','Announcements, big moves and halts on the shares you hold. Information only, not a trading signal.'],
 ['orders','Orders','Each month-end decision and its orders, the calendar of decision days and cut-offs, and a replay of how a month was decided.'],
 ['inbox','Inbox','Every message from the trader: approvals, alerts and the daily report. A dot marks unread ones.'],
 ['server','Server','The server\'s health, backups, updates and the Pause / Kill / Stop controls. Swipe left or right to move between tabs.']];
function tour(force){if(!force&&(store('bw.tour')==='1'||location.pathname.indexOf('/act')===0||!document.body.dataset.tab||!document.querySelector('.tabs .tab')))return;
 if(document.querySelector('.tourbg'))return;var k=0,bg=document.createElement('div'),ring=document.createElement('div'),tip=document.createElement('div');
 bg.className='tourbg';ring.className='tourring';tip.className='tourtip';tip.setAttribute('role','dialog');tip.setAttribute('aria-live','polite');
 document.body.appendChild(bg);document.body.appendChild(ring);document.body.appendChild(tip);
 function end(){store('bw.tour','1');bg.remove();ring.remove();tip.remove();}
 function show(){var s=TOUR[k],a=document.querySelector('.tab[data-tab='+s[0]+']');if(!a){end();return;}var r=a.getBoundingClientRect();
  ring.style.left=(r.left-4)+'px';ring.style.top=(r.top-4)+'px';ring.style.width=(r.width+8)+'px';ring.style.height=(r.height+8)+'px';
  tip.style.bottom=(window.innerHeight-r.top+18)+'px';
  tip.innerHTML='<p class="small muted">'+(k+1)+' of '+TOUR.length+'</p><p><b>'+s[1]+'</b></p><p>'+s[2]+'</p><div class="btns"><button type="button" class="btn sec" data-tskip>'+(k===TOUR.length-1?'Close':'Skip')+'</button><button type="button" class="btn" data-tnext>'+(k===TOUR.length-1?'Done':'Next')+'</button></div>';
  tip.querySelector('[data-tskip]').addEventListener('click',end);tip.querySelector('[data-tnext]').addEventListener('click',function(){k++;if(k>=TOUR.length)end();else{buzz();show();}});
  tip.querySelector('[data-tnext]').focus();}
 bg.addEventListener('click',end);show();}
function ptrSpin(p){var c=document.querySelector('#ptr circle');if(c)c.setAttribute('stroke-dasharray',(Math.min(p,1)*56).toFixed(1)+' 63');}
function bumpNumbers(){}
function tileValues(){var o={};$$('.tile').forEach(function(t){var l=t.querySelector('.tl'),v=t.querySelector('.tv');if(l&&v)o[l.textContent]=v.textContent;});return o;}
function enhance(){tmap();whatif();cal();cmp();replay();homeCards();prefs();search();swipeTabs();tips();bench();reminders();setup();badge();filters();charts();alerts();countup();rings();countdown();sorter();views();donut();sheet();inbox();markAll();resultToast();}
function skeleton(){main.innerHTML='<div class="skel s"></div><div class="skel"></div><div class="skel"></div>';}
function swap(html,url,push){
 var doc=new DOMParser().parseFromString(html,'text/html');var m=doc.getElementById('main');if(!m){location.href=url;return;}
 var old=push?null:tileValues();main.innerHTML=m.innerHTML;document.title=doc.title;setTab(doc.body.dataset.tab||'');
 document.body.dataset.latestInbox=doc.body.dataset.latestInbox||0;document.body.dataset.inboxIds=doc.body.dataset.inboxIds||'';document.body.dataset.refresh=doc.body.dataset.refresh||'1';document.body.dataset.waiting=doc.body.dataset.waiting||'0';document.body.dataset.latestNews=doc.body.dataset.latestNews||'0';
 if(push)history.pushState({},'',url);enhance();if(old)bumpNumbers(old);}
function go(url,push){main.classList.add('fade');var sk=setTimeout(skeleton,180);
 fetch(url,{credentials:'same-origin'}).then(function(r){if(!r.ok&&r.status!==404)throw r;return r.text();})
 .then(function(t){clearTimeout(sk);swap(t,url,push);if(push)window.scrollTo(0,0);})
 .catch(function(){location.href=url;}).then(function(){clearTimeout(sk);main.classList.remove('fade');
  var rb=document.getElementById('refresh');if(rb)rb.classList.remove('spin');var pt=document.getElementById('ptr');if(pt)pt.classList.remove('show','go');});}
document.addEventListener('click',function(ev){var b=ev.target.closest&&ev.target.closest('.btn');if(b)buzz();
 var a=ev.target.closest&&ev.target.closest('a[data-nav]');
 if(!a||ev.metaKey||ev.ctrlKey||a.target||a.dataset.sheet)return;var u=new URL(a.href,location.href);
 if(u.origin!==location.origin||u.pathname.indexOf('/act/')===0)return;ev.preventDefault();var hadSheet=dropSheet();if(hadSheet&&history.state&&history.state.bwSheet)history.replaceState({},'',location.href);
 if(a.classList.contains('tab')){if(document.body.dataset.tab!==a.dataset.tab)buzz();setTab(a.dataset.tab);}go(u.pathname+u.search,true);});
window.addEventListener('popstate',function(){if(dropSheet())return;go(location.pathname+location.search,false);});
function refresh(){var rb=document.getElementById('refresh');if(rb)rb.classList.add('spin');
 if(location.pathname.indexOf('/act/')===0){location.reload();return;}go(location.pathname+location.search,false);}
document.addEventListener('click',function(ev){var r=ev.target.closest&&ev.target.closest('#refresh');if(!r)return;ev.preventDefault();buzz();refresh();});
function topShadow(){var t=document.querySelector('.top');if(t)t.classList.toggle('scrolled',window.scrollY>4);}
document.documentElement.classList.add('js');window.addEventListener('scroll',topShadow,{passive:true});topShadow();
setInterval(function(){if(document.visibilityState==='visible'&&document.body.dataset.refresh==='1'&&location.pathname.indexOf('/act/')!==0&&!document.querySelector('.sheet'))refresh();},60000);
var y0=null,ptr=document.getElementById('ptr');
window.addEventListener('touchstart',function(ev){y0=window.scrollY===0&&!document.querySelector('.sheet')?ev.touches[0].clientY:null;},{passive:true});
window.addEventListener('touchmove',function(ev){if(y0===null||!ptr)return;var d=ev.touches[0].clientY-y0;ptr.classList.toggle('show',d>24);ptrSpin(d/90);},{passive:true});
window.addEventListener('touchend',function(){if(ptr&&ptr.classList.contains('show')){var c=ptr.querySelector('circle');
 if(c&&c.getAttribute('stroke-dasharray').split(' ')[0]>=50){ptr.classList.add('go');buzz();refresh();}else ptr.classList.remove('show');}y0=null;});
function alerts(){
 var b=document.getElementById('alerts-on');if(!b||b.dataset.bound)return;b.dataset.bound='1';
 var out=document.getElementById('alerts-state');
 function say(t){if(out)out.textContent=t;}
 if(!('serviceWorker' in navigator)||!('PushManager' in window)){say('This browser cannot show alerts. On iPhone: Share > Add to Home Screen first, then open Big Wins from the home screen.');b.disabled=true;return;}
 b.addEventListener('click',function(){
  var cc=document.getElementById('alerts-code');if(cc&&!/^[0-9]{6}$/.test(cc.value)){say('Type your 6-digit code first.');return;}
  Notification.requestPermission().then(function(p){if(p!=='granted'){say('Alerts are blocked. Allow notifications for Big Wins in the phone settings.');throw 0;}
   return navigator.serviceWorker.register('/sw.js',{scope:'/'});})
  .then(function(){return navigator.serviceWorker.ready;})
  .then(function(reg){var k=b.dataset.key,raw=atob(k.replace(/-/g,'+').replace(/_/g,'/')+'=='.slice(0,(4-k.length%4)%4)),arr=new Uint8Array(raw.length);
   for(var i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
   return reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:arr});})
  .then(function(sub){var c=document.getElementById('alerts-code');return fetch('/act/push/subscribe',{method:'POST',credentials:'same-origin',
   headers:{'Content-Type':'application/json','X-CSRF-Token':b.dataset.csrf},body:JSON.stringify({subscription:sub,code:c?c.value:''})});})
  .then(function(r){return r.text().then(function(t){say(r.ok?'Alerts are on for this phone. A test alert is on its way.':'Not saved: '+t);if(r.ok)toast('Alerts are on');});})
  .catch(function(x){if(x!==0)say('Could not turn alerts on: '+x);});
 });
}
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(function(){});
 navigator.serviceWorker.addEventListener('message',function(ev){if(ev.data&&ev.data.t==='inbox'&&!document.querySelector('.sheet'))refresh();});}
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='visible'&&location.pathname.indexOf('/act/')!==0&&!document.querySelector('.sheet'))refresh();});
window.addEventListener('pageshow',function(ev){if(ev.persisted)refresh();});
setTab(document.body.dataset.tab||'');enhance();setTimeout(function(){tour(false);},600);
})();
"""

SW = r"""
self.addEventListener('install',function(){self.skipWaiting();});
self.addEventListener('activate',function(ev){ev.waitUntil(self.clients.claim());});
self.addEventListener('push',function(ev){
 var d={};try{d=ev.data?ev.data.json():{};}catch(x){d={title:'Big Wins',body:ev.data?ev.data.text():''};}
 var urgent=d.kind==='page'||d.kind==='approval';
 ev.waitUntil(Promise.all([self.registration.showNotification(d.title||'Big Wins',{body:d.body||'',
  tag:d.tag||d.kind||'bw',renotify:urgent,requireInteraction:urgent,icon:'/icon-192.png',
  badge:'/icon-192.png',data:{url:d.url||'/inbox'}}),
  self.clients.matchAll({type:'window'}).then(function(cs){cs.forEach(function(c){c.postMessage({t:'inbox'});});})]));
});
self.addEventListener('notificationclick',function(ev){ev.notification.close();
 var url=new URL((ev.notification.data&&ev.notification.data.url)||'/inbox',self.location.origin).href;
 ev.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(function(cs){
  for(var i=0;i<cs.length;i++){if('focus' in cs[i]){cs[i].navigate(url);return cs[i].focus();}}
  return self.clients.openWindow(url);}));
});
"""

STATIC: dict[str, tuple[str, str]] = {
    "/app.css": ("text/css; charset=utf-8", CSS),
    "/app.js": ("text/javascript; charset=utf-8", JS),
    "/sw.js": ("text/javascript; charset=utf-8", SW),
}
