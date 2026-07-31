#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/diagnostic_tool.html を生成する。項目文の唯一の正本はこのファイル。"""

import json
import os

# 項目文・採点式・尺度定義を変えるたびに上げる。HTML（JS側定数）と
# items_manifest.json の両方に、この値ひとつから注入する（単一の出典）。
ITEM_VERSION = "3"

# (id, 本文, reverse)
LIKERT = {
    "P1": [("P1-1", "途中で中断した作業のことが、別のことをしている間も繰り返し頭に浮かぶ。", 0),
           ("P1-2", "未完了の案件があると、休日でも気持ちが完全には切り替わらない。", 0),
           ("P1-3", "一度着手したことは、区切りがつくまで落ち着かない。", 0),
           ("P1-4", "やりかけの用件を思い出して、夜中や早朝に目が覚めることがある。", 0),
           ("P1-5", "締め切りまで日数があっても、着手した案件は常に意識の片隅にある。", 0),
           ("P1-6", "処理していない用件があっても、特に気にならない。", 1)],
    "P2": [("P2-1", "目標を立てるとき、確実に届く水準よりやや上を設定する。", 0),
           ("P2-2", "「できて当たり前」の水準を、周囲より高く見積もっているほうだ。", 0),
           ("P2-3", "平均的な出来では、自分としては不十分だと感じる。", 0),
           ("P2-4", "最初から確実に達成できる範囲に目標を抑えることが多い。", 1),
           ("P2-5", "一度達成した水準は、次はさらに上げないと満足できない。", 0),
           ("P2-6", "自分に課す基準は、周囲が求める基準より厳しい。", 0)],
    "P3": [("P3-1", "難しい課題ほど、やってみたいと感じる。", 0),
           ("P3-2", "挑戦の場面では、まず「成功したときの成果」を思い描く。", 0),
           ("P3-3", "失敗の可能性が頭をよぎると、着手をためらう。", 1),
           ("P3-4", "結果が読めない仕事より、確実に無難にこなせる仕事を選ぶ。", 1),
           ("P3-5", "評価される場面では、緊張よりも意欲が上回る。", 0),
           ("P3-6", "恥をかくことを避けるために、目立つ役割を辞退することがある。", 1)],
    "P4": [("P4-1", "うまくいったときは、次の目標を少し上げる。", 0),
           ("P4-2", "失敗したときは、いったん水準を下げて足場を固め直す。", 0),
           ("P4-3", "結果が悪くても、同じ高さの目標に固執してしまう。", 1),
           ("P4-4", "一度の失敗で、その目標自体をあきらめてしまう。", 1),
           ("P4-5", "実績と目標の差を、数値や具体的な事実で確認してから次を決める。", 0),
           ("P4-6", "成功しても目標は変えず、同じ水準を繰り返すことが多い。", 1)],
    "P5": [("P5-1", "仕事、家庭、趣味など、場面ごとに気持ちを切り替えられる。", 0),
           ("P5-2", "一つの領域の不調を、他の領域まで引きずることは少ない。", 0),
           ("P5-3", "役割が変わると、自分の振る舞いも自然に変わる。", 0),
           ("P5-4", "職場での出来事を、家に帰っても引きずってしまう。", 1),
           ("P5-5", "自分の中で「これはこれ、それはそれ」と線を引くのが得意だ。", 0),
           ("P5-6", "どの場面でも同じ調子で振る舞い、切り替えは苦手だ。", 1)],
    "E1": [("E1-1", "新しいものや面白そうなものに、自然と引き寄せられる。", 0),
           ("E1-2", "目に入ったものに興味を惹かれ、予定外の行動を取ることがある。", 0),
           ("E1-3", "魅力的な選択肢が現れると、すぐに気持ちが動く。", 0),
           ("E1-4", "周囲に何があっても、自分の予定どおりに動く。", 1),
           ("E1-5", "環境が整っていると、自分でも驚くほど意欲が湧く。", 0),
           ("E1-6", "「やりたくなる仕掛け」があると、行動量が明らかに増える。", 0)],
    "E2": [("E2-1", "気の進まない要素が一つあると、その場全体が嫌になる。", 0),
           ("E2-2", "苦手な相手が一人いるだけで、その場を避けたくなる。", 0),
           ("E2-3", "少しでも嫌な予感がすると、早めに手を引く。", 0),
           ("E2-4", "多少不快な条件でも、目的のためなら気にならない。", 1),
           ("E2-5", "うまくいかなさそうな空気を、周囲より早く察知する。", 0),
           ("E2-6", "苦手な作業は、着手までの時間が極端に長くなる。", 0)],
    "E3": [("E3-1", "正面から進めないとき、別のルートを探すのが得意だ。", 0),
           ("E3-2", "制約条件が多いほど、かえって工夫の余地を見つけられる。", 0),
           ("E3-3", "壁にぶつかると、そこで止まってしまうことが多い。", 1),
           ("E3-4", "「できない理由」より先に「できる方法」を挙げる。", 0),
           ("E3-5", "障害の大きさを、実際よりも大きく感じてしまう。", 1),
           ("E3-6", "迂回して目的を達したことが、これまで何度もある。", 0)],
    "E4": [("E4-1", "手順やルールが明文化されていないと落ち着かない。", 0),
           ("E4-2", "役割分担が曖昧な状況は苦手だ。", 0),
           ("E4-3", "何をしてもよい自由な状況のほうが、力を発揮できる。", 1),
           ("E4-4", "目的や評価基準が示されないと、動き出しにくい。", 0),
           ("E4-5", "前例のない案件でも、自分なりの型を作って進められる。", 1),
           ("E4-6", "指示が抽象的なときは、確認せずには進められない。", 0)],
    "C1": [("C1-1", "どちらも魅力的な選択肢があるとき、比較的すぐに決められる。", 0),
           ("C1-2", "良い候補が複数あると、決めきれずに時間だけが過ぎる。", 1),
           ("C1-3", "選んだ後に「もう一方も良かった」と引き返したくなる。", 1),
           ("C1-4", "甲乙つけがたい場面では、基準を先に決めて機械的に選ぶ。", 0),
           ("C1-5", "決定の直前で、二つの間を何度も気持ちが行き来する。", 1)],
    "C2": [("C2-1", "どちらも避けたい選択肢しかないとき、決断を先送りしてしまう。", 1),
           ("C2-2", "二択がどちらも不利なとき、第三の道を探す。", 0),
           ("C2-3", "嫌な選択を迫られると、その場から離れたくなる。", 1),
           ("C2-4", "損失が避けられない場面でも、被害の小さいほうを選べる。", 0),
           ("C2-5", "板挟みになると、何も決めないまま状況に流されることがある。", 1)],
    "C3": [("C3-1", "魅力と不安が同居する話でも、決めた後は迷いを断てる。", 0),
           ("C3-2", "目標に近づくほど不安が強まり、直前でためらう。", 1),
           ("C3-3", "やりたい気持ちと避けたい気持ちの間で、行き来が長く続く。", 1),
           ("C3-4", "利得とリスクを書き出し、条件をつけたうえで進める。", 0),
           ("C3-5", "期待が大きい案件ほど、着手が遅れる。", 1)],
    "C4": [("C4-1", "複数の要素が絡む選択でも、優先順位をつけて整理できる。", 0),
           ("C4-2", "利害が複雑に絡むと、判断そのものを避けたくなる。", 1),
           ("C4-3", "関係者の思惑が異なる場面でも、落としどころを見つけられる。", 0),
           ("C4-4", "条件が多いほど混乱し、結論が出せなくなる。", 1),
           ("C4-5", "複雑な状況は、図や表に整理してから考える習慣がある。", 0)],
    "F1": [("F1-1", "現状に問題があれば、自分から動き出す。", 0),
           ("F1-2", "誰かが言い出すのを待つより、自分が最初の一人になる。", 0),
           ("F1-3", "変えるべきだと思っても、実際に動くのは他人任せになりがちだ。", 1),
           ("F1-4", "周囲を巻き込むための働きかけを、具体的に行う。", 0),
           ("F1-5", "改善案は、口頭だけでなく文書や数字の形にして示す。", 0),
           ("F1-6", "変化を起こす提案をしたことは、ここ一年ほとんどない。", 1)],
    "F2": [("F2-1", "反対しそうな人が誰か、事前に見当がつく。", 0),
           ("F2-2", "抵抗の理由を、感情ではなく利害や不安として捉える。", 0),
           ("F2-3", "反対されると、説得するより押し通そうとする。", 1),
           ("F2-4", "変化で不利益を被る人に、あらかじめ手当てを考える。", 0),
           ("F2-5", "表立った反対より、沈黙や様子見のほうが重要な信号だと感じる。", 0),
           ("F2-6", "抵抗が表面化してから、初めてその存在に気づくことが多い。", 1)],
    "F3": [("F3-1", "長年の慣行でも、根拠が薄ければ見直しを提起できる。", 0),
           ("F3-2", "「今までこうだった」という理由には納得しない。", 0),
           ("F3-3", "既存のやり方を崩すことに、強い抵抗感がある。", 1),
           ("F3-4", "問題を可視化して、危機感を共有する働きかけができる。", 0),
           ("F3-5", "自分自身の習慣を変えるのは苦手だ。", 1),
           ("F3-6", "現状維持のコストを具体的に示して、議論を始められる。", 0)],
    "F4": [("F4-1", "変更した内容は、手順書や記録の形に落とし込む。", 0),
           ("F4-2", "一度決めたことが元に戻らないよう、仕組みで支える。", 0),
           ("F4-3", "変えた直後は良くても、しばらくすると元に戻ってしまう。", 1),
           ("F4-4", "定着したかどうかを、一定期間おいてから確認する。", 0),
           ("F4-5", "新しいやり方を、教育や訓練の形にまで展開する。", 0),
           ("F4-6", "提案はするが、その後のフォローは続かない。", 1)],
    "G1": [("G1-1", "全員が同じ意見でも、違うと思えば口に出す。", 0),
           ("G1-2", "場の空気に合わせて、発言を変えることが多い。", 1),
           ("G1-3", "少数意見の側に立つことを恐れない。", 0),
           ("G1-4", "多数派の判断は、多くの場合正しいと考える。", 1),
           ("G1-5", "自分の判断基準を、集団の基準より優先することがある。", 0)],
    "G2": [("G2-1", "重要な変更は、関係者が話し合って決めたほうが定着すると考える。", 0),
           ("G2-2", "説得するより、当事者自身に決めてもらうほうが有効だと思う。", 0),
           ("G2-3", "決定は責任者が単独で下すほうが効率的だ。", 1),
           ("G2-4", "会議では、結論そのものと同じくらい合意の過程を重視する。", 0),
           ("G2-5", "全員に発言の機会が回るよう意識している。", 0)],
    "G4": [("G4-1", "複数の立場の間に立つ役回りになることが多い。", 0),
           ("G4-2", "どの集団にも完全には属していない感覚がある。", 0),
           ("G4-3", "一つの集団に深く帰属することで安心を得る。", 1),
           ("G4-4", "立場の異なる集団の言葉を、互いに翻訳して伝えることがある。", 0),
           ("G4-5", "どちらの側からも「あちら側の人」と見られていると感じることがある。", 0),
           ("G4-6", "自分を説明するとき、所属よりも役割で語ることが多い。", 0)],
    "V1": [("V1-1", "これまで一度も、約束の時間に遅れたことがない。", 0),
           ("V1-2", "誰に対しても、いらだちを感じたことは一度もない。", 0),
           ("V1-3", "自分の非を認めなかったことは、一度もない。", 0),
           ("V1-4", "他人の成功をうらやましく思ったことは、一度もない。", 0),
           ("V1-5", "面倒だと感じて手を抜いたことは、一度もない。", 0),
           ("V1-6", "陰で人の批判をしたことは、一度もない。", 0)],
    "V2": [("V2-1", "終わっていない仕事は、片づくまで気になり続ける。", 0),
           ("V2-2", "目標は少し高めに置くほうだ。", 0),
           ("V2-3", "難題であるほど意欲が湧く。", 0),
           ("V2-4", "手順やルールがはっきりしていないと落ち着かない。", 0),
           ("V2-5", "変えると決めたことは、仕組みにして残す。", 0),
           ("V2-6", "場の空気に合わせて、自分の発言を変えることが多い。", 0)],
}

G3 = [
    ("G3-1", "チームの方針を決めるとき", "自分が決めて示す", "全員で議論して決める", "各自に任せる"),
    ("G3-2", "メンバーが迷っているとき", "具体的に指示する", "一緒に選択肢を整理する", "本人が答えを出すまで待つ"),
    ("G3-3", "仕事の分担を決めるとき", "自分が割り振る", "話し合って決める", "手を挙げた人に任せる"),
    ("G3-4", "進捗を管理するとき", "定期的に自分が点検する", "相互に共有する場を作る", "各自の裁量に委ねる"),
    ("G3-5", "失敗が起きたとき", "原因を特定して是正を指示する", "全員で振り返る", "本人に任せて見守る"),
    ("G3-6", "新人を育てるとき", "手順を教え込む", "一緒に考えながら進める", "経験から学んでもらう"),
]

# 4つめの選択肢（全問共通）。「経験がない」は中間選択肢（回答の回避）とは異なり、
# 該当する場面をそもそも経験していないという申告。人の動かし方の判定から除外する。
G3_NO_EXPERIENCE = "この場面を経験したことがない"

# 表示名は日常語にする。カッコ内の理論用語は TECH に持ち、小さく併記する。
# （やさしい日本語ガイドラインの方針：専門用語は残す場合、直後に説明を付ける）
SUBSCALES = {
    "P1": "未完了の残りやすさ", "P2": "目標水準の置き方", "P3": "成功志向か、失敗回避か",
    "P4": "結果を見て目標を修正する", "P5": "気持ちを切り替える",
    "E1": "魅力への反応のしやすさ", "E2": "不快な要素への感度", "E3": "迂回路を見つける",
    "E4": "必要とする手順の明確さ",
    "C1": "どちらも魅力的な二択", "C2": "どちらも避けたい二択",
    "C3": "魅力と不安が同居する選択", "C4": "条件が入り組んだ選択",
    "F1": "自分から動き出す", "F2": "反対を察知する",
    "F3": "既存のやり方を崩す", "F4": "変えたことを定着させる",
    "G1": "異論を言うか、場に合わせるか", "G2": "決め方（合議か、責任者か）", "G3": "人の動かし方",
    "G4": "集団への関わり方",
}

TECH = {
    "P1": "緊張系の持続", "P2": "要求水準", "P3": "成功接近／失敗回避",
    "P4": "要求水準の可動性", "P5": "心理的分化と境界の透過性",
    "E1": "正の誘発性への感受性", "E2": "負の誘発性への感受性", "E3": "障壁への対処",
    "E4": "場の構造化要求",
    "C1": "接近-接近型の葛藤", "C2": "回避-回避型の葛藤",
    "C3": "接近-回避型の葛藤", "C4": "二重接近-回避型の葛藤",
    "F1": "推進力の生成", "F2": "抑制力への感受性",
    "F3": "解凍（unfreezing）", "F4": "凍結（freezing）",
    "G1": "集団規範からの独立", "G2": "集団決定の活用", "G3": "集団風土",
    "G4": "境界人（marginal man）",
}

# 両極性の項目は「高い＝良い」ではなく、両端がそれぞれ別の特性を表す。
# 図には両端の意味を書き、位置として読ませる（能力系の図とは別に描く）。
# [低い側の意味, 高い側の意味]
POLES = {
    "P1": ["切り替えが速い", "未完了が残り続ける"],
    "P2": ["届く範囲に置く", "高い水準を課す"],
    "P3": ["失敗回避を優先", "成功志向で動く"],
    "E1": ["計画どおりに動く", "魅力に反応しやすい"],
    "E2": ["多少の不快は流せる", "不快の兆候に敏感"],
    "E4": ["曖昧でも動ける", "明確な手順を求める"],
    "G1": ["場に合わせて調整", "違っても意見を言う"],
    "G2": ["責任者が決める", "関係者で決める"],
    "G4": ["特定の集団に根を張る", "複数の立場の間に立つ"],
}

SHORT = set("""P1-1 P1-3 P1-6 P2-1 P2-3 P2-4 P3-1 P3-3 P3-4 P4-1 P4-3 P4-5
P5-1 P5-4 P5-5 E1-1 E1-4 E1-6 E2-1 E2-3 E2-4 E3-1 E3-3 E3-4 E4-1 E4-3 E4-4
C1-1 C1-2 C1-4 C2-1 C2-2 C2-4 C3-1 C3-2 C3-4 C4-1 C4-2 C4-3 F1-1 F1-3 F1-5
F2-1 F2-3 F2-4 F3-1 F3-3 F3-6 F4-1 F4-3 F4-4 G1-1 G1-2 G1-3 G2-1 G2-3 G2-5
G3-1 G3-3 G3-5 G4-1 G4-2 G4-3 V1-1 V1-4 V2-1""".split())

SCREEN = set("""P1-1 P2-1 P3-1 P4-1 P5-1 E1-1 E2-1 E3-1 E4-1 C1-1 C2-1 C3-1
C4-1 F1-1 F2-1 F3-1 F4-1 G1-1 G2-1 G3-1 G4-1""".split())


def build_items():
    out = []
    order = ["P1", "P2", "P3", "P4", "P5", "E1", "E2", "E3", "E4",
             "C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4",
             "G1", "G2", "G3", "G4", "V1", "V2"]
    for sub in order:
        if sub == "G3":
            for iid, scene, a, b, c in G3:
                out.append({"id": iid, "sub": "G3", "type": "choice",
                            "text": scene, "opts": [a, b, c, G3_NO_EXPERIENCE],
                            "short": iid in SHORT, "screen": iid in SCREEN})
        else:
            for iid, text, rev in LIKERT[sub]:
                out.append({"id": iid, "sub": sub, "type": "likert",
                            "text": text, "rev": bool(rev),
                            "short": iid in SHORT, "screen": iid in SCREEN})
    return out


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="レヴィンの行動理論（B = f(P, E)）にもとづく、行動特性と変化への向き合い方のセルフチェックツール。回答はこの端末の中だけで処理され、外部には送信されません。">
<meta property="og:type" content="website">
<meta property="og:title" content="レヴィン行動理論による特性診断">
<meta property="og:description" content="レヴィンの行動理論（B = f(P, E)）にもとづく、行動特性と変化への向き合い方のセルフチェックツール。回答はこの端末の中だけで処理され、外部には送信されません。">
<meta property="og:url" content="https://m1m2carbine-source.github.io/lewin-behavior-diagnostic/">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b6bcb'/%3E%3Ctext x='32' y='45' font-family='Arial,Helvetica,sans-serif' font-size='36' font-weight='700' fill='white' text-anchor='middle'%3EL%3C/text%3E%3C/svg%3E">
<title>レヴィン行動理論による特性診断</title>
<style>
:root{
  /* 本文コントラスト比はWCAG AA（4.5:1）以上を確保する。
     --sub は #fbfbfa 上で約6.1:1、--faint は約4.7:1。
     以前使っていた #aeb4ba（約2.3:1）は基準を満たさないため廃止した。 */
  --ink:#1c1f23; --sub:#565e66; --faint:#676f77; --line:#c9ced4; --bg:#fbfbfa; --card:#ffffff;
  --accent:#215070; --accent-soft:#e8eff4; --warn:#7a4d16; --warn-bg:#fdf6e8;
  --focus:#0b6bcb; --ok:#1f5c3d; --ng:#8f2f26;
  /* 領域色は色覚多様性でも区別できる組み合わせを選ぶ。
     ただし色は補助であり、領域名は常に文字でも示す（色だけに情報を持たせない）。 */
  --p:#215070; --e:#5a6a2f; --c:#8a4b2a; --f:#553a7a; --g:#7a5a12;
  /* 力の場分析（forcefield()）専用の配色。他のチャートと違いドメイン色
     ではなく「変えようとする力／今のままにしておく力」の2区分なので
     独立した変数にする。ライトモードは以前ハードコードしていた値と同じ。 */
  --drive:#2f5d7c; --hold:#8a5a4a; --axis:#1c1f23;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Yu Gothic","游ゴシック体",YuGothic,"Hiragino Sans","Noto Sans JP",sans-serif;
  font-size:15px;line-height:1.75;-webkit-text-size-adjust:100%}
