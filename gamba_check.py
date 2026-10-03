#!/usr/bin/env python3
"""GitHub Actions用: ガンバ大阪 vs セレッソ大阪(2026/11/08) の
「ガンバサポーターシート」欄を1回確認し、買えそうならiPhoneへ通知する。
環境変数: NTFY_TOPIC(必須) / WATCH_URL(任意) / DEBUG=1 で該当欄のHTMLをログ表示"""
import os
import re
import sys
import urllib.request

WATCH_URL = os.environ.get("WATCH_URL") or "https://www.jleague-ticket.jp/sales/perform/2635731/001"
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
DEBUG = os.environ.get("DEBUG") == "1"

SEAT_NAME = "ガンバサポーターシート"
SOLD_OUT_WORDS = ["完売", "売切", "売り切れ", "売りきれ", "soldout", "sold-out",
                  "sold_out", "SOLD", "販売終了", "受付終了", "在庫なし", "販売前"]

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def extract_section(html):
    """見出し(h4)に SEAT_NAME を含むブロックを、次の見出しの手前まで切り出す"""
    for m in re.finditer(r"<h4[^>]*>(.*?)</h4>", html, flags=re.S):
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if title == SEAT_NAME:
            nxt = html.find("<h4", m.end())
            end = nxt if nxt != -1 else m.end() + 4000
            return html[max(0, m.start() - 300):end]
    return None


def is_available(section):
    if section is None:
        return False
    low = section.lower()
    return not any(w.lower() in low for w in SOLD_OUT_WORDS)


def notify(url):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data="大阪ダービー ガンバサポーターシートが購入可能になった可能性があります。今すぐ確認!".encode("utf-8"),
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
    section = extract_section(html)
    if DEBUG:
        print("=== 該当欄(raw) ===")
        print(section if section else "見つかりませんでした")
        print("===================")
    if section is None:
        print("サポーターシート欄が見つかりません(ページ構造変更?)")
    elif is_available(section):
        print("空き検知 → 通知")
        notify(WATCH_URL)
    else:
        print("まだ購入不可")


if __name__ == "__main__":
    main()
