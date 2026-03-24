#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-timeline}"
OUT_DIR="${2:-outputs/cnn-fear-greed}"
LOCAL_HTML="$OUT_DIR/cnn-fear-greed-page.html"

case "$MODE" in
  timeline)
    TAB_LABEL="Timeline"
    VIEWPORT="$OUT_DIR/cnn-fear-greed-timeline-widget.png"
    FINAL="$OUT_DIR/cnn-fear-greed-timeline-widget-only.png"
    SCROLL_Y=620
    ;;
  overview)
    TAB_LABEL="Overview"
    VIEWPORT="$OUT_DIR/cnn-fear-greed-overview-widget.png"
    FINAL="$OUT_DIR/cnn-fear-greed-overview-widget-only.png"
    SCROLL_Y=620
    ;;
  *)
    echo "Unsupported mode: $MODE" >&2
    exit 2
    ;;
esac

mkdir -p "$OUT_DIR"
python skills/cnn-fear-greed-index/scripts/save_local_page.py "$LOCAL_HTML"

agent-browser close || true
agent-browser --session cnn-fng-local open "file://$(pwd)/$LOCAL_HTML"
agent-browser --session cnn-fng-local wait 3000
agent-browser --session cnn-fng-local eval '(() => { const agree = [...document.querySelectorAll("a,button,input")].find(el => /agree/i.test((el.innerText || el.value || "").trim())); if (agree) { agree.click(); return {agree:true}; } return {agree:false}; })()' || true
agent-browser --session cnn-fng-local wait 1200
agent-browser --session cnn-fng-local eval "(() => { const label = ${TAB_LABEL@Q}; const el = [...document.querySelectorAll('div,button,a,span')].find(n => (n.textContent || '').trim() === label); if (!el) return {tab:false, label}; el.click(); return {tab:true, label, tag:el.tagName, cls:el.className}; })()"
agent-browser --session cnn-fng-local wait 1200
agent-browser --session cnn-fng-local eval "window.scrollTo(0, $SCROLL_Y); ({scrollY: window.scrollY, h: window.innerHeight, w: window.innerWidth})"
agent-browser --session cnn-fng-local wait 800
agent-browser --session cnn-fng-local screenshot "$VIEWPORT"
python skills/cnn-fear-greed-index/scripts/crop_timeline_widget.py --mode "$MODE" "$VIEWPORT" "$FINAL"

printf '%s\n' "$FINAL"
