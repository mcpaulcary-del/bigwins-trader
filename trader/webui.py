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

THEME = "#2853c8"  # BF-D62: the one accent colour

TABS: tuple[tuple[str, str, str], ...] = (
    ("home", "/", "Home"),
    ("holdings", "/holdings", "Holdings"),
    ("orders", "/orders", "Orders"),
    ("inbox", "/inbox", "Inbox"),
    ("server", "/server", "Server"),
)
ICONS = {
    "home": '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "holdings": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "orders": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"/>',
    "inbox": '<path d="M3 13l3-9h12l3 9v7H3zM3 13h5l1 3h6l1-3h5"/>',
    "server": '<path d="M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1'
    'M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-5-5"/>',
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
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</svg>'
    )


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
) -> str:
    """One whole page: header (brand, PAPER/DEMO badge, refresh, settings), the body in
    ``<main>`` and the bottom tab bar. ``active`` = the tab to highlight."""
    idx = next((i for i, (k, _, _) in enumerate(TABS) if k == active), -1)
    tabs = "".join(
        f'<a href="{href}" class="tab{" on" if key == active else ""}" data-nav data-tab="{key}"'
        + (' aria-current="page"' if key == active else "")
        + ">"
        f"{icon(key)}<span>{e(label)}</span>"
        + ('<b class="dot" hidden></b>' if key == "inbox" else "")
        + "</a>"
        for key, href, label in TABS
    )
    head = (
        '<header class="top"><a class="brand" href="/" data-nav><span class="logo">BW</span>'
        f'Big Wins</a><span class="badge">{mode_label(demo, live)}</span>'
        '<span class="sp"></span>'
        f'<button class="iconbtn" id="searchbtn" type="button" aria-label="Search">{icon("search")}'
        "</button>"
        f'<button class="iconbtn" id="refresh" type="button" aria-label="Refresh">{icon("refresh")}'
        f'</button><a class="iconbtn" href="/settings" data-nav aria-label="Settings">{icon("gear")}</a>'
        "</header>"
    )
    sub = f'<p class="muted small" id="sub">{e(subtitle)}</p>' if subtitle else ""
    note = "".join(f'<p class="note">{e(n)}</p>' for n in notes)
    noscript = '<noscript><meta http-equiv="refresh" content="60"></noscript>' if refresh else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f'<meta name="theme-color" content="{THEME}">'
        '<meta name="color-scheme" content="light dark">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="Big Wins">'
        '<link rel="manifest" href="/manifest.webmanifest">'
        '<link rel="icon" href="/icon.svg" type="image/svg+xml">'
        '<link rel="apple-touch-icon" href="/icon-192.png">'
        f"{noscript}<title>{e(title)} · Big Wins</title>"
        f'<link rel="stylesheet" href="/app.css"></head>'
        f'<body data-tab="{e(active)}" data-latest-inbox="{latest_inbox}"'
        f' data-inbox-ids="{",".join(str(int(i)) for i in inbox_ids)}"'
        f' data-refresh="{1 if refresh else 0}">'
        f'{head}<div id="ptr" class="ptr" aria-hidden="true"><svg viewBox="0 0 24 24"><circle '
        'cx="12" cy="12" r="9" stroke-dasharray="0 63" transform="rotate(-90 12 12)"/></svg></div>'
        f'<main id="main" data-title="{e(title)}">{sub}{note}{body}</main>'
        f'<nav class="tabs" aria-label="Sections"><div class="tabin">'
        f'<i class="tabind" aria-hidden="true" style="transform:translateX({idx * 100}%)'
        f'{";opacity:0" if idx < 0 else ""}"></i>{tabs}</div></nav>'
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


