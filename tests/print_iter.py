# -*- coding: utf-8 -*-
"""build_tool.py を再生成→PDF化→ページごとの文字数を測る。
   ほぼ空白のページ（ページ番号だけ）がないかを検出する。
"""
import os as _os
import sys as _sys

# プロジェクトルートを、このファイルの位置から求める（環境非依存）
_HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(_HERE, '..'))
# 一時ファイルの置き場。環境変数 TMPDIR があればそれに従う
TMP = _os.environ.get('TMPDIR', '/tmp')
_os.makedirs(TMP, exist_ok=True)

import subprocess
import sys

sys.path.insert(0, _os.path.join(ROOT, 'scripts'))

subprocess.run([sys.executable, _os.path.join('scripts', 'build_tool.py')],
                cwd=ROOT, check=True)
subprocess.run(['cp', _os.path.join(ROOT, 'assets', 'diagnostic_tool.html'),
                 _os.path.join(TMP, 'tool_for_preview.html')], check=True)

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto('file://' + _os.path.join(TMP, 'tool_for_preview.html'))
    page.evaluate("""
    () => {
      mode="full"; items=ITEMS.slice(); answers={};
      const prof={P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,
        C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5};
      items.forEach(it=>{ if(it.type==="choice"){answers[it.id]="b";return;}
        const b=prof[it.sub]||3.5; answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
      document.getElementById("intro").classList.add("hide");
      showResult();
    }
    """)
    page.wait_for_timeout(150)
    page.emulate_media(media="print")
    page.pdf(path="/tmp/print_preview/iter.pdf", format="A4", print_background=True)
    b.close()

r = subprocess.run(['pdftotext', _os.path.join(TMP, 'print_preview/iter.pdf'), '-'],
                    capture_output=True, text=True)
pages = r.stdout.split('\x0c')
pages = [pg for pg in pages if pg.strip() or True]
print(f"総ページ数: {len(pages)-1 if pages and pages[-1].strip()=='' else len(pages)}")
blank = 0
for i, pg in enumerate(pages, 1):
    body = pg.replace("ページ", "").strip()
    body = ''.join(ch for ch in body if not ch.isdigit() and ch not in ' /\n')
    n = len(body)
    if pg.strip():
        flag = "  ← ほぼ空白" if n < 15 else ""
        print(f"  ページ{i}: 実質{n}字{flag}")
        if n < 15:
            blank += 1
print(f"\nほぼ空白のページ: {blank}枚")
