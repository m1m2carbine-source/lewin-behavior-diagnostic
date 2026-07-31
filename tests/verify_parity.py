#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score.py（Python）とbuild_tool.pyが生成するJS採点エンジンの整合性を検査する。

第1弾で見つかった classify() の境界帯しきい値バグ（素点0.15のまま／中点スケール
1.76が正しい）は、JS側とPython側を別々に手で直したバグであり、両者の出力を
突き合わせる仕組みがあれば機械的に検出できたはずだった。この検査はその安全網。

2段構えで検査する：
  1. 回答（1〜6の整数）→ subscaleScores()/subscale_scores() の一致。
     回答データはNode側で1回だけ生成し（check_report.pyのTAILと同じ変換式）、
     その同じJSONをPython側にも渡す。回答生成そのものを両言語で別々に行うと、
     丸め方の違いが比較対象に混ざってしまうため。
  2. 下位尺度の平均点（小数）→ derive()/classify() の一致。
     1のルート（実際の1〜6の回答から作る）では、同じ尺度の全項目に同じ目標値を
     与えると全項目が同じ整数に丸まってしまい、しきい値ちょうど付近の小数
     （まさに第1弾のバグが隠れていた領域）を作れない。そのため、derive()/
     classify() は下位尺度平均を直接与えて呼び出し、丸めを経由させない。

使い方:
    python tests/verify_parity.py
