#!/usr/bin/env python3
# リタス kill switch (public/litus/status.json) の構造検証。
#
# なぜ要るか: アプリ側 parseKillSwitchStatus は disabled が配列でないと null
# (= 取得失敗) を返し、直近キャッシュへ無言でフォールバックする。壊れた保存に
# 誰も気づけない。正典は litus リポの src/health/killSwitch.ts。
#
# 使い方（出力なし = OK）:
#   python3 tools/validate-status-json.py                  # public/litus/status.json を検証
#   python3 tools/validate-status-json.py path/to/file.json
#   git show ":public/litus/status.json" | python3 tools/validate-status-json.py
#
# 詳細: docs/KILL-SWITCH-RUNBOOK.md

import json
import os
import re
import sys
from pathlib import Path

ALL_SENTINEL = "all"  # killSwitch.ts の disabledRaw.includes('all') に対応する特別値。
                       # KillSwitchFeature型には含まれない独立のリテラルなのでここだけは固定値。

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATUS_JSON = REPO_ROOT / "public" / "litus" / "status.json"
LITUS_REPO = Path(os.environ.get("LITUS_REPO", str(Path.home() / "dev" / "litus")))
KILLSWITCH_TS = LITUS_REPO / "src" / "health" / "killSwitch.ts"


def load_known_features():
    """litus側のKillSwitchFeature型からfeature名を読む。ここではハードコードしない
    （列挙を2箇所に書くと必ずズレる。'all'を除く3値は将来増減しうる）。"""
    if not KILLSWITCH_TS.exists():
        return None, f"litus正典が見つかりません: {KILLSWITCH_TS}（LITUS_REPO環境変数で場所を指定できます）"
    text = KILLSWITCH_TS.read_text(encoding="utf-8")
    m = re.search(r"export type KillSwitchFeature\s*=\s*([^\n]+)", text)
    if not m:
        return None, f"{KILLSWITCH_TS} に KillSwitchFeature 型定義が見つかりません（litus側の実装が変わった可能性）"
    names = re.findall(r"'([a-zA-Z0-9_]+)'", m.group(1))
    if not names:
        return None, f"{KILLSWITCH_TS} の KillSwitchFeature からfeature名を抽出できません"
    return set(names), None


def is_plain_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check_disabled_array(value, path, allowed, errors):
    if not isinstance(value, list):
        errors.append(
            f"{path}: 配列ではありません（型={type(value).__name__}）。"
            "disabledが配列でないとアプリはstatus取得失敗として扱い、直近キャッシュへ無言でフォールバックします"
        )
        return
    for v in value:
        if v not in allowed:
            errors.append(
                f"{path}: 未知の値 {v!r}（使えるのは {sorted(allowed)}）。"
                "未知の値は安全側に倒れて『無視されるだけ』＝止めたいのに何も止まりません"
            )


def check_text_field(data, key, errors, prefix=""):
    if key in data and data[key] is not None and not isinstance(data[key], str):
        errors.append(f"{prefix}{key} が文字列ではありません（型={type(data[key]).__name__}）")


def validate(raw, allowed_disabled_values):
    errors = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"JSONとして解析できません: {e}"]

    if not isinstance(data, dict):
        return [f"トップレベルがオブジェクトではありません（型={type(data).__name__}）"]

    if "schemaVersion" not in data:
        errors.append("schemaVersion がありません")
    elif not is_plain_int(data["schemaVersion"]):
        errors.append(f"schemaVersion が整数ではありません（型={type(data['schemaVersion']).__name__}）")

    if "disabled" not in data:
        errors.append("disabled がありません（トップレベル必須）")
    else:
        check_disabled_array(data["disabled"], "disabled", allowed_disabled_values, errors)

    check_text_field(data, "message", errors)
    check_text_field(data, "title", errors)

    if "versionRules" in data:
        rules = data["versionRules"]
        if not isinstance(rules, list):
            errors.append(f"versionRules が配列ではありません（型={type(rules).__name__}）")
        else:
            for i, rule in enumerate(rules):
                p = f"versionRules[{i}]"
                if not isinstance(rule, dict):
                    errors.append(f"{p}: オブジェクトではありません（型={type(rule).__name__}）")
                    continue
                if "disabled" not in rule:
                    errors.append(f"{p}.disabled がありません")
                else:
                    check_disabled_array(rule["disabled"], f"{p}.disabled", allowed_disabled_values, errors)
                for bkey in ("minBuild", "maxBuild"):
                    if bkey in rule and not is_plain_int(rule[bkey]):
                        errors.append(f"{p}.{bkey} が整数ではありません（型={type(rule[bkey]).__name__}）")
                check_text_field(rule, "message", errors, prefix=f"{p}.")
                check_text_field(rule, "title", errors, prefix=f"{p}.")

    return errors


def main():
    if len(sys.argv) > 1:
        source_label = sys.argv[1]
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    elif sys.stdin.isatty():
        source_label = str(DEFAULT_STATUS_JSON)
        raw = DEFAULT_STATUS_JSON.read_text(encoding="utf-8")
    else:
        source_label = "(stdin)"
        raw = sys.stdin.read()

    known_features, feat_err = load_known_features()
    if feat_err:
        # 正典を参照できない = このチェックの目的（disabledの値を検証すること）を
        # 果たせない。判定不能として通すのではなく、安全側でブロックする。
        print(f"✗ 検証を実行できません: {feat_err}", file=sys.stderr)
        sys.exit(1)

    allowed = known_features | {ALL_SENTINEL}
    errors = validate(raw, allowed)

    if errors:
        print(f"✗ {source_label}: status.json の検証で {len(errors)} 件の問題:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
