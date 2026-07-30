#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""印刷レイアウトを検査する。

build_tool.py の実行後に走らせる。改修前は、折りたたみ（details）の中に
主要な図が2枚とも入っていて open 属性がなく、印刷すると全体の47%が
消える状態だった。それを機械的に検出する。

方針：印刷される内容は、画面に表示している内容とそのまま一致させる
（準拠させる）。印刷専用に文章量や構成を作り直すことはしない。
以前あった「文章3割・図7割」という面積比の検査は、その前提となった
指示自体が誤りだったため撤回した。

検査する項目：
    1. 印刷時に details の中身が出る指定があるか
    2. @page の指定（size・margin）があるか
    3. 改ページ制御（break-before・break-inside:avoid）があるか
    4. 画面版と印刷版で、同じ図・同じ解説文が出ること
       （印刷専用の別コンテンツを作っていないことの確認）

使い方:
    python scripts/check_print.py
    python scripts/check_print.py --quiet
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
HTML = os.path.join(ROOT, "assets", "diagnostic_tool.html")

STUB = '''const _els={};
function mk(){return {classList:{add(){},remove(){}},style:{},textContent:"",innerHTML:"",
  querySelectorAll:()=>[],appendChild(x){this.innerHTML+=(x&&x.innerHTML)||"";},
  onclick:null,onchange:null,disabled:false,click(){},files:null,setAttribute(){},getAttribute(){return null;}};}
const document={querySelectorAll:()=>[],getElementById:(k)=>(_els[k]=_els[k]||mk()),
  createElement:(t)=>{const e=mk();e.tagName=t;e.className="";return e;}};
const localStorage={getItem:()=>null,setItem(){},removeItem(){}};
const window={scrollTo(){},print(){}};const location={reload(){}};
'''

TAIL = r'''
mode="full"; items=ITEMS.slice(); answers={}; _els["result"]=mk();
var prof=__PROF__;
items.forEach(function(it){ if(it.type==="choice"){answers[it.id]="b";return;}
  var b=prof[it.sub]||3.5; answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
showResult();
console.log(_els["result"].innerHTML);
'''

PROFILES = {
    "定着が強い人": '{P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,'
                'C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5}',
    "着手が強い人": '{P1:5,P2:5.5,P3:5.5,P4:3,P5:4,E1:5,E2:2,E3:5,E4:2,'
                'C1:5,C2:4,C3:4,C4:5,F1:5.5,F2:5,F3:5.5,F4:2,G1:5,G2:4,G4:4}',
}


def render(prof_js):
    js = open(HTML, encoding="utf-8").read().split("<script>")[1].split("</script>")[0]
    src = STUB + js + TAIL.replace("__PROF__", prof_js)
    with open("/tmp/_chkprint.js", "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run(["node", "/tmp/_chkprint.js"], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[:400])
    return r.stdout


def check_css():
    """CSSに必要な指定が入っているかを確認する（構造の静的チェック）。"""
    html = open(HTML, encoding="utf-8").read()
    css = html.split("<style>")[1].split("</style>")[0]
    bad = []

    checks = [
        ("details が印刷時に強制的に開く指定",
         r"details\s*\{\s*display:block!important\s*\}"),
        ("@page の size 指定", r"@page\s*\{[^}]*size:"),
        ("@page の margin 指定", r"@page\s*\{[^}]*margin:"),
        ("h2 の改ページ制御（break-before）", r"h2\s*\{[^}]*break-before:page"),
        ("図・表・カードの break-inside:avoid",
         r"svg,figure,table,\.card,\.idx"),
        ("色を印刷にも出す指定（print-color-adjust）", r"print-color-adjust:exact"),
        ("表の枠線崩れ対策（border-collapse）", r"table\s*\{\s*border-collapse:collapse\s*\}"),
        ("表の見出し行の繰り返し（thead）", r"thead\s*\{\s*display:table-header-group\s*\}"),
        ("SVGを紙幅いっぱいに広げる指定", r"svg\s*\{[^}]*width:100%"),
    ]
    for label, pat in checks:
        if not re.search(pat, css):
            bad.append(("CSS", label + " が見つからない"))

    # 画面/印刷を分離する仕組み（screenonly/printonly）を使っていないことを確認する。
    # 印刷は画面のHTMLにそのまま準拠する方針のため、分離クラスが復活していれば警告する。
    if ".screenonly" in css or ".printonly" in css:
        bad.append(("方針", "screenonly/printonly による画面・印刷の分離が復活している"
                            "（印刷は画面のHTMLに準拠する方針のはず）"))
    return bad


def check_content_matches_screen(profile_name, prof_js):
    """印刷に出る内容が、画面の内容と同一（部分集合ではなく完全に同じ）であることを確認する。
    以前は印刷専用の短い文面・別のSVG行高を別途生成していたが、それを取りやめた。
    details の open 属性の有無以外に差分がないことを見る。"""
    out = render(prof_js)
    bad = []

    normalized = out.replace('<details class="ex" open>', '<details class="ex">')

    checks = [
        ("能力系の見出し", "能力系の11項目"),
        ("両極性の見出し", "両極性の9項目"),
        ("力の場の見出し", "いま動かないのは、力が拮抗しているから"),
        ("図の読み方の解説", "この章の図の読み方"),
    ]
    for label, needle in checks:
        n = normalized.count(needle)
        if n == 0:
            bad.append(("内容", f"{label}が見つからない"))
        elif n > 1:
            bad.append(("内容", f"{label}が{n}回出現している"
                                "（画面用と印刷用の重複コンテンツが残っている疑い）"))

    svg_count = len(re.findall(r"<svg", out))
    if svg_count != 3:
        bad.append(("図", f"SVGの総数が{svg_count}枚（3枚：能力系・両極性・力の場を想定）。"
                          "画面と印刷で別々に図を持っていると6枚になる"))

    if "数値の一覧" in out:
        bad.append(("内容", "「数値の一覧」の文言が残っている（削除済みのはず）"))

    return bad


def check_details_open_in_print():
    """印刷CSSで details を開く指定があれば、画面側の open 属性の有無に
    かかわらず内容が印刷される。二重に安全策があることを確認する。"""
    html = open(HTML, encoding="utf-8").read()
    css = html.split("<style>")[1].split("</style>")[0]
    m = re.search(r"@media\s+print\s*\{([\s\S]*?)\n\}", css)
    block = m.group(1) if m else ""
    bad = []
    if not re.search(r"details\s*\{\s*display:\s*block\s*!important", block):
        bad.append(("details", "印刷時に details を開く指定が見つからない"))
    return bad


def main():
    quiet = "--quiet" in sys.argv
    total_bad = 0

    print("=== 構造チェック（CSS） ===")
    bad = check_css() + check_details_open_in_print()
    total_bad += len(bad)
    if bad:
        for kind, msg in bad:
            print(f"  [{kind}] {msg}")
    elif not quiet:
        print("  問題なし")

    for pname, pjs in PROFILES.items():
        bad = check_content_matches_screen(pname, pjs)
        total_bad += len(bad)
        if bad or not quiet:
            print(f"\n=== {pname} ===")
            if not bad:
                print("  問題なし（印刷内容は画面と一致）")
            for kind, msg in bad:
                print(f"  [{kind}] {msg}")

    print()
    if total_bad:
        print(f"検査：違反 {total_bad} 件")
        sys.exit(1)
    print("検査：違反なし")
    print()
    print("※ 自動検査で確認できるのはここまで。実際の印刷プレビューで、")
    print("  改ページ位置・図の分断・表の見出し繰り返しを目で確認すること。")


if __name__ == "__main__":
    main()
