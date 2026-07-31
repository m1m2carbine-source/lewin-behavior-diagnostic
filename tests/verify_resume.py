#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中断・再開（localStorage経由のresume）の検証。

resumeパスはこれまで一度もテストで実行されていなかった（gen_full.py等の
STUBはlocalStorage.getItemが常にnullを返すため、resume用IIFEは常に
早期returnしていた）。ファイル復元パスと共通化した sanitizeAnswers() が、
正常データ・旧版データ・壊れたデータのそれぞれで期待どおりに働く
（壊れたデータでは再開ボタンを出さない＝fail-closed）ことを確認する。

使い方:
    python tests/verify_resume.py
"""

import json
import os as _os
import re
import subprocess
import sys

HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(HERE, ".."))
HTML = _os.path.join(ROOT, "assets", "diagnostic_tool.html")
TMP = _os.environ.get("TMPDIR", "/tmp")

_html_text = open(HTML, encoding="utf-8").read()
_m = re.search(r'const ITEM_VERSION = "([^"]*)"', _html_text)
ITEM_VERSION = _m.group(1) if _m else "?"

JS = _html_text.split("<script>")[1].split("</script>")[0]

STUB_TMPL = '''const _els={};
function mk(){return {classList:{add(){},remove(){}},style:{},textContent:"",innerHTML:"",
  querySelectorAll:()=>[],appendChild(x){this.innerHTML+=(x&&x.innerHTML)||"";},
  onclick:null,onchange:null,disabled:false,click(){},files:null,setAttribute(){},getAttribute(){return null;}};}
const document={querySelectorAll:()=>[],getElementById:(k)=>(_els[k]=_els[k]||mk()),
  createElement:(t)=>{const e=mk();e.tagName=t;e.className="";return e;}};
const localStorage={getItem:()=>(__STORED__),setItem(){},removeItem(){}};
const window={scrollTo(){},print(){}};const location={reload(){}};
'''

TAIL = r'''
var r=document.getElementById("resume");
var out={ shown: r.style.display==="inline-block", hasOnclick: typeof r.onclick==="function" };
if(out.shown && out.hasOnclick){
  r.onclick();
  out.mode=mode; out.page=page; out.answerCount=Object.keys(answers).length;
}
console.log(JSON.stringify(out));
'''


def run(stored_text):
    """stored_text: localStorage.getItem() が返すべき生の文字列（None なら null）。"""
    stored_js = "null" if stored_text is None else json.dumps(stored_text)
    stub = STUB_TMPL.replace("__STORED__", stored_js)
    src = stub + JS + TAIL
    tmp = _os.path.join(TMP, "_resume.js")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run(["node", tmp], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(r.stderr[:400])
    return json.loads(r.stdout)


def main():
    bad = []

    # 1. 正常・版が一致するデータ → 再開ボタンが出て、押すと回答が復元される
    valid = json.dumps({"mode": "full", "answers": {"P1-1": 5, "P1-2": 4}, "page": 2,
                         "itemVersion": ITEM_VERSION})
    out = run(valid)
    if not out["shown"]:
        bad.append("正常データで再開ボタンが表示されない")
    elif out.get("answerCount") != 2:
        bad.append(f"正常データの回答復元件数が不一致: {out.get('answerCount')}（期待値2）")
    elif out.get("mode") != "full":
        bad.append(f"正常データのmodeが不一致: {out.get('mode')}")

    # 2. 版が古い（設問IDと採点方法は変わっていないため、続行するが警告する設計）
    stale = json.dumps({"mode": "full", "answers": {"P1-1": 5}, "page": 0,
                         "itemVersion": "旧バージョン（現在は存在しない）"})
    out = run(stale)
    if not out["shown"]:
        bad.append("版の古いデータで再開ボタンが表示されない（続行して警告のみ、の設計のはず）")

    # 3. JSONとして壊れているデータ → fail-closed（再開ボタンを出さない）
    out = run("{not valid json")
    if out["shown"]:
        bad.append("壊れたJSONでも再開ボタンが表示されてしまう（fail-closedになっていない）")

    # 4. answersキーが無いデータ
    out = run(json.dumps({"mode": "full", "page": 0}))
    if out["shown"]:
        bad.append("answersが無いデータでも再開ボタンが表示されてしまう")

    # 5. answersはあるが有効な項目が1件もない（範囲外の値・存在しないID）
    out = run(json.dumps({"mode": "full", "answers": {"P1-1": 99, "NOT-A-REAL-ID": 3}, "page": 0}))
    if out["shown"]:
        bad.append("有効回答が0件のデータでも再開ボタンが表示されてしまう")

    # 6. データが無い（localStorageが空、通常時の初回アクセス）
    out = run(None)
    if out["shown"]:
        bad.append("保存データが無いのに再開ボタンが表示されてしまう")

    for msg in bad:
        print(f"  [不一致] {msg}")
    print()
    if bad:
        print(f"検査：違反 {len(bad)} 件")
        sys.exit(1)
    print("検査：違反なし")


if __name__ == "__main__":
    main()
