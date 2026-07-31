#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""結果画面の重複と表記ゆれを検査する。

build_tool.py の実行後に走らせる。以前、章ごとに最適な言い方・数値を
選んだ結果、同じ項目が最大4通りの呼び名と2種類の数値で登場し、
同じ結論が3つの章で繰り返される状態になった。それを機械的に防ぐ。

画面と印刷は同一のHTMLに準拠しており、別コンテンツを持たない
（印刷専用に内容を作り直すことはしない方針）。そのため、この検査は
画面・印刷の両方に共通する唯一の内容を対象にする。
印刷固有の構造（@page・改ページ・detailsを開く指定など）は
check_print.py で別途検査する。

使い方:
    python scripts/check_report.py
    python scripts/check_report.py --quiet   # 違反があるときだけ出力
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
HTML = os.path.join(ROOT, "assets", "diagnostic_tool.html")
NAMES = os.path.join(ROOT, "assets", "scale_names.json")

# 本文とみなさない章（対応表・定義集なので、専門用語や素点が出てよい）
DETAIL_SECTIONS = (
    "行動特性の内訳", "能力系の11項目", "両極性の9項目", "組み合わせて見える",
    "どこまでがレヴィンの理論か", "この診断が測れていないこと",
    "特徴の一覧", "回答の確認", "人の動かし方",
)

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
/* 画面と印刷は同一のHTMLに準拠しており、分離用のdivは存在しない。
   そのため出力全体（innerHTML）をそのまま検査対象にする。 */
var o=_els["result"].innerHTML.replace(/<h2[^>]*>/g,"\n@@").replace(/<h3[^>]*>/g,"\n@@");
console.log(o.replace(/<\/(p|li|div|dt|dd|summary|tr|h2|h3)>/g,"\n")
  .replace(/<[^>]+>/g,"").replace(/\n{2,}/g,"\n"));