"""

import json
import os as _os
import re
import subprocess
import sys

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(HERE, ".."))
HTML = _os.path.join(ROOT, "assets", "diagnostic_tool.html")

# 一時ファイルの置き場。環境変数 TMPDIR があればそれに従う
TMP = _os.environ.get("TMPDIR", "/tmp")

sys.path.insert(0, _os.path.join(ROOT, "scripts"))
import score  # noqa: E402  build_tool.py実行後（items_manifest.json生成後）に import 可能

STUB = '''const _els={};
function mk(){return {classList:{add(){},remove(){}},style:{},textContent:"",innerHTML:"",
  querySelectorAll:()=>[],appendChild(x){this.innerHTML+=(x&&x.innerHTML)||"";},
  onclick:null,onchange:null,disabled:false,click(){},files:null,setAttribute(){},getAttribute(){return null;}};}
const document={querySelectorAll:()=>[],getElementById:(k)=>(_els[k]=_els[k]||mk()),
  createElement:(t)=>{const e=mk();e.tagName=t;e.className="";return e;}};
const localStorage={getItem:()=>null,setItem(){},removeItem(){}};
const window={scrollTo(){},print(){}};const location={reload(){}};
'''

ANSWER_TAIL = r'''
mode="full"; items=ITEMS.slice(); answers={};
var prof=__PROF__;
items.forEach(function(it){ if(it.type==="choice"){answers[it.id]=null;return;}
  var b=prof[it.sub]; if(b==null){answers[it.id]=null;return;}
  answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
console.log(JSON.stringify({answers:answers, scores:subscaleScores()}));
'''

DERIVE_TAIL = r'''
var s=__PROF__;
var d=derive(s);
var cls=classify(d);
console.log(JSON.stringify({derived:d, classify:cls}));
'''

# --- 1. 回答→下位尺度平均のプロファイル（丸めを経由する）---
ANSWER_PROFILES = {
    "定着が強い人": {"P1": 5.5, "P2": 5, "P3": 5, "P4": 2.5, "P5": 2, "E1": 3, "E2": 5, "E3": 2.5, "E4": 5,
                 "C1": 4, "C2": 2.5, "C3": 3, "C4": 5, "F1": 5, "F2": 4, "F3": 5, "F4": 5, "G1": 2, "G2": 5, "G4": 5},
    "着手が強い人": {"P1": 5, "P2": 5.5, "P3": 5.5, "P4": 3, "P5": 4, "E1": 5, "E2": 2, "E3": 5, "E4": 2,
                 "C1": 5, "C2": 4, "C3": 4, "C4": 5, "F1": 5.5, "F2": 5, "F3": 5.5, "F4": 2, "G1": 5, "G2": 4, "G4": 4},
    "全項目が下端（1）": {k: 1 for k in score.SCORED_SUBS},
    "全項目が上端（6）": {k: 6 for k in score.SCORED_SUBS},
    "一部尺度が欠測（P4/P5）": {"P1": 5, "P2": 5, "P3": 5, "E1": 3, "E2": 5, "E3": 2.5, "E4": 5,
                        "C1": 4, "C2": 2.5, "C3": 3, "C4": 5, "F1": 5, "F2": 4, "F3": 5, "F4": 5,
                        "G1": 2, "G2": 5, "G4": 5},
}

# --- 2. 下位尺度平均を直接与えるプロファイル（丸めを経由しない）---
# pe軸・ffb軸それぞれについて、しきい値のすぐ内側／外側になる小数を作る。
# 「ffb軸だけが境界帯」は、pe軸をはっきり非境界（約41）にしたうえで、ffb軸の
# 中点スコア差を1.2（0.15 < 1.2 < 1.76）にしてある。旧バグの素点しきい値0.15
# ではこの値は非境界（false）と判定され、正しい中点しきい値1.76では境界
# （true）と判定される差なので、スケール不一致の再発を機械的に検出できる。
DERIVE_PROFILES = {
    "定着が強い人": {"P1": 5.5, "P2": 5, "P3": 5, "P4": 2.5, "P5": 2, "E1": 3, "E2": 5, "E3": 2.5, "E4": 5,
                 "C1": 4, "C2": 2.5, "C3": 3, "C4": 5, "F1": 5, "F2": 4, "F3": 5, "F4": 5, "G2": 5},
    "着手が強い人": {"P1": 5, "P2": 5.5, "P3": 5.5, "P4": 3, "P5": 4, "E1": 5, "E2": 2, "E3": 5, "E4": 2,
                 "C1": 5, "C2": 4, "C3": 4, "C4": 5, "F1": 5.5, "F2": 5, "F3": 5.5, "F4": 2, "G2": 4},
    "境界帯ぴったり（全尺度が理論的中点3.5）": {
        "P1": 3.5, "P2": 3.5, "P3": 3.5, "P4": 3.5, "P5": 3.5, "E1": 3.5, "E2": 3.5, "E3": 3.5, "E4": 3.5,
        "C1": 3.5, "C2": 3.5, "C3": 3.5, "C4": 3.5, "F1": 3.5, "F2": 3.5, "F3": 3.5, "F4": 3.5, "G2": 3.5},
    "全尺度が下端（1、T=20クランプ）": {k: 1 for k in
        ["P1", "P2", "P3", "P4", "P5", "E1", "E2", "E3", "E4", "C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4", "G2"]},
    "全尺度が上端（6、T=80クランプ）": {k: 6 for k in
        ["P1", "P2", "P3", "P4", "P5", "E1", "E2", "E3", "E4", "C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4", "G2"]},
    "一部尺度が欠測（P4/P5がnull）": {
        "P1": 5, "P2": 5, "P3": 5, "P4": None, "P5": None, "E1": 3, "E2": 5, "E3": 2.5, "E4": 5,
        "C1": 4, "C2": 2.5, "C3": 3, "C4": 5, "F1": 5, "F2": 4, "F3": 5, "F4": 5, "G2": 5},
    "ffb軸だけが境界帯（旧しきい値0.15では検出できない値）": {
        "P1": 5.5, "P2": 5.5, "P3": 5.5, "P4": 5.5, "P5": 5.5, "E1": 2, "E2": 2, "E3": 3.5, "E4": 2,
        "C1": 4, "C2": 4, "C3": 4, "C4": 4, "F1": 3.6, "F2": 3.5, "F3": 3.6, "F4": 3.5, "G2": 3.5},
    "pe軸だけが境界帯（1.0、しきい値1.5未満）": {
        "P1": 3.585, "P2": 3.585, "P3": 3.585, "P4": 3.585, "P5": 3.585,
        "E1": 3.5, "E2": 3.5, "E3": 3.5, "E4": 3.5,
        "C1": 4, "C2": 4, "C3": 4, "C4": 4, "F1": 5, "F2": 3.5, "F3": 5, "F4": 2, "G2": 3.5},
}


def run_js(tail, profile):
    js = open(HTML, encoding="utf-8").read().split("<script>")[1].split("</script>")[0]
    src = STUB + js + tail.replace("__PROF__", json.dumps(profile))
    tmp = _os.path.join(TMP, "_parity.js")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run(["node", tmp], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(r.stderr[:400])
    return json.loads(r.stdout)


def close(a, b, tol=0.1):
    """T得点換算の丸め方式の違い（Pythonのround()は偶数丸め、JSのMath.roundは
    四捨五入）による1目盛り未満の誤差は許容し、実質的な不一致だけを検出する。"""
    if a is None or b is None:
        return a == b
    return abs(a - b) <= tol


def check_answer_profile(profile):
    js = run_js(ANSWER_TAIL, profile)
    py_scores = score.subscale_scores(js["answers"], "full")
    bad = []
    for k in score.SCORED_SUBS:
        if not close(js["scores"].get(k), py_scores.get(k)):
            bad.append(f"下位尺度{k}の素点平均: JS={js['scores'].get(k)} Python={py_scores.get(k)}")
    return bad


def check_derive_profile(profile):
    js = run_js(DERIVE_TAIL, profile)
    py_d = score.derived(profile)
    py_cls = score.classify(py_d)

    bad = []
    js_d = js["derived"]
    if not close(js_d.get("pe"), py_d.get("_pe")):
        bad.append(f"pe: JS={js_d.get('pe')} Python={py_d.get('_pe')}")
    if not close(js_d.get("ffb"), py_d.get("_ffb")):
        bad.append(f"ffb: JS={js_d.get('ffb')} Python={py_d.get('_ffb')}")
    if js_d.get("weak") != py_d.get("_weak"):
        bad.append(f"weak: JS={js_d.get('weak')} Python={py_d.get('_weak')}")
    if js_d.get("quad") != py_d.get("目標の置き方"):
        bad.append(f"quad: JS={js_d.get('quad')} Python={py_d.get('目標の置き方')}")

    tli_py = (py_d.get("仕事の持ち帰りやすさ") or {}).get("値")
    if not close(js_d.get("tli"), tli_py):
        bad.append(f"tli: JS={js_d.get('tli')} Python={tli_py}")

    aux_py = py_d.get("あわせて見るもの") or {}
    js_aux = js_d.get("aux") or {}
    if not close(js_aux.get("g2"), aux_py.get("合意して決める(G2)")):
        bad.append(f"aux.g2: JS={js_aux.get('g2')} Python={aux_py.get('合意して決める(G2)')}")
    if not close(js_aux.get("e3"), aux_py.get("迂回路を見つける(E3)")):
        bad.append(f"aux.e3: JS={js_aux.get('e3')} Python={aux_py.get('迂回路を見つける(E3)')}")

    eb_py = py_d.get("環境側の内訳") or {}
    js_eb = js_d.get("eBreak") or {}
    if not close(js_eb.get("incentive"), eb_py.get("近づきたくなるものへの反応")):
        bad.append("eBreak.incentiveが不一致")
    if not close(js_eb.get("removal"), eb_py.get("避けたくなるものへの反応")):
        bad.append("eBreak.removalが不一致")

    js_cls = js["classify"]
    py_unclassified = py_cls.get("類型") == "判定不能"
    if (js_cls is None) != py_unclassified:
        bad.append(f"classify()のnull/判定不能: JS={js_cls} Python={py_cls}")
    elif js_cls is not None:
        py_name = re.sub("（.*?）", "", py_cls["類型"])
        if py_name != js_cls["name"]:
            bad.append(f"類型名: JS={js_cls['name']} Python={py_name}")
        if bool(js_cls["border"]) != bool(py_cls["境界帯"]):
            bad.append(f"境界帯判定: JS={js_cls['border']} Python={py_cls['境界帯']}")

    return bad


def main():
    total_bad = 0

    print("--- 回答→下位尺度平均（subscaleScores/subscale_scores）---")
    for name, profile in ANSWER_PROFILES.items():
        bad = check_answer_profile(profile)
        total_bad += len(bad)
        print(f"\n=== {name} ===")
        if not bad:
            print("  問題なし")
        for msg in bad:
            print(f"  [不一致] {msg}")

    print("\n--- 下位尺度平均→導出指標・類型（derive/classify）---")
    for name, profile in DERIVE_PROFILES.items():
        bad = check_derive_profile(profile)
        total_bad += len(bad)
        print(f"\n=== {name} ===")
        if not bad:
            print("  問題なし")
        for msg in bad:
            print(f"  [不一致] {msg}")

    print()
    if total_bad:
        print(f"検査：不一致 {total_bad} 件")
        sys.exit(1)
    print("検査：不一致なし")


if __name__ == "__main__":
    main()
