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

tail = r'''
mode="full"; items=ITEMS.slice(); answers={}; _els["result"]=mk();
var prof={P1:5.5,P2:5,P3:5,P4:2.5,P5:2,E1:3,E2:5,E3:2.5,E4:5,
  C1:4,C2:2.5,C3:3,C4:5,F1:5,F2:4,F3:5,F4:5,G1:2,G2:5,G4:5};
items.forEach(function(it){ if(it.type==="choice"){answers[it.id]="b";return;}
  var b=prof[it.sub]||3.5; answers[it.id]=Math.max(1,Math.min(6,Math.round(it.rev?7-b:b))); });
showResult();
var out=_els["result"].innerHTML;
// 見出しで区切って出力する
out=out.replace(/<h2[^>]*>/g,"\n@@H2@@").replace(/<h3[^>]*>/g,"\n@@H3@@");
var txt=out.replace(/<\/(p|li|div|dt|dd|summary|tr|h2|h3)>/g,"\n")
  .replace(/<[^>]+>/g,"").replace(/\n{2,}/g,"\n");
console.log(txt);
'''

open(_os.path.join(TMP, 'dump.js'), 'w', encoding='utf-8').write(stub + js + tail)
raw = subprocess.run(['node', _os.path.join(TMP, 'dump.js')], capture_output=True,
                     text=True).stdout

# 章ごとに分ける
sections = []
cur = "（冒頭）"
buf = []
for line in raw.split('\n'):
    line = line.strip()
    if not line:
        continue
    if line.startswith('@@H2@@') or line.startswith('@@H3@@'):
        if buf:
            sections.append((cur, buf))
        cur = line.replace('@@H2@@', '■ ').replace('@@H3@@', '  □ ')
        buf = []
    else:
        buf.append(line)
if buf:
    sections.append((cur, buf))

# 文単位に割って重複を探す
sent_where = {}
for name, lines in sections:
    for ln in lines:
        for sent in re.split(r'(?<=。)', ln):
            sent = sent.strip()
            if len(sent) < 12:
                continue
            sent_where.setdefault(sent, []).append(name)

print("=== 完全に同じ文が複数の章に出ている ===")
dup = 0
for sent, wheres in sent_where.items():
    uniq = sorted(set(wheres))
    if len(wheres) > 1:
        dup += 1
        print(f"\n[{len(wheres)}回] {sent[:60]}")
        for w in uniq:
            print(f"     ← {w}")
print(f"\n完全重複: {dup}件")

# 部分的な重なり（10文字以上の共通部分を持つ別章の文）
print("\n=== 章をまたいで内容が重なっている（部分一致） ===")
items_ = [(s, sorted(set(w))[0]) for s, w in sent_where.items()
          if len(set(w)) == 1]
seen = set()
cnt = 0
for i, (a, wa) in enumerate(items_):
    for b, wb in items_[i + 1:]:
        if wa == wb:
            continue
        # 共通の最長部分を雑に探す
        best = ""
        for L in range(len(a), 13, -1):
            found = False
            for st in range(0, len(a) - L + 1):
                if a[st:st + L] in b:
                    best = a[st:st + L]
                    found = True
                    break
            if found:
                break
        if len(best) >= 14:
            key = tuple(sorted([best, wa, wb]))
            if key in seen:
                continue
            seen.add(key)
            cnt += 1
            print(f"\n・共通「{best[:44]}」")
            print(f"   {wa}")
            print(f"   {wb}")
print(f"\n部分重複: {cnt}件")
