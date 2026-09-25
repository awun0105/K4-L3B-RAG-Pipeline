"""Theme tokens and presentation styles for UniGuide AI."""

APP_CSS = """
<style>
:root {
  --bg: #f7f8fc; --surface: #ffffff; --ink: #152238; --muted: #65748a;
  --accent: #2759d6; --accent-soft: #edf2ff; --line: #e4e9f2;
  --nav: #12213b; --nav-muted: #afbed4; --success: #16855d;
  --radius: 14px; --radius-sm: 9px;
}
html, body, [class*="css"] { font-family: "Segoe UI", ui-sans-serif, system-ui, sans-serif; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--bg); color: var(--ink); }
header[data-testid="stHeader"] { display:block!important; height:0!important; min-height:0!important; background:transparent!important; pointer-events:none!important; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none!important; }
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"] { display:flex!important; position:fixed!important; top:12px!important; left:12px!important; z-index:100000!important; pointer-events:auto!important; background:#fff!important; color:var(--accent)!important; border:1px solid #d8e1f4!important; border-radius:50%!important; box-shadow:0 2px 8px rgba(23,42,78,.15)!important; }
[data-testid="stSidebarCollapseButton"] svg, [data-testid="stSidebarCollapsedControl"] svg { fill:var(--accent)!important; }
[data-testid="stSidebar"] { background:var(--nav); border:0; }
[data-testid="stSidebar"][aria-expanded="false"]{min-width:340px!important;transform:translateX(0)!important;box-shadow:2px 0 14px rgba(20,34,59,.10)}
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"]{width:340px!important}
[data-testid="stSidebar"] * { color:#f4f7fc; }
[data-testid="stSidebar"] .stButton button { background:transparent; border:1px solid #3a4b67; color:#e5ebf5; border-radius:var(--radius-sm); min-height:2.45rem; font-weight:600; }
[data-testid="stSidebar"] .stButton button:hover { background:#203552; border-color:#6784b4; }
.block-container { max-width: 1360px; padding: 1.5rem 2.5rem 6.5rem!important; }
.brand-kicker { color:#8ab4ff; font-size:.68rem; font-weight:700; letter-spacing:.1em; margin:2.6rem 0 .55rem; }
.brand-name { color:#fff; font-size:1.35rem; font-weight:750; letter-spacing:-.03em; }
.brand-copy { color:var(--nav-muted); font-size:.82rem; line-height:1.6; margin:.55rem 0 1.7rem; }
.status-panel { border-top:1px solid #32445f; border-bottom:1px solid #32445f; padding:1rem 0; margin:1.2rem 0; color:var(--nav-muted); font-size:.75rem; line-height:1.75; }
.top-k-panel{margin:1.4rem 0 .25rem;padding:0}.top-k-title{color:#fff;font-size:.82rem;font-weight:700}.top-k-copy{color:var(--nav-muted);font-size:.72rem;line-height:1.5;margin-top:.2rem}[data-testid="stSidebar"] [data-testid="stSlider"]{padding:.1rem 0 .55rem}[data-testid="stSidebar"] [data-testid="stSlider"] label{color:#fff!important;font-size:.82rem!important;font-weight:700!important}[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]{background:#fff!important;border-color:#fff!important}
.status-panel strong { color:#fff; font-weight:650; }.status-panel .ready { color:#75d6ad; }.status-panel .limited { color:#ffd27d; }
.side-summary { color:var(--nav-muted); font-size:.75rem; line-height:1.75; margin:1.25rem 0; }
[data-testid="stSidebar"] [data-testid="stExpander"] { background:#1a2d4b; border:1px solid #32445f; border-radius:var(--radius-sm); }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { font-size:.79rem; font-weight:600; }
.app-header { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; padding:1.05rem 1.2rem; border:1px solid var(--line); border-radius:var(--radius); background:var(--surface); }
.app-header h1 { font-size:1.12rem; letter-spacing:-.03em; margin:0 0 .28rem; }.app-header p { color:var(--muted); font-size:.82rem; margin:0; }
.header-status { color:var(--accent); background:var(--accent-soft); border-radius:999px; padding:.36rem .65rem; font-size:.7rem; font-weight:650; white-space:nowrap; }
.welcome { padding:3.6rem 0 1.8rem; }.welcome-label { color:var(--accent); font-size:.72rem; font-weight:700; }.welcome h2 { font-size:clamp(2rem,4.4vw,3.5rem); line-height:1.12; letter-spacing:-.055em; max-width:670px; margin:.7rem 0 .9rem; }.welcome p { max-width:570px; color:var(--muted); line-height:1.7; margin:0; }
.section-label { color:#65748a; font-size:.78rem; font-weight:700; margin:1.4rem 0 .7rem; }
.suggestion-button button { min-height:120px; text-align:left; white-space:pre-wrap; background:var(--surface)!important; color:var(--ink)!important; border:1px solid var(--line)!important; border-radius:var(--radius)!important; padding:1rem 1.1rem!important; box-shadow:none!important; font-size:.82rem!important; line-height:1.55!important; }
.suggestion-button button:hover { border-color:#9cb5f3!important; background:#fbfcff!important; box-shadow:0 5px 14px rgba(34,72,150,.08)!important; transform:translateY(-1px); }
.user-row { display:flex; justify-content:flex-end; margin:1.8rem 0 1.4rem; }.user-bubble { max-width:72%; background:var(--accent); color:#fff; padding:.8rem 1rem; border-radius:var(--radius) var(--radius) 4px var(--radius); font-size:.91rem; line-height:1.55; }
.assistant-turn { margin:1.35rem 0 2.4rem; max-width:980px; }.assistant-label { color:var(--accent); font-size:.72rem; font-weight:750; letter-spacing:.06em; margin-bottom:.45rem; }.assistant-label i { font-style:normal; margin-right:.25rem; }.answer-copy { font-size:.97rem; line-height:1.8; color:#25344b; }.citation { color:var(--accent); background:var(--accent-soft); border-radius:5px; padding:.05rem .3rem; font-size:.75em; font-weight:700; text-decoration:none; }.refusal { margin-top:.9rem; padding:.8rem .9rem; background:#fff6e8; border-radius:var(--radius-sm); color:#995c10; font-size:.8rem; }[data-testid="stVerticalBlockBorderWrapper"]{background:var(--surface);border-color:var(--line)!important;border-radius:var(--radius)!important;box-shadow:0 6px 18px rgba(34,56,95,.05)}
.evidence { display:flex; align-items:baseline; gap:.65rem; flex-wrap:wrap; margin:1.5rem 0 .55rem; }.evidence b { color:#34445e; font-size:.77rem; }.evidence small { color:#8490a2; font-size:.7rem; }
.source-card { display:grid; grid-template-columns:32px minmax(0,1fr); gap:.7rem; padding:1rem 0; border-top:1px solid var(--line); }.source-no { color:var(--accent); background:var(--accent-soft); width:26px; height:26px; display:grid; place-items:center; border-radius:7px; font-size:.7rem; font-weight:700; }.source-kicker { color:#8a96a8; font-size:.64rem; letter-spacing:.08em; }.source-title { font-size:.88rem; font-weight:700; margin:.22rem 0; overflow-wrap:anywhere; }.source-file,.source-meta { color:#7c899c; font-size:.7rem; overflow-wrap:anywhere; }.snippet { color:#5c6b80; font-size:.79rem; line-height:1.6; margin:.55rem 0; }.mock { color:#9a6414; background:#fff1d7; padding:.1rem .28rem; border-radius:4px; font-size:.58rem; }
.source-card + [data-testid="stExpander"] { margin:-.25rem 0 .75rem 2.45rem; border:0; background:transparent; }.source-card + [data-testid="stExpander"] summary { color:var(--accent); font-size:.75rem; }
[data-testid="stChatInput"] { max-width:1060px; left:50%; transform:translateX(-50%); padding:0 2rem 1rem; background:transparent!important; } [data-testid="stChatInput"] textarea { background:#fff!important; border:1px solid #d8e1ee!important; border-radius:var(--radius)!important; box-shadow:0 5px 18px rgba(24,43,79,.10)!important; color:var(--ink)!important; }
@media(max-width:800px) { [data-testid="stSidebar"][aria-expanded="false"]{min-width:0!important;transform:translateX(-100%)!important;box-shadow:none}[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"]{width:auto!important}.block-container { padding:1.2rem 1rem 6rem!important; }.app-header{padding-left:2.6rem}.header-status{display:none}.welcome{padding:2.5rem 0 1.35rem}.welcome h2{font-size:2.25rem}.user-bubble{max-width:91%}.source-card{grid-template-columns:29px minmax(0,1fr)}[data-testid="stChatInput"]{padding:0 1rem 1rem}.suggestion-button button{min-height:105px} }
</style>
"""

