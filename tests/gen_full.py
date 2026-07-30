
import os as _os
import sys as _sys

# プロジェクトルートを、このファイルの位置から求める（環境非依存）
_HERE = _os.path.dirname(_os.path.abspath(__file__))
ROOT = _os.path.normpath(_os.path.join(_HERE, '..'))
# 一時ファイルの置き場。環境変数 TMPDIR があればそれに従う
TMP = _os.environ.get('TMPDIR', '/tmp')
_os.makedirs(TMP, exist_ok=True)

h=open('assets/diagnostic_tool.html',encoding='utf-8').read()
js=h.split('<script>')[1].split('</script>')[0]
stub = '''const _els={};let LASTBLOB=null;
function mk(){return {classList:{add(){},remove(){}},style:{},textContent:"",innerHTML:"",
  querySelectorAll:()=>[],appendChild(x){this.innerHTML+=(x&&x.innerHTML)||"";},
  onclick:null,onchange:null,disabled:false,click(){},files:null,setAttribute(){},getAttribute(){return null;}};}
const document={querySelectorAll:()=>[],getElementById:(k)=>(_els[k]=_els[k]||mk()),
  createElement:(t)=>{const e=mk();e.tagName=t;e.className="";return e;}};
const localStorage={getItem:()=>null,setItem(){},removeItem(){}};
const window={scrollTo(){},print(){}};const location={reload(){}};
class Blob{constructor(p){LASTBLOB=p.join("");}}const URL={createObjectURL:()=>"x"};
class FileReader{readAsText(f){this.result=f._t;setTimeout(()=>this.onload(),0);}}
'''
tail = r'''
var pass=0,fail=0;
function check(n,c){ if(c)pass++; else {fail++; console.log("  X "+n);} }
function fill(m,g3){
  mode=m; items=ITEMS.filter(function(it){return m==="full"?true:(m==="short"?it.short:it.screen);});
  answers={}; _els["result"]=mk();
  var sd=13; var rnd=function(){sd=(sd*1103515245+12345)%2147483648;return sd/2147483648;};
  items.forEach(function(it){ answers[it.id]= it.type==="choice"?(g3||["a","b","c","d"][Math.floor(rnd()*4)]):1+Math.floor(rnd()*6); });
}
console.log("=== 3版の描画 ===");
["full","short","screening"].forEach(function(m){
  fill(m);
  try{ showResult(); check(m+"版 描画", _els["result"].innerHTML.length>800); }
  catch(e){ fail++; console.log("  X "+m+"版 例外: "+e.message); }
});
console.log("=== 新しい構成 ===");
fill("full","b"); showResult();
var out=_els["result"].innerHTML;
var hs=(out.match(/<h2[^>]*>[\s\S]*?<\/h2>/g)||[]).map(function(x){return x.replace(/<[^>]+>/g,"");});
check("最初の見出しが位置の提示", hs[0]==="いまのあなたの位置");
check("2番目が21項目の図", hs[1]==="21項目の結果（図）");
check("3番目が行動の式", hs[2]==="なぜそうなるのか　── あなたの行動の式");
check("4番目が力の場", hs[3]==="いま動かないのは、力が拮抗しているから");
check("5番目が結論", hs[4]==="ひとことでいうと");
check("6番目が打ち手", hs[5]==="この結果で、まず何をするか");
check("場面別がある", hs.indexOf("場面別に見ると")>=0);
check("反証チェックがある", out.indexOf("こんなこと、ありませんか")>=0);
check("外れの案内がある", out.indexOf("この判定は外れています")>=0);
check("呼び名がある", /最初の一人|守り手|仕掛け人|調整役/.test(out));
check("ほかの型の一覧がある", out.indexOf("ほかの3つの型")>=0);
check("組む相手の根拠がある", out.indexOf("互いの穴がちょうど噛み合う")>=0);
check("強み苦手が同格", out.indexOf('class="sw"')>=0);
check("有名人紹介は入れていない", out.indexOf("有名人")<0);
check("適職診断は入れていない", out.indexOf("適職")<0);
check("詳しい数値は後方", hs.indexOf("詳しい数値")>=4);
check("タイトルが残っている", out.indexOf("診断結果")>=0);
check("打ち手に なぜ効くか", out.indexOf("なぜあなたに効くか")>=0);
check("打ち手に 今週の一歩", out.indexOf("今週の一歩")>=0);
check("打ち手に 放置すると", out.indexOf("放置すると")>=0);
check("3か月後の確認項目", out.indexOf("3か月後に見るもの")>=0);
check("21項目の図が常時表示", out.indexOf("21項目の結果（図）")>=0);
check("数値の一覧表は出ない", out.indexOf("数値の一覧")<0);
check("指標の詳細は折りたたまれている", out.indexOf("組み合わせて見える6つの指標を見る")>=0);
console.log("=== 妥当性NG時 ===");
mode="full"; items=ITEMS.slice(); answers={}; _els["result"]=mk();
items.forEach(function(it){ answers[it.id]= it.type==="choice"?"a":5; });
showResult();
check("ブロック画面が出る", _els["result"].innerHTML.indexOf("結果の表示を見合わせています")>=0);
check("ブロック時もタイトルあり", _els["result"].innerHTML.indexOf("診断結果")>=0);
_els["forceShow"].onclick();
check("強制表示で結論が出る", _els["result"].innerHTML.indexOf("ひとことでいうと")>=0);
console.log("=== 往復 ===");
fill("full","c"); showResult();
var before=JSON.stringify(subscaleScores());
_els["dl"].onclick(); var saved=LASTBLOB;
answers={}; items=[];
_els["loadFile"].onchange({target:{files:[{_t:saved}]}});
setTimeout(function(){
  check("読み込みで復元", Object.keys(answers).length===132);
  check("採点が一致", before===JSON.stringify(subscaleScores()));
  console.log("\n合計: 合格 "+pass+" / 失敗 "+fail);
},10);
'''
open(_os.path.join(TMP, 'full.js'),'w',encoding='utf-8').write(stub+js+tail)
