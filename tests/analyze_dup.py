# -*- coding: utf-8 -*-
"""同じ項目・同じ事実が、何通りの言い方で出てくるかを数える。"""
import os as _os
import sys as _sys

# プロジェクトルートを、このファイルの位置から求める（環境非依存）
_HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(_HERE, '..'))
# 一時ファイルの置き場。環境変数 TMPDIR があればそれに従う
TMP = _os.environ.get('TMPDIR', '/tmp')
_os.makedirs(TMP, exist_ok=True)

import json
import re
import subprocess

BASE = ROOT + '/'
h = open(BASE + 'assets/diagnostic_tool.html', encoding='utf-8').read()
js = h.split('<script>')[1].split('</script>')[0]

names = json.load(open(BASE + 'assets/scale_names.json', encoding='utf-8'))
SUB = names['subscales']
TECH = names['tech']
POLES = names.get('poles', {})

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
var o=_els["result"].innerHTML.replace(/<h2[^>]*>/g,"\n@@").replace(/<h3[^>]*>/g,"\n@@");
console.log(o.replace(/<\/(p|li|div|dt|dd|summary|tr|h2|h3)>/g,"\n")
  .replace(/<[^>]+>/g,"").replace(/\n{2,}/g,"\n"));
'''
open(_os.path.join(TMP, 'an.js'), 'w', encoding='utf-8').write(stub + js + tail)
raw = subprocess.run(['node', _os.path.join(TMP, 'an.js')], capture_output=True,
                     text=True).stdout

# 章に分ける
secs = []
cur, buf = "（冒頭）", []
for line in raw.split('\n'):
    line = line.strip()
    if not line:
        continue
    if line.startswith('@@'):
        if buf:
            secs.append((cur, '\n'.join(buf)))
        cur, buf = line[2:], []
    else:
        buf.append(line)
if buf:
    secs.append((cur, '\n'.join(buf)))

print("=== 1つの項目が、いくつの呼び名で出てくるか ===")
multi = 0
for k in SUB:
    if k == "G3":
        continue
    labels = {}
    cands = [("項目名", SUB[k]), ("専門用語", TECH.get(k, ""))]
    if k in POLES:
        cands += [("低い側の極", POLES[k][0]), ("高い側の極", POLES[k][1])]
    for kind, lab in cands:
        if not lab:
            continue
        where = [nm for nm, body in secs if lab in body]
        if where:
            labels[kind] = (lab, where)
    if len(labels) >= 2:
        multi += 1
        print(f"\n  {k}：{len(labels)}通り")
        for kind, (lab, where) in labels.items():
            print(f"    {kind:<10}「{lab}」→ {len(where)}章")
print(f"\n複数の呼び名を持つ項目: {multi} / 20")

print("\n=== 同じ項目に、いくつの数値が出るか ===")
# 素点（1〜6、小数1桁）と中点スコア（20〜80）の混在を調べる
for nm, body in secs:
    raw6 = re.findall(r'[^\d](\d\.\d{1,2})[^\d%]', body)
    raw6 = [x for x in raw6 if 1.0 <= float(x) <= 6.0]
    sc = re.findall(r'[^\d](\d{2}\.\d)[^\d%]', body)
    sc = [x for x in sc if 20.0 <= float(x) <= 80.0]
    if raw6 and sc:
        print(f"  {nm}：素点{len(raw6)}個 と 中点スコア{len(sc)}個 が同居")

print("\n=== 章ごとの分量 ===")
for nm, body in secs:
    t = body.replace('\n', '')
    print(f"  {len(t):>5}字  {nm}")
print(f"  {sum(len(b.replace(chr(10),'')) for _, b in secs):>5}字  合計")