DARK_OVERRIDE = """
<style>
:root{--bg:#101826;--surface:#172235;--ink:#edf3ff;--muted:#b1bdd0;--accent:#89aaff;--accent-soft:#1c315d;--line:#2a3850}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stBottom"],[data-testid="stBottomBlockContainer"]{background:var(--bg)!important;color:var(--ink)}.app-header{border-color:var(--line)}.app-header h1,.welcome h2,.answer-copy{color:var(--ink)}.welcome p,.snippet{color:var(--muted)}.suggestion-button button{background:var(--surface)!important;color:var(--ink)!important;border-color:var(--line)!important}.suggestion-button button:hover{border-color:#7599f5!important;background:#1b2a43!important}.source-card{border-color:var(--line)}.source-title{color:var(--ink)}.source-file,.source-meta{color:#aab8cc}.citation{color:#c7d7ff;background:var(--accent-soft)}.evidence b{color:#d7e1f1}[data-testid="stVerticalBlockBorderWrapper"]{background:var(--surface);box-shadow:none}[data-testid="stChatInput"] textarea{background:var(--surface)!important;color:var(--ink)!important;border-color:#344865!important}[data-testid="stChatInput"] textarea::placeholder{color:#aab8cc!important;opacity:1}[data-testid="stExpander"]{background:var(--surface)!important;border-color:var(--line)!important}
</style>
"""
