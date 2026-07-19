#!/usr/bin/env python3
"""map-full.svg / map-mobile.svg (+日本中心版) / countries.json の生成スクリプト。

ベースデータ: Natural Earth 10m Admin 0 - Countries (パブリックドメイン)
国マスタ正本: tabinote-countries.json (tabiNote location_tags type='country')

使い方:
    python3 scripts/build.py            # data/ に NE データが無ければダウンロード
依存: Python 3.9+ 標準ライブラリのみ
"""
import json
import math
import os
import re
import sys
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_10m_admin_0_countries.geojson"
)
NE_PATH = os.path.join(ROOT, "data", "ne_10m_admin_0_countries.geojson")
MASTER_PATH = os.path.join(ROOT, "tabinote-countries.json")

# マスタ外だが地図上は中立表示する地域 (class="territory"、色塗り対象外)
TERRITORIES = {
    "TWN": ("TW", "台湾", "Taiwan", "Asia"),
    "KOS": ("XK", "コソボ", "Kosovo", "Europe"),
    "SAH": ("EH", "西サハラ", "Western Sahara", "Africa"),
    # アルメニアは国連加盟国だが tabiNote 国マスタ (194 件) に存在しないため、
    # マスタ正の原則に従い色塗り対象外の territory として収録する (地図の穴を防ぐ)
    "ARM": ("AM", "アルメニア", "Armenia", "Asia"),
}
# 実効支配地域などをマスタ国へ吸収するオーバーライド (ADM0_A3 -> ISO alpha-2)
MERGE_OVERRIDES = {
    "CYN": "CY",  # 北キプロス -> キプロス
    "SOL": "SO",  # ソマリランド -> ソマリア
    "KAS": "IN",  # シアチェン氷河 (NE の分離フィーチャ) -> インド
    "USG": "CU",  # グァンタナモ湾 -> キューバ
    "CNM": "CY",  # キプロス国連緩衝地帯 -> キプロス (地図上の隙間を防ぐ)
}
# 完全に除外するフィーチャ (南極・無主地・岩礁など)
DROP = {"ATA", "BJN", "SER", "SCR", "SPI", "PGA", "ESB", "WSB", "KAB", "BRI", "BRT"}

DEFAULT_FILL = "#EEEEEE"
STROKE = "#000000"
SEAM_EPS = 179.999  # 元データの ±180 度線 (日付変更線) 上の頂点の判定

# Equal Earth projection (Šavrič, Patterson, Jenny 2018)
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2


def equal_earth(lon, lat):
    lam = math.radians(lon)
    phi = math.radians(lat)
    theta = math.asin(M * math.sin(phi))
    t2 = theta * theta
    t6 = t2 * t2 * t2
    x = lam * math.cos(theta) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = theta * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


def dp_simplify(points, tol):
    """Douglas-Peucker (反復実装)。points は [(x, y), ...]。両端は必ず残す。"""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        s, e = stack.pop()
        if e <= s + 1:
            continue
        ax, ay = points[s]
        bx, by = points[e]
        dx, dy = bx - ax, by - ay
        seg2 = dx * dx + dy * dy
        dmax, imax = -1.0, -1
        for i in range(s + 1, e):
            px, py = points[i]
            if seg2 == 0:
                d2 = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = ((px - ax) * dx + (py - ay) * dy) / seg2
                t = max(0.0, min(1.0, t))
                cx, cy = ax + t * dx, ay + t * dy
                d2 = (px - cx) ** 2 + (py - cy) ** 2
            if d2 > dmax:
                dmax, imax = d2, i
        if dmax > tol * tol:
            keep[imax] = True
            stack.append((s, imax))
            stack.append((imax, e))
    return [p for p, k in zip(points, keep) if k]


def ring_area(points):
    a = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def slugify(name_en):
    return re.sub(r"[^a-z0-9]+", "-", name_en.lower()).strip("-")


def continent_class(continent):
    return re.sub(r"[^a-z0-9]+", "-", continent.lower()).strip("-")


def load_ne():
    if not os.path.exists(NE_PATH):
        os.makedirs(os.path.dirname(NE_PATH), exist_ok=True)
        print("downloading Natural Earth data ...", file=sys.stderr)
        urllib.request.urlretrieve(NE_URL, NE_PATH)
    with open(NE_PATH) as f:
        return json.load(f)["features"]