.wrap{max-width:820px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:21px;font-weight:600;margin:0 0 4px;letter-spacing:.02em}
h2{font-size:16px;font-weight:600;margin:32px 0 10px;padding-bottom:6px;
  border-bottom:1px solid var(--line)}
h3{font-size:14px;font-weight:600;margin:20px 0 6px;color:var(--sub)}
p{margin:0 0 12px}
.lead{color:var(--sub);font-size:13.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding:20px 22px;margin:16px 0}
.btn{display:inline-block;background:var(--accent);color:#fff;border:0;border-radius:4px;
  padding:10px 20px;font-size:14px;font-family:inherit;cursor:pointer;letter-spacing:.03em}
.btn:hover{opacity:.88}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn:disabled{background:#c3c8ce;cursor:default}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.modes{display:grid;gap:10px;margin:16px 0}
.mode{border:1px solid var(--line);border-radius:5px;padding:12px 14px;cursor:pointer;
  background:#fff;text-align:left;font-family:inherit;font-size:14px}
.mode:hover{border-color:var(--accent);background:var(--accent-soft)}
.mode b{display:block;font-size:14.5px;margin-bottom:2px}
.mode span{color:var(--sub);font-size:12.5px}
.progress{position:sticky;top:0;background:var(--bg);padding:10px 0 8px;z-index:5;
  border-bottom:1px solid var(--line)}
.bar{height:4px;background:var(--line);border-radius:2px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent);width:0;transition:width .25s}
.meta{display:flex;justify-content:space-between;font-size:12px;color:var(--sub);
  margin-bottom:6px}
.q{border-bottom:1px solid var(--line);padding:16px 0}
.q:last-child{border-bottom:0}
.qtext{margin-bottom:10px}
.qno{color:var(--sub);font-size:12px;margin-right:8px;font-variant-numeric:tabular-nums}
.scale{display:grid;grid-template-columns:repeat(6,1fr);gap:4px}
.scale label{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
  gap:5px;border:1px solid var(--line);border-radius:4px;padding:9px 2px;cursor:pointer;
  font-size:11px;color:var(--sub);text-align:center;line-height:1.35;background:#fff;
  min-height:44px}
.scale label:hover{border-color:var(--accent);background:var(--accent-soft)}
/* display:none だとキーボード操作もスクリーンリーダーでの読み上げもできなくなる。
   視覚的にのみ隠し、フォーカスと支援技術には残す。 */
.scale input,.vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
  overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0}
