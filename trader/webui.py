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

THEME = "#0f6b4f"

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
}

CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}


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
) -> str:
    """One whole page: header (brand, PAPER/DEMO badge, refresh, settings), the body in
    ``<main>`` and the bottom tab bar. ``active`` = the tab to highlight."""
    tabs = "".join(
        f'<a href="{href}" class="tab{" on" if key == active else ""}" data-nav data-tab="{key}">'
        f"{icon(key)}<span>{e(label)}</span>"
        + ('<b class="dot" hidden></b>' if key == "inbox" else "")
        + "</a>"
        for key, href, label in TABS
    )
    head = (
        '<header class="top"><a class="brand" href="/" data-nav><span class="logo">BW</span>'
        f'Big Wins</a><span class="badge">{"DEMO" if demo else "PAPER"}</span>'
        '<span class="sp"></span>'
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
        f' data-refresh="{1 if refresh else 0}">'
        f'{head}<div id="ptr" class="ptr">Release to refresh</div>'
        f'<main id="main" data-title="{e(title)}">{sub}{note}{body}</main>'
        f'<nav class="tabs" aria-label="Sections">{tabs}</nav>'
        '<script src="/app.js" defer></script></body></html>'
    )


def section(title: str, body: str, cls: str = "", aside: str = "") -> str:
    head = f"<h2>{e(title)}{aside}</h2>" if title else ""
    return f'<section class="{cls}">{head}{body}</section>'


def tile(label: str, value: str, sub: str = "", tone: str = "") -> str:
    return (
        f'<div class="tile"><div class="tl">{e(label)}</div>'
        f'<div class="tv {tone}">{e(value)}</div>'
        + (f'<div class="ts">{e(sub)}</div>' if sub else "")
        + "</div>"
    )


