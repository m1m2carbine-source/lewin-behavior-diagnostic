#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レヴィン行動理論 特性診断　採点スクリプト（第3版）

使い方:
    python score.py answers.json
    python score.py answers.json --json     # 機械可読な出力

answers.json の形式:
{
  "form": "full",                 # full | short | screening（「形式」キーでも可）
  "answers": {
    "P1-1": 5, "P1-2": 4, ...,    # 6件法は 1-6 の整数
    "G3-1": "b", "G3-2": "a", ... # G3 は "a"/"b"/"c"/"d"（dは経験なし）
  }
}

無回答は キーを省略するか null にする。

このスクリプトの採点ロジックは assets/diagnostic_tool.html（build_tool.pyが
生成するJS）と厳密に一致させている。項目一覧・逆転区分・版ごとの項目集合は
assets/items_manifest.json を単一の出典として読み込む。このファイルが
無い場合はビルドされていないとみなしエラーにする（食い違った採点を防ぐため）。
"""

import json
import os
import sys
import statistics
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

# ---------------------------------------------------------------------------
# 項目データの読み込み（build_tool.py が生成する manifest を単一の出典とする）
# ---------------------------------------------------------------------------

_manifest_path = os.path.join(ROOT, "assets", "items_manifest.json")
_names_path = os.path.join(ROOT, "assets", "scale_names.json")

if not os.path.exists(_manifest_path):
    sys.exit(
        "assets/items_manifest.json が見つかりません。\n"
        "先に `python scripts/build_tool.py` を実行してビルドしてください。"
    )

with open(_manifest_path, encoding="utf-8") as _f:
    _manifest = json.load(_f)

ITEM_VERSION = _manifest["item_version"]
ALL_ITEMS = _manifest["items"]  # [{id, sub, type, text, rev?, opts?, short, screen}, ...]
ITEMS_BY_ID = {it["id"]: it for it in ALL_ITEMS}

SUBSCALE_NAMES = OrderedDict()
TECH = {}
POLES = {}
if os.path.exists(_names_path):
    with open(_names_path, encoding="utf-8") as _f:
        _n = json.load(_f)
    SUBSCALE_NAMES = OrderedDict(_n.get("subscales", {}))
    TECH = _n.get("tech", {})
    POLES = _n.get("poles", {})

DOMAIN_OF = {"P": "本人の側の力", "E": "環境の見え方", "C": "迷う場面",
             "F": "変える力", "G": "集団の中での動き"}

# 能力系＝低いと不足を意味する／両極性＝高低に優劣がない（build_tool.pyのSCALETYPEと同一）
SCALE_TYPE = {"P1": "両", "P2": "両", "P3": "両", "P4": "能", "P5": "能",
              "E1": "両", "E2": "両", "E3": "能", "E4": "両",
              "C1": "能", "C2": "能", "C3": "能", "C4": "能",
              "F1": "能", "F2": "能", "F3": "能", "F4": "能",
              "G1": "両", "G2": "両", "G4": "両"}

CONSISTENCY_PAIRS = [
    ("V2-1", "P1-1"), ("V2-2", "P2-1"), ("V2-3", "P3-1"),
    ("V2-4", "E4-1"), ("V2-5", "F4-1"), ("V2-6", "G1-2"),
]

# 得点が出る20尺度の表示順（build_tool.py の order 配列と同一）。
# scale_names.json はUI表示用にG3（選択式・得点なし）も含むため、
# プロファイル集計はこの明示リストに限定する。
SCORED_SUBS = ["P1", "P2", "P3", "P4", "P5", "E1", "E2", "E3", "E4",
               "C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4",
               "G1", "G2", "G4"]


def items_for_form(form):
    if form == "short":
        return [it for it in ALL_ITEMS if it.get("short")]
    if form == "screening":
        return [it for it in ALL_ITEMS if it.get("screen")]
    return list(ALL_ITEMS)


# ---------------------------------------------------------------------------
# 基礎関数
# ---------------------------------------------------------------------------

def conv(v, rev):
    return (7 - v) if rev else v


def mean(vals):
    vals = [v for v in vals if v is not None]
    return statistics.mean(vals) if vals else None


def r2(x):
    return None if x is None else round(x, 2)


def mean_of(scores, keys):
    vals = [scores.get(k) for k in keys if scores.get(k) is not None]
    return round(statistics.mean(vals), 2) if vals else None


def t_score(m):
    """「中点スコア」：規範集団のデータではなく、6段階の理論的中点（3.50）を
    50とした暫定値。境界30/40/60/70は20000人規模のモンテカルロ検証で、
    両端の出現率がそれぞれ約6%になるよう校正した（build_tool.pyのT()と同一式）。"""
    if m is None:
        return None
    t = 50 + 10 * (m - 3.50) / 0.85
    return round(max(20, min(80, t)), 1)


def band(t):
    if t is None:
        return "測定できません"
    if t >= 70:
        return "中点よりかなり上"
    if t >= 60:
        return "中点より上"
    if t >= 40:
        return "中点に近い"
    if t >= 30:
        return "中点より下"
    return "中点よりかなり下"


def pole_band(k, t):
    """両極性の項目は「中点より下」ではなく「どちら寄りか」で示す。
    表示名を高い側の極にすると低い人の行が自己矛盾するため、表示名は
    次元名にし、方向は極ラベルが担う（build_tool.py の poleBand と同一）。"""
    if t is None:
        return "測定できません"
    if SCALE_TYPE.get(k) != "両" or k not in POLES:
        return band(t)
    lo, hi = POLES[k]
    if t >= 70:
        return f"「{hi}」に強く寄る"
    if t >= 60:
        return f"「{hi}」寄り"
    if t > 40:
        return "どちらでもない"
    if t > 30:
        return f"「{lo}」寄り"
    return f"「{lo}」に強く寄る"


def t_mean(scores, keys):
    vals = [t_score(scores.get(k)) for k in keys]
    vals = [v for v in vals if v is not None]
    return round(statistics.mean(vals), 2) if vals else None


# ---------------------------------------------------------------------------
# 採点
# ---------------------------------------------------------------------------

def subscale_scores(answers, form):
    """下位尺度ごとの平均を返す。欠測は絶対数ではなく比率で判定する
    （その尺度の設問のうち3分の1を超えて欠測なら測定不能）。版によって
    1尺度あたりの問数が違うため、絶対数基準では版ごとに扱いが揺れていた
    （旧版の不具合。監査での指摘に加え、score.pyがformを一切見ておらず
    短縮版JSONを読ませると全項目が誤って欠測扱いになるバグも本改修で発見・修正）。
    """
    items = items_for_form(form)
    buckets, totals = {}, {}
    for it in items:
        if it["type"] != "likert":
            continue
        sub = it["sub"]
        totals[sub] = totals.get(sub, 0) + 1
        v = answers.get(it["id"])
        if v is None:
            continue
        buckets.setdefault(sub, []).append(conv(int(v), it.get("rev", False)))
    out = {}
    for sub, n in totals.items():
        vals = buckets.get(sub, [])
        missing = n - len(vals)
        out[sub] = None if (n > 0 and missing > n / 3) else (
            round(statistics.mean(vals), 2) if vals else None)
    return out


def leadership_profile(answers, form):
    """6問（短縮版は3問、スクリーニング版は1問）しかないため百分率は精度を
    偽装する。件数を主に返す。「経験がない（d）」は判定から除外し、
    無経験が3問以上ならプロファイル自体を無効とする。"""
    items = [it for it in items_for_form(form) if it["type"] == "choice"]
    counts = {"a": 0, "b": 0, "c": 0}
    n = 0
    no_exp = 0
    asked = 0
    for it in items:
        v = answers.get(it["id"])
        if v is None:
            continue
        asked += 1
        if v == "d":
            no_exp += 1
            continue
        if v in counts:
            counts[v] += 1
            n += 1
    if asked == 0:
        return None
    if no_exp >= 3:
        return {"insufficient": True, "無経験の数": no_exp, "回答数": asked}
    if not n:
        return None
    labels = {"a": "指示型", "b": "合議型", "c": "委任型"}
    named_counts = {labels[k]: v for k, v in counts.items()}
    pct = {labels[k]: round(v / n * 1000) / 10 for k, v in counts.items()}
    ranked = sorted(named_counts.items(), key=lambda x: -x[1])
    style = ranked[0][0]
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] <= 1:
        style = f"{ranked[0][0]}・{ranked[1][0]}併用型"
    return {
        "counts": named_counts, "percent": pct, "主導スタイル": style,
        "回答数": n, "無経験の数": no_exp, "設問数": asked,
    }


def validity(answers, scores, form):
    """社会的望ましさと回答一貫性は、項目数が十分な標準版でのみ算出する
    （短縮版はV1が2問・一貫性ペアが1組のみで、絶対数基準のまま当てはめると
    誤差が数倍に増幅されるため）。回答の偏り（標準偏差）は項目数が
    ある程度あれば意味を持つため、screening以外で算出する。"""
    if form == "screening":
        return None

    items = items_for_form(form)
    item_ids = {it["id"] for it in items}
    w = []
    v1mean = None
    cons = None

    if form == "full":
        v1_keys = [f"V1-{i}" for i in range(1, 7)]
        v1 = [answers[k] for k in v1_keys if answers.get(k) is not None]
        v1mean = round(statistics.mean(v1), 2) if len(v1) == 6 else None
        if v1mean is not None and v1mean >= 4.5:
            w.append("社会的望ましさが高い。各尺度がやや高めに出ている可能性を考慮して読む。")

        diffs = []
        for a, b_ in CONSISTENCY_PAIRS:
            va, vb = answers.get(a), answers.get(b_)
            if va is not None and vb is not None:
                diffs.append(abs(int(va) - int(vb)))
        cons = round(statistics.mean(diffs), 2) if len(diffs) == 6 else None
        if cons is not None and cons >= 1.5:
            w.append("回答の一貫性が低い。時間を空けての再実施を勧める。")

    likert_vals = [int(answers[k]) for k in item_ids
                   if k in answers and ITEMS_BY_ID[k]["type"] == "likert"
                   and answers.get(k) is not None]
    sd = round(statistics.pstdev(likert_vals), 2) if len(likert_vals) > 1 else None
    if sd is not None and sd <= 0.60:
        w.append("選択が偏っている。項目を読まずに回答した可能性がある。")

    verdict = "再実施を推奨" if len(w) >= 2 else ("参考値として扱う" if w else "範囲内")
    return {
        "社会的望ましさ（平均）": v1mean, "反応一貫性（平均絶対差）": cons,
        "回答の標準偏差": sd, "警告": w, "標準版のみ算出": form != "full",
        "判定": verdict,
    }


def derived(scores):
    """導出指標。build_tool.py の derive() と厳密に一致させている。
    改訂点（監査所見への対応）は各コメントを参照。"""
    d = {}

    # 自分基準で動くか、状況で動くか（PE差）。
    # 旧: P平均÷(P平均+E平均) の比率 → 値が50に強く引き寄せられ、境界帯（中間型）
    # が約半数を占めていた（20000人のモンテカルロ検証で確認）。
    # 新: 中点スコアどうしの「差」に変更。E側からE3（能力系＝迂回路を見つける）
    # を除く。E3は「環境の見え方」を表す感受性の尺度ではないため（所見1・3）。
    p_t = t_mean(scores, ["P1", "P2", "P3", "P4", "P5"])
    e_t = t_mean(scores, ["E1", "E2", "E4"])
    pe = round(p_t - e_t, 2) if (p_t is not None and e_t is not None) else None
    pe_label = None
    if pe is not None:
        pe_label = "ほぼ同程度" if abs(pe) < 1.5 else ("自分の基準が優位" if pe > 0 else "環境の条件が優位")
    d["自分基準か状況か（中点スコアの差）"] = {"値": pe, "解釈": pe_label}

    # 着手する力と定着させる力。
    # 旧: mean(F1,F3) − mean(F2,F4) → F2「反対を察知する」は変化を妨げる力
    # ではなく成功させる対処能力であり、保持側に含めると変革に長けた人ほど
    # 「定着が優位」と誤判定されかねない。F4のみを保持側に、F2は独立指標に
    # 分離した（所見9）。
    # 本文の数値は中点スコアに統一している（素点と2つの数字が混在すると、
    # 同じ項目が「5」と「67.6」で出て読み手が混乱するため）。
    # 差の換算係数は 10/0.85 = 11.76 なので、閾値も掛け直す。
    f13 = t_mean(scores, ["F1", "F3"])
    f4 = t_score(scores.get("F4"))
    ffb = round(f13 - f4, 2) if (f13 is not None and f4 is not None) else None
    ffb_label = None
    if ffb is not None:
        ffb_label = "ほぼ均衡" if abs(ffb) < 1.76 else ("着手が優位" if ffb > 0 else "定着が優位")
    d["着手する力と定着させる力（中点スコアの差）"] = {"値": ffb, "解釈": ffb_label}
    d["抵抗への備え（反対を察知する）"] = t_score(scores.get("F2"))

    # 迷う場面での決断力。最も弱い型は、2位との差が0.5未満（実質同点）なら
    # 特定しない（所見11）。
    cti = t_mean(scores, ["C1", "C2", "C3", "C4"])
    cvals = {k: t_score(scores[k]) for k in ["C1", "C2", "C3", "C4"]
             if scores.get(k) is not None}
    weak = None
    if len(cvals) >= 2:
        ordered = sorted(cvals, key=lambda k: cvals[k])
        if cvals[ordered[1]] - cvals[ordered[0]] >= 5.9:
            weak = ordered[0]
    elif len(cvals) == 1:
        weak = next(iter(cvals))
    d["迷う場面での決断力"] = {
        "値": cti, "最も弱い型": weak,
        "最も弱い型の名称": SUBSCALE_NAMES.get(weak) if weak else None,
    }

    p2, p4 = scores.get("P2"), scores.get("P4")
    quad = None
    if p2 is not None and p4 is not None:
        if p2 > 3.5 and p4 > 3.5:
            quad = "高く設定し、修正もできる"
        elif p2 > 3.5:
            quad = "高く設定するが、修正できない"
        elif p4 > 3.5:
            quad = "堅実に設定し、修正もできる"
        else:
            quad = "低い水準に固定している"
    d["目標の置き方"] = quad

    p1, p5 = t_score(scores.get("P1")), t_score(scores.get("P5"))
    tli = round(p1 - p5, 2) if (p1 is not None and p5 is not None) else None
    tli_label = None
    if tli is not None:
        tli_label = ("持ち帰りが多い" if tli >= 11.8
                     else ("切り替えが速い" if tli <= -11.8 else "ふつう"))
    d["仕事の持ち帰りやすさ"] = {"値": tli, "解釈": tli_label}

    # 「変革を担う力（F1〜F4の平均）」は廃止した。F2をそのまま含み、
    # F1・F3・F4は着手差が使っているため、同じ数字を二度示すことになる
    # （尺度を独立に生成した模擬データでも、抵抗への備えとの相関は +0.51）。
    # G2・E3は高低に優劣がないので指標にせず、補助情報として置く。
    d["あわせて見るもの"] = {"合意して決める(G2)": t_score(scores.get("G2")),
                             "迂回路を見つける(E3)": t_score(scores.get("E3"))}

    # 環境調整の効きやすさ。旧: mean(E1,E2) − mean(P1,P3) → E1（近づきたくなる
    # 感度）とE2（避けたくなる感度）は向きが逆の力で、平均すると「良い環境で
    # 伸びる人」と「嫌な要素で止まる人」が同じ値になってしまう。処方が違う
    # 2つを分離した（所見8）。
    # 「誘因設計の効きやすさ」「障害除去の効きやすさ」も独立の指標にしない。
    # どちらも E から P を引いた形で、PE差と同じことを別角度から見ているだけ
    # （構造的な相関はいずれも −0.59）。PE差の内訳として持つ。
    p13 = t_mean(scores, ["P1", "P3"])
    e1, e2 = t_score(scores.get("E1")), t_score(scores.get("E2"))
    d["環境側の内訳"] = {
        "近づきたくなるものへの反応": round(e1 - p13, 2) if (e1 is not None and p13 is not None) else None,
        "避けたくなるものへの反応": round(e2 - p13, 2) if (e2 is not None and p13 is not None) else None,
    }

    d["_pe"] = pe
    d["_ffb"] = ffb
    d["_weak"] = weak
    return d


def classify(d):
    """境界帯：どちらかの軸が中立圏内なら型を断定しない。PE差±1.5・
    力の場±0.15は、20000人規模のモンテカルロ検証で境界帯の発生率が
    全体の約24%になるよう校正した値（変更前は約49%が中間型だった）。"""
    pe, ffb = d.get("_pe"), d.get("_ffb")
    if pe is None or ffb is None:
        return {"類型": "判定不能"}
    border = abs(pe) < 1.5 or abs(ffb) < 0.15
    internal = pe > 0
    launching = ffb > 0
    if internal and launching:
        name = "自ら動き出す型（推進者型）"
    elif internal:
        name = "決めたことを守り抜く型（基準保持型）"
    elif launching:
        name = "仕組みを組み替える型（場再編型）"
    else:
        name = "場に合わせて回す型（場適応型）"
    weak = d.get("_weak")
    sub = SUBSCALE_NAMES.get(weak, "") if weak else ""
    return {
        "類型": name + ("（境界帯：断定を避ける）" if border else ""),
        "サブタイプ": f"{name}／{sub}に注意" if sub else name,
        "境界帯": border,
        "注記": "呼び名は同じ人が2回受けても7割ほどしか一致しない。"
                "切る前の2軸の位置は9割方一致するので、位置のほうを見ること。",
    }


def score_all(payload):
    answers_raw = payload.get("answers", {})
    form_raw = payload.get("形式") or payload.get("form") or "full"
    form = form_raw if form_raw in ("short", "screening") else "full"

    items = items_for_form(form)
    valid_ids = {it["id"] for it in items}
    answers = {}
    for k, v in answers_raw.items():
        if v is None or k not in valid_ids:
            continue
        it = ITEMS_BY_ID.get(k)
        if it is None:
            continue
        if it["type"] == "choice":
            if v in ("a", "b", "c", "d"):
                answers[k] = v
        else:
            try:
                iv = int(v)
            except (TypeError, ValueError):
                continue
            if 1 <= iv <= 6:
                answers[k] = iv

    scores = subscale_scores(answers, form)
    file_version = payload.get("項目版")
    version_note = None
    if file_version and str(file_version) != str(ITEM_VERSION):
        version_note = (
            f"この結果は旧版（項目版{file_version}）の設問文にもとづいています。"
            "設問IDと採点方法は変わっていないため採点はできますが、"
            "数問の文言が現在の版と異なる場合があります。"
        )

    profile = OrderedDict()
    for k in SCORED_SUBS:
        name = SUBSCALE_NAMES.get(k, k)
        m = scores.get(k)
        t = t_score(m)
        profile[k] = {"項目": name, "専門用語": TECH.get(k), "領域": DOMAIN_OF[k[0]],
                      "種類": "能力系" if SCALE_TYPE.get(k) == "能" else "両極性",
                      "素点平均": m, "中点スコア": t, "判定": pole_band(k, t)}
    ability = [k for k in SCORED_SUBS if SCALE_TYPE.get(k) == "能"]
    bipolar = [k for k in SCORED_SUBS if SCALE_TYPE.get(k) == "両"]
    ab = sorted((k for k in ability if profile[k]["中点スコア"] is not None),
                key=lambda k: -profile[k]["中点スコア"])
    for i, k in enumerate(ab):
        profile[k]["順位"] = f"{i + 1} / {len(ab)}（群内）"
    bp = sorted((k for k in bipolar if profile[k]["中点スコア"] is not None),
                key=lambda k: -abs(profile[k]["中点スコア"] - 50))
    for i, k in enumerate(bp):
        profile[k]["順位"] = f"{i + 1} / {len(bp)}（際立ち）"

    d = derived(scores)
    result = OrderedDict([
        ("項目版", ITEM_VERSION),
        ("読み込んだ項目版", file_version),
        ("版の注記", version_note),
        ("形式", form),
        ("妥当性", validity(answers, scores, form)),
        ("プロファイル", profile),
        ("リーダーシップ風土", leadership_profile(answers, form)),
        ("導出指標", {k: v for k, v in d.items() if not k.startswith("_")}),
        ("類型", classify(d) if form != "screening" else None),
    ])
    return result


# ---------------------------------------------------------------------------
# 表示
# ---------------------------------------------------------------------------

def render(res):
    out = []
    if res.get("版の注記"):
        out.append("! " + res["版の注記"])
        out.append("")

    va = res["妥当性"]
    out.append("■ 結果を読む前の確認")
    if va is None:
        out.append("  （スクリーニング版のため実施していません）")
    else:
        out.append(f"  判定: {va['判定']}")
        for key in ["社会的望ましさ（平均）", "反応一貫性（平均絶対差）", "回答の標準偏差"]:
            val = va[key]
            note = "（標準版のみ算出）" if val is None and va["標準版のみ算出"] and "偏差" not in key else ""
            out.append(f"  {key}: {val if val is not None else '—'}{note}")
        for w in va["警告"]:
            out.append(f"  ! {w}")
    out.append("")

    if va and va["判定"] == "再実施を推奨":
        out.append("※ 妥当性の確認で複数の問題が見つかりました。以降は参考値として読んでください。")
        out.append("")

    out.append("■ プロファイル（21項目）")
    out.append(f"  {'記号':<5}{'項目名':<24}{'平均':>5}{'スコア':>7}{'順位':>16}  読み方")
    cur = None
    for k, p in res["プロファイル"].items():
        if p["領域"] != cur:
            cur = p["領域"]
            out.append(f"  --- {cur} ---")
        rank = p.get("順位", "—")
        out.append(f"  {k:<5}{p['項目']:<24}{str(p['素点平均']):>5}"
                   f"{str(p['中点スコア']):>7}{str(rank):>16}  {p['判定']}")
    out.append("")

    lp = res["リーダーシップ風土"]
    if lp and lp.get("insufficient"):
        out.append("■ 人の動かし方")
        out.append(f"  無経験の回答が{lp['無経験の数']}問あり、判定に十分な回答が得られませんでした。")
        out.append("")
    elif lp:
        out.append("■ 人の動かし方（" + str(lp["回答数"]) + "問／" + str(lp["設問数"]) + "問中、経験なしを除く）")
        out.append("  " + " / ".join(f"{k} {v}件" for k, v in lp["counts"].items()))
        out.append(f"  主導スタイル: {lp['主導スタイル']}")
        out.append("")

    out.append("■ 導出指標")
    for k, val in res["導出指標"].items():
        if isinstance(val, dict):
            body = "  ".join(f"{kk}={vv}" for kk, vv in val.items() if vv is not None)
            out.append(f"  {k}: {body}")
        else:
            out.append(f"  {k}: {val}")
    out.append("")

    if res["類型"]:
        out.append("■ 類型判定")
        for k, val in res["類型"].items():
            out.append(f"  {k}: {val}")
        out.append("")

    out.append("※ 中点スコアは規範集団データではなく理論的中点を基準にした暫定値。母集団と比較したものではない。")
    out.append("※ 本診断は学術的に検証された心理検査ではなく、自己理解のための道具である。")
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    with open(args[0], encoding="utf-8") as f:
        payload = json.load(f)
    res = score_all(payload)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render(res))


if __name__ == "__main__":
    main()