.scale input:checked + em{background:var(--accent);color:#fff;border-color:var(--accent)}
.scale input:focus-visible + em{outline:3px solid var(--focus);outline-offset:2px}
.scale label:has(input:checked){border-color:var(--accent);background:var(--accent-soft)}
.scale em{font-style:normal;min-width:28px;height:28px;border-radius:50%;
  border:1.5px solid var(--line);display:flex;align-items:center;justify-content:center;
  font-size:13px;background:#fff;font-weight:600;color:var(--ink)}
.choices{display:grid;gap:6px}
.choices label{border:1px solid var(--line);border-radius:4px;padding:11px 12px;cursor:pointer;
  background:#fff;font-size:13.5px;min-height:44px;display:flex;align-items:center}
.choices label:hover{border-color:var(--accent);background:var(--accent-soft)}
.choices input{margin-right:10px;width:18px;height:18px;accent-color:var(--accent);flex:none}
.choices input:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.choices input:checked ~ span{font-weight:600}
.choices label:has(input:checked){border-color:var(--accent);background:var(--accent-soft)}
.choices label.noexp{border-style:dashed;color:var(--sub);font-size:12.5px}
.choices label.noexp:has(input:checked){border-style:dashed}
fieldset.q{border:0;margin:0;padding:16px 0;border-bottom:1px solid var(--line)}
fieldset.q:last-of-type{border-bottom:0}
legend.qtext{margin-bottom:10px;padding:0;display:block;width:100%}
table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0 16px}
th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:middle}
th{font-weight:600;color:var(--sub);font-size:12px;background:#f4f5f6}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbar{height:7px;background:#eceef0;border-radius:3px;position:relative;min-width:110px}
.tbar i{position:absolute;top:0;height:100%;border-radius:3px;background:var(--accent)}
.tbar u{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--faint);left:50%}
.note{background:var(--warn-bg);border-left:3px solid var(--warn);padding:11px 14px;
  font-size:13px;margin:12px 0;border-radius:0 4px 4px 0}
.dim{color:var(--sub);font-size:12.5px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13.5px}
.kv dt{color:var(--sub)}
.kv dd{margin:0}
.type{font-size:18px;font-weight:600;margin:4px 0 2px}
.eq{background:#f4f5f6;border-radius:5px;padding:16px 18px;font-size:14px;line-height:1.9}
.eq b{color:var(--accent)}
svg{max-width:100%;height:auto;display:block;margin:8px auto}
.tag{display:inline-block;border:1px solid var(--line);border-radius:3px;padding:1px 7px;
  font-size:11.5px;color:var(--sub);margin-right:5px}
details.ex{border:1px solid var(--line);border-radius:5px;background:#fff;
  margin:10px 0 16px;font-size:13px}
details.ex>summary{cursor:pointer;padding:9px 14px;color:var(--accent);font-weight:600;
  list-style:none;user-select:none}
details.ex>summary::-webkit-details-marker{display:none}
details.ex>summary::before{content:"▼ ";font-size:9px}
details.ex:not([open])>summary::before{content:"▶ "}
details.ex .body{padding:2px 16px 14px;line-height:1.8}
details.ex .body p{margin:0 0 9px}
details.ex .body ul{margin:0 0 9px;padding-left:20px}
details.ex .body li{margin-bottom:5px}
.you{background:var(--accent-soft);border-left:3px solid var(--accent);
  border-radius:0 4px 4px 0;padding:10px 14px;margin:10px 0;font-size:13.5px;line-height:1.8}
.you b{color:var(--accent)}
.idx{border:1px solid var(--line);border-radius:5px;background:#fff;
  padding:13px 16px;margin:10px 0}
.idx-h{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:7px}
.idx-n{font-weight:600;font-size:14.5px}
.idx-v{font-size:19px;font-weight:600;color:var(--accent);font-variant-numeric:tabular-nums}
.idx-w{margin:0 0 7px;font-size:12.5px;color:var(--sub)}
.idx-y{margin:0;font-size:13.5px;line-height:1.8}
.qc{font-size:12.5px}
.qc td.ok{color:#2f6b45}
.qc td.ng{color:#a4453a;font-weight:600}
.styletag{font-size:11px;padding:1px 6px;border-radius:3px;white-space:nowrap}
.st-a{background:#eef2f6;color:#3a5a72}
.st-b{background:#f2f0ea;color:#6b5f3a}
.sw{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.sw>div{border:1px solid var(--line);border-radius:5px;padding:12px 14px;background:var(--card)}
.sw-a{border-left:3px solid var(--ok)!important}
.sw-b{border-left:3px solid var(--warn)!important}
.sw p{margin:0;font-size:13.5px}
ul.chk{list-style:none;padding:0;margin:6px 0 14px}
ul.chk li{position:relative;padding:8px 10px 8px 34px;border:1px solid var(--line);
  border-radius:4px;margin-bottom:6px;background:var(--card);font-size:13.5px;line-height:1.7}
ul.chk li::before{content:"";position:absolute;left:11px;top:12px;width:13px;height:13px;
  border:1.5px solid var(--faint);border-radius:2px}
@media (max-width:600px){.sw{grid-template-columns:1fr}}
.axes{margin:6px 0 12px}
.axis{display:grid;grid-template-columns:96px 1fr 96px 46px;align-items:center;gap:8px;
  margin-top:10px}
.axis-l{font-size:11px;color:var(--sub);text-align:right}
.axis-r{font-size:11px;color:var(--sub)}
.axis-v{font-size:12.5px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink)}
.axis-t{position:relative;height:16px}
.axis-t::before{content:"";position:absolute;top:7px;left:0;right:0;height:2px;
  background:var(--line);border-radius:1px}
.axis-t u{position:absolute;top:2px;bottom:2px;left:50%;width:1px;background:var(--faint)}
.axis-t i{position:absolute;top:2px;width:12px;height:12px;border-radius:50%;
  background:var(--accent);transform:translateX(-50%)}
.axis-n{font-size:11.5px;color:var(--sub);margin:2px 0 0 104px}
@media (max-width:600px){
  .axis{grid-template-columns:74px 1fr 74px 40px;gap:5px}
  .axis-l,.axis-r{font-size:10px}
  .axis-n{margin-left:0}
}
.hide{display:none}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);
  font-size:11.5px;color:var(--sub)}
/* ── ユニバーサルデザイン ─────────────────────────────── */
/* すべての操作要素に、見てわかるフォーカス表示を付ける */
a:focus-visible,button:focus-visible,summary:focus-visible,
input:focus-visible,[tabindex]:focus-visible{
  outline:3px solid var(--focus);outline-offset:2px;border-radius:3px}
/* 判定の可否は色だけでなく記号でも示す（色覚多様性・白黒印刷への配慮） */
.qc td.ok::before{content:"✓ ";font-weight:700}
.qc td.ng::before{content:"! ";font-weight:700}
.qc td.ok{color:var(--ok)}
.qc td.ng{color:var(--ng);font-weight:600}
/* 動きに敏感な人のために、動きの表現を止める */
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
    transition-duration:.001ms!important;scroll-behavior:auto!important}
}
/* OSでコントラストを上げている場合、境界と文字をさらに強める */
@media (prefers-contrast:more){
  :root{--ink:#000;--sub:#333a41;--faint:#333a41;--line:#767c83;--accent:#123a52}
  .card,.idx,details.ex,.choices label,.scale label{border-width:2px}
}
/* OSがダークモードなら配色を反転させる（自分で切り替える必要をなくす） */
@media (prefers-color-scheme:dark){
  :root{
    --ink:#e9edf1; --sub:#b6bfc8; --faint:#9aa4ae; --line:#454d55; --bg:#16191c; --card:#1e2226;
    --accent:#7fb8dc; --accent-soft:#22323d; --warn:#e0b877; --warn-bg:#2c2617;
    --focus:#6cb6ff; --ok:#7fc79b; --ng:#f0918a;
    --p:#7fb8dc; --e:#a8c06a; --c:#dd9c74; --f:#b39ae0; --g:#d8bb61;
    /* --accent（8.23:1）・--warn（9.49:1）・--line（2.06:1）はいずれも
       背景 --bg:#16191c に対して検証済みの値なのでそのまま再利用する。
       以前は forcefield() が固定16進色を使っており、軸線がほぼ不可視
       （1.07:1）、矢印線もコントラスト比不足（2.50:1／3.06:1）だった。 */
    --drive:#7fb8dc; --hold:#e0b877; --axis:#454d55;
  }
  .scale label,.choices label,.scale em,.card,.idx,details.ex{background:var(--card)}
  th{background:#262b30}
  .eq{background:#22262b}
  .tbar{background:#33393f}
  .qc td.ok{color:var(--ok)} .qc td.ng{color:var(--ng)}
  svg text,svg tspan{fill:var(--ink)}
}
/* ── 印刷レイアウト ─────────────────────────────────
   印刷される内容は、画面に表示している内容とそのまま一致させる
   （準拠させる）。印刷専用に文章量や構成を作り直すことはしない。
   CSSで行うのは次の3点だけ。
   1. 折りたたみ（details）は open がないと印刷しても中身が出ない。
      印刷時は強制的に開き、開閉の見出し（summary）は消す。
   2. 用紙サイズ・余白・改ページ・色・ページ番号を指定する。
      @page の中では size と margin 以外は指定できず、em も使えない。
   3. SVGは viewBox で描いているため width:100% にするだけで
      紙幅いっぱいに拡大できる（内容そのものを作り替える必要がない）。 */
@page{ size:A4 portrait; margin:14mm 12mm 16mm 12mm; }
@page:first{ margin-top:10mm; }

@media print{
  /* 1. 折りたたみを全部開いた状態にする */
  details{ display:block!important }
  details>summary{ display:none!important }
  details>.body{ display:block!important }

  /* 2. 基本設定 */
  .noprint{ display:none!important }
  body{ background:#fff; color:#000; font-size:9.5pt; line-height:1.45 }
  .wrap{ max-width:none; padding:0 }
  h1{ font-size:15pt } h2{ font-size:12pt } h3{ font-size:10.5pt }
  p{ orphans:3; widows:3 }
  .card,.idx,details.ex,.eq{ border:1px solid #999; padding:8px 10px; margin:6px 0;
    background:#fff!important }

  /* 改ページの制御。章（h2）の境目で新しいページに移る。
     図・表・カードはページの境目で割らない。 */
  h2{ break-before:page; break-after:avoid }
  h2:first-of-type{ break-before:auto }
  h3{ break-after:avoid }
  svg,figure,table,.card,.idx,.axes,ul.chk{ break-inside:avoid }
  table{ border-collapse:collapse }
  thead{ display:table-header-group }
  tfoot{ display:table-footer-group }

  /* 3. 図は紙幅いっぱいに広げる（viewBoxで描いているため崩れない） */
  svg{ width:100%; height:auto; max-width:none }

  /* 色分けした判定は白黒印刷でも読めるよう記号を併記済みだが、
     色そのものも出しておく（背景色は既定で印刷されないため） */
  *{ -webkit-print-color-adjust:exact; print-color-adjust:exact }

  /* ページ番号は入れない。counter(pages)（総ページ数）はChromiumの
     印刷エンジンが対応しておらず、入れると常に「0 / 0」という
     誤った表示になる。誤表示を出すよりは、無いほうがよい。 */
}
@media (max-width:600px){
  .scale{grid-template-columns:repeat(3,1fr)}
  .wrap{padding:18px 14px 60px}
}
</style>
</head>
<body>
<div class="wrap">

<div id="intro">
  <h1>あなたの行動の決まり方を調べる</h1>
  <p class="dim" style="margin:0 0 10px">レヴィンの行動理論による特性診断</p>
  <p class="lead"><b>B = f(P, E)</b> ── 行動は、その人と環境の両方で決まる。<br>
  心理学者クルト・レヴィンのこの考え方をもとに、
  あなたを動かしている「本人の側の力」と「環境の側の力」を
  21の項目（点数の出る20項目と、選択式の1項目）に分けて測定し、
  その2つがどう組み合わさっているかを示します。</p>

  <div class="card">
    <h3 style="margin-top:0">実施する版を選んでください</h3>
    <div class="modes">
      <button class="mode" data-mode="full"><b>標準版　132問（所要 20〜30分）</b>
        <span>最も詳細な結果が出ます。21項目すべての点数、7つの指標、タイプの判定、
        そして「あなたの行動の式」までを算出します。</span></button>
      <button class="mode" data-mode="short"><b>短縮版　66問（所要 10〜15分）</b>
        <span>1項目につき3問。おおよその傾向はつかめますが、
        個々の点数の精度は標準版に劣ります。</span></button>
      <button class="mode" data-mode="screening"><b>スクリーニング版　21問（所要 3〜5分）</b>
        <span>1項目につき1問のみ。大まかな見当をつけるためのものです。
        回答の偏りの確認は行いません。</span></button>
    </div>
    <p class="dim" style="margin-bottom:0">回答は6段階から選びます。
    考えこまずに、この1か月の普段の自分に近いほうを選んでください。
    「どちらでもない」は意図的に置いていません。
    ただし「人の動かし方」を問う6問だけは、該当する場面を経験したことがない場合に選べる
    選択肢を別に用意しています。これは回答を避けるための選択肢ではなく、
    その場面がそもそも自分に当てはまらないことを示すためのものです。</p>
  </div>

  <div class="you"><b>このURLを誰に伝えても、回答や結果が他人に見られることはありません</b><br>
    このツールは、開いているブラウザの中だけで計算しています。回答も点数も、
    外部のサーバーには一切送信されません。同じURLを複数の人が開いても、
    それぞれの回答・結果はその人自身の画面の中だけに残り、混ざったり、
    他の人から見えたりすることはありません。</div>

  <div class="note">
    これは正式に検証された心理検査ではありません。レヴィンの理論枠組みを借りた、
    自己理解のための道具です。表示される点数は、多数の対象者を測定して作った基準ではなく、
    「6段階の中点を50とする」という取り決めから算出した暫定値です。
    医学的な診断や、採用・人事評価には使用しないでください。
  </div>
  <div class="row">
    <button class="btn ghost" id="resume" style="display:none">前回の続きから再開</button>
    <button class="btn ghost" id="loadBtn">保存したデータを読み込む</button>
    <input type="file" id="loadFile" accept=".json,application/json" style="display:none">
  </div>
  <p class="dim" id="loadMsg" style="margin-top:8px"></p>
</div>

<div id="quiz" class="hide">
  <div class="progress">
    <div class="meta"><span id="pmeta"></span><span id="pcount"></span></div>
    <div class="bar" id="pbarwrap" role="progressbar" aria-valuemin="0" aria-valuemax="100"
         aria-valuenow="0" aria-label="回答の進み具合"><i id="pbar"></i></div>
    <p class="vh" id="plive" aria-live="polite"></p>
  </div>
  <div class="card" id="qcard"></div>
  <div class="row">
    <button class="btn ghost" id="prev">戻る</button>
    <button class="btn" id="next">次へ</button>
    <span class="dim" id="pagehint"></span>
  </div>
</div>

<div id="result" class="hide"></div>

<footer class="noprint">
  レヴィン行動理論 特性診断ツール　第2版／全132問・21項目<br>
  クルト・レヴィン（1890-1947）の考え方をもとにした、自分を振り返るための道具です。<br>
  点数の作り方はこのツール独自のもので、レヴィン本人によるものではありません。
</footer>
</div>

<script>
const ITEMS = __ITEMS__;
const SUBS  = __SUBS__;
const SUBNAMES = __SUBNAMES__;
const TECH = __TECH__;
const POLES = __POLES__;
const LIKERT_LABELS = ["まったく<br>当てはまらない","ほとんど<br>当てはまらない","あまり<br>当てはまらない",
  "やや<br>当てはまる","かなり<br>当てはまる","非常に<br>当てはまる"];
const DOMAIN = {P:"本人の側の力",E:"環境の見え方",C:"迷う場面",F:"変える力",G:"集団の中での動き"};
const DCOLOR = {P:"var(--p)",E:"var(--e)",C:"var(--c)",F:"var(--f)",G:"var(--g)"};
const PER_PAGE = 8;
const KEY = "lewin_diag_v1";
/* 回答途中の再開（KEY）とは別に、完了した結果だけを別枠で覚えておく。
   「3か月後に見るもの」の自動比較に使う。同じ端末・同じブラウザでのみ働く。 */
const KEY_HIST = "lewin_diag_result_v1";
const MODE_LABEL = {full:"標準版",short:"短縮版",screening:"スクリーニング版"};
/* 項目文や採点式を変えるたびに上げる。読み込んだJSONの版がずれていても
   採点は試みるが、目立たない形で伝える（設問IDと逆転区分は今回変えていないため、
   version不一致でも採点自体は成立する）。 */
const ITEM_VERSION = "__ITEM_VERSION__";

let mode="full", items=[], answers={}, page=0;

/* ---------- storage (無ければ黙って諦める) ---------- */
function save(){ try{ localStorage.setItem(KEY, JSON.stringify({mode,answers,page})); }catch(e){} }
function load(){ try{ return JSON.parse(localStorage.getItem(KEY)); }catch(e){ return null; } }
function clearSave(){ try{ localStorage.removeItem(KEY); }catch(e){} }
function saveResultSnapshot(order,s,mode){
  try{
    const scores={}; order.forEach(k=>{ if(s[k]!=null) scores[k]=T(s[k]); });
    localStorage.setItem(KEY_HIST, JSON.stringify({date:new Date().toISOString(), mode, scores}));
  }catch(e){}
}
function loadResultSnapshot(){ try{ return JSON.parse(localStorage.getItem(KEY_HIST)); }catch(e){ return null; } }

/* ---------- 開始 ---------- */
document.querySelectorAll(".mode").forEach(b=>b.onclick=()=>{ start(b.dataset.mode); });
(function(){ const s=load(); if(s&&s.answers&&Object.keys(s.answers).length){
  const r=document.getElementById("resume"); r.style.display="inline-block";
  r.onclick=()=>{ mode=s.mode; answers=s.answers; page=s.page||0; start(mode,true); };
}})();

/* ---------- 保存データの読み込み ---------- */
document.getElementById("loadBtn").onclick=()=>document.getElementById("loadFile").click();
document.getElementById("loadFile").onchange=e=>{
  const f=e.target.files && e.target.files[0];
  if(!f) return;
  const r=new FileReader();
  r.onload=()=>{
    const msg=document.getElementById("loadMsg");
    try{
      const data=JSON.parse(r.result);
      const a=data.answers || data;
      if(typeof a!=="object" || !Object.keys(a).length) throw new Error("answers が見つかりません");
      const valid={}; let bad=0;
      ITEMS.forEach(it=>{
        const v=a[it.id];
        if(v==null) return;
        if(it.type==="choice"){ if(["a","b","c","d"].includes(v)) valid[it.id]=v; else bad++; }
        else { const num=parseInt(v,10);
               if(num>=1&&num<=6) valid[it.id]=num; else bad++; }
      });
      const cnt=Object.keys(valid).length;
      if(!cnt) throw new Error("読み取れる回答が1件もありません");
      const formRaw = data.形式 || data.form;
      const form=(formRaw==="short"||formRaw==="screening")? formRaw : "full";
      mode=form;
      items=ITEMS.filter(it=> form==="full"?true:(form==="short"?it.short:it.screen));
      answers=valid; page=0; save();
      document.getElementById("intro").classList.add("hide");
      showResult();
      const notes=[];
      if(bad) notes.push("範囲外の値を"+bad+"件読み飛ばしました。");
      const fileVersion = data.項目版;
      if(fileVersion && fileVersion!==ITEM_VERSION){
        notes.push("この結果は旧版（項目版"+fileVersion+"）の設問文にもとづいています。"+
          "設問IDと採点方法は変わっていないため採点はできますが、"+
          "数問の文言が現在の版と異なる場合があります。");
      }
      if(notes.length) console.warn(notes.join(" "));
    }catch(err){
      msg.textContent="読み込めませんでした（"+err.message+"）。"+
        "このツールが書き出したJSONファイルを選んでください。";
      msg.style.color="#a4453a";
    }
  };
  r.readAsText(f);
};

function start(m, resume){
  mode=m;
  items = ITEMS.filter(it => m==="full" ? true : (m==="short" ? it.short : it.screen));
  if(!resume){ answers={}; page=0; }
  document.getElementById("intro").classList.add("hide");
  document.getElementById("quiz").classList.remove("hide");
  render();
}

function pages(){ return Math.ceil(items.length/PER_PAGE); }

function render(){
  const start_=page*PER_PAGE, slice=items.slice(start_, start_+PER_PAGE);
  const done=items.filter(it=>answers[it.id]!=null).length;
  document.getElementById("pbar").style.width=(done/items.length*100)+"%";
  document.getElementById("pcount").textContent=done+" / "+items.length+" 問";
  document.getElementById("pmeta").textContent="ページ "+(page+1)+" / "+pages();
  const c=document.getElementById("qcard"); c.innerHTML="";
  slice.forEach((it,i)=>{
    const n=start_+i+1;
    const d=document.createElement("fieldset"); d.className="q";
    if(it.type==="likert"){
      d.innerHTML='<legend class="qtext"><span class="qno">問'+n+'</span>'+it.text+'</legend>'+
        '<div class="scale">'+LIKERT_LABELS.map((L,k)=>
          '<label><input type="radio" name="'+it.id+'" value="'+(k+1)+'"'+
          (answers[it.id]==k+1?" checked":"")+
          ' aria-label="'+(k+1)+'：'+L.replace(/<br>/g,"")+'">'+
          '<em aria-hidden="true">'+(k+1)+'</em>'+
          '<span aria-hidden="true">'+L+'</span></label>'
        ).join("")+'</div>';
    } else {
      d.innerHTML='<legend class="qtext"><span class="qno">問'+n+'</span>'+it.text+
        '<span class="dim">　── 最も自分に近いものを1つ</span></legend>'+
        '<div class="choices">'+["a","b","c","d"].map((k,j)=>
          '<label'+(k==="d"?' class="noexp"':'')+'><input type="radio" name="'+it.id+'" value="'+k+'"'+
          (answers[it.id]===k?" checked":"")+'><span>'+it.opts[j]+'</span></label>'
        ).join("")+'</div>';
    }
    c.appendChild(d);
  });
  c.querySelectorAll("input[type=radio]").forEach(r=>r.onchange=e=>{
    const v=e.target.value; answers[e.target.name]= isNaN(v)? v : parseInt(v,10);
    save(); refresh();
  });
  document.getElementById("prev").disabled = page===0;
  const last = page===pages()-1;
  document.getElementById("next").textContent = last ? "結果を見る" : "次へ";
  refresh();
  window.scrollTo({top:0,behavior:"instant"});
}

function refresh(){
  const done=items.filter(it=>answers[it.id]!=null).length;
  const pct=Math.round(done/items.length*100);
  document.getElementById("pbar").style.width=pct+"%";
  const wrap=document.getElementById("pbarwrap");
  if(wrap){ wrap.setAttribute("aria-valuenow",pct);
            wrap.setAttribute("aria-valuetext",done+"問中"+items.length+"問"); }
  document.getElementById("pcount").textContent=done+" / "+items.length+" 問";
  const start_=page*PER_PAGE, slice=items.slice(start_,start_+PER_PAGE);
  const unfilled=slice.filter(it=>answers[it.id]==null).length;
  document.getElementById("pagehint").textContent = unfilled? ("このページに未回答が"+unfilled+"問あります") : "";
}

document.getElementById("prev").onclick=()=>{ if(page>0){page--;save();render();} };
document.getElementById("next").onclick=()=>{
  const start_=page*PER_PAGE, slice=items.slice(start_,start_+PER_PAGE);
  const un=slice.filter(it=>answers[it.id]==null);
  if(un.length && !confirm("このページに未回答が"+un.length+"問あります。このまま進みますか。")) return;
  if(page<pages()-1){ page++; save(); render(); }
  else { showResult(); }
};

/* ---------- 採点 ---------- */
function conv(v,rev){ return rev ? 7-v : v; }
function mean(a){ return a.length? a.reduce((x,y)=>x+y,0)/a.length : null; }
function r2(x){ return x==null? null : Math.round(x*100)/100; }

/* 欠測は絶対数ではなく比率で判定する（版によって1尺度あたりの問数が違うため）。
   その尺度の設問のうち3分の1を超えて欠測なら測定不能とする。
   これにより標準版（6問なら3問以上欠測）と短縮版（3問なら2問以上欠測）で
   同じ基準になる。 */
function subscaleScores(){
  const buck={}, total={};
  items.forEach(it=>{
    if(it.type!=="likert") return;
    buck[it.sub]=buck[it.sub]||[];
    total[it.sub]=(total[it.sub]||0)+1;
    const v=answers[it.id];
    if(v==null) return;
    buck[it.sub].push(conv(v,it.rev));
  });
  const out={};
  Object.keys(total).forEach(s=>{
    const n=total[s], answered=(buck[s]||[]).length, missing=n-answered;
    out[s]= (n>0 && missing > n/3) ? null : r2(mean(buck[s]));
  });
  return out;
}
/* 「中点スコア」：6段階の理論的中点（3.50）を50、1目盛りを10として置き直した数値。
   規範集団のデータではなく、あくまで理論上の中点からの距離を表す指標であるため、
   確立した統計用語である「T得点」の呼称は使わず、判定語も母集団比較を思わせる
   「非常に高い／低い」ではなく、中点からの距離を表す語にする。
   境界は 30/40/60/70（従来の35/45/56/65より広い）。20000人規模のモンテカルロ
   検証で、この境界だと両端の出現率がそれぞれ約6%となり、母集団を仮定しない
   範囲で妥当な水準になることを確認している。 */
function T(m){ if(m==null) return null;
  return Math.round(Math.max(20,Math.min(80, 50+10*(m-3.5)/0.85))*10)/10; }
function band(t){ if(t==null) return "測定できません";
  return t>=70?"中点よりかなり上": t>=60?"中点より上": t>=40?"中点に近い": t>=30?"中点より下":"中点よりかなり下"; }
function mOf(s,ks){ const v=ks.map(k=>s[k]).filter(x=>x!=null); return v.length? r2(mean(v)) : null; }

/* 6問しかないため百分率は16.7%刻みで精度を偽装する。件数を主表示にする（所見14）。
   「経験がない（d）」は判定から除外し、無経験が多い場合はプロファイル自体を
   出さない（所見17）。 */
function leadership(){
  const c={a:0,b:0,c:0}; let n=0, noExp=0, asked=0;
  items.filter(i=>i.type==="choice").forEach(i=>{
    const v=answers[i.id];
    if(v==null) return;
    asked++;
    if(v==="d"){ noExp++; return; }
    if(v in c){ c[v]++; n++; }
  });
  if(asked===0) return null;
  if(noExp>=3) return { insufficient:true, noExp, asked };
  if(!n) return null;
  const L={a:"指示型",b:"合議型",c:"委任型"};
  const pct={}; Object.keys(c).forEach(k=>pct[L[k]]=Math.round(c[k]/n*1000)/10);
  const counts={}; Object.keys(c).forEach(k=>counts[L[k]]=c[k]);
  const rank=Object.entries(counts).sort((x,y)=>y[1]-x[1]);
  let style=rank[0][0];
  if(rank[1] && rank[0][1]-rank[1][1]<=1) style=rank[0][0]+"・"+rank[1][0]+"併用型";
  return {pct,counts,style,n,noExp,asked};
}

/* 社会的望ましさと回答一貫性は、標準版でしか十分な項目数がない
  （短縮版はV1が2問・一貫性ペアが1組のみで、絶対数のまま基準に当てると
  1問の誤差が数倍に増幅される）。そのため標準版でのみ算出する（所見12）。
  回答の偏り（標準偏差）は項目数が多ければ短縮版でも意味を持つため、
  screening以外の版で算出する。 */
function validity(){
  if(mode==="screening") return null;
  const w=[];
  let v1mean=null, cons=null;
  if(mode==="full"){
    const v1=["V1-1","V1-2","V1-3","V1-4","V1-5","V1-6"].map(k=>answers[k]).filter(x=>x!=null);
    v1mean = v1.length===6 ? r2(mean(v1)) : null;
    if(v1mean!=null && v1mean>=4.5) w.push("社会的望ましさが高く出ています。全体にやや高めの結果になっている可能性を考慮して読んでください。");
    const pairs=[["V2-1","P1-1"],["V2-2","P2-1"],["V2-3","P3-1"],["V2-4","E4-1"],["V2-5","F4-1"],["V2-6","G1-2"]];
    const dif=pairs.map(([a,b])=> (answers[a]!=null&&answers[b]!=null)? Math.abs(answers[a]-answers[b]) : null).filter(x=>x!=null);
    cons = dif.length===6 ? r2(mean(dif)) : null;
    if(cons!=null && cons>=1.5) w.push("同じ内容を尋ねた項目の間で回答がそろっていません。時間を空けての再実施を勧めます。");
  }
  const all=items.filter(i=>i.type==="likert").map(i=>answers[i.id]).filter(x=>x!=null);
  const mu=mean(all), sd = all.length>1? r2(Math.sqrt(mean(all.map(x=>(x-mu)*(x-mu))))) : null;
  if(sd!=null && sd<=0.6) w.push("選択が特定の値に偏っています。項目を読まずに回答した可能性があります。");
  return {v1mean,cons,sd,w, limited: mode!=="full",
    verdict: w.length>=2?"再実施を推奨": (w.length?"参考値として扱う":"範囲内")};
}

function Tmean(s,ks){ const v=ks.map(k=>T(s[k])).filter(x=>x!=null); return v.length? r2(mean(v)) : null; }

function derive(s){
  const d={};

  /* 自分基準で動くか、状況で動くか。
     以前は P平均÷(P平均+E平均) という比率だったが、分子・分母が同じ1〜6の
     尺度に載るため値が50に強く引き寄せられ、境界帯（中間型）が約半数を
     占めてしまっていた（20000人のモンテカルロ検証で確認）。
     中点スコアどうしの「差」に変更し、境界帯を約24%まで下げている。
     E側の代表からE3（回り道を見つける＝対処能力）を外す。E3は能力系尺度で
     あり、「環境の見え方」を表す感受性の尺度ではないため（所見3）。 */
  const pT = Tmean(s,["P1","P2","P3","P4","P5"]);
  const eT = Tmean(s,["E1","E2","E4"]);
  d.pe = (pT!=null&&eT!=null)? r2(pT-eT) : null;
  d.peLabel = d.pe==null? null : (Math.abs(d.pe)<1.5 ? "ほぼ同程度" : (d.pe>0?"自分の基準が優位":"環境の条件が優位"));

  /* 着手する力と定着させる力。
     以前は mean(F1,F3) − mean(F2,F4) だったが、F2「反対を察知する」は
     変化を妨げる力ではなく、変化を成功させるための対処能力である。
     察知できる人ほど手を打てるため、推進側の力に近い。誤って保持側に
     算入すると、変革に長けた人ほど「定着が優位」と判定されかねない。
     F2は独立指標「抵抗への備え」として別に示す（所見9）。 */
  const f13=Tmean(s,["F1","F3"]);
  const tF4=T(s.F4);
  d.ffb = (f13!=null&&tF4!=null)? r2(f13-tF4) : null;
  d.ffbLabel = d.ffb==null? null : (Math.abs(d.ffb)<1.76 ? "ほぼ均衡" : (d.ffb>0?"着手が優位":"定着が優位"));
  d.f2 = T(s.F2);

  d.cti = Tmean(s,["C1","C2","C3","C4"]);
  /* 最も弱い葛藤型は、2位との差が0.5未満（実質同点）なら特定しない。
     3000人規模の模擬回答で、この差が0.2未満の受検者が2割程度おり、
     僅差での断定は誤解を招くため（所見11）。 */
  const cv=["C1","C2","C3","C4"].filter(k=>s[k]!=null);
  if(cv.length>=2){
    const sorted=[...cv].sort((a,b)=>T(s[a])-T(s[b]));
    d.weak = (T(s[sorted[1]])-T(s[sorted[0]]) >= 5.9) ? sorted[0] : null;
  } else { d.weak = cv.length? cv[0] : null; }

  if(s.P2!=null&&s.P4!=null){
    d.quad = s.P2>3.5 ? (s.P4>3.5?"高く設定し、修正もできる":"高く設定するが、修正できない")
                      : (s.P4>3.5?"堅実に設定し、修正もできる":"低い水準に固定している");
  }
  if(s.P1!=null&&s.P5!=null){
    d.tli=r2(T(s.P1)-T(s.P5));
    d.tliLabel = d.tli>=11.8?"持ち帰りが多い": d.tli<=-11.8?"切り替えが速い":"ふつう";
  }

  /* 変革を担う力。以前は mean(F1..F4)*0.7 + mean(G2,E3)*0.3 だったが、
     G2「合意して決める」は高低に優劣のない両極性尺度であり、それを
     「高いほど良い」方向で合算するのは尺度の性質と矛盾する。
     F群のみで合成し、G2・E3は合算せず補助情報として別に示す（所見7）。 */
  /* 「変革を担う力（F1〜F4の平均）」は廃止した。
     F2をそのまま含み、F1・F3・F4は着手差が使っているため、
     同じ数字を二度示すことになっていた（構造的な相関 +0.51）。
     合意して決める力と迂回路を見つける力は、変革の成否に効くが
     高低に優劣がないので、指標にせず補助情報として置く。 */
  d.aux = { g2: T(s.G2), e3: T(s.E3) };

  /* 環境調整の効きやすさ。以前は mean(E1,E2) − mean(P1,P3) だったが、
     E1（近づきたくなる感度）とE2（避けたくなる感度）は向きが逆の力で
     あり、平均すると「良い環境で伸びる人」と「嫌な要素で止まる人」が
     同じ値になってしまう。処方がまったく違う2つを、誘因設計の効きやすさ
     と障害除去の効きやすさに分けて別々に示す（所見8）。 */
  /* 「誘因設計の効きやすさ」「障害除去の効きやすさ」も独立の指標にしない。
     どちらも E から P を引いた形で、PE差と同じことを別の角度から見ているだけ
     （構造的な相関はいずれも −0.59）。PE差の内訳として並べる。 */
  const p13=Tmean(s,["P1","P3"]);
  d.eBreak = {
    incentive: (T(s.E1)!=null&&p13!=null)? r2(T(s.E1)-p13) : null,
    removal:   (T(s.E2)!=null&&p13!=null)? r2(T(s.E2)-p13) : null
  };

  return d;
}

function classify(d){
  if(d.pe==null||d.ffb==null) return null;
  /* 境界帯：どちらかの軸が中立圏内なら型を断定しない。
     PE差 ±1.5・力の場 ±1.76（中点スコア換算後の値。素点0.15を
     T得点換算式と同じ係数10/0.85で換算＝0.15×10/0.85≈1.76）は、
     20000人規模のモンテカルロ検証で境界帯の発生率が全体の約24%に
     なるよう校正した値（変更前は約49%が中間型になっていた）。
     以前はこの定数が素点スケールの0.15のまま残っており、着手/定着の
     軸で境界帯と判定される人がほぼ出ない状態になっていた（score.pyの
     同名定数も同時に修正済み）。 */
  const border = (Math.abs(d.pe)<1.5) || (Math.abs(d.ffb)<1.76);
  const name = d.pe>0 ? (d.ffb>0?"自ら動き出す型":"決めたことを守り抜く型")
                      : (d.ffb>0?"仕組みを組み替える型":"場に合わせて回す型");
  return {name, border, weak:d.weak, weakName: d.weak? SUBNAMES[d.weak]:null};
}

const TYPEDESC = {
  "自ら動き出す型":{
    tech:"推進者型（ドライバー）",
    nick:"最初の一人",
    portrait:"誰も動かない場で、最初に手を挙げる人。",
    checks:["「言い出しっぺがやることになる」と分かっていて、それでも言うことがある",
            "自分が始めた取り組みが、いつの間にか元に戻っていた経験がある",
            "「なぜ今までこうしてきたのか」を人に尋ねたことが、この1年で複数回ある"],
    pair:"決めたことを守り抜く型",
    near:"仕組みを組み替える型",
    ws:"始めたことを、記録や仕組みとして残す工程",
    s:"自分の中の目標が行動を動かします。問題があれば自分から動き出せる人です。誰も動かない場で、最初の一人になれます。",
    strong:"既存のやり方を「これでよいのか」と問い直せます。止まっている場に、最初のひと押しを入れられます。",
    weak:"始めた変化を根づかせるのが弱いところです。提案は出るものの、積み上がりません。反対する人の存在にも気づきにくくなります。",
    rx:"変えたら、手順書や記録に書き残すところまでを1つの仕事と決めてください。提案する前に「これで誰が損をするか」を書き出す習慣もつけてください。"},
  "決めたことを守り抜く型":{
    tech:"基準保持型（アンカー）",
    nick:"守り手",
    portrait:"決まったことを、決まったとおりに回し続けられる人。",
    checks:["「あの件どうなったか」を覚えているのが、たいてい自分である",
            "手順が守られていないのを見ると、指摘せずにいられない",
            "新しいやり方の提案に対して、まず運用の穴が見えてしまう"],
    pair:"自ら動き出す型",
    near:"場に合わせて回す型",
    ws:"古くなったやり方を、自分から壊す作業",
    s:"自分の中の基準がはっきりしていて、決まったことを確実に根づかせます。品質と一貫性を支える人です。",
    strong:"手順をそろえる、人に教える、記録を整える。組織の記憶を守る役割が得意です。",
    weak:"今までのやり方を壊すのが苦手です。理由がなくなった手順まで、そのまま残してしまいます。",
    rx:"「この手順は今も必要か」を確かめる場を、行事として決めてください。1年に1つ、自分からやめるものを選ぶのも有効です。"},
  "仕組みを組み替える型":{
    tech:"場再編型（リフレーマー）",
    nick:"仕掛け人",
    portrait:"人を説得するより、置き方を変えて結果を変える人。",
    checks:["人を説得するより、そもそも起きない形に変えたことがある",
            "自分のやる気に頼らず、道具や置き場所を変えて解決したことがある",
            "方針が状況によって変わることを、周囲から指摘されたことがある"],
    pair:"場に合わせて回す型",
    near:"自ら動き出す型",
    ws:"場が変わってもぶれない、自分の基準を持つこと",
    s:"周囲の力の流れを読んで、場そのものを組み替えます。人を変えずに、結果のほうを変えられる人です。",
    strong:"仕組みづくりが得意です。やる気に頼らず、仕組みで行動を変えられます。",
    weak:"自分の中の基準が薄いところです。場が変わると方針も変わり、周囲からはぶれて見えることがあります。",
    rx:"変えない決まりを3つだけ紙に書いて持ってください。場を組み替えるときは、その目的をそのつど言葉にしてください。"},
  "場に合わせて回す型":{
    tech:"場適応型（アダプター）",
    nick:"調整役",
    portrait:"その場の要請を読んで、決まったことを崩さず回す人。",
    checks:["「あの人に任せると崩れない」と言われたことがある",
            "会議が終わってから「本当はこう思っていた」と感じることがある",
            "おかしいと思っても、何度か様子を見てから言うほうだ"],
    pair:"仕組みを組み替える型",
    near:"決めたことを守り抜く型",
    ws:"自分が変化の口火を切ること",
    s:"その場が何を求めているかを読み、それに合わせて着実に回します。組織の実務を支える人です。",
    strong:"調整がうまく、決まったことを安定して続けられます。人とぶつかりません。",
    weak:"自分から変化を起こすことが少なめです。環境が悪化しても、我慢して続けてしまいます。",
    rx:"「おかしい」と思ったら、その場でメモに残してください。3件たまったら必ず言う、と自分で決めておくと動けます。"}
};

const CONFLICT_RX = {
  C1:"選ぶ前に、何を重く見るかを先に決めてください。決めたあとは「いつまで考え直してよいか」の期限も決めます。",
  C2:"決めないままでいると何を失うかを、数値にしてください。そのうえで第三案を必ず1つ書き出してください。",
  C3:"「ここまでで駄目ならやめる」という線を先に書いてください。最初の一歩は、できるだけ小さく切ります。",
  C4:"要素を表に分けて書き出してください。関係する人ごとに、得することと損することを書き分けます。"
};

/* 低いと「足りない」を意味する尺度。直し方は、気持ちではなく手順・記録・環境の話にする */
const LOWRX = {
  P4:"結果を見て目標を修正できていません。目標と実績の差を、月に1回、数値で確認する時間を設けてください。",
  P5:"仕事と私生活の仕切りが薄くなっています。終業時に未完了を書き出して閉じる。そういう区切りを決めてください。",
  E3:"妨げを実際より大きく見積もっています。何が妨げになっているかを書き出し、本当に動かせないものだけを選び直してください。",
  F1:"必要だと思っても、動くのは人任せになりがちです。提案の締切を自分で決めて、手帳に書いてください。",
  F2:"反対が表に出てから気づきます。変える前に「これで誰が損をするか」を3人分書き出してください。",
  F3:"今までどおりでいたい力が強く働いています。まず1件だけ、その手順がなぜあるのかを調べ直すところから始めてください。",
  F4:"変えても元に戻ります。変更は、手順書と記録用紙を直すところまでを必ずセットにしてください。"
};

/* 高低に良し悪しがない尺度。[高いとき, 低いとき] */
const BIPOLAR = {
  P1:["未完了が強く気にかかり、それが推進力になります。ただし休んでいる間も気持ちが休まらず、慢性的な疲労につながります。どこで区切るかを決めてください。",
      "切り替えが速く、疲れにくいほうです。ただし長い仕事は、始める日と次の一手を予定表に書かないと動きません。"],
  P2:["自分に高い目標を課しています。伸びは速いのですが、常に不足感が残ります。達成できたことを記録に残し、定期的に見返してください。",
      "届く範囲に目標を置き、安定して結果を出します。自分の上限を試す機会は、意識して作る必要があります。"],
  P3:["成功する場面を思い描いて動けます。挑戦する場面で力が出ます。撤退条件だけは先に決めておいてください。",
      "失敗しないことを先に考えて動きます。品質管理やリスク管理に強いタイプです。やめる条件を先に決めておくと、挑戦が大きく下がります。"],
  E1:["面白そうなものにすぐ反応します。良い環境に置かれると大きく伸びます。半面、気が散りやすくもあります。",
      "環境に左右されず、決めたとおりに動きます。環境をよくするより、手順と予定を整えるほうが有効です。"],
  E2:["不調の兆しに早く気づきます。予防に強いタイプです。半面、不快な要素が一つあるだけで全体をあきらめやすくなります。",
      "少しくらい嫌でも前に進めます。危ない合図を見落とさないよう、決まった見張り項目を2つ決めて定期的に確認してください。"],
  E4:["手順と基準がはっきりしていれば、正確に動けます。標準化や仕組みづくりで強みになります。",
      "枠組みが決まっていない場でも動けます。立ち上げに強い半面、細かく決められた場では窮屈に感じます。"],
  G1:["みんなと違っても意見を言えます。まちがった合意を止められます。言い方を選ぶと、もっと通ります。",
      "その場の空気に合わせて調整します。摩擦は少なく済みます。主張したいことは、会議の前に1行だけ文書で出しておくと通りやすくなります。"],
  G2:["当事者に決めてもらう進め方を選びます。変えたことが根づきやすくなります。急ぐ場面だけ切り替えてください。",
      "上の人が決めるやり方を選びます。速いのですが、現場では根づきにくくなります。根づかせたい変更のときだけ、本人たちに決めてもらってください。"],
  G4:["いくつもの立場の間に立ち、通訳のように働きます。孤立感を抱えやすいので、落ち着ける居場所を1つ確保してください。",
      "どこかに深く属することで落ち着きます。集団をまたぐ調整役は、意識して引き受ける必要があります。"]
};

/* ---------- 解説の部品 ---------- */
/* 既定はすべて閉じる。実測値・「あなたの場合」・図そのものはこの関数の
   外側で別途出力しており、ここに渡すのは理論的な背景の説明だけなので、
   閉じても個人化された結論は隠れない。各章の要点は、この折りたたみより
   前に常時表示の導入文として出しているため、折りたたみ自体を開かせる
   必要はない。
   以前は「21項目の図の読み方」だけ openOnLoad=true で既定を開いていたが、
   これは折りたたみが印刷で消える問題への対処だった。現在は
   @media print の details{display:block!important} により、
   開閉状態にかかわらず印刷時は全折りたたみが強制的に開くため
   （check_print.py で検証済み）、この特例は不要になっている。 */
function ex(title, body, openOnLoad){
  return '<details class="ex"'+(openOnLoad?' open':'')+'><summary>'+title+'</summary><div class="body">'+body+'</div></details>';
}
function you(html){ return '<div class="you"><b>あなたの場合</b>　'+html+'</div>'; }

/* 能力系＝低いと不足を意味する／両極性＝高低に優劣がない */
const SCALETYPE={P1:"両",P2:"両",P3:"両",P4:"能",P5:"能",E1:"両",E2:"両",E3:"能",E4:"両",
  C1:"能",C2:"能",C3:"能",C4:"能",F1:"能",F2:"能",F3:"能",F4:"能",G1:"両",G2:"両",G4:"両"};

/* 両極性の項目は「次元の名前」を表示名に持ち、方向は極ラベルが担う。
   表示名を「高い側の極」にすると、低い人の行が
   「目標を高く設定する ／ 中点よりかなり下」のように自己矛盾する。
   場面ごとに必要なものが違うので、使い分けをここに集約する。
   ・sidePole … その人がどちら側にいるか（位置の記述に使う）
   ・highPole … 高いほど強まる力としての名前（力の場の矢印など）
   ・poleBand … 「どちら寄りか」の判定文（能力系の band() に対応するもの） */
function isBip(k){ return SCALETYPE[k]==="両" && !!POLES[k]; }
function sidePole(k,t){ return isBip(k) ? (t>=50? POLES[k][1] : POLES[k][0]) : SUBNAMES[k]; }
function highPole(k){ return isBip(k) ? POLES[k][1] : SUBNAMES[k]; }
/* 本文用。常に項目名から始めることで、同じ項目だと分かるようにする。 */
function forceLabel(k){ return SUBNAMES[k]; }
/* 「項目名（数値／どちら側）」の形にまとめる。
   項目名を先頭に置くことで、別の章に出ても同じ項目だと分かる。 */
function sideLabel(k,t){
  return isBip(k)
    ? "<b>"+SUBNAMES[k]+"</b>（"+t+"／「"+sidePole(k,t)+"」の側）"
    : "<b>"+SUBNAMES[k]+"</b>（"+t+"）";
}
function poleBand(k,t){
  if(t==null) return "測定できません";
  if(!isBip(k)) return band(t);
  if(t>=70) return "「"+POLES[k][1]+"」に強く寄る";
  if(t>=60) return "「"+POLES[k][1]+"」寄り";
  if(t>40)  return "どちらでもない";
  if(t>30)  return "「"+POLES[k][0]+"」寄り";
  return "「"+POLES[k][0]+"」に強く寄る";
}

const LEADER_DESC={
  "指示型":{
    tech:"専制型（autocratic）",
    f:"リーダーが見ている間の作業量は最も多くなりました。ところがリーダーが席を外すと、作業は止まりました。"+
      "ある班では仲間への攻撃が増え、別の班では逆に無気力になりました。無気力だった班は、リーダーが部屋を出たとたんに攻撃が噴き出しました。",
    u:"急ぐとき、安全にかかわるとき、経験の浅い人が集まったばかりのとき",
    c:"メンバーが自分で考える力は育ちにくくなります。あなたが見ていない時間に質が落ちていないか、別のやり方で確かめてください。"},
  "合議型":{
    tech:"民主型（democratic）",
    f:"作業量は指示型よりやや少なめでした。ただしリーダーが席を外しても作業は続きました。"+
      "工夫や助け合いが多く出ました。20人のうち19人が、指示するリーダーより、"+
      "合意して決めるリーダーのほうを好みました。",
    u:"根づかせたい変更、続けたい改善、専門職の集まりを動かすとき",
    c:"決めるまでに時間がかかります。急ぐ場面や、まだ慣れていない相手のときは、意識して切り替える判断が要ります。"},
  "委任型":{
    tech:"放任型（laissez-faire）",
    f:"作業量が最も少なく、質も低くなりました。攻撃的なふるまいは、実際にはこの進め方で最も多く記録されました。"+
      "方向が定まらず、対立に流れやすかったためです。",
    u:"力のある専門職どうしで、目的をはっきり共有できているとき",
    c:"慣れていない集まりや、目的があいまいな場面では機能しません。「関わらないこと」と「任せること」は違います。"}
};

/* 導出指標：w＝何を見ているか／r(値)＝あなたの場合どうなるか
   単位はいずれも中点スコア（20〜80、50が中点）どうしの差、または
   素点（1〜6）どうしの差。0が「差がない」を意味する。 */
const IDX={
  pe:{n:"自分基準で動くか、状況で動くか",t:"中点スコアの差（P群−E群）",u:"（0が分かれ目、±1.5未満はほぼ同程度）",
    w:"あなたを動かしているのが、自分の中の基準なのか、その場の条件なのか。レヴィンの式 B = f(P, E) の、PとEのどちらが強く効いているかを、中点スコアの差として見ます。",
    r:v=> Math.abs(v)<1.5 ? "自分の基準と場の条件が、ほぼ同じくらいの強さで働いています。どちらか一方に絞らず、両方の対策を試してください。"
        : v>=1.5 ? "自分の中の基準が主に動かしています。環境を整えるより、<b>自分のルールを作り直す</b>ほうが行動が変わります。締切の置き方、判断の基準、「ここまで来たら始める」という条件を決めることです。半面、環境が悪化しても気づかず、我慢し続けることがあります。"
        : "場の条件が主に動かしています。気持ちで努力するより、<b>まわりを変える</b>ほうが確実です。作業する場所、手元に置くもの、同席する人、締切の見え方を変えてください。決意だけでは戻ります。",
    caveat:"なおこの指標は、PとEを厳密に切り分けたものではありません。"+
      "理由は最後の章に書いています。"},
  ffb:{n:"着手する力と定着させる力",t:"中点スコアの差（着手側−定着側）",u:"（0が分かれ目、±1.8未満はほぼ均衡）",
    w:"変化を起こす力（自分から動き出す・既存のやり方を崩す）と、支えて根づかせる力（変えたことを定着させる）の差です。",
    r:v=> Math.abs(v)<1.76 ? "着手する力と定着させる力がつり合っています。単独で最後まで運べますが、そのぶん負担も全部あなたに来ます。どこかを人に渡す形を作ってください。"
        : v>=1.76 ? "始めるのは得意で、根づかせるのが弱い組み合わせです。<b>あなたが変えたことは、あなたが見ていないと元に戻ります。</b>「手順書と記録用紙を直すまで」を1件と数えてください。"
        : "支えて定着させるのが得意で、始めるのが弱い組み合わせです。<b>動き出した変化を、あなたは最後まで運べます。</b>口火は人に切ってもらい、2番目に入るほうがうまくいきます。"},
  cti:{n:"迷う場面での決断力",t:"葛藤耐性",u:"（4場面の平均、50が中点）",
    w:"引っぱる力と引き止める力がつり合って動けなくなる場面で、決められるかどうか。4つの場面の平均です。",
    r:null},
  quad:{n:"目標設定のタイプ",t:"要求水準の象限",u:"",
    w:"目標をどれくらい高く置くかと、結果を見てその目標を動かせるかの組み合わせです。",
    r:null},
  tli:{n:"仕事の持ち帰りやすさ",t:"緊張系負荷",u:"（中点スコアの差、0が真ん中）",
    w:"未完了の残りやすさから、気持ちを切り替える力を引いた数値です。仕事をどれくらい心に持ち帰っているかの目安になります。",
    r:v=> v>=11.8 ? "未完了の気がかりが、生活全体ににじみ出ています。これは意志では止まらないので、区切りは手続きで作るしかありません。"
        : v<=-11.8 ? "気がかりは仕事の中に収まっています。疲れは少ないのですが、<b>長い仕事は自分から思い出さないと動きません。</b>始める日と次の一手を予定表に書いてください。"
        : "持ち帰りはありますが、区切りもある程度きいています。忙しい時期にこのつり合いが崩れやすいので、その時期だけ区切りを足してください。"},
  f2:{n:"抵抗への備え",t:"反対を察知する（中点スコア）",u:"（50が中点）",
    w:"反対されそうな人や理由を、事前にどれだけ読めているか。変化を妨げる力ではなく、変化を成功させるための対処能力です。",
    r:v=> v>=60 ? "反対の所在を先読みできています。着手する力・定着させる力のどちらとも組み合わせやすい強みです。"
        : v<40 ? "反対が表に出てから気づくほうです。変えるときに、抵抗の在りかを読む工程が抜けます。"
        : "反対への備えは平均的です。"}
};

const CONFLICT_SCENE={
  C1:"魅力的な選択肢が2つ以上並んだとき",
  C2:"どちらも避けたい二択を迫られたとき",
  C3:"やりたい気持ちと不安が同じ対象に混在し、いよいよ着手する直前",
  C4:"関係者の思惑が異なり、条件が増えたとき"
};

const QUAD_DESC={
  "高く設定し、修正もできる":"高く狙いながら、結果を見て刻めています。<b>最も伸びる組み合わせ</b>です。気をつけるのは成果ではなく、疲れの管理だけです。",
  "高く設定するが、修正できない":"高い目標を掲げていますが、結果に合わせて動かせていません。届かない状態が続き、<b>疲労がたまりやすい組み合わせ</b>です。3か月に1回、実際の結果に合わせて目標を書き直す時間を作ってください。",
  "堅実に設定し、修正もできる":"無理をせず着実に積めています。安定しますが、<b>自分の上限を試す機会が減ります</b>。1年に1件だけ、届くか分からない目標を混ぜてください。",
  "低い水準に固定している":"失敗しないように目標を低いまま止めています。安全ですが、<b>結果から学ぶことが起きにくい</b>状態です。まず1件、失敗しても実害の小さい場で高めの目標を試してください。"
};

function theorySources(){
  return '<h2>どこまでがレヴィンの理論か</h2>'+
  '<p class="dim">レヴィン本人の研究に由来する部分と、本ツールが作成した部分を分けて示します。</p>'+
  '<table><thead><tr><th>部分</th><th>出どころ</th></tr></thead><tbody>'+
  '<tr><td>B = f(P, E)、生活空間、引きつける力／遠ざける力（誘発性）、妨げになるもの（障壁）</td>'+
  '<td class="dim">レヴィン『トポロジー心理学の原理』1936、『パーソナリティの力学説』1935</td></tr>'+
  '<tr><td>未完了が気にかかる仕組み（緊張系）</td>'+
  '<td class="dim">レヴィンの理論。学生のツァイガルニクが1927年に実験で確認した</td></tr>'+
  '<tr><td>目標の高さと、その上げ下げ（要求水準）</td>'+
  '<td class="dim">ホッペ 1930・デンボ 1931 が初出。レヴィン、デンボ、フェスティンガー、シアーズ 1944 が体系化。なお「成功で上げ、失敗で下げるのが良い」という単純な話ではなく、失敗が続くと『確実に届く低さ』か『届かなくて当然の高さ』に逃げることが知られている</td></tr>'+
  '<tr><td>迷う場面の3つの型</td>'+
  '<td class="dim">レヴィン 1931/1935。「近づくほど不安が強まる」もレヴィンが提唱し、'+
  'ミラーが1944年に実験で示した。4つめの「条件が入り組んだ選択」はミラーによる追加</td></tr>'+
  '<tr><td>変える力と、今のままにしておく力（力の場）</td>'+
  '<td class="dim">レヴィン 1947/1951。本来は特定の変更案（例：この職場にこの新手順を'+
  '入れる）について、その場に働く力を洗い出す道具。本ツールでは、これを個人の特性の'+
  '記述に転用している</td></tr>'+
  '<tr><td>崩す→動かす→固める</td>'+
  '<td class="dim">レヴィンは1947年の論文に「Unfreezing, Moving, Freezing」と書いた。'+
  'ただし「再凍結（refreezing）」という語は使っておらず、'+
  '今よく知られる3段階の変革モデルは没後に他の人が整えたという指摘がある'+
  '（カミングスら 2016）。これに対する反論もある（バーンズ 2020）</td></tr>'+
  '<tr><td>3つのリーダーの進め方</td>'+
  '<td class="dim">レヴィン、リピット、ホワイト 1939。10歳前後の子どもの集団が対象</td></tr>'+
  '<tr><td>合意して決めると根づく</td>'+
  '<td class="dim">レヴィン 1943の食習慣研究。話し合って決めた群は52%が実行し、'+
  '講義だけの群は10%だった</td></tr>'+
  '<tr><td>複数の立場の間に立つ人（境界人）</td>'+
  '<td class="dim">レヴィン『社会的葛藤の解決』1948</td></tr>'+
  '<tr><td><b>132問の質問文、21の項目、中点スコア、6つの指標、4つの型</b></td>'+
  '<td class="dim"><b>すべて本ツールが作成したものです。</b>'+
  'レヴィン本人は質問紙も点数も作成していません。'+
  '考え方の枠組みのみを借りています</td></tr>'+
  '</tbody></table>'+
  '<h3>この診断が測れていないこと</h3>'+
  '<p>改善を重ねても、実装では解消できない限界が4つあります。</p><ul>'+
  '<li><b>比べる相手がいません。</b>他の人と比べて高い・低いということは、この診断からは'+
  '言えません。言えるのは、自分の中での凹凸と、6段階の理論的な中点からの隔たりだけです</li>'+
  '<li><b>21という区分そのものが、確かめられていません。</b>'+
  'これが本当に21個の別々のものを測っているかを調べるには因子分析が必要で、'+
  'それには数百人分の実データが要ります。行っていないため、'+
  '項目どうしが実は同じものを測っている可能性が残ります</li>'+
  '<li><b>呼び名（4つの型）は、連続した量を切って作ったものです。</b>'+
  '同じ人が2回受けても、呼び名が一致するのは7割ほどです。'+
  '切る前の位置は9割方一致するので、位置のほうを信用してください</li>'+
  '<li><b>「環境」の4項目は、環境そのものではなく、環境をどう感じるかという感受性です。</b>'+
  '感じ方も本人の特性の一部であるため、この診断はP（本人）とE（環境）を完全には'+
  '切り分けられていません。環境そのものを測るには、本来は他者評価や場の観察が必要です</li></ul>'+
  '<p>この4点がある限り、本ツールは測定器ではなく、'+
  '<b>構造化された振り返りの道具</b>として使うのが適切です。'+
  '点数を「測定値」として受け取らず、<b>自分を振り返るための問いかけ</b>として使ってください。</p>';
}

/* ---------- 結果表示 ---------- */
/* force=true のときは、妥当性の警告が2件以上でも本文を表示する
   （「警告を理解したうえで結果を見る」ボタンから呼ばれる）。所見5対応。 */
function showResult(force){
  const s=subscaleScores(), d=derive(s), cls=classify(d), lp=leadership(), va=validity();
  const order=["P1","P2","P3","P4","P5","E1","E2","E3","E4","C1","C2","C3","C4",
               "F1","F2","F3","F4","G1","G2","G4"];
  const blocked = !!(va && va.verdict==="再実施を推奨" && !force);
  const SEC={};

  let h='<h1>診断結果</h1><p class="lead">'+
    ({full:"標準版 132問",short:"短縮版 66問",screening:"スクリーニング版 21問"}[mode])+
    "　実施日 "+new Date().toLocaleDateString("ja-JP")+'</p>';
  if(!blocked){
    /* この案内文は、以下の screenBody の章構成（位置→根拠→なぜ→総合判定→
       対策→場面→型）を要約したもの。章の順番・役割を変えたときは、
       この文言も必ず合わせて見直すこと。 */
    h+='<p>ここから、あなたの回答をもとに、'+
       '<b>①行動の特徴とその位置づけ　②なぜ今そうなっているのか　③これからどうすればよいか</b>'+
       '　の順に説明していきます。判断に必要な情報は、そのつど本文中に記載します。</p>';
    h+='<p class="noprint"><button class="btn ghost" id="toggleEx" style="padding:5px 12px;font-size:12.5px">解説をすべて開く</button></p>';
  }
  SEC.title=h; h='';

  /* 0 妥当性 */
  if(va){
    h+='<h2>回答の確認</h2>';
    h+=ex("ここで何を見ているか",
      '<p>自分で答える診断は、本人にその意図がなくても回答が偏ります。'+
      'そこで結果を読む前に、この回答をそのまま解釈してよいかを先に確認します。'+
      '体重計に乗る前に、目盛りがゼロからずれていないかを確かめるのと同じ位置づけです。</p>'+
      '<p>確認しているのは次の3点です。</p><ul>'+
      '<li><b>回答が良い方向に偏っていないか</b>　「今まで一度も遅刻したことがない」のような、'+
      '現実にはまず当てはまらない内容へ、どれだけ肯定したか。'+
      '高いと全体が好ましい方向へずれます</li>'+
      '<li><b>回答に一貫性があるか</b>　同じことを言い方を変えて2回尋ねた6組の答えの差。'+
      '差が大きい場合、設問を読まずに回答したか、途中で判断基準が変わった可能性があります</li>'+
      '<li><b>選択が特定の値に偏っていないか</b>　選んだ数字のばらつき。'+
      '同じ値ばかりが並ぶ場合、内容を読まずに回答した可能性があります</li></ul>'+
      '<p>3つとも問題がなければ、以降の得点は額面どおり読んで差し支えありません。'+
      (va.limited? '　なお社会的望ましさと回答の一貫性は、項目数が十分な標準版でのみ確認できます。'+
        '今回の版では、選択の偏りのみを確認しています。':'')+'</p>');
    const vr=[["回答が良い方向に偏っていないか", va.v1mean, "4.5 より小さい", va.v1mean!=null&&va.v1mean>=4.5, va.v1mean==null&&mode!=="full"],
              ["回答に一貫性があるか", va.cons, "1.50 より小さい", va.cons!=null&&va.cons>=1.5, va.cons==null&&mode!=="full"],
              ["選択が特定の値に偏っていないか", va.sd, "0.60 より大きい", va.sd!=null&&va.sd<=0.6, false]];
    h+='<table class="qc"><thead><tr><th>確認項目</th><th class="num">測定値</th>'+
       '<th>許容範囲</th><th>判定</th></tr></thead><tbody>';
    vr.forEach(r=> h+='<tr><td>'+r[0]+'</td><td class="num">'+(r[1]??"—")+'</td>'+
      '<td class="dim">'+(r[4]?"標準版のみ":r[2])+'</td><td class="'+(r[4]?"":(r[3]?"ng":"ok"))+'">'+
      (r[4]?"対象外":(r[3]?"範囲外":"範囲内"))+'</td></tr>');
    h+='</tbody></table>';
    va.w.forEach(x=> h+='<div class="note">'+x+'</div>');
    h+=you(va.verdict==="範囲内"
      ? '確認できた項目はすべて許容範囲でした。<b>このあとの結果は、そのまま読んで問題ありません。</b>'
      : va.verdict==="参考値として扱う"
      ? '1つが範囲からはずれました。<b>結果は「おおよその目安」として読んでください。</b>'+
        'タイプの判定を決めつけずに受け取ってください。'
      : '2つ以上が範囲からはずれました。<b>このあとの詳しい結果は表示していません。</b>'+
        '日を改めて、もう一度やってみることをおすすめします。');
  }

  if(blocked){
    h+='<div class="note"><b>結果の表示を見合わせています</b><br>'+
       '回答の確認で複数の問題が見つかったため、タイプ判定や行動の式など、'+
       'このあとの詳しい結果は表示していません。回答データは保存できます。'+
       '内容を理解したうえでそれでも見たい場合は、下のボタンから表示できます。</div>';
    h+='<div class="row noprint" style="margin-top:16px">'+
       '<button class="btn ghost" id="dl">回答データを保存（JSON）</button>'+
       '<button class="btn ghost" id="forceShow">警告を理解したうえで結果を見る</button>'+
       '<button class="btn ghost" id="again">最初からやり直す</button></div>';
    const R=document.getElementById("result");
    R.innerHTML=SEC.title+h; R.classList.remove("hide");
    document.getElementById("quiz").classList.add("hide");
    const dl=(txt,name,mime)=>{ const a=document.createElement("a");
      a.href=URL.createObjectURL(new Blob([txt],{type:mime})); a.download=name; a.click(); };
    document.getElementById("dl").onclick=()=>
      dl(JSON.stringify({ツール:"レヴィン行動理論 特性診断",項目版:ITEM_VERSION,形式:mode,
        実施日時:new Date().toISOString(),注記:"妥当性の確認で警告が2件以上のため未採点で保存",
        answers},null,2),"lewin_diagnostic_raw.json","application/json");
    document.getElementById("forceShow").onclick=()=>showResult(true);
    document.getElementById("again").onclick=()=>{ clearSave(); location.reload(); };
    window.scrollTo({top:0,behavior:"instant"});
    return;
  }
  if(force && va && va.verdict==="再実施を推奨"){
    h+='<div class="note"><b>警告を理解したうえで表示しています。</b>'+
       '妥当性の確認で複数の問題が見つかった回答です。以下のタイプ判定・行動の式などは、'+
       '参考として読んでください。</div>';
  }

  SEC.validity=h; h='';

  /* 1 プロファイル */
  const ABILITY=order.filter(k=>SCALETYPE[k]==="能");
  const BIPOLARK=order.filter(k=>SCALETYPE[k]==="両");
  /* 順位は群をまたいで付けない。さらに両極性は「高いほど上位」で並べると
     高い側の極が優れているという含みが出るため、中点からの隔たり
     （どれだけ際立っているか）で順位を付ける。方向を含まない指標になる。 */
  const rankOf={}, rankTot={};
  {
    const ab=ABILITY.filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));
    ab.forEach((k,i)=>{ rankOf[k]=i+1; rankTot[k]=ab.length; });
    const bp=BIPOLARK.filter(k=>s[k]!=null)
      .sort((a,b)=>Math.abs(T(s[b])-50)-Math.abs(T(s[a])-50));
    bp.forEach((k,i)=>{ rankOf[k]=i+1; rankTot[k]=bp.length; });
  }
  const rk=order.filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));

  h+='<h2>行動特性の内訳</h2>';
  h+='<p class="dim">上の「いまのあなたの位置」は、これから見る21項目の回答をもとに算出しています。'+
     'まずはその内訳を、項目ごとに確認します。</p>';
  h+=ex("この章の図の読み方",
      '<p><b>中点スコア</b>は、6段階の平均点を「理論上の中点（3.50）を50」として置き直した数値です。'+
      '母集団のデータと比較したものではなく、あくまで理論上の中点からの距離を表します。'+
      '40〜59が中点に近い、60以上・70以上で中点より上、30未満・40未満で中点より下という目安です。'+
      '図では、縦の破線が50の位置です。</p>'+
      '<p><b>項目は2種類あり、意味が違うので図を分けています。</b></p><ul>'+
      '<li><span class="styletag st-a">能力</span>'+
      '<b>高いほうが有利な11項目。</b>低ければ伸ばす余地があります。'+
      '中点50を基線とした横棒で示し、右へ伸びるほど強み、左へ伸びるほど補強の余地です</li>'+
      '<li><span class="styletag st-b">両極</span>'+
      '<b>高い・低いに優劣がない9項目。</b>'+
      'どちらの側にも、それぞれの強みと引き換えの代償があります。'+
      'たとえば「未完了の残りやすさ」が高い人は強い推進力を持ちますが、同時に疲労もたまります。'+
      '低い人は消耗が少ない代わりに、長い仕事が動き出しにくくなります。'+
      'そこでこの9項目は横棒を塗らず、<b>左右の端にそれぞれの意味を書いた図</b>で、'+
      '「どちら寄りか」という位置として示します。'+
      '項目名も高い側・低い側どちらにも使える<b>物差しそのものの名前</b>です</li></ul>'+
      '<p>残る1項目「人の動かし方」は選択式のため点数が出ず、この節の後半に別途示します。</p>');

  h+='<h3>能力系の11項目　── 高いほうが有利</h3>';
  h+=abilityPlot(s,ABILITY);

  h+='<h3>両極性の9項目　── どちら寄りかを示すもので、優劣はありません</h3>';
  h+=bipolarPlot(s,BIPOLARK);

  /* リーダーシップ */
  if(lp){
    h+='<p class="dim">ここまでの21項目とは別枠で、人をどう動かすかについて、'+
       'もう1問だけ選択式でたずねています。得点ではなく選んだ回数で表れるため、'+
       '上の図とは分けて示します。</p>';
  }
  if(lp && lp.insufficient){
    h+='<h3>人の動かし方（'+lp.asked+'問中）</h3>';
    h+='<div class="note">'+lp.noExp+'問で「この場面を経験したことがない」を選んでいます。'+
       '経験にもとづく回答が少ないため、この項目の判定は表示していません。</div>';
  } else if(lp){
    h+='<h3>人の動かし方（'+lp.n+'問／'+lp.asked+'問中、経験なしを除く）</h3>';
    h+=ex("型が分かると何が言えるのか",
      '<p>レヴィンらが1939年に行った実験があります。'+
      '10歳前後の子どもたちのクラブに、3つの進め方のリーダーを順に入れ替えて、'+
      '作業量とふるまいがどう変わるかを比較しました。結果は次のとおりです。</p><ul>'+
      '<li><b>指示型</b>　'+LEADER_DESC["指示型"].f+'</li>'+
      '<li><b>合議型</b>　'+LEADER_DESC["合議型"].f+'</li>'+
      '<li><b>委任型</b>　'+LEADER_DESC["委任型"].f+'</li></ul>'+
      '<p>つまりこの結果は「あなたはこういう性格です」という話ではありません。'+
      '<b>あなたが普段選ぶやり方が、周囲に何をもたらすか</b>の見通しです。</p>'+
      '<p>優劣ではなく<b>使い分け</b>の話です。'+
      '全体では「合議型」が最も良い結果でしたが、'+
      '急ぐときや、まだ慣れていない人が相手のときは「指示型」のほうが機能します。</p>'+
      '<p class="dim">6問（または短縮版では3問）しかないため、割合は16.7%刻みでしか動きません。'+
      '下の表では件数を主に示します。'+
      '※1939年に子どもの集団を対象に行われた研究です。'+
      '自律した専門職の集団にそのまま当てはまるとは限りません。</p>');
    h+='<table><thead><tr><th>進め方</th><th class="num">選んだ数</th>'+
       '<th>向いている場面</th></tr></thead><tbody>';
    Object.entries(lp.counts).forEach(([k,v])=>
      h+='<tr><td>'+k+'</td><td class="num"><b>'+v+' / '+lp.n+'</b>'+
         '<span class="dim">（'+lp.pct[k]+'%）</span></td>'+
         '<td class="dim">'+LEADER_DESC[k].u+'</td></tr>');
    h+='</tbody></table>';
    if(lp.noExp>0) h+='<p class="dim">このほか'+lp.noExp+'問は「経験したことがない」でした。集計から除いています。</p>';
    {
      const main=Object.entries(lp.counts).sort((a,b)=>b[1]-a[1]);
      const top=main[0][0], second=main[1];
      const zero=main.filter(x=>x[1]===0).map(x=>x[0]);
      let t='あなたが普段選ぶのは<b>'+lp.style+'</b>です。　'+LEADER_DESC[top].c;
      if(zero.length && main.some(x=>x[1]>=Math.max(4,Math.ceil(lp.n*0.66)))){
        t+='　また'+zero.join('と')+'を一度も選んでいません。'+
           '<b>その引き出しが今のところ手薄かもしれません。</b>'+
           `（回答が${lp.n}問と少ないため、選ばなかっただけの可能性もあります。）`+
           'いつものやり方が合わない場面に当たると手が止まりやすいので、'+
           'どういう条件のときは別のやり方を採るのか、1つだけ決めておいてください。';
      } else if(zero.length){
        t+='　'+zero.join('と')+'は選ばれていませんが、'+
           `回答数（${lp.n}問）が少ないため、断定はできません。`;
      } else if(main[0][1]-second[1]<=1){
        t+='　あわせて'+second[0]+'も'+second[1]+'回選んでおり、'+
           '<b>すでに切り替えの下地があります。</b>'+
           'その切り替えを何を基準に行っているかを言葉にできれば、意識的に使えるようになります。';
      }
      h+=you(t);
    }
  }

  {
    const abLow=ABILITY.filter(k=>s[k]!=null).sort((a,b)=>T(s[a])-T(s[b]));
    const bpEnd=BIPOLARK.filter(k=>s[k]!=null)
      .sort((a,b)=>Math.abs(T(s[b])-50)-Math.abs(T(s[a])-50));
    let t='';
    if(abLow.length>=2){
      t+='能力系で最も低いのは<b>'+SUBNAMES[abLow[0]]+'（'+T(s[abLow[0]])+'）</b>と<b>'+
         SUBNAMES[abLow[1]]+'（'+T(s[abLow[1]])+'）</b>です。'+
         (T(s[abLow[0]])<40? 'ここが補強の余地にあたります。' : 'ただし、いずれも中点から大きくは離れていません。');
    }
    if(bpEnd.length>=2){
      const f=(k)=>{ const v=T(s[k]);
        return '<b>'+SUBNAMES[k]+'</b>（'+v+'／「'+sidePole(k,v)+'」の側）'; };
      t+='　両極性では'+f(bpEnd[0])+'、'+f(bpEnd[1])+'が最も端に寄っています。'+
         'これは長所でも短所でもなく、あなたの行動を特徴づけている位置です。';
    }
    if(t) h+=you(t+'　これらの組み合わせが、次に示す「行動の式」の内容と、後半に示すタイプ判定を決めています。');
  }

  SEC.profile=h; h='';

  /* 2 導出指標
     ここは根拠であって結論ではない。以前は6つすべてに「あなたの場合」を
     付けていたため、結論の章より長くなり、対策とも内容が重なっていた。
     中点から離れているものだけを解説し、残りは表にまとめる。 */
  if(mode!=="screening"){
    h+='<h3>組み合わせて見える6つの指標</h3>';
    h+=ex("この章は何のためにあるのか",
      '<p>前章の各項目は、単独で見ても「それで、どうすればよいのか」が出てきません。'+
      'この章は、いくつかの項目を組み合わせて<b>対策のもとになる形</b>に変換した数値です。</p>'+
      '<p>対策そのものは「まず何をするか」に書いています。'+
      'ここはその根拠なので、納得できていれば読み飛ばして差し支えありません。</p>'+
      '<p class="dim">※この6つの指標は、レヴィンの考え方をもとに'+
      '<b>本ツールが構成したもの</b>です。レヴィン本人がこれらの数値を用いたわけではありません。</p>');

    /* 中点から離れているものだけを説明する。
       以前は一覧表とカードの両方を出していたため、
       同じ指標名・単位・値が2度ずつ並んでいた。表は廃止する。 */
    const FAR = {
      pe:   d.pe!=null  && Math.abs(d.pe)>=1.5,
      ffb:  d.ffb!=null && Math.abs(d.ffb)>=1.76,
      f2:   d.f2!=null  && (d.f2>=60 || d.f2<40),
      cti:  !!d.weak,
      quad: !!d.quad,
      tli:  d.tli!=null && Math.abs(d.tli)>=11.8
    };
    const vals={pe:d.pe, ffb:d.ffb, f2:d.f2, cti:d.cti, quad:d.quad, tli:d.tli};
    const labs={pe:d.peLabel, ffb:d.ffbLabel, f2:null, cti:null, quad:null, tli:d.tliLabel};
    const order6=["pe","ffb","f2","cti","quad","tli"];

    const near=order6.filter(k=>vals[k]!=null && !FAR[k]);
    if(near.length){
      h+='<p class="dim">中点に近く、特筆する点がないもの：'+
        near.map(k=>IDX[k].n+' '+vals[k]).join('　／　')+'</p>';
    }

    order6.filter(k=>vals[k]!=null && FAR[k]).forEach(k=>{
      if(k==="cti"){
        h+=idxCard("cti", d.cti, null,
          '4つの場面のうち<b>'+SUBNAMES[d.weak]+'</b>が最も低く出ました。'+
          'あなたが決められなくなるのは<b>'+CONFLICT_SCENE[d.weak]+'</b>です。'+
          'これは性格によるものではなく、その場で力が拮抗しているためです。');
      } else if(k==="quad"){
        h+=idxCard("quad", d.quad, null, QUAD_DESC[d.quad]);
      } else {
        h+=idxCard(k, vals[k], labs[k]);
        if(k==="pe"){
          const eb=d.eBreak;
          if(eb && (eb.incentive!=null || eb.removal!=null)){
            h+='<p class="dim" style="margin-top:-6px"><b>環境側の内訳</b>　'+
              (eb.incentive!=null? '近づきたくなるものへの反応 '+eb.incentive+'　':'')+
              (eb.removal!=null? '避けたくなるものへの反応 '+eb.removal:'')+
              '。前者が大きければ、やりたくなる仕掛けを足すのが効きます。'+
              '後者が大きければ、嫌な要素を1つ取り除くほうが効きます。</p>';
          }
          h+='<p class="dim" style="margin-top:-6px">'+IDX.pe.caveat+'</p>';
        }
      }
    });

    if(d.aux.g2!=null || d.aux.e3!=null){
      h+='<p class="dim">あわせて見るもの（指標にはしていません）：'+
        (d.aux.g2!=null? '合意して決める '+d.aux.g2+'　':'')+
        (d.aux.e3!=null? '迂回路を見つける '+d.aux.e3:'')+
        '。どちらも変化の成否に効きますが、高い低いに優劣がないため合算していません。</p>';
    }
  }

  SEC.indices=h; h='';

  /* 3 類型 */
  if(cls){
    const td=TYPEDESC[cls.name];
    h+='<h2>あなたのタイプと、組むとよい相手</h2>';
    h+='<p class="dim">冒頭の「いまのあなたの位置」で、あなたは<b>'+td.nick+'</b>と判定されています。'+
      'ここではその型の詳しい説明と、あなたの苦手を補ってくれる相手を補足として示します。'+
      '型は入り口であり、上で見た位置や式のほうが本体です。</p>';
    h+=ex("この4つの型はどう決まっているのか",
      '<p>ここまでに見た2つの指標を、縦軸と横軸に取った4分割です。'+
      '性格の分類ではなく、<b>あなたが変化に対してどの位置にいるか</b>を表します。</p>'+
      '<ul><li><b>縦軸</b>　自分の中の基準で動くか、その場の条件で動くか</li>'+
      '<li><b>横軸</b>　変化を起こす側か、根づかせる側か</li></ul>'+
      '<table><thead><tr><th></th><th>起こす側</th><th>根づかせる側</th></tr></thead><tbody>'+
      '<tr><td class="dim">自分の中の基準で動く</td><td>自ら動き出す型</td><td>決めたことを守り抜く型</td></tr>'+
      '<tr><td class="dim">その場の条件で動く</td><td>仕組みを組み替える型</td><td>場に合わせて回す型</td></tr>'+
      '</tbody></table>'+
      '<p>4つに優劣はありません。組織にはこの4つがすべて必要です。'+
      'どれかが欠けると、変化が起きないか、起きても元に戻ります。'+
      '自分の型を知る意味は、<b>足りない部分を自力で埋めようとせず、'+
      '別の型の人と組む判断ができるようになる</b>ことにあります。</p>'+
      '<p class="dim">※この4分類も、レヴィン本人の分類ではありません。</p>');
    h+='<div class="card">'+
      '<div class="type">'+(td.nick? td.nick+'　':'')+
        '<span style="font-size:15px;font-weight:400">'+cls.name+'</span></div>'+
      '<div class="dim" style="font-size:12px">専門用語：'+td.tech+'</div>'+
      (cls.weakName? '<div class="dim">苦手な場面：'+cls.weakName+'</div>':'')+
      (cls.border? '<div class="note">2つの軸のどちらかが、ちょうど分かれ目の近くにあります。'+
        'このタイプは仮のものと考えて、隣のタイプの説明もあわせて読んでください。</div>':'')+
      '<p style="margin-top:12px">'+td.s+'</p>'+
      '<div class="sw"><div class="sw-a"><h3 style="margin-top:0">強み</h3><p>'+td.strong+'</p></div>'+
      '<div class="sw-b"><h3 style="margin-top:0">苦手</h3><p>'+td.weak+'</p></div></div>'+
      '<dl class="kv" style="margin-top:12px"><dt>対策</dt><dd>'+td.rx+'</dd></dl></div>';
    /* 組む相手は好みではなく、2軸の構造から決まる。
       欠けやすい工程を持っているのは、根づかせる／起こすの軸が反対の型。 */
    if(td.pair && TYPEDESC[td.pair]){
      const o=TYPEDESC[td.pair];
      h+='<h3>組むとよい相手</h3>'+
        '<div class="card"><p>あなたが単独で最後までやろうとしたとき、最も抜けやすいのは'+
        '<b>'+td.ws+'</b>です。これは力量の不足ではなく、2つの軸のどこに立つかという配置の問題です。</p>'+
        '<p>この工程を得意にしているのが<b>'+o.nick+'（'+td.pair+'）</b>です。'+o.strong+'</p>'+
        '<p>いっぽうであなたは、その人が苦手とする「'+o.ws+'」を引き受けられます。'+
        '<b>互いの穴がちょうど噛み合う組み合わせ</b>です。</p>'+
        '<p class="dim" style="margin-bottom:0">これは相性占いではありません。'+
        '4つの型は「自分の基準か場の条件か」「起こす側か根づかせる側か」の2軸で決まるため、'+
        '足りない工程を持つ相手が構造的に定まります。</p></div>';
    }
    h+='<h3>ほかの3つの型</h3>'+
      '<div class="card"><p class="dim">当てはまらないと感じた場合は、'+
      'こちらを読んでみてください。境界の近くにいる人は珍しくありません。</p><table>'+
      '<thead><tr><th>型</th><th>どういう人か</th></tr></thead><tbody>'+
      Object.keys(TYPEDESC).filter(k=>k!==cls.name).map(k=>{
        const t=TYPEDESC[k];
        return '<tr><td><b>'+t.nick+'</b><br><span class="dim" style="font-size:11px">'+k+
          '</span></td><td class="dim">'+t.portrait+'</td></tr>';
      }).join('')+'</tbody></table></div>';
  }

  SEC.type=h; h='';

  /* 4 行動方程式 */
  if(mode!=="screening"){
    h+='<h2>なぜそうなるのか　── あなたの行動の式</h2>';
    h+=ex("なぜその対策なのかは、この式で決まっています",
      '<p>レヴィンの基本の式は <b>B = f(P, E)</b> です。'+
      'Bは行動、Pはその人、Eは環境を指します。'+
      '「行動は、その人と環境の両方で決まる」という意味です。</p>'+
      '<p>同じ人物でも、置かれる場が変われば動き方は変わります。'+
      'だから性格だけを見ても実際の行動は予測できない。これがレヴィンの立場でした。</p>'+
      '<p>ここまでの点数を、その考え方に沿って1つの文章にまとめ直したのが下の記述です。'+
      'このあとに出てくる「まず何をするか」の対策は、この式から導いています。'+
      '<b>点数ではなく、この文章のほうを持ち帰ってください。</b></p>');
    h+=equation(s,d,order);
  }

  SEC.equation=h; h='';

  /* 5 力の場 */
  if(s.F1!=null){
    h+='<h2>なぜ、分かっていても行動が変わらないのか</h2>';
    h+='<p class="dim">「変えたほうがいいと分かっているのに変えられない」というのは、'+
       '意志が弱いからではありません。<b>あなたの中で、変えようとする力と'+
       '現状を保とうとする力が、ちょうど釣り合っている</b>ために起きます。'+
       '下の図で、その釣り合いを見ていきます。</p>';
    h+=ex("なぜ今のままなのかを図で見る",
      '<p>レヴィンは、変わらない状態を「力が働いていない状態」とは考えませんでした。'+
      '<b>変えようとする力と、現状を保とうとする力が拮抗して止まっている</b>と捉えます。'+
      'これを準定常的均衡と呼びます。</p>'+
      '<p>左が変えようとする力、右が現状を保とうとする力です。'+
      '動かないのは力がないからではなく、両側から同じだけ押されているためです。</p>'+
      '<p>ここから、実用的な結論が1つ出てきます。'+
      '<b>変えたいときは、押す力を強めるより、押し返す力を減らすほうが有効です。</b>'+
      '押す力を強めれば押し返す力も同程度に強まり、'+
      '緊張と疲労だけが増えるためです。'+
      '「もっと努力する」がうまくいかないのは、この構造によるものです。</p>');
    h+=forcefield(s);
  }

  SEC.force=h; h='';

  /* 6 提案 */
  const acts=topActions(s,d,cls);
  let secAction='<h2>この結果で、まず何をするか</h2>';
  if(acts.length){
    secAction+='<p class="dim">21項目と6つの指標を横断して、'+
      '<b>いま最も効く順に'+acts.length+'つだけ</b>選びました。'+
      '全部を直そうとしないでください。上から順に、1つずつで十分です。</p>';
    acts.forEach((a,i)=> secAction+=actionCard(a,i));
  } else {
    secAction+='<div class="card">はっきりした不足や偏りは出ていません。'+
      'この場合は弱点を補うより、強みが活きる場面を 増やす方向に時間を使ってください。</div>';
  }
  {
    const watch=[...new Set(acts.map(a=>a.k).filter(k=>k&&s[k]!=null))];
    if(watch.length){
      const prev=loadResultSnapshot();
      const prevScores=prev&&prev.scores;
      const hasPrev=!!(prevScores && watch.some(k=>prevScores[k]!=null));
      secAction+='<div class="card"><h3 style="margin-top:0">3か月後に見るもの</h3>';
      if(hasPrev){
        const prevDate=new Date(prev.date).toLocaleDateString("ja-JP");
        secAction+='<p class="dim">この端末に残っていた前回（'+prevDate+'）の記録と自動で比べています。'+
          '他の人がこの記録を見ることはありません。'+
          'ただし前後の差が5点未満は、この診断の精度では変化として読めません'+
          '（この目安は測定誤差から求めたものではなく、暫定的に置いた値です）。</p>'+
          (prev.mode && prev.mode!==mode
            ? '<p class="dim">前回は'+MODE_LABEL[prev.mode]+'、今回は'+MODE_LABEL[mode]+'です。'+
              '版が違うと精度が変わるため、目安としてご覧ください。</p>'
            : '')+
          '<table><thead><tr><th>見る項目</th><th class="num">前回</th>'+
          '<th class="num">今回</th><th class="num">差</th></tr></thead><tbody>'+
          watch.map(k=>{
            const pv=prevScores[k], cv=T(s[k]);
            const diff=(pv!=null)? Math.round((cv-pv)*10)/10 : null;
            const diffTxt=diff==null? "—" : (diff>0?"+":"")+diff+(Math.abs(diff)<5?"（誤差の範囲）":"");
            return '<tr><td>'+SUBNAMES[k]+'</td>'+
              '<td class="num'+(pv==null?' dim':'')+'">'+(pv??"—")+'</td>'+
              '<td class="num">'+cv+'</td>'+
              '<td class="num'+(diff==null?' dim':'')+'">'+diffTxt+'</td></tr>';
          }).join('')+
          '</tbody></table>'+
          '<p class="dim" style="margin-bottom:0">この自動比較は、同じ端末・同じブラウザで続けて使った場合にだけ働きます。'+
          '別の端末で続きを見たいときは、下の「結果と回答を保存（JSON）」で書き出しておき、'+
          '次回の開始画面にある「保存したデータを読み込む」から読み込んでください。</p>';
      } else {
        secAction+='<p class="dim">全部を測り直す必要はありません。'+
          '上の対策に対応する項目だけを比べてください。'+
          'ただし前後の差が5点未満は、この診断の精度では変化として読めません'+
          '（この目安は測定誤差から求めたものではなく、暫定的に置いた値です）。'+
          'この端末で3か月後にもう一度このページを開けば、今回の記録が自動で目印として残ります。</p>'+
          '<table><thead><tr><th>見る項目</th><th class="num">今回</th>'+
          '<th class="num">次回</th></tr></thead><tbody>'+
          watch.map(k=>'<tr><td>'+SUBNAMES[k]+'</td>'+
            '<td class="num">'+T(s[k])+'</td><td class="num dim">—</td></tr>').join('')+
          '</tbody></table>';
      }
      secAction+='</div>';
    }
  }
  const secDetailNote=suggestions(s,d,order);

  SEC.action=secAction;
  /* 妥当性の確認で複数警告が出ている（参考として読んでください、という
     force表示の）結果は、信頼性が低いため次回比較の基準に使わない。
     2件以上の警告で表示自体を見合わせているときは、この行より前で
     return しているためそもそも到達しない。 */
  if(!(va && va.verdict==="再実施を推奨")) saveResultSnapshot(order, s, mode);

  /* 場面別に落とす */
  const sc=scenes(s,d);
  if(sc.length){
    let secScene='<h2>場面別に見ると</h2>'+
      '<p class="dim">上の対策は項目ごとの話でした。ここでは同じ内容を、'+
      '日常のどの場面で起きているかという切り口で読み直します。'+
      'どの項目の何点から書いているかも並べます。'+
      '違うと思ったら、その項目の設問を見直してください。</p>';
    sc.forEach(x=> secScene+='<div class="idx"><div class="idx-h">'+
      '<span class="idx-n">'+x.t+'</span></div>'+
      '<p class="idx-y">'+x.b+'</p>'+x.e+'</div>');
    SEC.scene=secScene;
  } else { SEC.scene=''; }

  /* ── 総合判定（結論を最初に置く） ── */
  let head3='';
  {
    /* 型名は先頭の「いまのあなたの位置」で示しているので、ここでは人物像を1行で繰り返す */
    const t1 = cls&&TYPEDESC[cls.name]
      ? "<b>"+TYPEDESC[cls.name].nick+"</b>（"+cls.name+"）"
      : null;
    const border = cls&&cls.border
      ? "2つの軸のどちらかが分かれ目の近くにあるため、決めつけずに読んでください。"
      : "";
    const t2 = d.pe==null? null
      : (Math.abs(d.pe)<1.5 ? "自分のルールを変えるのと、環境を変えるのと、どちらも同じくらい効きます"
        : d.pe>0 ? "行動を変えたいときは、<b>環境を整えるより自分のルールを作り直す</b>ほうが効きます"
                 : "行動を変えたいときは、<b>意志で頑張るより置かれる場を組み替える</b>ほうが効きます");
    const t3 = (d.weak && CONFLICT_SCENE[d.weak])
      ? "とくに判断や着手が止まりやすいのは<b>"+CONFLICT_SCENE[d.weak]+"</b>の場面です。"
      : "";
    const lead = t1
      ? "ここまでの内容を総合すると、あなたは"+t1+"にあたります。"+border+t3
      : "";
    head3='<div class="card" style="border-width:2px;border-color:var(--accent);box-shadow:0 2px 10px rgba(33,80,112,.10)">'+
      '<h2 style="margin-top:0;border:0;padding:0">総合判定</h2>'+
      (lead? '<p style="margin-top:0">'+lead+'</p>':'')+
      '<dl class="kv">'+
      (t2? '<dt>力の入れどころ</dt><dd>'+t2+'</dd>':'')+
      (acts.length? '<dt>最初にやること</dt><dd><b>'+acts[0].t+'</b>'+
        '<span class="dim">　── 中身はすぐ下に</span></dd>':'')+
      '</dl><p class="dim" style="margin-bottom:0">'+
      'ここまでの内容を総合して判定しました。'+
      '時間がなければ、この下の「まず何をするか」だけ読んでも足ります。</p></div>';
  }

  /* ── 画面用の組み立て：位置 → 根拠 → まとめ → 対策 → 場面 → 型（補足） → 詳細データ ──
     測定の順（妥当性→素点→指標→類型）は分析する側の順序であって、
     読む側の順序ではない。読み手の問いは
     「自分はどういう人か」「なぜそう言えるか」「だから何をすればいいか」
     の順に来るので、その順に並べ替える。
     型（4分類）は連続量である2軸の位置を切って呼び名にした入り口に
     過ぎず、結論ではない（レヴィン自身が1931年に二分法的な分類を
     批判している）。そのため「いまのあなたの位置」で軸の位置と型名の
     両方に触れたあとは、型の詳しい説明（あなたのタイプと、組むとよい
     相手）をサブコンテンツとして対策・場面のあとに回す。
     ただし21項目の図（能力系・両極性）とその読み方の解説は、
     折りたたみに入れず常時表示にする。図と、図を理解するための解説は
     省略してはならない要素であり、クリックしないと見えない場所に
     置くと「必ず出す」という要件を満たせないため。
     残りの詳細な数値・指標説明は、根拠として最後に畳んで置く。
     この内容はそのまま印刷にも使う。以前は印刷専用に構成を作り直して
     いたが、それは取りやめた。画面に表示している内容と、印刷される
     内容を一致させる（準拠させる）方針にしている。図を紙幅いっぱいに
     広げる・改ページを整える・折りたたみを開くといった印刷用の調整は
     CSS側（@media print）だけで行い、内容そのものは変えない。 */
  let screenBody = portraitBlock(cls,d)
    + SEC.profile + SEC.equation + SEC.force
    + head3 + SEC.action + SEC.scene + SEC.type
    + (va && va.verdict==="範囲内"
        ? '<details class="ex"><summary>回答の確認（問題なし）</summary><div class="body">'
          + SEC.validity + '</div></details>'
        : SEC.validity)
    + '<h2>詳しい数値</h2>'
    + '<p class="dim">ここから先は根拠です。'+
      '上の結論に納得できていれば、読まなくても差し支えありません。</p>'
    + fold("組み合わせて見える6つの指標を見る", SEC.indices)
    + fold("特徴の一覧（優劣ではないもの）を見る", secDetailNote);

  screenBody += fold("レヴィンの理論との対応・出典を見る", theorySources());
  screenBody += '<div class="note"><b>結果を使うときに</b><br>'+
     '病気の診断、向き不向きの判定、採用や人事評価には使わないでください。<br>'+
     '回答や結果は、この端末・このブラウザの中だけで処理しています。'+
     '外部のサーバーに送信されることはありません。<br>'+
     '結果は、今の環境の中でのあなたを写したものです。'+
     '環境が変われば結果も変わります。'+
     'レヴィンの理論そのものが「人は場との関わりの中で変わる」と言っているので、'+
     'それは測りそこないではなく、理論どおりの出来事です。<br>'+
     '強い疲労感や気分の落ち込みが続く場合は、この診断で対処しようとせず、'+
     '産業医・心理士など専門家に相談してください。</div>';

  h = SEC.title + screenBody;

  h+='<div class="row noprint" style="margin-top:20px">'+
     '<button class="btn" onclick="window.print()">印刷／PDF保存</button>'+
     '<button class="btn ghost" id="dl">結果と回答を保存（JSON）</button>'+
     '<button class="btn ghost" id="dlcsv">表計算用に保存（CSV）</button>'+
     '<button class="btn ghost" id="again">最初からやり直す</button></div>';

  const R=document.getElementById("result");
  R.innerHTML=h; R.classList.remove("hide");
  document.getElementById("quiz").classList.add("hide");
  const payload=()=>{
    const prof={};
    order.forEach(k=>{ prof[k]={項目:SUBNAMES[k], 専門用語:TECH[k], 領域:DOMAIN[k[0]],
      種類:(SCALETYPE[k]==="能"?"能力系":"両極性"), 素点平均:s[k], 中点スコア:T(s[k]),
      順位:rankOf[k]??null, 判定:poleBand(k,T(s[k]))}; });
    return {
      ツール:"レヴィン行動理論 特性診断", 版:"第3版", 項目版:ITEM_VERSION,
      形式:mode, 実施日時:new Date().toISOString(),
      注記:"中点スコアは規範集団データではなく、6件法の理論的中点3.50を50とした暫定値。母集団と比較したものではない。",
      妥当性:va, プロファイル:prof, リーダーシップ風土:lp,
      導出指標:{
        "自分基準か状況か（中点スコアの差）":{値:d.pe, 解釈:d.peLabel},
        "着手する力と定着させる力（素点の差）":{値:d.ffb, 解釈:d.ffbLabel},
        "抵抗への備え（反対を察知する）":d.f2,
        "迷う場面での決断力":{値:d.cti, 最も弱い型:d.weak, 最も弱い型の名称:d.weak?SUBNAMES[d.weak]:null},
        "目標の置き方":d.quad,
        "仕事の持ち帰りやすさ":{値:d.tli, 解釈:d.tliLabel},
        "環境側の内訳":d.eBreak,
        "あわせて見るもの":d.aux
      },
      類型:cls, answers
    };
  };
  const dl=(txt,name,mime)=>{
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob([txt],{type:mime}));
    a.download=name; a.click();
  };
  document.getElementById("dl").onclick=()=>
    dl(JSON.stringify(payload(),null,2),"lewin_diagnostic.json","application/json");
  document.getElementById("dlcsv").onclick=()=>{
    const q=x=>'"'+String(x).replace(/"/g,'""')+'"';
    /* ブロック1：項目別の要約（数値のみ） */
    let c="\ufeff項目版,"+ITEM_VERSION+"\n\n";
    c+="■ 項目別の要約\n";
    c+="項目コード,項目名,専門用語,領域,種類,素点平均,中点スコア,順位,判定\n";
    order.forEach(k=>{ c+=[k,q(SUBNAMES[k]),q(TECH[k]),q(DOMAIN[k[0]]),
      SCALETYPE[k]==="能"?"能力系":"両極性",s[k]??"",T(s[k])??"",rankOf[k]??"",
      q(poleBand(k,T(s[k])))].join(",")+"\n"; });
    /* ブロック2：6件法の設問明細（換算値は数値のみ） */
    c+="\n■ 設問明細（6件法）\n";
    c+="設問コード,所属項目,設問文,回答値,逆転項目,換算値\n";
    ITEMS.forEach(it=>{
      if(it.type!=="likert") return;
      const v=answers[it.id]; if(v==null) return;
      c+=[it.id, q(SUBNAMES[it.sub]||it.sub), q(it.text), v,
          it.rev?"逆転":"", conv(v,it.rev)].join(",")+"\n";
    });
    /* ブロック3：選択式の設問明細（人の動かし方。換算値は選択肢名のみ） */
    c+="\n■ 設問明細（選択式）\n";
    c+="設問コード,所属項目,設問文,回答コード,選んだ選択肢\n";
    const CH={a:"指示型",b:"合議型",c:"委任型",d:"経験なし"};
    ITEMS.forEach(it=>{
      if(it.type!=="choice") return;
      const v=answers[it.id]; if(v==null) return;
      c+=[it.id, q(SUBNAMES[it.sub]||it.sub), q(it.text), v, q(CH[v]||v)].join(",")+"\n";
    });
    dl(c,"lewin_diagnostic.csv","text/csv");
  };
  document.getElementById("again").onclick=()=>{ clearSave(); location.reload(); };
  const tg=document.getElementById("toggleEx");
  if(tg) tg.onclick=()=>{
    const ds=R.querySelectorAll("details.ex");
    const anyOpen=[...ds].some(x=>x.open);
    ds.forEach(x=>x.open=!anyOpen);
    tg.textContent = anyOpen? "解説をすべて開く" : "解説をすべて閉じる";
  };
  window.scrollTo({top:0,behavior:"instant"});
}

/* ── 対策の統合 ───────────────────────────────────────
   指標を1つずつ「あなたの場合」で解説しても、9個並べば
   どれから手を付けるのかが分からず「だから何なのか」が残る。
   ここでは全指標を横断して、効く順に3つだけ選び直す。
   優先順位はレヴィンの考え方に沿う：
   (1) 押し返す力を1段ゆるめる（推進力を足すより有効）
   (2) 能力系の明確な不足
   (3) 決められなくなる場面への手順
   (4) 着手と定着の偏り
   (5) 持ち帰りの多さ
   各項目には「なぜあなたに効くか」「今週の一歩」「放置するとどうなるか」を必ず付ける。 */
function topActions(s,d,cls){
  const A=[];
  const hold=[["F4","F4"],["E4","E4"],["E2","E2"]].filter(x=>s[x[1]]!=null)
    .sort((a,b)=>T(s[b[1]])-T(s[a[1]]));
  if(hold.length && T(s[hold[0][1]])>=56){
    const k=hold[0][1];
    const detail={
      F4:{t:"決めたことを守る力を、意図的に1つだけ外す",
          w:"「変えたことを定着させる」が"+T(s.F4)+"と高く、これが現状を保つ側で最も強く働いています。長所ですが、見直すべき手順まで残します。",
          f:"いま運用している手順のうち、根拠を説明できないものを1つ選び、「なぜ続けているか」を関係者に聞いてください。",
          n:"古い手順が積み重なり、新しいやり方を入れる余地がなくなっていきます。"},
      E4:{t:"完全な手順を待たず、暫定版で始める",
          w:"「必要とする手順の明確さ」が"+T(s.E4)+"と高く、条件が揃うまで動き出せない状態です。",
          f:"いま止まっている案件を1つ選び、80点の暫定手順を自分で書いて走らせてください。",
          n:"整うのを待つ間に機会が過ぎ、結局は誰かが決めた手順に従うだけになります。"},
      E2:{t:"「何が嫌なのか」を1点に絞り込む",
          w:"「不快な要素への感度」が"+T(s.E2)+"と高く、一部が嫌なだけで全体をあきらめかけています。",
          f:"避けている案件を1つ選び、嫌な点を箇条書きにしてください。多くの場合1つだけです。そこだけ手を打ちます。",
          n:"取り組めば済んだ仕事を避け続け、選べる範囲が少しずつ狭まります。"}
    }[k];
    A.push({p:1,...detail,k:k,tag:"押し返す力をゆるめる"});
  }
  const low=["P4","P5","E3","F1","F2","F3","F4"].filter(k=>s[k]!=null&&T(s[k])<40)
    .sort((a,b)=>T(s[a])-T(s[b]));
  if(low.length){
    const k=low[0];
    A.push({p:2,tag:"不足を補う",k:k,
      t:"「"+SUBNAMES[k]+"」を、意志ではなく仕組みで補う",
      w:"「"+SUBNAMES[k]+"」が"+T(s[k])+"で、能力系11項目の中で最も低く出ています。",
      f:LOWRX[k],
      n:"この工程が抜けたまま進むため、努力の量にかかわらず同じところで止まり続けます。"});
  }
  if(d.weak){
    A.push({p:3,tag:"決まらない場面を通り抜ける",k:d.weak,
      t:"「"+CONFLICT_SCENE[d.weak]+"」用の手順を、先に決めておく",
      w:"4つの決断場面のうち「"+SUBNAMES[d.weak]+"」が"+T(s[d.weak])+"と最も低く出ています。ここで止まりやすいということです。",
      f:CONFLICT_RX[d.weak],
      n:"決めないまま時間が過ぎ、選択肢が減ってから決めるはめになります。"});
  }
  if(d.ffb!=null && Math.abs(d.ffb)>=5.9){
    A.push(d.ffb>0
      ? {p:4,tag:"偏りを補う",k:"F4",t:"変えたことを、記録に残すところまでを1件と数える",
         w:"着手する力が定着させる力を"+d.ffb+"上回っています。始めるのは得意で、根づかせる側が弱いという組み合わせです。",
         f:"直近で変えたことを1つ選び、手順書か記録用紙のどちらかを今週中に直してください。",
         n:"あなたが見ていない間に元へ戻り、同じ改善を何度もやり直します。"}
      : {p:4,tag:"偏りを補う",k:"F1",t:"口火は人に任せ、2番目に入る",
         w:"定着させる力が着手する力を"+Math.abs(d.ffb)+"上回っています。動き出したものを最後まで運べます。",
         f:"周囲で始まりかけている取り組みを1つ選び、実務の引き受け役として名乗り出てください。",
         n:"自分から始めようとして消耗し、本来得意な定着の役割が活きないままになります。"});
  }
  if(d.tli!=null && d.tli>=11.8){
    A.push({p:5,tag:"消耗を止める",k:"P5",t:"終業時に、未完了を書き出して閉じる",
      w:"未完了の残りやすさが切り替える力を"+d.tli+"上回っており、仕事が生活側へにじみ出ています。",
      f:"今日から、退勤前の3分でやり残しを紙に書き出してください。書けば脳は「預けた」と扱います。",
      n:"休んでも回復しきらない状態が続き、集中力そのものが落ちていきます。"});
  }
  if(!A.length){
    /* 不足も偏りもない場合。補強すべき点がないので、
       強みが効く場面を増やす方向で1つだけ出す。 */
    const abil=["P4","P5","E3","C1","C2","C3","C4","F1","F2","F3","F4"]
      .filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));
    /* 強みを使う対策に加えて、相対的に低いほうも1つ挙げる。
       1つだけだと、根拠の章のほうが長くなってしまう。 */
    if(abil.length>=2){
      const low=abil[abil.length-1];
      A.push({p:9.5,tag:"底を上げる",k:low,
        t:"「"+SUBNAMES[low]+"」を、意識して使う場面を作る",
        w:"不足というほどではありませんが、11項目の中では最も低いところです（"+T(s[low])+"）。"+
          "偏りが小さいうちに底を上げておくと、強みが効く場面が広がります。",
        f:LOWRX[low] || "この力が要る場面を、今週1つだけ意識して引き受けてください。",
        n:"いまは困りませんが、負荷が上がったときに最初に崩れるのがここです。"});
    }
    if(abil.length){
      const top=abil[0];
      A.push({p:9,tag:"強みを使う",k:top,
        t:"「"+SUBNAMES[top]+"」が活きる場面を、意図的に増やす",
        w:"目立った不足や偏りはありません。この場合、足りないところを補うより、"+
          "すでに高いところが効く場面を増やすほうが成果につながります。"+
          "いま最も高いのは「"+SUBNAMES[top]+"」（"+T(s[top])+"）です。",
        f:"今週の予定から、この力が要る場面を1つ選んでください。"+
          "なければ、自分から引き受ける先を1つ作ってください。",
        n:"平均的な状態のまま時間が過ぎ、何が自分の武器なのか分からなくなります。"});
    }
  }
  return A.sort((a,b)=>a.p-b.p).slice(0,3);
}

function actionCard(a,i){
  return '<div class="idx"><div class="idx-h">'+
    '<span class="tag">対策 '+(i+1)+'</span>'+
    '<span class="idx-n">'+a.t+'</span></div>'+
    '<p class="idx-y"><b style="color:var(--accent)">なぜあなたに効くか</b>　'+a.w+'</p>'+
    '<p class="idx-y"><b style="color:var(--accent)">今週の一歩</b>　'+a.f+'</p>'+
    '<p class="idx-w">放置すると：'+a.n+'</p></div>';
}

/* 中身が空の章は折りたたみごと出さない（版によって存在しない章がある） */
function fold(title, body){
  return (body && body.trim())
    ? '<details class="ex"><summary>'+title+'</summary><div class="body">'+body+'</div></details>'
    : '';
}

/* ── 反証できる形で提示する ─────────────────────────────
   「あなたは調整力があります」のような文は、誰にでも当てはまるため
   当たっていなくても読み手が気づけない（バーナム効果）。
   フォアラーの結論は「感じられる正確さを妥当性の証拠にしてはならない」。
   そこでタイプを言い渡す代わりに、観察できる出来事で本人に確かめてもらう。
   これは正式なMBTIが専門家との対話で行う「ベストフィットタイプの確認」を、
   ひとりでもできる形に落としたもの。 */
function axisBar(label, lo, hi, v, range){
  const pct=Math.max(0,Math.min(100,(v+range)/(range*2)*100));
  return '<div class="axis"><div class="axis-l">'+lo+'</div>'+
    '<div class="axis-t"><i style="left:'+pct.toFixed(1)+'%"></i>'+
    '<u></u></div><div class="axis-r">'+hi+'</div>'+
    '<div class="axis-v">'+(v>0?'+':'')+v+'</div></div>'+
    '<div class="axis-n">'+label+'</div>';
}

function portraitBlock(cls,d){
  if(!cls) return '';
  const td=TYPEDESC[cls.name];
  if(!td || !td.checks) return '';
  const other=TYPEDESC[td.near];
  let axes='';
  if(d && d.pe!=null && d.ffb!=null){
    axes='<div class="axes">'+
      axisBar("その場の条件で動くか、自分の基準で動くか","場の条件寄り","自分の基準寄り",d.pe,12)+
      axisBar("根づかせる側か、起こす側か","定着寄り","着手寄り",d.ffb,1.6)+
      '</div>'+
      '<p class="dim">この2本の位置から下の呼び名がつきます。'+
      '<b>位置のほうが本体で、呼び名は入り口です。</b>'+
      '0に近いほど、呼び名は入れ替わりやすくなります。</p>';
  }
  return '<div class="card" style="border-width:2px;border-color:var(--accent);box-shadow:0 2px 10px rgba(33,80,112,.10)">'+
    '<h2 style="margin-top:0;border:0;padding:0">いまのあなたの位置</h2>'+
    axes+
    '<div class="type">'+td.nick+'<span class="dim" style="font-size:14px;font-weight:400">'+
      '　── '+cls.name+'</span></div>'+
    '<p style="margin:6px 0 14px">'+td.portrait+'</p>'+
    '<h3 style="margin-top:0">こんなこと、ありませんか</h3>'+
    '<ul class="chk">'+td.checks.map(c=>'<li>'+c+'</li>').join('')+'</ul>'+
    '<div class="note" style="margin-bottom:0"><b>当てはまるものが0〜1個なら、この判定は外れています。</b><br>'+
    '心当たりがなければ、'+(other? '<b>'+other.nick+'（'+td.near+'）</b>':'ほかの型')+
    'の説明のほうが近いかもしれません（下の「あなたのタイプと、組むとよい相手」に4つとも載せています）。'+
    '<span class="dim">型の名前の再現性については、後半の「この診断が測れていないこと」に書いています。</span></div></div>';
}

/* ── 場面別に落とす ───────────────────────────────────
   対策だけでは「日常のどの瞬間の話か」が見えない。
   4つの場面それぞれについて、根拠となる項目と実測値を明示したうえで
   文章を出し分ける。数値が変われば文章も変わるので、
   誰にでも当てはまる記述にはならない。 */
function scenes(s,d){
  const has=(...ks)=>ks.every(k=>s[k]!=null);
  const hi=k=>T(s[k])>=60, lo=k=>T(s[k])<40;
  const ev=(...ks)=>'<p class="idx-w">根拠：'+
    ks.filter(k=>s[k]!=null).map(k=>SUBNAMES[k]+' '+T(s[k])).join('　／　')+'</p>';
  const out=[];

  if(has("P1","P5")){
    let t;
    if(hi("P1")&&lo("P5")) t="締切前は集中できます。ただし終わったあとも緊張が残り、休んだ感覚のないまま次に入ります。区切る手続きがないと、疲れだけが積み上がります。";
    else if(hi("P1")) t="締切前に集中でき、終わればきちんと切り替えられます。負荷のかかり方としては望ましい組み合わせです。";
    else if(lo("P1")&&!lo("P5")) t="やりかけが気にかからないぶん、締切が近づくまで動き出さない可能性があります。着手する日そのものを予定に入れておくと確実です。";
    else if(lo("P1")&&lo("P5")) t="締切に追われる感覚は薄いほうです。ただし切り替えも得意ではないので、締切とは別のところで疲れが残ります。";
    else t="締切への反応は、強くも弱くもありません。忙しい時期にだけ区切りを足せば足ります。";
    out.push({t:"締切の前で",b:t,e:ev("P1","P5")});
  }
  if(has("G1","G2")){
    let t = lo("G1") ? "反対意見は、その場よりあとから出てくるほうです。決まったあとで違和感が残りやすくなります。"
          : hi("G1") ? "違うと思えばその場で言えます。全員が同じ方向を向いて硬直した場面で、流れを変えられる立場です。"
          : "場に応じて、言うか控えるかを使い分けているようです。";
    t += hi("G2") ? "決め方は、関係者で話し合うほうを選びます。決まったことは根づきますが、時間はかかります。"
       : lo("G2") ? "決め方は、責任者が決めて示すほうが速いと考えています。速いぶん、現場では根づきません。"
       : "決め方は、状況によって使い分けています。";
    out.push({t:"会議で",b:t,e:ev("G1","G2")});
  }
  if(d.ffb!=null && s.F2!=null){
    let t = d.ffb>=1.76 ? "始めるのは得意です。ただし、あなたが見ていないと元に戻ります。変えたことを手順書か記録に落とすまでが1件です。"
          : d.ffb<=-1.76 ? "口火を切るのは得意ではありませんが、動き出したものは最後まで運べます。2番目に入る役回りが向いています。"
          : "始める力と根づかせる力がつり合っています。ひとりで最後まで運べる反面、負荷も全部ひとりに来ます。";
    t += T(s.F2)>=60 ? "反対しそうな人と、その理由に見当がつきます。" :
         T(s.F2)<40 ? "反対は表面化してから気づきがちです。変える前に「誰が損をするか」を3人分書き出すと変わります。" :
         "反対への備えは平均的です。大きな変更のときだけ、事前の聞き取りを増やしてください。";
    out.push({t:"新しいやり方を入れるとき",b:t,e:ev("F1","F3","F4","F2")});
  }
  if(s.E2!=null){
    let t = T(s.E2)>=60 ? "気の進まない要素が1つあると、その場ごと投げ出しかけます。たいてい嫌なのは1点だけなので、それを書き出せば戻れます。"
          : T(s.E2)<40 ? "多少不快な条件でも前に進めます。ただし、まずい兆候そのものを見落とすことがあるため、定点で確認する項目を決めておくと安全です。"
          : "不快さへの反応は極端ではありません。";
    if(d.tli!=null && d.tli>=1) t+="あわせて、仕事が生活の側までしみ出しています。休むつもりでは休めないので、区切る手続きを決めてください。";
    if(s.E1!=null && T(s.E1)>=60) t+="いっぽう、良い環境に移ったときの戻りは速いほうです。場所や道具を変えると効きます。";
    out.push({t:"うまくいかないとき",b:t,e:ev("E2","E1")});
  }
  return out;
}

function idxCard(key, val, tag, override){
  const m=IDX[key];
  if(val==null) return '';
  const body = override || (m.r? m.r(val) : null);
  return '<div class="idx"><div class="idx-h">'+
    '<span class="idx-n">'+m.n+'</span>'+
    '<span class="idx-v">'+val+'</span>'+
    '<span class="dim" style="font-size:11.5px">'+m.u+
      (m.t? '　専門用語：'+m.t : '')+'</span>'+
    (tag? '<span class="tag">'+tag+'</span>' : '')+
    '</div><p class="idx-w">見ているもの：'+m.w+'</p>'+
    (body? '<p class="idx-y"><b style="color:var(--accent)">あなたの場合</b>　'+body+'</p>' : '')+
    '</div>';
}

/* レーダーチャートは撤去した（所見18）。理由は2つ：
   (1) 20〜21軸は可視化の定石（推奨5〜8軸）から大きく外れ、面積は軸の並び順で
       変わるため誤読を招く。
   (2) 領域平均に、能力系尺度（高いほど良い）と両極性尺度（高低に優劣なし）が
       混在する領域（P・E）があり、平均という操作自体の意味が定まらない。
   共通の基線（中点50）を持つドットプロットのほうが、誤読の余地なく
   20項目すべてを正確に比較できる。 */

/* 能力系と両極性は「意味」が違うので、1枚の図に混ぜない。
   偏差バーという図法自体が「右に伸びるほど良い」という印象を与えるため、
   両極性の項目を同じ図に置くと、左端＝弱点という誤読を招く。
   ・能力系  → 中点50を基線とする偏差バー（左＝補強の余地／右＝強み）
   ・両極性  → 両端に意味を書いたセマンティック・ディファレンシャル
              （バーを塗らず、点の位置だけで「どちら寄りか」を示す）
   領域（P/E/C/F/G）のまとまりは、どちらの図でも見出しとして保つ。 */

function abilityPlot(s, keys, rowH){
  rowH = rowH || 23;
  const rows=keys.filter(k=>T(s[k])!=null);
  if(!rows.length) return '';
  const W=620, L=210, R=44, plotW=W-L-R, H=rows.length*rowH+58;
  const x = t => L + (t-20)/60*plotW;
  let g='<svg viewBox="0 0 '+W+' '+H+'" role="img" '+
    'aria-label="能力系の項目の中点スコア。中点50より右が強み、左が補強の余地。数値は下の表にもあります。">';
  [20,30,40,50,60,70,80].forEach(t=>{
    const major=(t===50);
    g+='<line x1="'+x(t)+'" y1="26" x2="'+x(t)+'" y2="'+(H-30)+'" stroke="'+
       (major?"#7d858d":"#dfe3e7")+'" stroke-width="'+(major?1.4:1)+'"'+
       (major?' stroke-dasharray="4 3"':'')+'/>';
    g+='<text x="'+x(t)+'" y="18" font-size="10" fill="currentColor" opacity=".72" text-anchor="middle">'+t+'</text>';
  });
  rows.forEach((k,i)=>{
    const y=40+i*rowH, t=T(s[k]), col=DCOLOR[k[0]];
    g+='<text x="'+(L-10)+'" y="'+(y+4)+'" font-size="11" fill="currentColor" text-anchor="end">'+
       SUBNAMES[k]+'</text>';
    g+='<line x1="'+x(50)+'" y1="'+y+'" x2="'+x(t)+'" y2="'+y+'" stroke="'+col+
       '" stroke-width="5" opacity=".38" stroke-linecap="round"/>';
    g+='<circle cx="'+x(t)+'" cy="'+y+'" r="4.6" fill="'+col+'"/>';
    g+='<text x="'+(x(t)+(t>=50?10:-10))+'" y="'+(y+4)+'" font-size="10.5" fill="currentColor" '+
       'opacity=".8" text-anchor="'+(t>=50?"start":"end")+'">'+t+'</text>';
  });
  g+='<text x="'+x(35)+'" y="'+(H-10)+'" font-size="10.5" fill="currentColor" opacity=".8" text-anchor="middle">← 補強の余地</text>';
  g+='<text x="'+x(50)+'" y="'+(H-10)+'" font-size="10.5" fill="currentColor" opacity=".6" text-anchor="middle">中点</text>';
  g+='<text x="'+x(65)+'" y="'+(H-10)+'" font-size="10.5" fill="currentColor" opacity=".8" text-anchor="middle">強み →</text>';
  return g+'</svg>';
}

function bipolarPlot(s, keys, rowH){
  rowH = rowH || 33;
  const rows=keys.filter(k=>T(s[k])!=null && POLES[k]);
  if(!rows.length) return '';
  const W=620, L=168, R=168, plotW=W-L-R, H=rows.length*rowH+58;
  const x = t => L + (t-20)/60*plotW;
  let g='<svg viewBox="0 0 '+W+' '+H+'" role="img" '+
    'aria-label="両極性の項目の位置。左右の端にそれぞれの意味を示しています。どちらが優れているという図ではありません。">';
  [20,35,50,65,80].forEach(t=>{
    const major=(t===50);
    g+='<line x1="'+x(t)+'" y1="26" x2="'+x(t)+'" y2="'+(H-28)+'" stroke="'+
       (major?"#7d858d":"#e6e9ec")+'" stroke-width="'+(major?1.4:1)+'"'+
       (major?' stroke-dasharray="4 3"':'')+'/>';
  });
  g+='<text x="'+x(50)+'" y="18" font-size="10" fill="currentColor" opacity=".6" text-anchor="middle">どちらでもない</text>';
  rows.forEach((k,i)=>{
    const y=40+i*rowH, t=T(s[k]), col=DCOLOR[k[0]], pole=POLES[k];
    /* 目盛り線だけを引き、バーは塗らない。塗ると「量」に見えてしまう。 */
    g+='<line x1="'+x(20)+'" y1="'+y+'" x2="'+x(80)+'" y2="'+y+'" stroke="'+col+
       '" stroke-width="1.2" opacity=".22"/>';
    g+='<text x="'+(L-10)+'" y="'+(y+4)+'" font-size="10.5" fill="currentColor" opacity=".85" text-anchor="end">'+
       pole[0]+'</text>';
    g+='<text x="'+(W-R+10)+'" y="'+(y+4)+'" font-size="10.5" fill="currentColor" opacity=".85">'+
       pole[1]+'</text>';
    g+='<circle cx="'+x(t)+'" cy="'+y+'" r="5.4" fill="'+col+'"/>';
    g+='<circle cx="'+x(t)+'" cy="'+y+'" r="9" fill="none" stroke="'+col+'" stroke-width="1" opacity=".35"/>';
    g+='<text x="'+x(t)+'" y="'+(y-13)+'" font-size="10" fill="currentColor" opacity=".8" text-anchor="middle">'+
       SUBNAMES[k]+'</text>';
  });
  g+='<text x="'+x(50)+'" y="'+(H-8)+'" font-size="10.5" fill="currentColor" opacity=".75" text-anchor="middle">'+
     '点の位置が、どちら寄りかを表します</text>';
  return g+'</svg>';
}

/* F2「反対を察知する」は保持側（今のままにしておく力）には入れない。
   反対の察知は変化を妨げる力ではなく、変化を成功させる対処能力であり、
   誤って保持側に数えると、変革に長けた人ほど「定着が優位」と誤判定される
   （所見9）。図の外に別枠で示す。 */
function forcefield(s, rowH){
  rowH = rowH || 34;
  /* 表示する数値は中点スコアに統一する。矢印の長さは相対的な大きさが
     分かればよいので、中点スコアでも図の意味は変わらない。 */
  const drive=[["F1",T(s.F1)],["F3",T(s.F3)],["P2",T(s.P2)],["E3",T(s.E3)]]
    .filter(x=>x[1]!=null).map(x=>[forceLabel(x[0]),x[1]]);
  const hold=[["F4",T(s.F4)],["E4",T(s.E4)],["E2",T(s.E2)]]
    .filter(x=>x[1]!=null).map(x=>[forceLabel(x[0]),x[1]]);
  const H=Math.max(drive.length,hold.length)*rowH+70;
  let g='<svg viewBox="0 0 620 '+H+'" role="img" aria-label="力の場分析">';
  g+='<line x1="310" y1="20" x2="310" y2="'+(H-30)+'" stroke="var(--axis)" stroke-width="2"/>';
  g+='<text x="310" y="'+(H-12)+'" font-size="11" text-anchor="middle" fill="#5b636c">今の状態</text>';
  g+='<text x="120" y="16" font-size="11" fill="#2f5d7c" text-anchor="middle">変えようとする力</text>';
  g+='<text x="500" y="16" font-size="11" fill="#8a5a4a" text-anchor="middle">今のままにしておく力</text>';
  drive.forEach((x,i)=>{ const y=42+i*rowH, len=Math.max(24,((x[1]-20)/60)*180);
    g+='<line x1="'+(305-len)+'" y1="'+y+'" x2="300" y2="'+y+'" stroke="var(--drive)" stroke-width="'+
      (1+(x[1]-20)/20).toFixed(1)+'" marker-end="url(#ar1)"/>'+
      '<text x="'+(300-len-8)+'" y="'+(y+4)+'" font-size="11" text-anchor="end" fill="#1c1f23">'+
      x[0]+' <tspan fill="#5b636c">'+x[1]+'</tspan></text>'; });
  hold.forEach((x,i)=>{ const y=42+i*rowH, len=Math.max(24,((x[1]-20)/60)*180);
    g+='<line x1="'+(315+len)+'" y1="'+y+'" x2="320" y2="'+y+'" stroke="var(--hold)" stroke-width="'+
      (1+(x[1]-20)/20).toFixed(1)+'" marker-end="url(#ar2)"/>'+
      '<text x="'+(320+len+8)+'" y="'+(y+4)+'" font-size="11" fill="#1c1f23">'+
      x[0]+' <tspan fill="#5b636c">'+x[1]+'</tspan></text>'; });
  g+='<defs><marker id="ar1" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'+
     '<path d="M0,0 L7,3 L0,6 z" fill="var(--drive)"/></marker>'+
     '<marker id="ar2" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'+
     '<path d="M0,0 L7,3 L0,6 z" fill="var(--hold)"/></marker></defs></svg>'+
     '<p class="dim">矢印の太さと長さは、それぞれの得点の大きさを表します。'+
     (s.F2!=null? '「反対を察知する」は、妨げる力ではないのでこの図には入れていません。' : '')+'</p>';
  return g;
}

function equation(s,d,order){
  const pArr=["P1","P2","P3","P4","P5"].filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));
  if(pArr.length<3) return '<div class="eq">P領域の回答が不足しているため、行動方程式は算出できません。</div>';
  const hi=pArr.slice(0,2), lo=pArr[pArr.length-1];
  /* E側の代表からE3（回り道を見つける）を除く。E3は能力系尺度で、
     「環境の見え方」を表す感受性の尺度ではないため（所見3）。 */
  const eArr=["E1","E2","E4"].filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));
  const eTop=eArr[0];
  const f = (k)=> sideLabel(k,T(s[k]));
  /* 両極性の項目は、低いことが不足を意味しない。
     「◯◯が低く、妨げになっています」と書くと、
     その項目の低い側が持つ特性を欠点として提示してしまう。 */
  const lowTxt = (k)=>{
    const t=T(s[k]);
    if(isBip(k))
      return 'いっぽう<b>'+SUBNAMES[k]+'</b>（'+t+'）は「'+sidePole(k,t)+'」側です。'+
             'これは不足ではなく、もう一方の側の特性です。';
    return t<40 ? 'いっぽうで'+f(k)+'が低く、ここが動きの妨げになっています。'
                : '低めなのは'+f(k)+'ですが、中点に近い範囲に収まっています。';
  };
  const spread = T(s[hi[0]]) - T(s[lo]);
  /* この章は本ツールの主コンテンツなので、測定している5項目・3項目を
     できるだけ本文の語りに含める。全項目そろっているときだけこの
     フルプロファイル版を使い、そろわない版（スクリーニング等）では
     従来どおり上位・下位だけを述べる簡易版にフォールバックする。 */
  const pBip=["P1","P2","P3"].filter(k=>s[k]!=null)
    .sort((a,b)=>Math.abs(T(s[b])-50)-Math.abs(T(s[a])-50));
  const pAbl=["P4","P5"].filter(k=>s[k]!=null).sort((a,b)=>T(s[b])-T(s[a]));
  let pTxt;
  if(pBip.length===3 && pAbl.length===2){
    const hiK=pAbl[0], loK=pAbl[1];
    /* 「強み」は band() の基準（60以上で中点より上）に合わせる。
       pAbl内で相対的に高いというだけでhiKを「強み」と呼ぶと、
       両方が40未満（不足水準）でも高いほうが強みとして表示され、
       他章の「40未満＝不足」という基準と矛盾する。 */
    pTxt = 'あなたの中の5つの要素は、それぞれ次の位置にあります。'+
      pBip.map(k=>f(k)).join('、')+'という位置です。<br>'+
      '能力の面では'+
      (T(s[hiK])>=60? f(hiK)+'が強みで、' : f(hiK)+'がやや高いものの際立った強みではなく、')+
      f(loK)+'は'+
      (T(s[loK])<40? 'やや低く、ここに伸びしろがあります。' : '中点に近い範囲に収まっています。');
  } else if(spread < 10){
    pTxt = '自分の中の5つの項目に大きな差がありません（最も高い所と低い所の差は'+
      Math.round(spread)+'点）。特定の力がとびぬけてあなたを動かしている状態ではありません。'+
      'この場合、行動を決めているのは自分の側の偏りよりも、その時々の場の条件です。'+
      '強いていえば'+f(hi[0])+'がやや目立ち、'+SUBNAMES[lo]+'は中点寄りです。';
  } else {
    pTxt = 'あなたを主に動かしているのは、'+f(hi[0])+'と'+f(hi[1])+'です。'+lowTxt(lo);
  }
  const eBip=["E1","E2","E4"].filter(k=>s[k]!=null)
    .sort((a,b)=>Math.abs(T(s[b])-50)-Math.abs(T(s[a])-50));
  const eTxt = eBip.length===3
    ? '環境の側では、'+eBip.map(k=>f(k)).join('、')+'という位置にあります。'
    : eTop? '環境の側では'+f(eTop)+'が最も強く働いています。' : '';
  let txt='<div class="eq">あなたの行動 <b>B</b> は、次のように書けます。<br><br>'+
    '<b>B = f(P, E)</b>　（行動は、その人と環境の両方で決まる）<br><br>'+
    '<b>P＝あなたという人</b>　'+pTxt+'<br><br>'+
    '<b>E＝あなたから見えている環境</b>　'+eTxt+
    'この感じ方が、あなたにとっての場の見え方を決めています。'+
    '<span class="dim">（この「環境」が何を指すかは、最後の章で触れます）</span><br><br>'+
    '<b>2つのつながり方</b>　';
  if(d.pe!=null){
    txt += '「自分基準で動くか、状況で動くか」の差は '+d.pe+' でした。あなたは'+
      (Math.abs(d.pe)<1.5 ? "環境の条件と自分の中の基準を、ほぼ同じくらい使っている"
        : d.pe>0?"環境よりも、自分の中の基準で動く":"自分の中の基準よりも、その場の条件に合わせて動く")+
      'ほうです。';
  }
  if(d.ffb!=null){
    txt += 'そこに「着手する力と定着させる力」の差'+d.ffb+'（'+d.ffbLabel+'）を重ねると、'+
      'あなたの行動を最も大きく変えるのは、'+
      (d.pe>0 ? "環境を整えることよりも<b>「自分のルールをどう作るか」</b>のほうです。"
               : "自分に言い聞かせることよりも<b>「置かれる場をどう組み替えるか」</b>のほうです。");
  }
  return txt+'</div>';
}