def collect_groups(features, master):
    """フィーチャを国コード単位に集約する。"""
    master_codes = set(master.keys())
    sov_to_code = {}
    for f in features:
        pr = f["properties"]
        code = pr.get("ISO_A2_EH") or pr.get("ISO_A2")
        if code in master_codes:
            sov_to_code.setdefault(pr["SOV_A3"], code)

    groups = defaultdict(list)  # code -> [polygon(rings of lonlat)]
    terr_groups = defaultdict(list)
    unmatched = []
    for f in features:
        pr = f["properties"]
        adm = pr["ADM0_A3"]
        if adm in DROP:
            continue
        code = pr.get("ISO_A2_EH") or pr.get("ISO_A2")
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        if adm in TERRITORIES:
            terr_groups[TERRITORIES[adm][0]].extend(polys)
        elif code in master_codes:
            groups[code].extend(polys)
        elif adm in MERGE_OVERRIDES:
            groups[MERGE_OVERRIDES[adm]].extend(polys)
        elif pr["SOV_A3"] in sov_to_code:
            # 属領・海外領土は本国へ吸収
            groups[sov_to_code[pr["SOV_A3"]]].extend(polys)
        else:
            unmatched.append((adm, pr.get("NAME"), pr.get("TYPE")))
    return groups, terr_groups, unmatched


def clip_x(pts, xmin=-180.0, xmax=180.0):
    """Sutherland-Hodgman で経度方向の帯 [xmin, xmax] にクリップする。"""
    def clip_half(points, bound, keep_left):
        out = []
        n = len(points)
        for i in range(n):
            cur, nxt = points[i], points[(i + 1) % n]
            cin = (cur[0] <= bound) if keep_left else (cur[0] >= bound)
            nin = (nxt[0] <= bound) if keep_left else (nxt[0] >= bound)
            if cin:
                out.append(cur)
            if cin != nin:
                t = (bound - cur[0]) / (nxt[0] - cur[0])
                out.append((bound, cur[1] + t * (nxt[1] - cur[1])))
        return out

    pts = clip_half(pts, xmax, True)
    if pts:
        pts = clip_half(pts, xmin, False)
    return pts


def seam_runs(marks):
    """circular なマーク列から連続 run のリスト [(start, end)] を返す。"""
    n = len(marks)
    if all(marks) or not any(marks):
        return []
    runs = []
    in_run = False
    start = 0
    for i in range(n):
        if marks[i] and not in_run:
            start, in_run = i, True
        elif not marks[i] and in_run:
            runs.append((start, i - 1))
            in_run = False
    if in_run:
        if runs and marks[0]:
            first = runs.pop(0)
            runs.append((start, first[1]))
        else:
            runs.append((start, n - 1))
    return runs


def recenter_ring(ring, center):
    """1 リングを中央経線 center で回転し、[(pts, closed), ...] を返す。

    - 元データが日付変更線 (±180) で分割されているリングは、切断辺を
      暗黙の閉路 (ストロークされない) にして継ぎ目の線を消す
    - 新しい切れ目 (center±180) をまたぐリングは 2 つに分割する
    """
    pts = ring[:-1] if ring[0] == ring[-1] else list(ring)
    pts = [(c[0], c[1]) for c in pts]
    if len(pts) < 3:
        return []
    shifted = [((((lon - center + 540) % 360) - 180), lat) for lon, lat in pts]

    if center != 0:
        marks = [abs(lon) >= SEAM_EPS for lon, lat in pts]
        runs = seam_runs(marks)
        if len(runs) == 1:
            i, j = runs[0]
            run_len = (j - i) % len(pts) + 1
            if run_len >= 2:
                n = len(pts)
                order = [(j + k) % n for k in range((i - j) % n + 1)]
                return [([shifted[k] for k in order], False)]

    # unwrap して連続化
    out = [shifted[0]]
    for x, y in shifted[1:]:
        while x - out[-1][0] > 180:
            x -= 360
        while x - out[-1][0] < -180:
            x += 360
        out.append((x, y))
    xs = [p[0] for p in out]
    if min(xs) >= -180 and max(xs) <= 180:
        return [(out, True)]
    pieces = []
    for off in (-360, 0, 360):
        c = clip_x([(x + off, y) for x, y in out])
        if len(c) >= 3 and ring_area(c) > 1e-9:
            pieces.append((c, True))
    return pieces


