# -*- coding: utf-8 -*-
"""重複整理で理論的に重要な記述が落ちていないかを確認する。"""
import os as _os
import sys as _sys

# プロジェクトルートを、このファイルの位置から求める（環境非依存）
_HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(_HERE, '..'))
# 一時ファイルの置き場。環境変数 TMPDIR があればそれに従う
TMP = _os.environ.get('TMPDIR', '/tmp')
_os.makedirs(TMP, exist_ok=True)

import re
import subprocess

h = open(_os.path.join(ROOT, 'assets', 'diagnostic_tool.html'),
         encoding='utf-8').read()
js = h.split('<script>')[1].split('</script>')[0]

stub = '''const _els={};
function mk(){return {classList:{add(){},remove(){}},style:{},textContent:"",innerHTML:"",
  querySelectorAll:()=>[],appendChild(x){this.innerHTML+=(x&&x.innerHTML)||"";},
  onclick:null,onchange:null,disabled:false,click(){},files:null,setAttribute(){},getAttribute(){return null;}};}
const document={querySelectorAll:()=>[],getElementById:(k)=>(_els[k]=_els[k]||mk()),
  createElement:(t)=>{const e=mk();e.tagName=t;e.className="";return e;}};
const localStorage={getItem:()=>null,setItem(){},removeItem(){}};
const window={scrollTo(){},print(){}};const location={reload(){}};
'''
tail = r'''
mode="full"; items=ITEMS.slice(); answers={}; _els["result"]=mk();
var prof={P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,
  C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5};
items.forEach(function(it){ if(it.type==="choice"){answers[it.id]="b";return;}
  var b=prof[it.sub]||3.5; answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
showResult();
console.log(_els["result"].innerHTML.replace(/<[^>]+>/g," "));
'''
open(_os.path.join(TMP, 'th.js'), 'w', encoding='utf-8').write(stub + js + tail)
t = subprocess.run(['node', _os.path.join(TMP, 'th.js')], capture_output=True, text=True, encoding='utf-8').stdout

must = [
    ("B = f(P, E) の式", r"B = f\(P, E\)"),
    ("行動は人と環境の両方で決まる", r"その人と環境の両方で決まる"),
    ("緊張系（未完了が残る）", r"未完了"),
    ("要求水準（目標の高さと修正）", r"目標水準の置き方|要求水準"),
    ("誘発性（引きつける／遠ざける）", r"魅力への反応|不快な要素への感度"),
    ("障壁（迂回路）", r"迂回路"),
    ("葛藤の型", r"どちらも避けたい二択|どちらも魅力的な二択"),
    ("ミラーによる4つ目の追加", r"ミラー"),
    ("力の場（拮抗して止まる）", r"拮抗"),
    ("準定常的均衡", r"準定常的均衡"),
    ("★抑制力を減らすほうが有効", r"押し返す力を減らす|押す力を足すより"),
    ("解凍・移動・凍結（再凍結を使わない）", r"Unfreezing, Moving, Freezing"),
    ("「再凍結」は後世の語という注記", r"refreezing"),
    ("集団風土1939（子どもの集団）", r"1939"),
    ("★専制型が作業量最多", r"作業量は最も多く|作業量は最も多"),
    ("★放任型で攻撃が最多", r"攻撃的なふるまいは、実際にはこの進め方で最も多く"),
    ("集団決定の実測値", r"52%|52％"),
    ("境界人", r"境界人|複数の立場の間に立つ"),
    ("規範集団がないという限界", r"比べる相手がいません|規範集団"),
    ("EはPと切り分けられないという限界", r"環境をどう感じるかという感受性"),
    ("力の場は本来は特定の変更案の道具", r"特定の変更案"),
    ("人は場との関わりで変わる", r"場との関わりの中で変わる"),
    ("点数は本ツールの構成であるという明示", r"本ツールの構成|本ツールが構成"),
]

ng = []
for label, pat in must:
    if not re.search(pat, t):
        ng.append(label)
        print(f"  欠落 {label}")

print()
if ng:
    print(f"欠落 {len(ng)} 件")
else:
    print(f"理論上の要点 {len(must)} 件、すべて残っている")
