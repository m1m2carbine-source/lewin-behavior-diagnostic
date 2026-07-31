# -*- coding: utf-8 -*-
"""指定した見出し文字列が、閉じた<details>（open属性なし）の中にあるかを
   タグの深さを正確に数えて判定する。単純なlastIndexOfでは入れ子で誤判定するため。
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

BASE = ROOT + '/'
h = open(BASE + 'assets/diagnostic_tool.html', encoding='utf-8').read()
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
console.log(_els["result"].innerHTML);
'''
open(_os.path.join(TMP, 'av.js'), 'w', encoding='utf-8').write(stub + js + tail)
out = subprocess.run(['node', _os.path.join(TMP, 'av.js')], capture_output=True, text=True, encoding='utf-8').stdout


def extract_div(html, cls):
    """指定クラスのdivを深さを数えて取り出す。
    現在は画面・印刷を分離していないため、この関数は使っていない。
    分離構造が復活した場合の判定用に残している。"""
    marker = '<div class="' + cls + '">'
    start = html.find(marker)
    if start < 0:
        return None
    i = start + len(marker)
    depth = 1
    while depth and i < len(html):
        o = html.find('<div', i)
        c = html.find('</div>', i)
        if c == -1:
            break
        if o != -1 and o < c:
            depth += 1
            i = o + 4
        else:
            depth -= 1
            i = c + 6
    return html[start:i]


# 画面と印刷は同一のHTMLに準拠しており、.screenonly のような
# 分離用divは存在しない。そのため出力全体をそのまま検査対象にする。
# （分離構造が復活していた場合は、その中身だけを対象にする）
screen = extract_div(out, 'screenonly') or out


def is_inside_closed_details(html, needle):
    """needleの直前までのタグを走査し、開いたまま閉じられていない
    <details（openなし）>があるかを、開閉のスタックで正確に判定する。"""
    idx = html.find(needle)
    if idx < 0:
        return None, -1
    stack = []
    i = 0
    while i < idx:
        o = html.find('<details', i)
        c = html.find('</details>', i)
        if o != -1 and o < idx and (c == -1 or o < c):
            tag_end = html.find('>', o)
            tag = html[o:tag_end + 1]
            stack.append('open' in tag)
            i = tag_end + 1
        elif c != -1 and c < idx:
            if stack:
                stack.pop()
            i = c + len('</details>')
        else:
            break
    closed_ancestors = [x for x in stack if not x]
    return (len(closed_ancestors) > 0), idx


for label in ['能力系の11項目', '両極性の9項目', 'この章の図の読み方',
              '組み合わせて見える6つの指標を見る', '特徴の一覧（優劣ではないもの）を見る']:
    inside, idx = is_inside_closed_details(screen, label)
    print(f"「{label}」: 位置{idx}　"
          f"{'閉じた折りたたみの中（非表示）' if inside else '常時表示' if inside is False else '見つからない'}")

print()
print("画面版のsvg数:", screen.count('<svg'))
print("「数値の一覧」の残存:", '数値の一覧' in out)
