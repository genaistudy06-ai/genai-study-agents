"""Builds ../Everlit.html: one offline file holding all three views.

Each source page is embedded as an <iframe srcdoc>, so their styles and scripts stay isolated.
Run:  python build.py   (from this folder, or anywhere)
"""
import json, pathlib, re, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "Everlit.html"

VIEWS = [  # (id, tab label, short label for phones, source file)
    ("executive", "Executive brief", "Brief", "executive.html"),
    ("overview", "How it works", "How it works", "overview.html"),
    ("product", "Product", "Product", "product.html"),
]

icon_svg = (HERE / "everlit-icon.svg").read_text(encoding="utf-8").strip()
ICON = "data:image/svg+xml," + urllib.parse.quote(icon_svg, safe=" =:/',;()")

# Runs inside each embedded view: sibling links switch tabs; shell messages set roadmap / theme / tour.
BRIDGE = """<script>(()=>{const P=window.parent;if(P===window)return;
const V={"executive.html":"executive","overview.html":"overview","product.html":"product"};
document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a[href]");if(!a)return;const[f,h]=a.getAttribute("href").split("#");const v=V[f];if(v){e.preventDefault();P.postMessage({everlit:"view",view:v,tour:h==="tour",anchor:h&&h!=="tour"&&h[0]!=="/"?h:null},"*");}},true);
addEventListener("message",e=>{const d=e.data||{};if(!d.everlit)return;
if(d.everlit==="roadmap"){document.documentElement.dataset.roadmap=d.on?"on":"off";}
else if(d.everlit==="anchor"){const el=document.getElementById(d.id);if(el)el.scrollIntoView();}
else if(d.everlit==="theme"||d.everlit==="tour"){dispatchEvent(new CustomEvent("everlit:"+d.everlit,{detail:d}));}});
window.__embedded=true;document.documentElement.dataset.embedded="1";})();</script>"""


def prepare(html: str) -> str:
    html = html.replace('href="everlit-icon.svg"', f'href="{ICON}"')
    # about:srcdoc base keeps #/routes and history.replaceState inside the frame
    return html.replace("<head>", '<head>\n<base href="about:srcdoc">\n' + BRIDGE, 1)


def blob(html: str) -> str:
    return json.dumps(html, ensure_ascii=False).replace("<", "\\u003c")


views = {vid: prepare((HERE / src).read_text(encoding="utf-8")) for vid, _, _, src in VIEWS}
shell = (HERE / "shell.html").read_text(encoding="utf-8")
shell = shell.replace('href="everlit-icon.svg"', f'href="{ICON}"').replace('src="everlit-icon.svg"', f'src="{ICON}"')
tabs = "".join(f'<button role="tab" data-view="{vid}" id="tab-{vid}" aria-selected="false" aria-label="{label}"><span class="tl">{label}</span><span class="ts" aria-hidden="true">{short}</span></button>' for vid, label, short, _ in VIEWS)
data = "".join(f'<script type="application/json" id="src-{vid}">{blob(html)}</script>\n' for vid, html in views.items())
shell = shell.replace("<!--TABS-->", tabs).replace("<!--VIEWS-->", data)
OUT.write_text(shell, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