/* 低得点が「不足」を意味する能力系尺度のみを提案対象にする。
   P1/P2/P3/E1/E2/E4/G1/G2/G4 は高低が優劣ではない両極性尺度なので、
   改善対象ではなく「特徴」として別に扱う。
   改善対象の判定基準は、第1章の判定帯（band()）と同じ「中点スコア40未満」を
   使う。以前は素点<3.5という別基準を使っており、第1章で「中点に近い」と
   表示された項目が第6章では改善対象に挙がるという矛盾があった（所見4）。 */
const SUGGEST_POOL=["P4","P5","E3","F1","F2","F3","F4"];

function suggestions(s,d,order){
  /* ここは両極性の項目の「特徴」だけを載せる。
     具体的な対策は「まず何をするか」に一本化しているので繰り返さない。 */
  /* 該当するものを全部並べると9項目近くになり、「特徴」ではなくなる。
     中点から離れている順に3つまでに絞る。 */
  const bp=Object.keys(BIPOLAR).filter(k=>s[k]!=null && (T(s[k])>=60||T(s[k])<40))
    .sort((a,b)=>Math.abs(T(s[b])-50)-Math.abs(T(s[a])-50)).slice(0,3);
  if(!bp.length) return '<p class="dim">中点から大きく離れている項目はありません。</p>';
  let h='<p class="dim">高い・低いに優劣のない項目のうち、'+
    '中点から離れている順に3つ挙げます。直す対象ではなく、'+
    '知っておくと動きやすくなる特徴です。</p><ul>';
  bp.forEach(k=>{ const t=T(s[k]);
    h+='<li><b>'+SUBNAMES[k]+'</b>（'+t+'／「'+sidePole(k,t)+'」の側）'+
      '<br><span class="dim">'+
      (t>=60? BIPOLAR[k][0] : BIPOLAR[k][1])+'</span></li>'; });
  return h+'</ul>';
}
</script>
</body>
</html>
"""


def main():
    items = build_items()
    html = (TEMPLATE
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__SUBS__", json.dumps(list(SUBSCALES), ensure_ascii=False))
            .replace("__SUBNAMES__", json.dumps(SUBSCALES, ensure_ascii=False))
            .replace("__TECH__", json.dumps(TECH, ensure_ascii=False))
            .replace("__POLES__", json.dumps(POLES, ensure_ascii=False))
            .replace("__ITEM_VERSION__", ITEM_VERSION))
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "..", "assets"), exist_ok=True)
    out = os.path.join(here, "..", "assets", "diagnostic_tool.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    # GitHub Pages はリポジトリ直下の index.html を配信する。
    # 既にその配置（Pages公開済み）のプロジェクトでだけ、ビルドのたびに同期する。
    index_path = os.path.join(here, "..", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
    names_path = os.path.join(here, "..", "assets", "scale_names.json")
    with open(names_path, "w", encoding="utf-8") as f:
        json.dump({"subscales": SUBSCALES, "tech": TECH, "poles": POLES},
                  f, ensure_ascii=False, indent=1)

    # score.py が版（full/short/screening）を認識して欠測比率を正しく計算できるよう、
    # 項目一覧をそのまま書き出す。以前の score.py は常に全132問を前提にしており、
    # 短縮版のJSONを読ませると存在しない設問まで「欠測」として数えてしまう
    # バグがあった（所見13の実装中に発見）。
    manifest_path = os.path.join(here, "..", "assets", "items_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"item_version": ITEM_VERSION, "items": items}, f, ensure_ascii=False, indent=1)

    n_lik = sum(1 for i in items if i["type"] == "likert")
    n_ch = sum(1 for i in items if i["type"] == "choice")
    print(f"生成: {os.path.normpath(out)}")
    if os.path.exists(index_path):
        print(f"  同期: {os.path.normpath(index_path)}（GitHub Pages用）")
    print(f"  6件法 {n_lik}問 ／ 強制選択 {n_ch}問 ／ 合計 {len(items)}問")
    print(f"  短縮版 {sum(1 for i in items if i['short'])}問"
          f" ／ スクリーニング版 {sum(1 for i in items if i['screen'])}問")


if __name__ == "__main__":
    main()
