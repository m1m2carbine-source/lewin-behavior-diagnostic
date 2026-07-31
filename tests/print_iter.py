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

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, _os.path.join(ROOT, 'scripts'))

subprocess.run([sys.executable, _os.path.join('scripts', 'build_tool.py')],
                cwd=ROOT, check=True)
# 外部の cp コマンドは使わない。Git Bash 経由だとMSYS側の/tmpに解決され、
# Playwright（ネイティブWindowsプロセス）が file:// で参照する/tmpと
# 食い違うことがあるため、同一プロセス内で完結するshutilを使う。
preview_path = _os.path.join(TMP, 'tool_for_preview.html')
shutil.copyfile(_os.path.join(ROOT, 'assets', 'diagnostic_tool.html'), preview_path)

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    # 'file://' + パス文字列 だとWindowsではバックスラッシュ混じりの
    # URLになり解決に失敗する。Path.resolve().as_uri() でOS非依存に組み立てる。
    page.goto(Path(preview_path).resolve().as_uri())
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
    _os.makedirs(_os.path.join(TMP, 'print_preview'), exist_ok=True)
    pdf_path = _os.path.join(TMP, 'print_preview', 'iter.pdf')
    page.pdf(path=pdf_path, format="A4", print_background=True)
    b.close()

# -enc UTF-8 が無いと pdftotext は既定のテキストエンコーディング（日本語を
# 表現できない）で出力し、日本語の文字だけが無音で消える。数字やラテン文字は
# 残るため、実際は文字がぎっしり入っているページまで「ほぼ空白」と誤判定
# していた（このテストが初めて実行された今回、それに気づかず出した最初の
# 判定結果は誤りだった）。
r = subprocess.run(['pdftotext', '-enc', 'UTF-8', pdf_path, '-'],
                    capture_output=True, text=True, encoding='utf-8')
pages = r.stdout.split('\x0c')
# pdftotextは各ページの末尾に\x0cを出力するため、split結果の最後には
# 必ず空文字列の要素が1つ余分にできる（実在するページではない）。
# これだけを取り除く。以前は「pg.strip()が空でない要素だけ扱う」という
# 条件でこれを弾いていたが、その条件だと本物の空白ページ（中身が空白
# 文字だけ）まで一緒に取り除かれ、検出対象を素通りさせてしまっていた。
if pages and pages[-1] == '':
    pages.pop()
print(f"総ページ数: {len(pages)}")
blank = 0
for i, pg in enumerate(pages, 1):
    # 数字を除外していたのは「ページ番号だけの余白ページ」を弾くためだったが、
    # build_tool.py の印刷CSSはページ番号を出力しない設計（Chromiumの
    # counter(pages)が信用できないため、誤表示より非表示を選んだ）。
    # そのためこのテストで数字を除外する意味はなく、逆に力の場図・棒グラフ等
    # 数値ラベル主体のページを誤って「ほぼ空白」と判定していた。
    # 空白ページの検出は「実質的な文字数がほぼゼロか」だけを見ればよいので、
    # 空白文字だけを取り除いて数える。
    body = ''.join(ch for ch in pg if ch not in ' \t\n\r')
    n = len(body)
    flag = "  ← ほぼ空白" if n < 15 else ""
    print(f"  ページ{i}: 実質{n}字{flag}")
    if n < 15:
        blank += 1
print(f"\nほぼ空白のページ: {blank}枚")