CSS = """
:root{color-scheme:light;--bg:#f3f5f9;--card:#ffffff;--card2:#f7f9fc;--ink:#10131a;--ink2:#4a5263;
--line:#e3e7ee;--acc:#2853c8;--acc-ink:#ffffff;--acc-soft:#e8eefc;--up:#0b7a3b;--down:#c22b2b;
--up-soft:#e3f4ea;--down-soft:#fbe6e6;--amber:#8a5a00;--amber-soft:#fdf1d8;--s1:#2853c8;
--s2:#d0661f;--s3:#7a4fd0;--tabbar:rgba(255,255,255,.92);--shadow:0 1px 2px rgba(16,19,26,.05),
0 4px 14px rgba(16,19,26,.06);--radius:18px;--danger:#b3261e;--danger-ink:#ffffff;
--c0:#2853c8;--c1:#0f8a7e;--c2:#d0661f;--c3:#7a4fd0;--c4:#b0457b;--c5:#5b7a1f;--c6:#a07a00;--c7:#55627a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#0e1117;
--card:#171b23;--card2:#1d222c;--ink:#eef1f6;--ink2:#b4bccb;--line:#2a303b;--acc:#8aa6ff;
--acc-ink:#0e1117;--acc-soft:#1f2a47;--up:#4fd18b;--down:#ff8f87;--up-soft:#173126;
--down-soft:#3a1d1d;--amber:#f2c35b;--amber-soft:#3a2e12;--s1:#8aa6ff;--s2:#f29a5b;--s3:#b69cff;
--tabbar:rgba(23,27,35,.92);--shadow:0 1px 2px rgba(0,0,0,.3);--danger:#ff6b61;
--danger-ink:#0e1117;--c0:#8aa6ff;--c1:#4fd1c5;--c2:#f29a5b;--c3:#b69cff;--c4:#f48fb1;
--c5:#b5d66b;--c6:#f2c35b;--c7:#9aa7bd}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0 auto;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,
"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;padding:0 16px calc(88px + env(safe-area-inset-bottom));
max-width:640px;-webkit-font-smoothing:antialiased}
a{color:var(--acc);text-underline-offset:2px}
.num,.tv,.r,td,.hv,.money{font-variant-numeric:tabular-nums}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;
padding:calc(10px + env(safe-area-inset-top)) 0 8px;background:var(--bg)}
.brand{font-weight:750;font-size:19px;display:flex;align-items:center;gap:9px;color:var(--ink);
text-decoration:none;letter-spacing:-.01em}
.logo{background:linear-gradient(135deg,var(--acc),#0f8a7e);color:#fff;border-radius:10px;
font-size:12px;font-weight:800;padding:6px 7px}
.badge{border:1px solid var(--amber);color:var(--amber);border-radius:999px;font-size:11px;
font-weight:750;padding:1px 8px;letter-spacing:.04em}.sp{flex:1}
.iconbtn{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;
border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--ink);
cursor:pointer;padding:0;box-shadow:var(--shadow)}
.iconbtn.spin .ic{animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.ic{width:20px;height:20px}
.ptr{height:0;overflow:hidden;text-align:center;color:var(--ink2);font-size:12px;transition:height .15s}
.ptr.show{height:28px;line-height:28px}
main{transition:opacity .18s ease,transform .18s ease}main.fade{opacity:.35;transform:translateY(4px)}
.tabs{position:fixed;left:0;right:0;bottom:0;z-index:6;display:flex;justify-content:center;
background:var(--tabbar);backdrop-filter:saturate(1.4) blur(12px);-webkit-backdrop-filter:blur(12px);
border-top:1px solid var(--line);padding:6px 4px calc(6px + env(safe-area-inset-bottom))}
.tabs .tabin{position:relative;display:flex;width:100%;max-width:640px}
.tabind{position:absolute;top:-6px;left:0;width:20%;height:3px;border-radius:0 0 3px 3px;
background:var(--acc);transition:transform .28s cubic-bezier(.2,.8,.2,1)}
.tab{position:relative;flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;
font-size:11px;color:var(--ink2);text-decoration:none;padding:4px 0;border-radius:12px}
.tab.on{color:var(--acc);font-weight:700}.tab .ic{width:22px;height:22px;transition:transform .2s}
.tab.on .ic{transform:translateY(-1px)}
.dot{position:absolute;top:0;left:calc(50% + 6px);min-width:17px;height:17px;border-radius:9px;
background:var(--down);color:#fff;font-size:10px;line-height:17px;text-align:center;padding:0 4px;
font-style:normal}
section{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:14px 16px;margin:14px 0;box-shadow:var(--shadow)}
h1{font-size:24px;margin:8px 0 4px;letter-spacing:-.02em}
h2{font-size:13px;margin:0 0 10px;color:var(--ink2);font-weight:650;display:flex;align-items:center;
gap:8px;text-transform:uppercase;letter-spacing:.06em}
.hero{padding:6px 2px 2px}.hl{font-size:13px;color:var(--ink2);font-weight:600}
.hv{font-size:38px;font-weight:780;letter-spacing:-.03em;line-height:1.1;margin:2px 0}
.hc{font-size:15px;font-weight:650}.hero .spk{width:100%;height:46px;margin-top:6px;display:block}
.spk.wide path{vector-effect:non-scaling-stroke}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.vs{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:4px 10px;
font-size:13px;font-weight:650;background:var(--card2);border:1px solid var(--line)}
.vs.up{background:var(--up-soft);color:var(--up);border-color:transparent}
.vs.down{background:var(--down-soft);color:var(--down);border-color:transparent}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.tile{background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:10px 12px}
.tl{font-size:12px;color:var(--ink2);font-weight:600}.tv{font-size:20px;font-weight:750;letter-spacing:-.01em}
.ts{font-size:12px;color:var(--ink2)}.tv{white-space:nowrap}.arr{font-size:.62em;vertical-align:.18em;margin-right:4px}
.muted{color:var(--ink2)}.small,.sub{font-size:12px}.sub{color:var(--ink2)}
.up,.sub.up{color:var(--up)}.down,.sub.down{color:var(--down)}.warn{color:var(--amber)}
.chartbox{position:relative}
.chart{width:100%;height:auto;display:block;touch-action:pan-y;overflow:visible}
.grid{stroke:var(--line);stroke-width:1}.base{stroke:var(--ink2);stroke-width:1;stroke-dasharray:3 4;opacity:.55}
.ax{fill:var(--ink2);font-size:10px}
.s1{fill:none;stroke:var(--s1);stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.s2{fill:none;stroke:var(--s2);stroke-width:1.8;stroke-linejoin:round;stroke-dasharray:5 3}
.s3{fill:none;stroke:var(--s3);stroke-width:2;stroke-linejoin:round}
.area{fill:url(#gA);stroke:none}.gA0{stop-color:var(--s1);stop-opacity:.28}.gA1{stop-color:var(--s1);stop-opacity:0}
.dd{fill:var(--down);opacity:.16;stroke:var(--down);stroke-width:1}
.bar{fill:var(--s2);opacity:.45}.bar.me{fill:var(--s1);opacity:1}
.d1{fill:var(--s1);stroke:var(--card);stroke-width:2}
.buyd{fill:var(--up);stroke:var(--card);stroke-width:1.5}.selld{fill:var(--down);stroke:var(--card);stroke-width:1.5}
.xh{stroke:var(--ink2);stroke-width:1;stroke-dasharray:2 3}.xd{fill:var(--card);stroke:var(--s1);stroke-width:2.5}
.tip{font-size:12px;fill:var(--ink)}.tipbox{fill:var(--card);stroke:var(--line)}
.ctip{position:absolute;top:4px;pointer-events:none;background:var(--card);border:1px solid var(--line);
border-radius:12px;box-shadow:var(--shadow);padding:7px 10px;font-size:12px;line-height:1.35;
min-width:150px;opacity:0;transition:opacity .12s;font-variant-numeric:tabular-nums}
.ctip.on{opacity:1}.ctip b{font-size:14px}
.legend{font-size:12px;color:var(--ink2);margin:6px 0}
.key{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin:0 4px 0 8px}
.k1{background:var(--s1)}.k2{background:var(--s2)}.k3{background:var(--s3)}
.seg{display:flex;gap:6px;margin:8px 0;flex-wrap:wrap}
.seg a,.seg button,.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);
border-radius:999px;padding:6px 13px;font-size:13px;text-decoration:none;cursor:pointer;font-weight:600;
transition:background .15s,color .15s}
.seg .on,.chip.on{background:var(--acc);border-color:var(--acc);color:var(--acc-ink)}
table{width:100%;border-collapse:collapse}td,th{padding:7px 4px;border-top:1px solid var(--line);
vertical-align:top;text-align:left}th{font-size:12px;color:var(--ink2);font-weight:600;border-top:0}
.r{text-align:right}.buy{color:var(--up)}.sell{color:var(--down)}
.list{list-style:none;padding:0;margin:0}.list li{padding:10px 0;border-top:1px solid var(--line)}
.list li:first-child{border-top:0}
.rowlink{display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none}
.rowlink .grow{flex:1;min-width:0}.chev{color:var(--ink2);font-size:18px}
.hold .spk{width:64px;height:24px;flex:none}
.bars{display:flex;gap:4px;margin-top:5px}.gb,.wb{height:4px;border-radius:2px;background:var(--line);
flex:1;overflow:hidden}.gb b,.wb b{display:block;height:100%}.gb.up b{background:var(--up)}
.gb.down b{background:var(--down)}.wb b{background:var(--acc)}
.hold li.hl{background:var(--acc-soft);border-radius:12px;margin:0 -8px;padding:10px 8px}
.donutrow{display:flex;gap:14px;align-items:center}
.donut{position:relative;margin:0;width:132px;flex:none}.donut svg{width:132px;height:132px}
.donut figcaption{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
justify-content:center;pointer-events:none}.donut figcaption b{font-size:16px}
.donut figcaption span,.ring figcaption span{font-size:11px;color:var(--ink2)}
.ds{fill:none;stroke-width:16;cursor:pointer;transition:stroke-width .15s,opacity .15s}
.ds.dim{opacity:.3}.ds.hl{stroke-width:20}
.c0{stroke:var(--c0)}.c1{stroke:var(--c1)}.c2{stroke:var(--c2)}.c3{stroke:var(--c3)}
.c4{stroke:var(--c4)}.c5{stroke:var(--c5)}.c6{stroke:var(--c6)}.c7{stroke:var(--c7)}
.legend2{list-style:none;margin:0;padding:0;font-size:12px;flex:1}.legend2 li{display:flex;gap:6px;
align-items:center;padding:2px 0}.legend2 i{width:9px;height:9px;border-radius:3px;display:inline-block}
.spk{overflow:visible}.spl{fill:none;stroke:var(--ink2);stroke-width:1.6;stroke-linejoin:round}
.spa{fill:var(--ink2);opacity:.08}.spk.up .spl{stroke:var(--up)}.spk.up .spa{fill:var(--up)}
.spk.down .spl{stroke:var(--down)}.spk.down .spa{fill:var(--down)}.spd{fill:var(--ink2)}
.spk.up .spd{fill:var(--up)}.spk.down .spd{fill:var(--down)}
.rings{display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.ring{position:relative;margin:0;width:92px}.ring svg{width:92px;height:92px}
.ring figcaption{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring figcaption b{font-size:17px}.rt{fill:none;stroke:var(--line);stroke-width:8}
.rv{fill:none;stroke:var(--acc);stroke-width:8;stroke-linecap:round;transition:stroke-dasharray .8s ease}
.ring.good .rv{stroke:var(--up)}.ring.warnr .rv{stroke:var(--amber)}
.gauge{width:100%;max-width:240px;display:block;margin:0 auto}.gt{fill:none;stroke:var(--line);stroke-width:14;stroke-linecap:round}
.gv{fill:none;stroke:var(--up);stroke-width:14;stroke-linecap:round}.gauge.bad .gv{stroke:var(--down)}
.gm{fill:var(--ink)}.gbig{font-size:30px;font-weight:800;fill:var(--ink)}
.tmeter{margin:8px 0 22px}.tbar{position:relative;height:10px;border-radius:5px;background:var(--line)}
.tbar b{display:block;height:100%;border-radius:5px;background:var(--up)}.tmeter.bad .tbar b{background:var(--down)}
.tk{position:absolute;top:-3px;width:2px;height:16px;background:var(--ink2);transform:translateX(-1px)}
.tl3{position:absolute;top:15px;font-size:10px;color:var(--ink2);transform:translateX(-50%);white-space:nowrap}
.pill{font-size:12px;font-weight:700;border-radius:999px;padding:2px 9px;white-space:nowrap;
background:var(--card2);border:1px solid var(--line)}
.ok{background:var(--up-soft);color:var(--up);border-color:transparent}.amber{background:var(--amber-soft);
color:var(--amber);border-color:transparent}.bad{background:var(--down-soft);color:var(--down);border-color:transparent}
.note{background:var(--amber-soft);color:var(--ink);border-radius:12px;padding:8px 12px;font-size:13px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;border:0;border-radius:14px;
padding:12px 16px;font-size:16px;font-weight:700;cursor:pointer;text-decoration:none;
background:var(--acc);color:var(--acc-ink);min-height:48px;box-shadow:var(--shadow);
transition:transform .08s ease,filter .15s}
.btn:active{transform:scale(.98)}.btn:focus-visible,.tab:focus-visible,.chip:focus-visible{outline:3px solid var(--acc);outline-offset:2px}
.btn.wide{width:100%}.btn.sec{background:var(--card);color:var(--ink);border:1px solid var(--line)}
.btn.danger{background:var(--danger);color:var(--danger-ink);border:2px solid var(--danger);
letter-spacing:.02em}.btn.warnb{background:var(--amber);color:var(--card)}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}
.code{font-size:28px;letter-spacing:8px;text-align:center;width:100%;padding:12px;border-radius:14px;
border:2px solid var(--line);background:var(--card2);color:var(--ink);font-variant-numeric:tabular-nums}
.code:focus{border-color:var(--acc);outline:none}
.summary{font-size:19px;font-weight:750;margin:4px 0 8px;letter-spacing:-.01em}
.waitcard{border:2px solid var(--amber);background:linear-gradient(180deg,var(--amber-soft),var(--card) 60%)}
.cd{display:inline-flex;gap:6px;align-items:center;font-weight:700;color:var(--amber);font-size:13px}
.msg{position:relative;border-left:4px solid var(--line);padding-left:12px!important;transition:transform .2s}
.msg.page{border-color:var(--down)}.msg.approval{border-color:var(--amber)}.msg.report{border-color:var(--s1)}
.msg.action{border-color:var(--c1)}.msg pre{white-space:pre-wrap;font:12px/1.4 ui-monospace,Menlo,Consolas,monospace;
margin:6px 0 0;color:var(--ink2);max-height:16em;overflow:auto}
.msg.unread .t{font-weight:750}.msg.unread:after{content:"";position:absolute;right:2px;top:16px;width:8px;
height:8px;border-radius:4px;background:var(--acc)}.msg.swiping{transition:none}
.day{font-size:12px;font-weight:700;color:var(--ink2);text-transform:uppercase;letter-spacing:.05em;
margin:14px 2px 4px;border-top:0!important;padding:0!important}
.steps{display:flex;align-items:center;gap:0;margin:8px 0 4px}.steps i{flex:none;width:12px;height:12px;
border-radius:6px;background:var(--line);border:2px solid var(--card)}.steps i.on{background:var(--acc)}
.steps i.bad{background:var(--down)}.steps em{flex:1;height:2px;background:var(--line)}.steps em.on{background:var(--acc)}
.stepl{display:flex;justify-content:space-between;font-size:10px;color:var(--ink2)}
.tl2{list-style:none;margin:6px 0 0;padding:0 0 0 14px;border-left:2px solid var(--line)}
.tl2 li{position:relative;padding:3px 0 3px 6px;font-size:13px;border-top:0!important}
.tl2 li:before{content:"";position:absolute;left:-20px;top:8px;width:10px;height:10px;border-radius:5px;background:var(--line)}
.tl2 li.done:before{background:var(--acc)}.tl2 li.badst:before{background:var(--down)}
.meter{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin:4px 0}
.meter b{display:block;height:100%;background:var(--acc)}.meter.hi b{background:var(--amber)}.meter.crit b{background:var(--down)}
.htiles{display:grid;grid-template-columns:1fr 1fr;gap:10px}.ht{border-radius:14px;padding:10px 12px;
background:var(--card2);border:1px solid var(--line)}.ht .tl{display:flex;justify-content:space-between}
.ht.good{border-left:4px solid var(--up)}.ht.warn2{border-left:4px solid var(--amber)}.ht.badt{border-left:4px solid var(--down)}
.logs{white-space:pre-wrap;font:11px/1.4 ui-monospace,Menlo,Consolas,monospace;max-height:20em;overflow:auto;
background:var(--card2);border-radius:10px;padding:10px}
label.chk{display:flex;gap:8px;align-items:center;margin:10px 0}
footer{font-size:12px;color:var(--ink2);text-align:center;margin-top:18px}
.skel{border-radius:var(--radius);background:linear-gradient(90deg,var(--card) 0%,var(--card2) 50%,var(--card) 100%);
background-size:200% 100%;animation:sh 1.1s linear infinite;height:120px;margin:14px 0;border:1px solid var(--line)}
.skel.s{height:60px}@keyframes sh{to{background-position:-200% 0}}
#toast{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translate(-50%,20px);
background:var(--ink);color:var(--bg);padding:10px 16px;border-radius:14px;font-size:14px;font-weight:600;
opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:9;max-width:90vw}
#toast.on{opacity:1;transform:translate(-50%,0)}
.sheetbg{position:fixed;inset:0;background:rgba(10,12,18,.42);z-index:7;opacity:0;transition:opacity .2s}
.sheetbg.on{opacity:1}.sheet{position:fixed;left:0;right:0;bottom:0;z-index:8;max-height:88vh;overflow:auto;
background:var(--bg);border-radius:22px 22px 0 0;padding:6px 16px calc(24px + env(safe-area-inset-bottom));
transform:translateY(100%);transition:transform .28s cubic-bezier(.2,.8,.2,1);max-width:640px;margin:0 auto}
.sheet.on{transform:translateY(0)}.grab{width:42px;height:5px;border-radius:3px;background:var(--line);margin:6px auto 4px}
.sheetx{float:right}
.sitem.done b{color:var(--up)}.setup .btn{margin-top:6px;min-height:40px;font-size:14px}
[hidden]{display:none!important}
@media (min-width:860px){body{max-width:980px;padding:0 24px calc(88px + env(safe-area-inset-bottom))}
main{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 16px;align-items:start}
main>*{grid-column:1/-1}main>section{grid-column:auto;min-width:0}
main>section.herocard,main>section:has(.list),main>section.wide,main>section.waitcard{grid-column:1/-1}
.tabs .tabin{max-width:720px}.sheet{max-width:760px}}
.hit{fill:transparent;cursor:crosshair}.hit.on{fill:var(--ink);fill-opacity:.06}
.ctip{white-space:pre-line}
[data-tips] .ctip{position:static;margin-top:6px;box-shadow:none;display:none;left:auto!important;opacity:1}
[data-tips] .ctip.on{display:block}
.cut{stroke-width:1;stroke-dasharray:4 3}.cut.c20{stroke:var(--up)}.cut.c40{stroke:var(--amber)}
.rk{fill:var(--card);stroke:var(--s1);stroke-width:2}.rk.top{fill:var(--up)}.rk.keep{fill:var(--amber)}
.out{fill:var(--line)}.fan1{fill:var(--s1);fill-opacity:.13}.fan2{fill:var(--s1);fill-opacity:.24}
.med{fill:none;stroke:var(--s1);stroke-width:2}.meanl{fill:none;stroke:var(--amber);stroke-width:2;stroke-dasharray:6 3}
.meand{fill:var(--amber)}.act{fill:none;stroke:var(--ink);stroke-width:2.4;stroke-linejoin:round}
.actd{fill:var(--ink);stroke:var(--card);stroke-width:1.5}.hypd{fill:var(--s3);stroke:var(--card);stroke-width:1.5}
.hi52{fill:none;stroke:var(--ink2);stroke-width:1.4;stroke-dasharray:2 3}
.fk1{background:var(--s1);opacity:.25;height:8px}.fk2{background:var(--s1);opacity:.5;height:8px}
.km{background:var(--amber)}.ka{background:var(--ink)}.khi{background:var(--ink2)}
.lead2{font-size:15px}.h3{font-size:14px;margin:14px 0 4px}.bul{margin:4px 0;padding-left:18px}.bul li{margin:4px 0}
.st-holding{background:var(--up-soft);color:var(--up);border-color:transparent}
.st-sold{background:var(--card2)}.st-proposed{background:var(--amber-soft);color:var(--amber);border-color:transparent}
.st-passed{background:var(--card2);color:var(--ink2)}
.about summary,details summary{cursor:pointer;font-size:13px;color:var(--acc);font-weight:600;margin:6px 0}
.doc h1{font-size:22px}.doc h2{font-size:17px;margin-top:18px}.doc p,.doc li{font-size:14px;line-height:1.5}
.tscroll{overflow-x:auto}.doc table{font-size:12px}
:root{--spring:cubic-bezier(.34,1.4,.64,1);--tu1:#dbe7ff;--tu1i:#0b1b3a;--tu2:#2f63c4;--tu3:#163f8c;
--td1:#ffe2cc;--td1i:#3a1a00;--td2:#a9500d;--td3:#7a3604;--tmi:#ffffff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--tu1:#1c3160;--tu1i:#e6eeff;--tu2:#2f63c4;
--tu3:#8fb0f5;--td1:#47280f;--td1i:#ffe6d2;--td2:#a9500d;--td3:#f2a866;--tmi3:#0e1117}}
.sheet{transition:transform .42s var(--spring),max-height .3s ease,border-radius .3s ease}
.sheet.full{max-height:100vh;border-radius:0;top:0}.sheet.dragging{transition:none}
.ghost{position:fixed;z-index:9;background:var(--card);border-radius:14px;box-shadow:var(--shadow);
overflow:hidden;pointer-events:none;padding:8px 12px}
.ptr{display:flex;align-items:center;justify-content:center}.ptr svg{width:24px;height:24px}
.ptr circle{fill:none;stroke:var(--acc);stroke-width:3;stroke-linecap:round}
.ptr.show{height:44px}.ptr.go svg{animation:spin .8s linear infinite}
main.sl{animation:sl .28s var(--spring)}main.sr{animation:sr .28s var(--spring)}
@keyframes sl{from{transform:translateX(40px);opacity:.3}to{transform:none;opacity:1}}
@keyframes sr{from{transform:translateX(-40px);opacity:.3}to{transform:none;opacity:1}}
.chip,.btn,.cday,.rdot{transition:transform .25s var(--spring),background .15s,color .15s}.chip:active,.cday:active{transform:scale(.94)}
.bump{animation:bump .6s var(--spring)}@keyframes bump{0%{transform:scale(1)}30%{transform:scale(1.06)}100%{transform:scale(1)}}
.vs.mile{background:var(--card2);color:var(--ink2);font-weight:600}
.tmap{position:relative;width:100%;aspect-ratio:100/62;margin:6px 0}
.tm{position:absolute;padding:2px;box-sizing:border-box;text-decoration:none}
.tmi{display:block;width:100%;height:100%;box-sizing:border-box;border-radius:8px;padding:5px 6px;font-size:12px;
line-height:1.25;overflow:hidden;transition:background .3s,transform .2s var(--spring);font-variant-numeric:tabular-nums}
.tm:active .tmi{transform:scale(.97)}.tm0{background:var(--card2);color:var(--ink);border:1px solid var(--line)}
.tmu1{background:var(--tu1);color:var(--tu1i)}.tmu2{background:var(--tu2);color:#fff}.tmu3{background:var(--tu3);color:var(--tmi3,#fff)}
.tmd1{background:var(--td1);color:var(--td1i)}.tmd2{background:var(--td2);color:#fff}.tmd3{background:var(--td3);color:var(--tmi3,#fff)}
.whatif label{display:block;font-weight:600}input[type=range]{width:100%;accent-color:var(--acc);height:34px;margin:4px 0 0}
.wscale{display:flex;justify-content:space-between;font-size:11px;color:var(--ink2)}.wv b{font-size:22px}
.wbar{position:relative;height:12px;border-radius:6px;background:var(--line);margin:16px 0 28px}
.wbar>b{display:block;height:100%;border-radius:6px;background:var(--acc);transition:width .35s var(--spring)}
.wbar.bad>b{background:var(--down)}.wbar.mid>b{background:var(--amber)}
.wk{position:absolute;top:-4px;width:2px;height:20px;background:var(--ink2)}
.wkl{position:absolute;top:18px;font-size:10px;transform:translateX(-50%);color:var(--ink2);white-space:nowrap}
.calnav{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.calnav .iconbtn{text-decoration:none;font-size:20px}
.calt{margin:0;font-size:17px;text-transform:none;letter-spacing:0;color:var(--ink)}
.cwk,.cgrid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:4px;text-align:center}
.cwk span{font-size:11px;color:var(--ink2);font-weight:600}
.cday{aspect-ratio:1;border:1px solid var(--line);background:var(--card);border-radius:10px;color:var(--ink);
font:inherit;font-size:13px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;padding:0;min-width:0}
.cday.out{opacity:.3}.cday.today{border:2px solid var(--acc);font-weight:750}.cday.has{background:var(--card2)}
.cday.sel{background:var(--acc);color:var(--acc-ink);border-color:var(--acc)}
.cdots{display:flex;gap:2px;height:6px}.cdots i,.cl i,.cdk{width:7px;height:7px;border-radius:4px;display:inline-block;flex:none}
.cd-decision{background:var(--acc)}.cd-cutoff{background:var(--amber)}.cd-exdiv{background:var(--c1)}
.cd-pay{background:var(--c5)}.cd-c6{background:var(--c3)}.cd-cgt{background:var(--c4)}.cd-eofy{background:var(--ink2)}
.clegend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:11px;color:var(--ink2);margin:10px 0 4px}
.cl{display:inline-flex;align-items:center;gap:4px}.cevs li{display:flex;gap:10px;align-items:flex-start}
.cevs .cdk{margin-top:6px}
.cmpout{position:static;opacity:1;margin-top:6px;box-shadow:none;min-height:2.6em}
.k-c0{background:var(--c0)}.k-c1{background:var(--c1)}.k-c2{background:var(--c2)}.k-c3{background:var(--c3)}
.rdots{display:flex;gap:6px;justify-content:center;margin:2px 0 12px}
.rdot{width:10px;height:10px;border-radius:5px;border:0;background:var(--line);padding:0;cursor:pointer}
.rdot.on{background:var(--acc);width:26px}
.replay.js .rpane{display:none}.replay.js .rpane.on{display:block;animation:rin .4s var(--spring)}
@keyframes rin{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.replay:not(.js) .rbtn,.replay:not(.js) [data-rplay],.replay:not(.js) .rdots{display:none}
.rbars{list-style:none;padding:0;margin:6px 0}.rb{display:grid;grid-template-columns:52px 1fr 40px;gap:8px;
align-items:center;font-size:12px;padding:2px 0!important;border:0!important}
.rbb{height:8px;background:var(--line);border-radius:4px;overflow:hidden}.rbb b{display:block;height:100%;background:var(--s2)}
.rb.pick .rbb b{background:var(--acc)}.replay.js .rpane.on .rbb b{animation:grow .7s var(--spring) both}
@keyframes grow{from{width:0}}.rbv{color:var(--ink2);text-align:right}
li.rbuy b{color:var(--up)}li.rsell b{color:var(--down)}
#srch{position:fixed;inset:0;z-index:10;background:var(--bg);padding:calc(12px + env(safe-area-inset-top)) 16px 16px;
overflow:auto;display:none}#srch.on{display:block;animation:rin .25s ease}
.sbar{display:flex;gap:8px;align-items:center;max-width:720px;margin:0 auto}.sbar input{flex:1;font:inherit;font-size:17px;
padding:12px 14px;border-radius:14px;border:2px solid var(--line);background:var(--card);color:var(--ink)}
.sbar input:focus{border-color:var(--acc);outline:none}#sres{max-width:720px;margin:8px auto}
#sres h3{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink2);margin:14px 0 4px}
#sres a{display:block;padding:9px 4px;border-top:1px solid var(--line);color:var(--ink);text-decoration:none}
#sres a .sub{display:block}#sres mark{background:var(--amber-soft);color:inherit;border-radius:3px}
.tourbg{position:fixed;inset:0;z-index:11;background:rgba(10,12,18,.55)}
.tourring{position:fixed;z-index:12;border:3px solid #fff;border-radius:14px;box-shadow:0 0 0 4px var(--acc);
pointer-events:none;transition:all .35s var(--spring)}
.tourtip{position:fixed;z-index:12;left:16px;right:16px;max-width:360px;margin:0 auto;background:var(--card);
color:var(--ink);border-radius:16px;padding:14px 16px;box-shadow:var(--shadow);transition:bottom .35s var(--spring)}
.tourtip .btns{margin:10px 0 0}.tourtip p{margin:4px 0}
body.editing section[data-card]{outline:2px dashed var(--acc);outline-offset:2px}
.cardbar{display:none;gap:6px;justify-content:flex-end;margin:-4px 0 8px}body.editing .cardbar{display:flex}
.cardbar button{min-width:44px}section.hiddencard{display:none}
body.editing section.hiddencard{display:block;opacity:.45}#editdone{position:fixed;left:50%;transform:translateX(-50%);
bottom:calc(84px + env(safe-area-inset-bottom));z-index:9;display:none}body.editing #editdone{display:inline-flex}
.homehint{text-align:center}
body.compact section{padding:10px 12px;margin:9px 0}body.compact .tile{padding:7px 10px}
body.compact .tv{font-size:17px}body.compact .tiles{gap:7px}body.compact .hv{font-size:32px}
.sheetsk{padding:8px 0}.sheetsk .skel{margin:10px 0}
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
 a.classList.toggle('on',on);if(on){i=k;a.setAttribute('aria-current','page');}else a.removeAttribute('aria-current');});
 var ind=document.querySelector('.tabind');if(ind){ind.style.opacity=i<0?'0':'1';if(i>=0)ind.style.transform='translateX('+(i*100)+'%)';}}
function readSet(){var r=store('bw.read');try{return r?JSON.parse(r):[];}catch(x){return [];}}
function badge(){
 var latest=+(document.body.dataset.latestInbox||0),seen=+(store('bw.seen')||0),read=readSet();
 var ids=(document.body.dataset.inboxIds||'').split(',').filter(Boolean).map(Number);
 if(document.body.dataset.tab==='inbox'&&latest){store('bw.seen',latest);}
 $$('[data-inbox-id]').forEach(function(m){var id=+m.dataset.inboxId;m.classList.toggle('unread',id>seen&&read.indexOf(id)<0);});
 var d=document.querySelector('.tab[data-tab=inbox] .dot');if(!d)return;
 var n=ids.length?ids.filter(function(i){return i>seen&&read.indexOf(i)<0;}).length:Math.max(latest-seen,0);
 if(document.body.dataset.tab==='inbox')n=0;
 if(n>0){d.hidden=false;d.textContent=n>99?'99+':n;d.setAttribute('aria-label',n+' unread');}else{d.hidden=true;}
 try{if(navigator.setAppBadge){if(n>0)navigator.setAppBadge(n);else navigator.clearAppBadge();}}catch(x){}
}
function markRead(m){var id=+m.dataset.inboxId,r=readSet();if(r.indexOf(id)<0){r.push(id);store('bw.read',JSON.stringify(r.slice(-500)));}
 m.classList.remove('unread');}
function inbox(){$$('.msg[data-inbox-id]').forEach(function(m){if(m.dataset.sw)return;m.dataset.sw='1';var x0=null,dx=0;
 m.addEventListener('touchstart',function(ev){x0=ev.touches[0].clientX;dx=0;m.classList.add('swiping');},{passive:true});
 m.addEventListener('touchmove',function(ev){if(x0===null)return;dx=ev.touches[0].clientX-x0;if(dx<0)m.style.transform='translateX('+Math.max(dx,-90)+'px)';},{passive:true});
 m.addEventListener('touchend',function(){m.classList.remove('swiping');m.style.transform='';if(dx<-60){markRead(m);toast('Marked as read');}x0=null;});
 var d=m.querySelector('details');if(d)d.addEventListener('toggle',function(){if(d.open)markRead(m);});});}
function filters(){$$('[data-filter]').forEach(function(c){if(c.dataset.b)return;c.dataset.b='1';
 c.addEventListener('click',function(ev){ev.preventDefault();var k=c.dataset.filter;
  $$('[data-filter]').forEach(function(x){x.classList.toggle('on',x===c);});
  $$('[data-kind]').forEach(function(m){m.hidden=!(k==='all'||m.dataset.kind===k||(k==='alerts'&&m.dataset.kind==='page'));});
  $$('.day').forEach(function(h){var n=h.nextElementSibling,any=false;while(n&&!n.classList.contains('day')){if(!n.hidden)any=true;n=n.nextElementSibling;}h.hidden=!any;});});});}
function countup(){$$('[data-countup]').forEach(function(el){if(el.dataset.done)return;el.dataset.done='1';if(RM)return;
 var v=parseFloat(el.dataset.countup);if(!isFinite(v))return;var t0=null,from=v*0.92;
 function f(n){return 'A$'+n.toLocaleString('en-AU',{minimumFractionDigits:2,maximumFractionDigits:2});}
 function step(t){if(!t0)t0=t;var p=Math.min((t-t0)/700,1),q=1-Math.pow(1-p,3);el.textContent=f(from+(v-from)*q);if(p<1)requestAnimationFrame(step);}
 requestAnimationFrame(step);});}
function rings(){if(RM)return;$$('.rv[data-dash]').forEach(function(c){if(c.dataset.a)return;c.dataset.a='1';
 var full=c.getAttribute('stroke-dasharray').split(' ')[1];c.setAttribute('stroke-dasharray','0 '+full);
 requestAnimationFrame(function(){requestAnimationFrame(function(){c.setAttribute('stroke-dasharray',c.dataset.dash+' '+full);});});});}
function countdown(){$$('[data-deadline]').forEach(function(el){var off=el.dataset.now?Date.parse(el.dataset.now)-Date.now():0;
 function u(){var ms=Date.parse(el.dataset.deadline)-(Date.now()+off);
 if(!(ms>0)){el.textContent='deadline passed';return;}var h=Math.floor(ms/36e5),m=Math.floor(ms%36e5/6e4);
 el.textContent=(h?h+' h ':'')+m+' min left';}u();if(!el.dataset.t){el.dataset.t='1';setInterval(u,30000);}});}
function sorter(){$$('[data-sort]').forEach(function(c){if(c.dataset.b)return;c.dataset.b='1';c.addEventListener('click',function(ev){
 ev.preventDefault();var k=c.dataset.sort,ul=document.getElementById('hlist');if(!ul)return;
 $$('[data-sort]').forEach(function(x){x.classList.toggle('on',x===c);});
 var li=$$('li[data-code]',ul);li.sort(function(a,b){if(k==='name')return a.dataset.code<b.dataset.code?-1:1;
  return (+b.dataset[k])-(+a.dataset[k]);});li.forEach(function(x){ul.appendChild(x);});store('bw.sort',k);});});
 var k=store('bw.sort'),c=k&&document.querySelector('[data-sort="'+k+'"]');if(c&&!c.classList.contains('on'))c.click();}
function donut(){$$('.ds[data-code]').forEach(function(s){if(s.dataset.b)return;s.dataset.b='1';s.addEventListener('click',function(){
 var code=s.dataset.code,on=!s.classList.contains('hl');$$('.ds').forEach(function(x){x.classList.toggle('hl',on&&x===s);x.classList.toggle('dim',on&&x!==s);});
 $$('#hlist li[data-code]').forEach(function(li){li.classList.toggle('hl',on&&li.dataset.code===code);if(on&&li.dataset.code===code)li.scrollIntoView({block:'nearest',behavior:RM?'auto':'smooth'});});
 buzz();});});}
function closeSheet(){var s=document.querySelector('.sheet'),b=document.querySelector('.sheetbg');if(!s)return;
 s.classList.remove('on');b.classList.remove('on');setTimeout(function(){s.remove();b.remove();},RM?0:280);}
function sheet(){$$('a[data-sheet]').forEach(function(a){if(a.dataset.b)return;a.dataset.b='1';a.addEventListener('click',function(ev){
 if(ev.metaKey||ev.ctrlKey)return;ev.preventDefault();buzz();closeSheet();
 var r0=a.getBoundingClientRect(),b=document.createElement('div');b.className='sheetbg';var s=document.createElement('div');s.className='sheet';
 s.setAttribute('role','dialog');s.setAttribute('aria-modal','true');s.setAttribute('aria-label','Detail');
 var top='<div class="grab"></div><button class="iconbtn sheetx" type="button" aria-label="Close">&times;</button>';
 s.innerHTML=top+'<div class="sheetsk"><div class="skel s"></div><div class="skel"></div><div class="skel"></div></div>';
 document.body.appendChild(b);document.body.appendChild(s);b.addEventListener('click',closeSheet);
 function bindX(){s.querySelector('.sheetx').addEventListener('click',closeSheet);}bindX();
 if(!RM&&s.animate){var gh=document.createElement('div');gh.className='ghost';gh.innerHTML=a.innerHTML;
  gh.style.left=r0.left+'px';gh.style.top=r0.top+'px';gh.style.width=r0.width+'px';gh.style.height=r0.height+'px';document.body.appendChild(gh);
  var ty=window.innerHeight*0.12+24-r0.top,sx=Math.min(1.04,(Math.min(window.innerWidth,760)-32)/Math.max(r0.width,1));
  gh.animate([{transform:'translate(0,0) scale(1)',opacity:1},{transform:'translate(0,'+ty+'px) scale('+sx+')',opacity:0}],
   {duration:420,easing:'cubic-bezier(.34,1.4,.64,1)'}).onfinish=function(){gh.remove();};}
 var y0=null,dy=0;s.addEventListener('touchstart',function(e){y0=s.scrollTop===0?e.touches[0].clientY:null;dy=0;},{passive:true});
 s.addEventListener('touchmove',function(e){if(y0===null)return;dy=e.touches[0].clientY-y0;if(dy>0){s.classList.add('dragging');s.style.transform='translateY('+dy+'px)';}},{passive:true});
 s.addEventListener('touchend',function(){s.classList.remove('dragging');s.style.transform='';if(y0!==null){if(dy>90)closeSheet();else if(dy<-50){s.classList.add('full');buzz();}}y0=null;});
 requestAnimationFrame(function(){b.classList.add('on');s.classList.add('on');});
 fetch(a.href,{credentials:'same-origin'}).then(function(r){return r.text();}).then(function(t){
  var doc=new DOMParser().parseFromString(t,'text/html'),m=doc.getElementById('main');if(!m){location.href=a.href;return;}
  if(!s.parentNode)return;s.innerHTML=top+m.innerHTML;bindX();charts(s);rings();tips(s);bench(s);
 }).catch(function(){location.href=a.href;});});});}
// smooth path (monotone cubic) for the chart line and area
function smooth(P){if(P.length<3)return P.map(function(p,i){return (i?'L':'M')+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
 var d='M'+P[0][0].toFixed(1)+','+P[0][1].toFixed(1);for(var i=0;i<P.length-1;i++){var p0=P[i>0?i-1:i],p1=P[i],p2=P[i+1],p3=P[i+2<P.length?i+2:i+1];
  var c1x=p1[0]+(p2[0]-p0[0])/6,c1y=p1[1]+(p2[1]-p0[1])/6,c2x=p2[0]-(p3[0]-p1[0])/6,c2y=p2[1]-(p3[1]-p1[1])/6;
  d+=' C'+c1x.toFixed(1)+','+c1y.toFixed(1)+' '+c2x.toFixed(1)+','+c2y.toFixed(1)+' '+p2[0].toFixed(1)+','+p2[1].toFixed(1);}return d;}
function fd(t){return new Date(t*864e5).toLocaleDateString('en-AU',{day:'2-digit',month:'short',year:'2-digit',timeZone:'UTC'});}
function charts(root){
 $$('[data-chart]',root).forEach(function(box){
  if(box.dataset.b)return;box.dataset.b='1';
  var el=document.getElementById(box.dataset.chart)||(root&&root.querySelector('#'+box.dataset.chart));if(!el)return;
  var d;try{d=JSON.parse(el.textContent);}catch(x){return;}
  var svg=box.querySelector('svg'),ranges=$$('[data-range]',box),tip=box.querySelector('.ctip');
  var W=340,H=190,pl=34,pr=8,pt=10,pb=22,cur=null,anim=null;
  function view(days){var pts=d.book;var last=pts[pts.length-1][0],from=days?last-days:pts[0][0];
   var b=pts.filter(function(p){return p[0]>=from;});if(b.length<2)b=pts.slice(-2);
   var b0=b[0][1],idx=(d.index||[]).filter(function(p){return p[0]>=b[0][0];}),i0=idx.length?idx[0][1]:1;
   return {bk:b.map(function(p){return [p[0],p[1]/b0*100,p[1]];}),ix:idx.map(function(p){return [p[0],p[1]/i0*100];}),b0:b0,i0:i0};}
  function rebased(nv){return {bk:d.book.map(function(p){return [p[0],p[1]/nv.b0*100,p[1]];}),
   ix:(d.index||[]).map(function(p){return [p[0],p[1]/nv.i0*100];})};}
  function scale(v){var all=v.bk.map(function(p){return p[1];}).concat(v.ix.map(function(p){return p[1];}));
   var lo=Math.min.apply(0,all),hi=Math.max.apply(0,all),pad=Math.max((hi-lo)*.12,.5);
   return {lo:lo-pad,hi:hi+pad,x0:v.bk[0][0],x1:v.bk[v.bk.length-1][0]};}
  function render(v,s){var sp=Math.max(s.x1-s.x0,1);function X(t){return pl+(t-s.x0)/sp*(W-pl-pr);}function Y(y){return pt+(s.hi-y)/(s.hi-s.lo)*(H-pt-pb);}
   var g='<defs><linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="gA0"/><stop offset="1" class="gA1"/></linearGradient><clipPath id="cp"><rect x="'+pl+'" y="0" width="'+(W-pl-pr)+'" height="'+H+'"/></clipPath></defs>';
   for(var k=0;k<4;k++){var y=s.lo+(s.hi-s.lo)*(k+.5)/4;g+='<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(y).toFixed(1)+'" y2="'+Y(y).toFixed(1)+'" class="grid"/><text x="'+(pl-4)+'" y="'+(Y(y)+3).toFixed(1)+'" class="ax" text-anchor="end">'+y.toFixed(0)+'</text>';}
   var P=v.bk.map(function(p){return [X(p[0]),Y(p[1])];}),line=smooth(P);
   var area=line+' L'+P[P.length-1][0].toFixed(1)+','+(H-pb)+' L'+P[0][0].toFixed(1)+','+(H-pb)+' Z';
   var tr='';(d.trades||[]).forEach(function(t){if(t[0]<s.x0||t[0]>s.x1)return;var near=v.bk[0];v.bk.forEach(function(p){if(Math.abs(p[0]-t[0])<Math.abs(near[0]-t[0]))near=p;});
    tr+='<circle cx="'+X(near[0]).toFixed(1)+'" cy="'+(Y(near[1])).toFixed(1)+'" r="3" class="'+(t[1]==='b'?'buyd':'selld')+'"><title>'+(t[1]==='b'?'buy':'sell')+' '+fd(t[0])+'</title></circle>';});
   svg.innerHTML=g+'<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(100).toFixed(1)+'" y2="'+Y(100).toFixed(1)+'" class="base"/>'+
    '<g clip-path="url(#cp)"><path d="'+area+'" class="area"/>'+(v.ix.length?'<path d="'+smooth(v.ix.map(function(p){return [X(p[0]),Y(p[1])];}))+'" class="s2"/>':'')+
    '<path d="'+line+'" class="s1"/>'+tr+'</g>'+'<text x="'+pl+'" y="'+(H-6)+'" class="ax">'+fd(s.x0)+'</text><text x="'+(W-pr)+'" y="'+(H-6)+'" class="ax" text-anchor="end">'+fd(s.x1)+'</text>'+
    '<g id="xh" style="display:none"><line class="xh" y1="'+pt+'" y2="'+(H-pb)+'"/><circle class="xd" r="4.5"/></g>';
   cur={v:v,s:s,X:X,Y:Y};}
  function draw(days){var nv=view(days),ns=scale(nv);
   if(RM||!cur){render(nv,ns);return;}var os=cur.s,t0=null,full=rebased(nv);cancelAnimationFrame(anim);
   function step(t){if(!t0)t0=t;var p=Math.min((t-t0)/320,1),q=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;
    var s={lo:os.lo+(ns.lo-os.lo)*q,hi:os.hi+(ns.hi-os.hi)*q,x0:os.x0+(ns.x0-os.x0)*q,x1:os.x1+(ns.x1-os.x1)*q};
    if(p<1){render(full,s);anim=requestAnimationFrame(step);}else render(nv,ns);}
   anim=requestAnimationFrame(step);}
  function at(ev){if(!cur)return;var r=svg.getBoundingClientRect(),cx=((ev.touches?ev.touches[0].clientX:ev.clientX)-r.left)/r.width*W;
   var s=cur.s,v=cur.v,t=s.x0+(cx-pl)/(W-pl-pr)*Math.max(s.x1-s.x0,1),best=v.bk[0];
   v.bk.forEach(function(p){if(Math.abs(p[0]-t)<Math.abs(best[0]-t))best=p;});var ib=null;v.ix.forEach(function(p){if(p[0]<=best[0])ib=p;});
   var g=svg.querySelector('#xh');g.style.display='';var xx=cur.X(best[0]),yy=cur.Y(best[1]);
   var ln=g.querySelector('line');ln.setAttribute('x1',xx);ln.setAttribute('x2',xx);var c=g.querySelector('circle');c.setAttribute('cx',xx);c.setAttribute('cy',yy);
   if(tip){var ch=best[1]-100,gap=ib?best[1]-ib[1]:null;
    tip.innerHTML='<div class="sub">'+fd(best[0])+'</div><b>A$'+best[2].toLocaleString('en-AU',{maximumFractionDigits:0})+'</b> <span class="'+(ch>=0?'up':'down')+'">'+(ch>=0?'▲ +':'▼ −')+Math.abs(ch).toFixed(1)+'%</span>'+
     (ib?'<div>'+d.label+' '+(ib[1]>=100?'+':'−')+Math.abs(ib[1]-100).toFixed(1)+'%</div><div>gap <b class="'+(gap>=0?'up':'down')+'">'+(gap>=0?'▲ +':'▼ −')+Math.abs(gap).toFixed(1)+' pts</b></div>':'');
    tip.classList.add('on');var bw=box.getBoundingClientRect().width,px=xx/W*bw;tip.style.left=Math.max(0,Math.min(px-80,bw-170))+'px';}
   if(ev.cancelable&&ev.touches)ev.preventDefault();}
  function off(){var g=svg.querySelector('#xh');if(g)g.style.display='none';if(tip)tip.classList.remove('on');}
  svg.addEventListener('mousemove',at);svg.addEventListener('touchstart',at,{passive:false});svg.addEventListener('touchmove',at,{passive:false});
  svg.addEventListener('mouseleave',off);svg.addEventListener('touchend',function(){setTimeout(off,1500);});
  ranges.forEach(function(r){r.addEventListener('click',function(ev){ev.preventDefault();buzz();
   ranges.forEach(function(x){x.classList.toggle('on',x===r);x.setAttribute('aria-pressed',x===r?'true':'false');});draw(+r.dataset.range);});});
  draw(0);});}
function resultToast(){var h=main.querySelector('h1');if(h&&h.textContent.trim()==='Done'){var p=main.querySelector('section p');toast(p?p.textContent.replace(/^OK\s*/,'').slice(0,90):'Done');}}
function setup(){var box=document.getElementById('setup-ring');if(!box)return;
 var items=document.querySelectorAll('.sitem');
 function recount(){var n=0;items.forEach(function(li){var cb=li.querySelectorAll('input[data-setup-id]');
  var done=li.classList.contains('auto')?li.classList.contains('done'):(cb.length>0&&Array.prototype.every.call(cb,function(c){return c.checked;}));
  if(!li.classList.contains('auto'))li.classList.toggle('done',done);if(done)n++;});
  var t=+box.dataset.total,c=document.getElementById('setup-count');if(c)c.textContent=n+' of '+t+' done';
  var rv=box.querySelector('.rv'),b=box.querySelector('figcaption b');if(b)b.textContent=n+'/'+t;
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
  (t.closest&&t.closest('.chart,svg,[data-tips],.tmap,input,textarea,select,.seg,.msg,.cal,.tiles,table,.tscroll,[data-compare]'))){sx=null;return;}
  sx=ev.touches[0].clientX;sy=ev.touches[0].clientY;t0=Date.now();},{passive:true});
 main.addEventListener('touchend',function(ev){if(sx===null)return;var dx=ev.changedTouches[0].clientX-sx,dy=ev.changedTouches[0].clientY-sy;sx=null;
  if(Math.abs(dx)<70||Math.abs(dx)<1.6*Math.abs(dy)||Date.now()-t0>700)return;var tabs=tabList(),cur=document.body.dataset.tab,
  names=$$('.tabs .tab').map(function(a){return a.dataset.tab;}),i=names.indexOf(cur);if(i<0)return;var j=dx<0?i+1:i-1;if(j<0||j>=tabs.length)return;
  buzz();setTab(names[j]);main.classList.remove('sl','sr');void main.offsetWidth;if(!RM)main.classList.add(dx<0?'sl':'sr');go(tabs[j],true);},{passive:true});}
function tmap(){$$('[data-tmseg]').forEach(function(seg){if(seg.dataset.b)return;seg.dataset.b='1';var box=seg.parentNode.querySelector('[data-tmap]');
 $$('[data-tm]',seg).forEach(function(b){b.addEventListener('click',function(){var m=b.dataset.tm;
  $$('[data-tm]',seg).forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});
  $$('.tm',box).forEach(function(a){var i=a.querySelector('.tmi'),l=a.querySelector('.tml');i.className='tmi '+(m==='t'?a.dataset.ct:a.dataset.cs);
   if(l)l.textContent=m==='t'?a.dataset.lt:a.dataset.ls;});buzz();});});});}
function whatif(){$$('[data-whatif]').forEach(function(w){if(w.dataset.b)return;w.dataset.b='1';var d;
 try{d=JSON.parse(w.querySelector('[data-wi-data]').textContent);}catch(x){return;}
 var r=w.querySelector('input[type=range]'),lo=+w.dataset.lo,hi=+w.dataset.hi,bar=w.querySelector('[data-wi-bar]');
 function fmt(n){return 'A$'+Math.round(n).toLocaleString('en-AU');}
 function upd(){var m=+r.value/100,v=d.cash;d.h.forEach(function(h){v+=h[1]*(1+(h[2]===null?1:h[2])*m);});
  w.querySelector('[data-wi-m]').textContent=(m>0?'+':m<0?'−':'')+Math.abs(+r.value)+'%';
  w.querySelector('[data-wi-v]').textContent=fmt(v);var ch=v-d.now;
  w.querySelector('[data-wi-d]').textContent=(ch>=0?'▲ +':'▼ −')+fmt(Math.abs(ch)).replace('A$','A$');
  bar.style.width=Math.max(0,Math.min(100,(v-lo)/(hi-lo)*100)).toFixed(1)+'%';
  var L=d.lines,s;if(v>=L[0][0])s='Above the A$'+(L[0][0]/1000).toFixed(0)+'k check: the loss rule stays normal.';
  else if(v>=L[1][0])s='Below the A$'+(L[0][0]/1000).toFixed(0)+'k check: the trader would ask you to review.';
  else if(v>=L[2][0])s='Below A$'+(L[1][0]/1000).toFixed(0)+'k: new buys would pause (loss rule L11).';
  else s='Below A$'+(L[2][0]/1000).toFixed(0)+'k: the loss rule would stop the line.';
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
  if(leg){leg.textContent='';ser.forEach(function(s){var k=document.createElement('span');k.className='key k-'+s.c;leg.appendChild(k);leg.appendChild(document.createTextNode(s.k+' '));});
   leg.appendChild(document.createTextNode('· 100 = '+fd(t0)));}  // security review L5: names as text
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
  dots.forEach(function(d,i){d.classList.toggle('on',i===k);d.setAttribute('aria-current',i===k?'step':'false');});
  r.querySelector('[data-rprev]').disabled=k===0;r.querySelector('[data-rnext]').textContent=k===panes.length-1?'Start again':'Next ›';}
 function stop(){if(timer){clearInterval(timer);timer=null;play.textContent='▶ Play';}}
 r.querySelector('[data-rprev]').addEventListener('click',function(){stop();show(k-1);buzz();});
 r.querySelector('[data-rnext]').addEventListener('click',function(){stop();show(k===panes.length-1?0:k+1);buzz();});
 dots.forEach(function(d){d.addEventListener('click',function(){stop();show(+d.dataset.rgo);});});
 play.addEventListener('click',function(){if(timer){stop();return;}if(k===panes.length-1)show(0);play.textContent='❚❚ Pause';
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
    if(!RM)c.classList.add('bump');setTimeout(function(){c.classList.remove('bump');},600);}
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
var SIDX=null;
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
 ['orders','Orders','Each month-end decision and its orders, the calendar of decision days and cut-offs, and a replay of how a month was decided.'],
 ['inbox','Inbox','Every message from the trader: approvals, alerts and the daily report. The red badge counts unread ones.'],
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
function bumpNumbers(old){$$('.tile').forEach(function(t){var l=t.querySelector('.tl'),v=t.querySelector('.tv');if(!l||!v)return;
 var was=old[l.textContent];if(was===undefined||was===v.textContent)return;v.classList.add('bump');setTimeout(function(){v.classList.remove('bump');},700);
 var tn=v.lastChild;if(RM||!tn||tn.nodeType!==3||/%/.test(tn.textContent))return;var orig=tn.textContent,
 a=parseFloat(was.replace(/[^0-9.]/g,'')),b=parseFloat(orig.replace(/[^0-9.]/g,''));if(!isFinite(a)||!isFinite(b))return;var t0=null;
 function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/600,1),n=a+(b-a)*(1-Math.pow(1-p,3));
  tn.textContent=p<1?orig.replace(/[0-9][0-9,]*\.?[0-9]*/,n.toLocaleString('en-AU',{minimumFractionDigits:2,maximumFractionDigits:2})):orig;if(p<1)requestAnimationFrame(step);}
 requestAnimationFrame(step);});}
function tileValues(){var o={};$$('.tile').forEach(function(t){var l=t.querySelector('.tl'),v=t.querySelector('.tv');if(l&&v)o[l.textContent]=v.textContent;});return o;}
function enhance(){tmap();whatif();cal();cmp();replay();homeCards();prefs();search();swipeTabs();tips();bench();reminders();setup();badge();filters();charts();alerts();countup();rings();countdown();sorter();donut();sheet();inbox();resultToast();}
function skeleton(){main.innerHTML='<div class="skel s"></div><div class="skel"></div><div class="skel"></div>';}
function swap(html,url,push){
 var doc=new DOMParser().parseFromString(html,'text/html');var m=doc.getElementById('main');if(!m){location.href=url;return;}
 var old=push?null:tileValues();main.innerHTML=m.innerHTML;document.title=doc.title;setTab(doc.body.dataset.tab||'');
 document.body.dataset.latestInbox=doc.body.dataset.latestInbox||0;document.body.dataset.inboxIds=doc.body.dataset.inboxIds||'';document.body.dataset.refresh=doc.body.dataset.refresh||'1';
 if(push)history.pushState({},'',url);enhance();if(old)bumpNumbers(old);}
function go(url,push){main.classList.add('fade');var sk=setTimeout(skeleton,180);
 fetch(url,{credentials:'same-origin'}).then(function(r){if(!r.ok&&r.status!==404)throw r;return r.text();})
 .then(function(t){clearTimeout(sk);swap(t,url,push);if(push)window.scrollTo(0,0);})
 .catch(function(){location.href=url;}).then(function(){clearTimeout(sk);main.classList.remove('fade');
  var rb=document.getElementById('refresh');if(rb)rb.classList.remove('spin');var pt=document.getElementById('ptr');if(pt)pt.classList.remove('show','go');});}
document.addEventListener('click',function(ev){var b=ev.target.closest&&ev.target.closest('.btn');if(b)buzz();
 var a=ev.target.closest&&ev.target.closest('a[data-nav]');
 if(!a||ev.metaKey||ev.ctrlKey||a.target||a.dataset.sheet)return;var u=new URL(a.href,location.href);
 if(u.origin!==location.origin||u.pathname.indexOf('/act/')===0)return;ev.preventDefault();closeSheet();
 if(a.classList.contains('tab')){if(document.body.dataset.tab!==a.dataset.tab)buzz();setTab(a.dataset.tab);}go(u.pathname+u.search,true);});
window.addEventListener('popstate',function(){go(location.pathname+location.search,false);});
function refresh(){var rb=document.getElementById('refresh');if(rb)rb.classList.add('spin');
 if(location.pathname.indexOf('/act/')===0){location.reload();return;}go(location.pathname+location.search,false);}
var rb=document.getElementById('refresh');if(rb)rb.addEventListener('click',refresh);
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
