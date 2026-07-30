# -*- coding: utf-8 -*-
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

# 3種類のプロフィールで生成して検証する
profiles = {
    "定着が強い人": 'var prof={P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,'
                'C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5};',
    "着手が強い人": 'var prof={P1:5,P2:5.5,P3:5.5,P4:3,P5:4,E1:5,E2:2,E3:5,E4:2,'
                'C1:5,C2:4,C3:4,C4:5,F1:5.5,F2:5,F3:5.5,F4:2,G1:5,G2:4,G4:4};',
    "平坦な人": 'var prof={};',
}

allbad = []
for name, pf in profiles.items():
    tail = '''
mode="full"; items=ITEMS.slice(); answers={}; _els["result"]=mk();
''' + pf + '''
items.forEach(function(it){ if(it.type==="choice"){answers[it.id]="b";return;}
  var b=prof[it.sub]||3.5; answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
showResult();
var txt=_els["result"].innerHTML
  .replace(/<\\/(p|li|div|dt|dd|summary|tr|h2|h3)>/g,"\\n")
  .replace(/<[^>]+>/g,"").replace(/\\n{2,}/g,"\\n");
console.log(txt);
'''
    open(_os.path.join(TMP, 'v.js'), 'w', encoding='utf-8').write(stub + js + tail)
    t = subprocess.run(['node', _os.path.join(TMP, 'v.js')], capture_output=True,
                       text=True).stdout

    bad = []
    # 1) AIっぽい定型
    for pat, label in [
        (r'はずです', 'はずです'), (r'配置です', '配置です'),
        (r'ことになります', 'ことになります'), (r'と言えます', 'と言えます'),
        (r'重要なのは', '重要なのは'), (r'必要があります', '必要があります'),
        (r'ましょう', 'ましょう'), (r'非常に', '非常に'),
        (r'することができ', 'することができ'), (r'を行(い|う)', 'を行う'),
    ]:
        for m in re.finditer(pat, t):
            bad.append(('定型', label, t[max(0, m.start()-26):m.end()+14]))
    # 2) 文が途切れている・助詞の連続
    for m in re.finditer(r'[。、]{2,}|がが|をを|のの|はは', t):
        bad.append(('誤記', m.group(), t[max(0, m.start()-24):m.end()+14]))
    # 3) 空欄や未置換
    for m in re.finditer(r'undefined|NaN|null|\[object', t):
        bad.append(('未置換', m.group(), t[max(0, m.start()-30):m.end()+18]))
    # 4) 一文が長すぎる
    for line in t.split('\n'):
        for sent in re.split(r'(?<=。)', line):
            if len(sent.strip()) >= 95:
                bad.append(('長文', str(len(sent.strip())), sent.strip()[:70]))
    if bad:
        allbad.append((name, bad))

for name, bad in allbad:
    print(f"\n===== {name} =====")
    for kind, what, ctx in bad:
        print(f"  [{kind}:{what}] …{ctx.strip()}…")

if not allbad:
    print("3種類のプロフィールとも、検出パターンに該当なし")
