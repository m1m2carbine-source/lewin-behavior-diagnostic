#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""すべての検証をまとめて実行する。

引き継ぎ後、変更を加えたら必ずこれを走らせる。
個別に走らせたい場合は各スクリプトを直接呼んでもよい。

使い方:
    python tests/run_all.py            # 全部
    python tests/run_all.py --quick    # PDF生成を伴うものを飛ばす（速い）

終了コード 0 なら全て合格。1 なら要確認。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))

# (表示名, コマンド, 合格条件, PDFを使うか)
CHECKS = [
    ("ビルド（HTML再生成）",
     ['python3', os.path.join('scripts', 'build_tool.py')],
     lambda out: '生成:' in out, False),

    ("JS構文チェック",
     None,  # 特別扱い（下のjs_syntax_check）
     None, False),

    ("採点スクリプトの動作",
     ['python3', os.path.join('scripts', 'score.py'),
      os.path.join('assets', 'example_answers.json')],
     lambda out: '中点スコア' in out or 'プロファイル' in out, False),

    ("重複・表記ゆれの検査",
     ['python3', os.path.join('scripts', 'check_report.py'), '--quiet'],
     lambda out: '違反なし' in out, False),

    ("印刷レイアウトの検査",
     ['python3', os.path.join('scripts', 'check_print.py'), '--quiet'],
     lambda out: '違反なし' in out, False),

    ("機能の回帰テスト（29件）",
     ['python3', os.path.join('tests', 'gen_full.py')],
     None, False),  # 生成後に node で実行するので特別扱い

    ("レヴィン理論の要点が残っているか",
     ['python3', os.path.join('tests', 'verify_theory.py')],
     lambda out: 'すべて残っている' in out, False),

    ("章をまたぐ重複の検出",
     ['python3', os.path.join('tests', 'dupcheck.py')],
     lambda out: '完全重複: 0件' in out, False),

    ("図と解説が折りたたみに埋もれていないか",
     ['python3', os.path.join('tests', 'verify_fold_correct.py')],
     lambda out: '「この章の図の読み方」' in out and '常時表示' in out, False),

    ("印刷PDFの空白ページ検出",
     ['python3', os.path.join('tests', 'print_iter.py')],
     lambda out: 'ほぼ空白のページ: 0枚' in out, True),
]


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def js_syntax_check():
    """生成されたHTMLからJSを取り出し、node --check で構文を確認する。"""
    html_path = os.path.join(ROOT, 'assets', 'diagnostic_tool.html')
    html = open(html_path, encoding='utf-8').read()
    js = html.split('<script>')[1].split('</script>')[0]
    tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), '_syntax_check.js')
    stub = ("const document={querySelectorAll:()=>[],"
            "getElementById:()=>({classList:{add(){},remove(){}},style:{}})};"
            "const localStorage={getItem:()=>null};")
    open(tmp, 'w', encoding='utf-8').write(stub + js)
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or 'OK')[:200]


def regression_test():
    """gen_full.py がテスト用JSを生成し、それを node で実行する2段構え。"""
    code, out = run(['python3', os.path.join('tests', 'gen_full.py')])
    if code != 0:
        return False, out[:300]
    tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'full.js')
    if not os.path.exists(tmp):
        return False, 'テスト用JSが生成されなかった'
    r = subprocess.run(['node', tmp], capture_output=True, text=True)
    txt = r.stdout + r.stderr
    ok = '失敗 0' in txt
    tail = [ln for ln in txt.strip().split('\n') if ln.strip()][-1:]
    return ok, (tail[0] if tail else txt[:200])


def main():
    quick = '--quick' in sys.argv
    results = []

    for name, cmd, judge, needs_pdf in CHECKS:
        if quick and needs_pdf:
            results.append((name, None, 'PDF生成を伴うため省略'))
            continue

        if name == "JS構文チェック":
            ok, msg = js_syntax_check()
            results.append((name, ok, msg if not ok else 'OK'))
            continue

        if name.startswith("機能の回帰テスト"):
            ok, msg = regression_test()
            results.append((name, ok, msg))
            continue

        code, out = run(cmd)
        if judge is None:
            ok = (code == 0)
            msg = 'OK' if ok else out[-200:]
        else:
            ok = (code == 0) and judge(out)
            last = [ln for ln in out.strip().split('\n') if ln.strip()][-1:]
            msg = (last[0] if last else 'OK') if ok else out[-250:]
        results.append((name, ok, msg))

    print("=" * 64)
    ng = 0
    for name, ok, msg in results:
        if ok is None:
            mark = "－"
        elif ok:
            mark = "合格"
        else:
            mark = "失敗"
            ng += 1
        print(f"  [{mark}] {name}")
        if ok is False:
            for ln in str(msg).strip().split('\n')[:6]:
                print(f"        {ln}")
        elif ok is None:
            print(f"        {msg}")
    print("=" * 64)

    if ng:
        print(f"要確認: {ng} 件")
        sys.exit(1)
    print("すべて合格")
    print()
    print("※ 改ページ位置・図の分断は自動検査では分かりません。")
    print("  印刷まわりを変更したときは、実際の印刷プレビューも目で確認してください。")


if __name__ == '__main__':
    main()