def recenter_polygon(poly, center):
    """ポリゴン (outer + holes) を回転する。outer が分割された場合、
    穴は経度範囲が重なる方の piece に割り当てる。"""
    outer_pieces = recenter_ring(poly[0], center)
    if not outer_pieces:
        return []
    results = [[piece] for piece in outer_pieces]
    for hole in poly[1:]:
        hole_pieces = recenter_ring(hole, center)
        for hp, closed in hole_pieces:
            hx = sum(p[0] for p in hp) / len(hp)
            best = 0
            if len(results) > 1:
                for idx, r in enumerate(results):
                    xs = [p[0] for p in r[0][0]]
                    if min(xs) <= hx <= max(xs):
                        best = idx
                        break
            results[best].append((hp, closed))
    return results


def project_all(groups, terr_groups, width, center):
    """経緯度 -> 回転 -> Equal Earth -> ピクセル座標。高さを返す。"""
    raw = {}
    minx = miny = math.inf
    maxx = maxy = -math.inf
    for code, polys in list(groups.items()) + list(terr_groups.items()):
        pp = []
        for poly in polys:
            for rpoly in recenter_polygon(poly, center):
                rings = []
                for pts, closed in rpoly:
                    proj = [equal_earth(lon, lat) for lon, lat in pts]
                    rings.append((proj, closed))
                    for x, y in proj:
                        minx, maxx = min(minx, x), max(maxx, x)
                        miny, maxy = min(miny, y), max(maxy, y)
                pp.append(rings)
        raw[code] = pp
    scale = width / (maxx - minx)
    height = (maxy - miny) * scale
    out = {}
    for code, polys in raw.items():
        out[code] = [
            [([((x - minx) * scale, (maxy - y) * scale) for x, y in pts], closed)
             for pts, closed in poly]
            for poly in polys
        ]
    return out, height


