#!/usr/bin/env python3
"""ガンバ大阪 vs セレッソ大阪(2026/11/08) の「ガンバサポーターシート」が
買える状態に変わった瞬間だけ、iPhone(ntfy)へ通知する。
状態は state.txt に保存(unavailable / available)。"""
import os
import re
import sys
import urllib.request

WATCH_URL = os.environ.get("WATCH_URL") or "https://www.jleague-ticket.jp/sales/perform/2635731/001"
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = "state.txt"
SEAT_NAME = "ガンバサポーターシート"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def get_status(html):
    """席種名(h4)の直前にある状態アイコン(svg)で判定する。
    灰色(#999)の×印 = 購入不可 / それ以外(青い○など) = 購入可"""
    for m in re.finditer(r"<h4[^>]*>(.*?)</h4>", html, flags=re.S):
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if title != SEAT_NAME:
            continue
        before = html[max(0, m.start() - 1200):m.start()]
        svgs = re.findall(r"<svg.*?</svg>", before, flags=re.S)
        if not svgs:
            return "unknown", "アイコンが見つかりません"
        icon = svgs[-1]
        if "#999" in icon.lower() or "L20 17.65" in icon:
            return "unavailable", "灰色×アイコン"
        return "available", "×以外のアイコン: " + " ".join(re.findall(r'fill="([^"]+)"', icon))
    return "unknown", "席種名が見つかりません"


def read_state():
    try:
        return open(STATE_FILE).read().strip()
    except FileNotFoundError:
        return "unavailable"


def notify(url):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data="大阪ダービー ガンバサポーターシートが買える状態になりました(キャンセル/リセール)。今すぐ確認!".encode("utf-8"),
        headers={"Title": "Gamba Supporter Seat Available", "Priority": "urgent",
                 "Tags": "soccer,rotating_light", "Click": url},
    )
    urllib.request.urlopen(req, timeout=15)


def main():
    try:
        html = fetch(WATCH_URL)
    except Exception as e:
        print(f"取得エラー: {e}")
        sys.exit(0)
    status, detail = get_status(html)
    prev = read_state()
    print(f"今回={status}({detail}) / 前回={prev}")
    if status == "unknown":
        print("判定できませんでした(ページ構造が変わった可能性)。状態は更新しません")
        return
    if status == "available" and prev != "available":
        print("→ 買える状態に変化。通知します")
        notify(WATCH_URL)
    open(STATE_FILE, "w").write(status)


if __name__ == "__main__":
    main()