CSS = """
:root{color-scheme:light;--bg:#f6f6f3;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;
--line:#e2e1dc;--s1:#2a78d6;--s2:#eb6834;--s3:#8a63d2;--up:#0a7a3e;--down:#c0352f;
--amber:#9a6500;--ok-bg:#e3f3e8;--amber-bg:#fbeed3;--bad-bg:#fbe1df;--brand:#0f6b4f;
--brand-ink:#fff;--tabbar:rgba(252,252,251,.94);--shadow:0 1px 2px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;
--bg:#111110;--card:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#33332f;--s1:#3987e5;
--s2:#d95926;--s3:#a487e6;--up:#4cc27a;--down:#f07a72;--amber:#e0a63a;--ok-bg:#16301f;
--amber-bg:#3a2c10;--bad-bg:#3d1714;--brand:#2fa57c;--tabbar:rgba(26,26,25,.94);
--shadow:none}}
:root[data-theme=dark]{color-scheme:dark;--bg:#111110;--card:#1a1a19;--ink:#f0efec;
--ink2:#c3c2b7;--line:#33332f;--s1:#3987e5;--s2:#d95926;--s3:#a487e6;--up:#4cc27a;
--down:#f07a72;--amber:#e0a63a;--ok-bg:#16301f;--amber-bg:#3a2c10;--bad-bg:#3d1714;
--brand:#2fa57c;--tabbar:rgba(26,26,25,.94);--shadow:none}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0 auto;background:var(--bg);color:var(--ink);font:15px/1.4 system-ui,
-apple-system,"Segoe UI",Roboto,sans-serif;padding:0 16px calc(84px + env(safe-area-inset-bottom));
max-width:640px}
a{color:var(--s1)}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;
padding:calc(10px + env(safe-area-inset-top)) 0 8px;background:var(--bg)}
.brand{font-weight:700;font-size:19px;display:flex;align-items:center;gap:8px;
color:var(--ink);text-decoration:none}
.logo{background:var(--brand);color:#fff;border-radius:8px;font-size:12px;padding:5px 6px}
.badge{border:1px solid var(--amber);color:var(--amber);border-radius:6px;font-size:11px;
font-weight:700;padding:1px 7px}.sp{flex:1}
.iconbtn{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;
border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);
cursor:pointer;padding:0}
.ic{width:20px;height:20px}
.ptr{height:0;overflow:hidden;text-align:center;color:var(--ink2);font-size:12px;
transition:height .15s}.ptr.show{height:28px;line-height:28px}
main{transition:opacity .16s ease}main.fade{opacity:.25}
.tabs{position:fixed;left:0;right:0;bottom:0;z-index:6;display:flex;justify-content:center;
background:var(--tabbar);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
border-top:1px solid var(--line);padding:6px 4px calc(6px + env(safe-area-inset-bottom))}
.tab{position:relative;flex:1;max-width:128px;display:flex;flex-direction:column;
align-items:center;gap:2px;font-size:11px;color:var(--ink2);text-decoration:none;
padding:4px 0;border-radius:10px}
.tab.on{color:var(--brand);font-weight:700}.tab .ic{width:22px;height:22px}
.dot{position:absolute;top:2px;left:calc(50% + 6px);min-width:16px;height:16px;
border-radius:8px;background:var(--down);color:#fff;font-size:10px;line-height:16px;
text-align:center;padding:0 4px}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:12px 14px;margin:12px 0;box-shadow:var(--shadow)}
h1{font-size:22px;margin:6px 0 2px}
h2{font-size:15px;margin:0 0 8px;color:var(--ink2);font-weight:600;display:flex;
align-items:center;gap:8px}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px}
.tile{border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.tl{font-size:12px;color:var(--ink2)}.tv{font-size:20px;font-weight:700}
.ts{font-size:12px;color:var(--ink2)}
.up{color:var(--up)}.down{color:var(--down)}.warn{color:var(--amber)}
.muted{color:var(--ink2)}.small,.sub{font-size:12px}.sub{color:var(--ink2)}
.chart{width:100%;height:auto;display:block;touch-action:pan-y}
.grid{stroke:var(--line);stroke-width:1}.base{stroke:var(--ink2);stroke-width:1;
stroke-dasharray:3 3;opacity:.6}.ax{fill:var(--ink2);font-size:10px}
.s1{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round}
.s2{fill:none;stroke:var(--s2);stroke-width:2;stroke-linejoin:round}
.s3{fill:none;stroke:var(--s3);stroke-width:2;stroke-linejoin:round}
.dd{fill:var(--down);opacity:.18;stroke:var(--down);stroke-width:1}
.bar{fill:var(--s2);opacity:.55}.bar.me{fill:var(--s1);opacity:1}
.d1{fill:var(--s1);stroke:var(--card);stroke-width:2}
.buyd{fill:var(--up);stroke:var(--card);stroke-width:2}
.selld{fill:var(--down);stroke:var(--card);stroke-width:2}
.xh{stroke:var(--ink2);stroke-width:1}.tip{font-size:12px;fill:var(--ink)}
.tipbox{fill:var(--card);stroke:var(--line)}
.legend{font-size:12px;color:var(--ink2);margin:4px 0}
.key{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;
margin:0 4px 0 6px}.k1{background:var(--s1)}.k2{background:var(--s2)}.k3{background:var(--s3)}
.seg{display:flex;gap:6px;margin:6px 0;flex-wrap:wrap}
.seg a,.seg button,.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);
border-radius:999px;padding:4px 12px;font-size:13px;text-decoration:none;cursor:pointer}
.seg .on,.chip.on{background:var(--brand);border-color:var(--brand);color:#fff}
table{width:100%;border-collapse:collapse}td,th{padding:6px 4px;border-top:1px solid
var(--line);vertical-align:top;text-align:left}th{font-size:12px;color:var(--ink2);
font-weight:600;border-top:0}.r{text-align:right}
.buy{color:var(--up)}.sell{color:var(--down)}
.list{list-style:none;padding:0;margin:0}.list li{padding:8px 0;border-top:1px solid
var(--line)}.list li:first-child{border-top:0}
.rowlink{display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none}
.rowlink .grow{flex:1;min-width:0}.chev{color:var(--ink2)}
.pill{font-size:12px;font-weight:700;border-radius:6px;padding:1px 6px;white-space:nowrap}
.ok{background:var(--ok-bg);color:var(--up)}.amber{background:var(--amber-bg);
color:var(--amber)}.bad{background:var(--bad-bg);color:var(--down)}
.note{background:var(--amber-bg);border-radius:8px;padding:6px 10px;font-size:13px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;border:0;
border-radius:12px;padding:12px 16px;font-size:16px;font-weight:700;cursor:pointer;
text-decoration:none;background:var(--brand);color:#fff;min-height:46px}
.btn.wide{width:100%}.btn.sec{background:var(--card);color:var(--ink);border:1px solid var(--line)}
.btn.danger{background:var(--down)}.btn.warnb{background:var(--amber)}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}
.code{font-size:28px;letter-spacing:8px;text-align:center;width:100%;padding:10px;
border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
.summary{font-size:18px;font-weight:700;margin:4px 0 8px}
.msg{border-left:4px solid var(--line);padding-left:10px}
.msg.page{border-color:var(--down)}.msg.approval{border-color:var(--amber)}
.msg.report{border-color:var(--s1)}.msg.action{border-color:var(--brand)}
.msg pre{white-space:pre-wrap;font:12px/1.35 ui-monospace,Menlo,Consolas,monospace;
margin:6px 0 0;color:var(--ink2);max-height:16em;overflow:auto}
.msg.unread .t{font-weight:700}.new{color:var(--down);font-size:11px;font-weight:700}
.tl2{list-style:none;margin:6px 0 0;padding:0 0 0 14px;border-left:2px solid var(--line)}
.tl2 li{position:relative;padding:3px 0 3px 6px;font-size:13px}
.tl2 li:before{content:"";position:absolute;left:-20px;top:8px;width:10px;height:10px;
border-radius:5px;background:var(--line)}.tl2 li.done:before{background:var(--brand)}
.tl2 li.badst:before{background:var(--down)}
.meter{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin:4px 0}
.meter b{display:block;height:100%;background:var(--brand)}
.logs{white-space:pre-wrap;font:11px/1.35 ui-monospace,Menlo,Consolas,monospace;
max-height:20em;overflow:auto;background:var(--bg);border-radius:8px;padding:8px}
label.chk{display:flex;gap:8px;align-items:center;margin:8px 0}
footer{font-size:12px;color:var(--ink2);text-align:center;margin-top:16px}
[hidden]{display:none!important}
"""

