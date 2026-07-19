#!/usr/bin/env python3
"""tabiNote 国マスタ完全対応チェック + 突合レポート生成。

チェック内容:
  1. マスタ全件 (tabinote-countries.json) が SVG 上に <g class="... country"> として存在する
  2. data-code がマスタの country_code と一致し、重複がない
  3. <title> が「日本語名 / English name」形式でマスタの name と一致する
  4. 全マスタ国が「塗れる」(可視ジオメトリ or マーカーを持ち、実用サイズがある)
  5. マスタ外 territory が .country セレクタを汚染しない
  6. countries.json と SVG の収録内容が一致する

終了コード: 全合格 0 / 不合格 1
レポート: reports/tabinote-coverage.md
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVGS = [
    "map-full.svg",
    "map-mobile.svg",
    "map-full-japan-center.svg",
    "map-mobile-japan-center.svg",
]
NS = {"svg": "http://www.w3.org/2000/svg"}

# タップ可能とみなす最小サイズ (px)。これ未満でマーカーも無ければ不合格
MIN_PAINTABLE_PX = 3.0


def path_bbox(d):
    nums = re.findall(r"-?\d+\.?\d*", d)
    xs = [float(v) for v in nums[0::2]]
    ys = [float(v) for v in nums[1::2]]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def analyze_svg(path):
    tree = ET.parse(os.path.join(ROOT, path))
    groups = {}
    for g in tree.iter("{http://www.w3.org/2000/svg}g"):
        code = g.get("data-code")
        if code is None:
            continue
        classes = (g.get("class") or "").split()
        title_el = g.find("svg:title", NS)
        bbox = [float("inf")] * 2 + [float("-inf")] * 2
        n_paths = 0
        for p in g.findall("svg:path", NS):
            b = path_bbox(p.get("d", ""))
            if b:
                n_paths += 1
                bbox[0], bbox[1] = min(bbox[0], b[0]), min(bbox[1], b[1])
                bbox[2], bbox[3] = max(bbox[2], b[2]), max(bbox[3], b[3])
        markers = g.findall("svg:circle", NS)
        size = 0.0
        if n_paths:
            size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        if markers:
            size = max(size, 2 * max(float(c.get("r", "0")) for c in markers))
        groups.setdefault(code, []).append({
            "classes": classes,
            "title": title_el.text if title_el is not None else None,
            "n_paths": n_paths,
            "n_markers": len(markers),
            "size": size,
            "is_country": "country" in classes,
            "is_territory": "territory" in classes,
            "data_master": g.get("data-master"),
        })
    return groups


def main():
    with open(os.path.join(ROOT, "tabinote-countries.json")) as f:
        master_doc = json.load(f)
    master = {c["country_code"]: c for c in master_doc["countries"]}
    with open(os.path.join(ROOT, "countries.json")) as f:
        countries_json = {r["code"]: r for r in json.load(f)}

    all_errors = {}
    per_svg_summary = {}
    for svg in SVGS:
        errors = []
        groups = analyze_svg(svg)
        country_codes = {c for c, gs in groups.items() if any(g["is_country"] for g in gs)}

        # 1. 欠落
        missing = sorted(set(master) - country_codes)
        for c in missing:
            errors.append(f"欠落: {c} ({master[c]['name']}) の country グループが無い")
        # 2. 重複
        for c, gs in groups.items():
            if len(gs) > 1:
                errors.append(f"重複: data-code={c} が {len(gs)} 回出現")
        # 3. title / class / 塗り可能性
        for c in sorted(country_codes):
            g = groups[c][0]
            if c not in master:
                errors.append(f"余剰 country: {c} はマスタ外なのに country class を持つ")
                continue
            m = master[c]
            expected = f"{m['name']} / {m['name_en']}"
            if g["title"] != expected:
                errors.append(f"title 不一致: {c} '{g['title']}' != '{expected}'")
            if g["n_paths"] == 0 and g["n_markers"] == 0:
                errors.append(f"不可視: {c} ({m['name']}) にジオメトリが無い")
            elif g["size"] < MIN_PAINTABLE_PX:
                errors.append(
                    f"塗り不能: {c} ({m['name']}) 実用サイズ {g['size']:.1f}px < "
                    f"{MIN_PAINTABLE_PX}px でマーカーも無い")
        # 5. territory の汚染チェック
        for c, gs in groups.items():
            for g in gs:
                if g["is_territory"]:
                    if g["is_country"]:
                        errors.append(f"汚染: {c} が country と territory 両方の class を持つ")
                    if g["data_master"] != "false":
                        errors.append(f"territory {c} に data-master=\"false\" が無い")
        # 6. countries.json との整合
        svg_all = set(groups)
        json_all = set(countries_json)
        if svg_all != json_all:
            errors.append(f"countries.json 不整合: SVGのみ {sorted(svg_all - json_all)} / "
                          f"JSONのみ {sorted(json_all - svg_all)}")

        marker_countries = sorted(
            c for c in country_codes if groups[c][0]["n_markers"] > 0)
        per_svg_summary[svg] = {
            "countries": len(country_codes),
            "territories": len(svg_all - country_codes),
            "markers": marker_countries,
        }
        all_errors[svg] = errors

    # レポート生成
    ok = not any(all_errors.values())
    lines = ["# tabiNote 国マスタ突合レポート", ""]
    lines.append(f"- マスタ正本: `tabinote-countries.json` ({len(master)} カ国, "
                 f"取得日 {master_doc['fetched_at']})")
    lines.append(f"- 判定: **{'合格 (欠落 0 / code 不一致 0 / 名前解決不能 0)' if ok else '不合格'}**")
    lines.append("")
    for svg in SVGS:
        s = per_svg_summary[svg]
        lines.append(f"## {svg}")
        lines.append("")
        lines.append(f"- マスタ対応 country グループ: {s['countries']} / {len(master)}")
        lines.append(f"- マスタ外 territory グループ: {s['territories']} "
                     "(TW 台湾 / XK コソボ / EH 西サハラ)")
        lines.append(f"- 極小国マーカー付与: {len(s['markers'])} カ国")
        lines.append(f"  - {', '.join(s['markers'])}")
        if all_errors[svg]:
            lines.append("- **エラー:**")
            for e in all_errors[svg]:
                lines.append(f"  - {e}")
        else:
            lines.append("- エラー: なし")
        lines.append("")
    lines.append("## 特記事項")
    lines.append("")
    lines.append("- **アルメニア (AM)**: 当初 tabiNote 国マスタに欠落していたが、"
                 "2026-07-19 にマスタへ追加（migration 067、194 → 195 件）。"
                 "本リポジトリでも territory から `country`（色塗り対象）に昇格済み。")
    lines.append("- マスタ外 territory (TW/XK/EH) は `class=\"territory\"` "
                 "`data-master=\"false\"` を持ち、`.country` セレクタでは選択されない。")
    lines.append("- 属領・海外領土 (グリーンランド、プエルトリコ、ニューカレドニア等) は"
                 "本国のグループに吸収済み。")
    lines.append("- 除外: 南極大陸 (マスタに AQ が無い)、ビル・タウィール (無主地)、"
                 "南シナ海の岩礁等。")
    lines.append("")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "reports", "tabinote-coverage.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    for svg in SVGS:
        status = "OK" if not all_errors[svg] else f"{len(all_errors[svg])} errors"
        print(f"{svg}: {status}")
        for e in all_errors[svg]:
            print(f"  - {e}")
    print("report -> reports/tabinote-coverage.md")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