def build_paths(polys, tol, min_area):
    """簡略化してパス文字列群 (ポリゴン単位、穴を含む) と bbox を返す。
    全ポリゴンが閾値未満でも最大の 1 つは残す。"""
    outer_areas = {}
    for pi, poly in enumerate(polys):
        if poly:
            outer_areas[pi] = ring_area(poly[0][0])
    if not outer_areas:
        return [], None
    largest_pi = max(outer_areas, key=outer_areas.get)

    d_parts = []
    bbox = [math.inf, math.inf, -math.inf, -math.inf]
    for pi, poly in enumerate(polys):
        if outer_areas.get(pi, 0) < min_area and pi != largest_pi:
            continue
        subpaths = []
        for ri, (pts, closed) in enumerate(poly):
            if ri > 0 and ring_area(pts) < min_area:
                continue  # 極小の穴は省略
            sp = dp_simplify(pts, tol)
            if len(sp) < 3:
                sp = pts[:: max(1, len(pts) // 4)]
            if len(sp) < 3:
                continue
            coords = [f"{x:.1f} {y:.1f}" for x, y in sp]
            subpaths.append("M" + "L".join(coords) + ("Z" if closed else ""))
            if ri == 0:
                for x, y in sp:
                    bbox[0], bbox[1] = min(bbox[0], x), min(bbox[1], y)
                    bbox[2], bbox[3] = max(bbox[2], x), max(bbox[3], y)
        if subpaths:
            d_parts.append("".join(subpaths))
    if bbox[0] is math.inf:
        bbox = None
    return d_parts, bbox


def largest_polygon_centroid(polys):
    best, best_area = None, -1.0
    for poly in polys:
        if not poly:
            continue
        pts = poly[0][0]
        a = ring_area(pts)
        if a > best_area:
            best_area, best = a, pts
    xs = [p[0] for p in best]
    ys = [p[1] for p in best]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def render_svg(path, groups, terr_groups, master, width, height, tol, min_area,
               marker_threshold, marker_r, stroke_width):
    terr_meta = {v[0]: v for v in TERRITORIES.values()}
    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append(
        f'<svg class="world-svg-map" viewBox="0 0 {width} {math.ceil(height)}" '
        'xmlns="http://www.w3.org/2000/svg">'
    )
    lines.append("  <title>World Countries</title>")
    lines.append(
        "  <desc>SVG map of world countries. Based on Natural Earth (public domain). "
        "Generated for https://github.com/kazutax/world-map-svg</desc>"
    )
    lines.append('  <g class="svg-map">')
    lines.append('    <g class="countries">')

    marker_count = 0
    for code in sorted(groups.keys()) + sorted(terr_groups.keys()):
        is_master = code in groups and code in master
        polys = groups[code] if code in groups else terr_groups[code]
        if is_master:
            m = master[code]
            name_ja, name_en, continent = m["name"], m["name_en"], m["continent"]
            classes = f"{slugify(name_en)} {continent_class(continent)} country"
            extra = ""
        else:
            _, name_ja, name_en, continent = terr_meta[code]
            classes = f"{slugify(name_en)} {continent_class(continent)} territory"
            extra = ' data-master="false"'
        d_parts, bbox = build_paths(polys, tol, min_area)
        if not d_parts:
            continue
        lines.append(
            f'      <g class="{classes}" data-code="{code}"{extra} '
            f'fill="{DEFAULT_FILL}" fill-rule="evenodd" stroke="{STROKE}" '
            f'stroke-width="{stroke_width}" stroke-linejoin="round">'
        )
        lines.append(f"        <title>{name_ja} / {name_en}</title>")
        for d in d_parts:
            lines.append(f'        <path d="{d}"/>')
        if is_master and bbox:
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if max(w, h) < marker_threshold:
                cx, cy = largest_polygon_centroid(polys)
                lines.append(
                    f'        <circle class="country-marker" cx="{cx:.1f}" cy="{cy:.1f}" '
                    f'r="{marker_r}" stroke-width="{stroke_width}"/>'
                )
                marker_count += 1
        lines.append("      </g>")
    lines.append("    </g>")
    lines.append("  </g>")
    lines.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return marker_count


def main():
    with open(MASTER_PATH) as f:
        master_doc = json.load(f)
    master = {c["country_code"]: c for c in master_doc["countries"]}
    features = load_ne()
    groups, terr_groups, unmatched = collect_groups(features, master)

    missing = sorted(set(master) - set(groups))
    if missing:
        print("FATAL: master countries missing geometry:", missing, file=sys.stderr)
        sys.exit(1)
    if unmatched:
        print("dropped unmatched features:", unmatched, file=sys.stderr)

    width = 2000
    # (ファイル名, 中央経線, tol, min_area, marker_threshold, marker_r, stroke_width)
    variants = [
        ("map-full.svg", 0, 0.45, 2.5, 8.0, 4.0, 0.5),
        ("map-mobile.svg", 0, 1.0, 5.0, 14.0, 7.0, 0.8),
        ("map-full-japan-center.svg", 150, 0.45, 2.5, 8.0, 4.0, 0.5),
        ("map-mobile-japan-center.svg", 150, 1.0, 5.0, 14.0, 7.0, 0.8),
    ]
    projected_cache = {}
    for fname, center, tol, min_area, mth, mr, sw in variants:
        if center not in projected_cache:
            projected_cache[center] = project_all(groups, terr_groups, width, center)
        projected, height = projected_cache[center]
        proj_groups = {c: projected[c] for c in groups}
        proj_terrs = {c: projected[c] for c in terr_groups}
        n = render_svg(
            os.path.join(ROOT, fname), proj_groups, proj_terrs, master,
            width, height, tol=tol, min_area=min_area,
            marker_threshold=mth, marker_r=mr, stroke_width=sw,
        )
        print(f"{fname}: viewBox 0 0 {width} {math.ceil(height)}, markers={n}")

    # countries.json
    rows = []
    for code in sorted(set(list(groups) + list(terr_groups))):
        if code in master:
            m = master[code]
            rows.append({
                "code": code, "name_ja": m["name"], "name_en": m["name_en"],
                "region": m["continent"], "included_in_svg": True,
                "tabinote_matched": True, "notes": "",
            })
        else:
            t = {v[0]: v for v in TERRITORIES.values()}[code]
            rows.append({
                "code": code, "name_ja": t[1], "name_en": t[2],
                "region": t[3], "included_in_svg": True,
                "tabinote_matched": False,
                "notes": "tabiNote 国マスタ外。class='territory' として中立表示 (色塗り対象外)",
            })
    with open(os.path.join(ROOT, "countries.json"), "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"countries.json: {len(rows)} rows "
          f"(master {sum(1 for r in rows if r['tabinote_matched'])}, "
          f"territory {sum(1 for r in rows if not r['tabinote_matched'])})")


if __name__ == "__main__":
    main()