JS = r"""
(function(){
'use strict';
var main=document.getElementById('main');
function setTab(t){document.body.dataset.tab=t;document.querySelectorAll('.tab').forEach(function(a){
 a.classList.toggle('on',a.dataset.tab===t);});}
function badge(){
 var latest=+(document.body.dataset.latestInbox||0),seen=0;
 try{seen=+(localStorage.getItem('bw.seen')||0);}catch(x){}
 if(document.body.dataset.tab==='inbox'&&latest){try{localStorage.setItem('bw.seen',latest);}catch(x){}seen=latest;}
 var d=document.querySelector('.tab[data-tab=inbox] .dot');if(!d)return;
 var n=0;document.querySelectorAll('[data-inbox-id]').forEach(function(m){
  if(+m.dataset.inboxId>seen)m.classList.add('unread');});
 var cnt=+(document.body.dataset.unreadFrom||0);
 if(latest>seen){d.hidden=false;d.textContent=Math.min(latest-seen,99);}else{d.hidden=true;}
}
function filters(){
 document.querySelectorAll('[data-filter]').forEach(function(c){
  c.addEventListener('click',function(ev){ev.preventDefault();var k=c.dataset.filter;
   document.querySelectorAll('[data-filter]').forEach(function(x){x.classList.toggle('on',x===c);});
   document.querySelectorAll('[data-kind]').forEach(function(m){
    m.hidden=!(k==='all'||m.dataset.kind===k||(k==='alerts'&&m.dataset.kind==='page'));});
  });});
}
function chart(){
 document.querySelectorAll('[data-chart]').forEach(function(box){
  var el=document.getElementById(box.dataset.chart);if(!el)return;
  var d;try{d=JSON.parse(el.textContent);}catch(x){return;}
  var svg=box.querySelector('svg');var ranges=box.querySelectorAll('[data-range]');
  function draw(days){
   var pts=d.book;if(!pts.length)return;var last=pts[pts.length-1][0];
   var from=days?last-days:pts[0][0];
   var b=pts.filter(function(p){return p[0]>=from;});if(b.length<2)b=pts.slice(-2);
   var b0=b[0][1];var idx=(d.index||[]).filter(function(p){return p[0]>=b[0][0];});
   var i0=idx.length?idx[0][1]:1;
   var bk=b.map(function(p){return [p[0],p[1]/b0*100,p[1]];});
   var ix=idx.map(function(p){return [p[0],p[1]/i0*100];});
   var all=bk.map(function(p){return p[1];}).concat(ix.map(function(p){return p[1];}));
   var lo=Math.min.apply(0,all),hi=Math.max.apply(0,all),pad=Math.max((hi-lo)*.1,.5);lo-=pad;hi+=pad;
   var W=340,H=190,pl=34,pr=8,pt=10,pb=22,x0=bk[0][0],x1=bk[bk.length-1][0],sp=Math.max(x1-x0,1);
   function X(t){return pl+(t-x0)/sp*(W-pl-pr);}function Y(v){return pt+(hi-v)/(hi-lo)*(H-pt-pb);}
   function path(a){return a.map(function(p,i){return (i?'L':'M')+X(p[0]).toFixed(1)+','+Y(p[1]).toFixed(1);}).join(' ');}
   var g='';for(var k=0;k<4;k++){var v=lo+(hi-lo)*(k+.5)/4;g+='<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(v).toFixed(1)+'" y2="'+Y(v).toFixed(1)+'" class="grid"/><text x="'+(pl-4)+'" y="'+(Y(v)+3).toFixed(1)+'" class="ax" text-anchor="end">'+v.toFixed(0)+'</text>';}
   function fd(t){var dt=new Date(t*864e5);return dt.toLocaleDateString(undefined,{day:'2-digit',month:'short',year:'2-digit',timeZone:'UTC'});}
   svg.innerHTML=g+'<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(100).toFixed(1)+'" y2="'+Y(100).toFixed(1)+'" class="base"/>'+
    (ix.length?'<path d="'+path(ix)+'" class="s2"/>':'')+'<path d="'+path(bk)+'" class="s1"/>'+
    '<text x="'+pl+'" y="'+(H-6)+'" class="ax">'+fd(x0)+'</text><text x="'+(W-pr)+'" y="'+(H-6)+'" class="ax" text-anchor="end">'+fd(x1)+'</text>'+
    '<g id="xh" hidden><line class="xh" y1="'+pt+'" y2="'+(H-pb)+'"/><rect class="tipbox" rx="6" width="150" height="46"/><text class="tip"></text><text class="tip"></text><text class="tip"></text></g>';
   var xh=svg.querySelector('#xh');
   function at(ev){var r=svg.getBoundingClientRect();var cx=((ev.touches?ev.touches[0].clientX:ev.clientX)-r.left)/r.width*W;
    var t=x0+(cx-pl)/(W-pl-pr)*sp;var best=bk[0];bk.forEach(function(p){if(Math.abs(p[0]-t)<Math.abs(best[0]-t))best=p;});
    var ib=null;ix.forEach(function(p){if(p[0]<=best[0])ib=p;});
    var xx=X(best[0]);xh.hidden=false;var ln=xh.querySelector('line');ln.setAttribute('x1',xx);ln.setAttribute('x2',xx);
    var bx=Math.min(Math.max(xx-75,pl),W-pr-150);var rc=xh.querySelector('rect');rc.setAttribute('x',bx);rc.setAttribute('y',pt);
    var tx=xh.querySelectorAll('text');var lines=[fd(best[0]),'Book A$'+best[2].toLocaleString(undefined,{maximumFractionDigits:0})+' ('+(best[1]-100).toFixed(1)+'%)',
     ib?(d.label+' '+(ib[1]-100).toFixed(1)+'% · gap '+(best[1]-ib[1]).toFixed(1)+' pts'):''];
    tx.forEach(function(t,i){t.setAttribute('x',bx+8);t.setAttribute('y',pt+15+i*14);t.textContent=lines[i];});
    if(ev.cancelable&&ev.touches)ev.preventDefault();}
   svg.onmousemove=at;svg.ontouchstart=at;svg.ontouchmove=at;svg.onmouseleave=function(){xh.hidden=true;};
  }
  ranges.forEach(function(r){r.addEventListener('click',function(ev){ev.preventDefault();
   ranges.forEach(function(x){x.classList.toggle('on',x===r);});draw(+r.dataset.range);});});
  draw(0);
 });
}
function enhance(){badge();filters();chart();alerts();}
function swap(html,url,push){
 var doc=new DOMParser().parseFromString(html,'text/html');var m=doc.getElementById('main');if(!m){location.href=url;return;}
 main.innerHTML=m.innerHTML;document.title=doc.title;setTab(doc.body.dataset.tab||'');
 document.body.dataset.latestInbox=doc.body.dataset.latestInbox||0;document.body.dataset.refresh=doc.body.dataset.refresh||'1';
 if(push)history.pushState({},'',url);enhance();
}
function go(url,push){main.classList.add('fade');
 fetch(url,{credentials:'same-origin'}).then(function(r){if(!r.ok&&r.status!==404)throw r;return r.text();})
 .then(function(t){swap(t,url,push);if(push)window.scrollTo(0,0);})
 .catch(function(){location.href=url;}).then(function(){main.classList.remove('fade');});}
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a[data-nav]');
 if(!a||ev.metaKey||ev.ctrlKey||a.target)return;var u=new URL(a.href,location.href);
 if(u.origin!==location.origin||u.pathname.indexOf('/act/')===0)return;ev.preventDefault();go(u.pathname+u.search,true);});
window.addEventListener('popstate',function(){go(location.pathname+location.search,false);});
function refresh(){if(location.pathname.indexOf('/act/')===0){location.reload();return;}go(location.pathname+location.search,false);}
var rb=document.getElementById('refresh');if(rb)rb.addEventListener('click',refresh);
setInterval(function(){if(document.visibilityState==='visible'&&document.body.dataset.refresh==='1'&&location.pathname.indexOf('/act/')!==0)refresh();},60000);
var y0=null,ptr=document.getElementById('ptr');
window.addEventListener('touchstart',function(ev){y0=window.scrollY===0?ev.touches[0].clientY:null;},{passive:true});
window.addEventListener('touchmove',function(ev){if(y0!==null&&ptr)ptr.classList.toggle('show',ev.touches[0].clientY-y0>70);},{passive:true});
window.addEventListener('touchend',function(){if(ptr&&ptr.classList.contains('show')){ptr.classList.remove('show');refresh();}y0=null;});
function alerts(){
 var b=document.getElementById('alerts-on');if(!b||b.dataset.bound)return;b.dataset.bound='1';
 var out=document.getElementById('alerts-state');
 function say(t){if(out)out.textContent=t;}
 if(!('serviceWorker' in navigator)||!('PushManager' in window)){say('This browser cannot show alerts. On iPhone: Share > Add to Home Screen first, then open Big Wins from the home screen.');b.disabled=true;return;}
 b.addEventListener('click',function(){
  Notification.requestPermission().then(function(p){if(p!=='granted'){say('Alerts are blocked. Allow notifications for Big Wins in the phone settings.');throw 0;}
   return navigator.serviceWorker.register('/sw.js',{scope:'/'});})
  .then(function(){return navigator.serviceWorker.ready;})
  .then(function(reg){var k=b.dataset.key,raw=atob(k.replace(/-/g,'+').replace(/_/g,'/')+'=='.slice(0,(4-k.length%4)%4)),arr=new Uint8Array(raw.length);
   for(var i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
   return reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:arr});})
  .then(function(sub){return fetch('/act/push/subscribe',{method:'POST',credentials:'same-origin',
   headers:{'Content-Type':'application/json','X-CSRF-Token':b.dataset.csrf},body:JSON.stringify(sub)});})
  .then(function(r){return r.text().then(function(t){say(r.ok?'Alerts are on for this phone. A test alert is on its way.':'Not saved: '+t);});})
  .catch(function(x){if(x!==0)say('Could not turn alerts on: '+x);});
 });
}
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(function(){});}
enhance();
})();
"""

SW = r"""
self.addEventListener('install',function(){self.skipWaiting();});
self.addEventListener('activate',function(ev){ev.waitUntil(self.clients.claim());});
self.addEventListener('push',function(ev){
 var d={};try{d=ev.data?ev.data.json():{};}catch(x){d={title:'Big Wins',body:ev.data?ev.data.text():''};}
 var urgent=d.kind==='page'||d.kind==='approval';
 ev.waitUntil(self.registration.showNotification(d.title||'Big Wins',{body:d.body||'',
  tag:d.tag||d.kind||'bw',renotify:urgent,requireInteraction:urgent,icon:'/icon-192.png',
  badge:'/icon-192.png',data:{url:d.url||'/inbox'}}));
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