'''

PROFILES = {
    "定着が強い人": '{P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,'
                'C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5}',
    "着手が強い人": '{P1:5,P2:5.5,P3:5.5,P4:3,P5:4,E1:5,E2:2,E3:5,E4:2,'
                'C1:5,C2:4,C3:4,C4:5,F1:5.5,F2:5,F3:5.5,F4:2,G1:5,G2:4,G4:4}',
    "平坦な人": '{}',
}


def render(prof_js):
    js = open(HTML, encoding="utf-8").read().split("<script>")[1].split("</script>")[0]
    src = STUB + js + TAIL.replace("__PROF__", prof_js)
    with open("/tmp/_chk.js", "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run(["node", "/tmp/_chk.js"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(r.stderr[:400])
    return r.stdout


# 「タイプ」を含んでいてもよい行（型判定とは無関係な一般的な言い回し・MBTI公式用語の引用）
ALLOWED_TYPE_LINES = (
    "リスク管理に強いタイプです",
    "予防に強いタイプです",
    "ベストフィットタイプの確認",
)


def check_static_terms():
    """showResult()の出力ではなく、生成済みHTML全体（導入画面などの静的テキストを含む）を検査する。
    4類型判定は「型」に呼び名を統一する方針だが、その方針はshowResult()の出力にしか
    及ばないため、静的HTMLに残る「タイプ」表記の再発をここで機械的に検出する。"""
    html = open(HTML, encoding="utf-8").read()
    bad = []
    for i, line in enumerate(html.split("\n"), 1):
        if "タイプ" in line and not any(a in line for a in ALLOWED_TYPE_LINES):
            bad.append(("型/タイプ表記", f"{i}行目: {line.strip()[:80]}"))

    counts = set()
    for m in re.finditer(r"(\d+)つの指標", html):
        prefix = html[max(0, m.start() - 20):m.start()]
        if "ここまでに見た" in prefix:
            continue  # 2軸のみを指す別概念（指標の総数の主張ではない）
        counts.add(int(m.group(1)))
    if len(counts) > 1:
        bad.append(("指標の総数の食い違い", f"{sorted(counts)} が混在している"))

    return bad


def split_sections(raw):
    secs, cur, buf = [], "（冒頭）", []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("@@"):
            if buf:
                secs.append((cur, buf))
            cur, buf = line[2:], []
        else:
            buf.append(line)
    if buf:
        secs.append((cur, buf))
    return secs


def is_detail(name):
    return any(d in name for d in DETAIL_SECTIONS)


def check(profile_name, prof_js, names):
    raw = render(prof_js)
    secs = split_sections(raw)
    body = [(nm, lines) for nm, lines in secs if not is_detail(nm)]
    bad = []

    # 1. 本文に専門用語が出ていないこと
    for k, tech in names["tech"].items():
        if not tech:
            continue
        for nm, lines in body:
            for ln in lines:
                if tech in ln and names["subscales"].get(k, "") not in ln:
                    bad.append(("専門用語", f"{nm}：「{tech}」（{k}）"))

    # 2. 本文に素点（1.0〜6.0）が出ていないこと
    #    閾値の表記（±1.5 など）と負の値は除く
    for nm, lines in body:
        for ln in lines:
            cleaned = re.sub(r"±\d+(\.\d+)?", "", ln)
            cleaned = re.sub(r"[-−]\d+(\.\d+)?", "", cleaned)
            for m in re.finditer(r"(?<![\d.])(\d\.\d{1,2})(?![\d])", cleaned):
                v = float(m.group(1))
                if 1.0 <= v <= 6.0:
                    bad.append(("素点", f"{nm}：{m.group(1)} … {ln[:44]}"))

    # 3. 1項目が本文で2通り以上の呼び名で出ていないこと
    for k in names["subscales"]:
        if k == "G3":
            continue
        used = set()
        main = names["subscales"][k]
        poles = names.get("poles", {}).get(k, [])
        for nm, lines in body:
            for ln in lines:
                if main in ln:
                    used.add("項目名")
                for pl in poles:
                    # 項目名と同じ行にあるなら「項目名（○○の側）」の形なので可
                    if pl in ln and main not in ln:
                        used.add(f"極:{pl}")
        if len(used) >= 2:
            bad.append(("呼び名", f"{k}：{len(used)}通り {sorted(used)}"))

    # 4. 章をまたいで14字以上一致する文がないこと（項目名の参照は除く）
    seen = {}
    for nm, lines in secs:
        for ln in lines:
            for sent in re.split(r"(?<=。)", ln):
                sent = sent.strip()
                if len(sent) >= 14:
                    seen.setdefault(sent, set()).add(nm)
    for sent, where in seen.items():
        if len(where) >= 2:
            bad.append(("重複文", f"{sorted(where)}：{sent[:44]}"))

    # 5. 打ち手の章が、十分な分量を持ち、突出して長い章に埋もれていないこと
    #    章数が多いので「打ち手より長い章がないこと」は現実的でない。
    #    打ち手が痩せていないか、突出して長い章がないかを見る。
    # 折りたたみの中（詳細）は読み手の目に最初から入らないので、
    # 分量の比較は本文の章どうしで行う。
    sizes = {nm: sum(len(x) for x in lines) for nm, lines in secs
             if not is_detail(nm)}
    act = next((v for k, v in sizes.items() if "まず何をするか" in k), 0)
    if act < 250:
        bad.append(("分量", f"打ち手の章が{act}字しかない（250字以上を想定）"))
    huge = [(k, v) for k, v in sizes.items()
            if v > act * 2.5 and "まず何をするか" not in k]
    if huge:
        top = sorted(huge, key=lambda x: -x[1])[:3]
        bad.append(("分量", "打ち手の2.5倍を超える章："
                    + "、".join(f"{k}({v}字)" for k, v in top)))

    total = sum(sizes.values())
    return bad, total


def main():
    quiet = "--quiet" in sys.argv
    names = json.load(open(NAMES, encoding="utf-8"))
    ng_total = 0

    bad = check_static_terms()
    ng_total += len(bad)
    if bad or not quiet:
        print("\n=== 静的テキスト（画面全体）===")
        if not bad:
            print("  問題なし")
        for kind, msg in bad:
            print(f"  [{kind}] {msg}")

    for pname, pjs in PROFILES.items():
        bad, total = check(pname, pjs, names)
        ng_total += len(bad)
        if bad or not quiet:
            print(f"\n=== {pname}（全体 {total}字）===")
            if not bad:
                print("  問題なし")
            for kind, msg in bad:
                print(f"  [{kind}] {msg}")
    print()
    if ng_total:
        print(f"検査：違反 {ng_total} 件")
        sys.exit(1)
    print("検査：違反なし")


if __name__ == "__main__":
    main()
