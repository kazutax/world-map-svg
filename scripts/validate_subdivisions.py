#!/usr/bin/env python3
"""国の中の区画 SVG (subdivisions/{code}/) の検証。

期待値 (分母・安定 ID の集合・除外領域) はこのファイルに独立して持つ。
ビルド結果 (regions.json / SVG) から期待値を作らないことで、検証をオラクルとして保つ。

チェック内容 (国ごと、map-full.svg と map-mobile.svg の両方):
  1. 区分数が分母と一致する (SVG / regions.json)
  2. data-code の欠落・重複がなく、安定 ID の期待集合および regions.json と一致する
  3. <title> が「name_ja / name_en」(regions.json) と一致する
  4. 全区分が塗れる (パスまたはマーカーがあり、実用サイズがある)
  5. class="country" / country-marker が混ざっていない
  6. 除外すると決めた領域が分母に数えられていない (コード・名称・代表地点)
  7. パスは M / L / Z のみ、fill-rule="evenodd"、マーカーは親の fill を継承する
  8. モバイル版は簡略化され、線が太く、マーカーが大きい。各区分の最大ポリゴンが残っている
  9. 米国: アラスカ・ハワイが図の中にあり、本土と重なっていない

状態が pending の国は、ディレクトリが無ければ「未完了」として表示し失敗にしない。
ディレクトリがあれば released と同じ検証をかける。

終了コード: 全合格 0 / 不合格 1
レポート: reports/subdivisions-coverage.md
"""
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBDIR = os.path.join(ROOT, "subdivisions")
SVG_NS = "http://www.w3.org/2000/svg"
NS = {"svg": SVG_NS}
VARIANTS = ["map-full.svg", "map-mobile.svg"]

# 塗れるとみなす最小サイズ (viewBox 単位、長辺 1000 基準)。未満ならマーカー必須
MIN_PAINTABLE = 3.0

US_STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY"
).split()

# ONS ITL2 (January 2025)。ONS の Names and Codes 表 (ITL2_JAN_2025_UK_NC) と同じ 46 件
GB_ITL2_2025 = (
    "TLC3 TLC4 TLD1 TLD3 TLD4 TLD6 TLD7 TLE1 TLE2 TLE3 TLE4 TLF1 TLF2 TLF3 "
    "TLG1 TLG2 TLG3 TLH2 TLH3 TLH4 TLH5 TLH6 TLI3 TLI4 TLI5 TLI6 TLI7 "
    "TLJ1 TLJ2 TLJ3 TLJ4 TLK3 TLK4 TLK5 TLK6 TLK7 TLL3 TLL4 TLL5 "
    "TLM0 TLM1 TLM2 TLM3 TLM5 TLM9 TLN0"
).split()
# ITL 2021 (41 地域) にだけ存在するコード。2025 年版と混ざっていたら失敗
GB_ITL2_2021_ONLY = "TLC1 TLC2 TLH1 TLK1 TLK2 TLL1 TLL2 TLM6 TLM7 TLM8".split()

# URA Master Plan 2025 の計画区域 55。区分として数えてはいけない
SG_PLANNING_AREAS = [
    "ANG MO KIO", "BEDOK", "BISHAN", "BOON LAY", "BUKIT BATOK", "BUKIT MERAH",
    "BUKIT PANJANG", "BUKIT TIMAH", "CENTRAL WATER CATCHMENT", "CHANGI", "CHANGI BAY",
    "CHOA CHU KANG", "CLEMENTI", "DOWNTOWN CORE", "GEYLANG", "HOUGANG", "JURONG EAST",
    "JURONG WEST", "KALLANG", "LIM CHU KANG", "MANDAI", "MARINA EAST", "MARINA SOUTH",
    "MARINE PARADE", "MUSEUM", "NEWTON", "NORTH-EASTERN ISLANDS", "NOVENA", "ORCHARD",
    "OUTRAM", "PASIR RIS", "PAYA LEBAR", "PIONEER", "PUNGGOL", "QUEENSTOWN",
    "RIVER VALLEY", "ROCHOR", "SELETAR", "SEMBAWANG", "SENGKANG", "SERANGOON",
    "SIMPANG", "SINGAPORE RIVER", "SOUTHERN ISLANDS", "STRAITS VIEW", "SUNGEI KADUT",
    "TAMPINES", "TANGLIN", "TENGAH", "TOA PAYOH", "TUAS", "WESTERN ISLANDS",
    "WESTERN WATER CATCHMENT", "WOODLANDS", "YISHUN",
]

# sentinels: (説明, 経度, 緯度, 期待) 期待 = None ならどの区分にも含まれない、
# コードならその区分に含まれる
SPEC = {
    "us": {
        "country": "US", "denominator": 51, "status": "released",
        "codes": [f"US-{s}" for s in US_STATES] + ["US-DC"],
        "excluded_codes": ["US-PR", "US-GU", "US-VI", "US-AS", "US-MP", "US-UM", "PR", "GU",
                           "VI", "AS", "MP", "UM"],
        "excluded_names": ["puerto rico", "guam", "virgin islands", "american samoa",
                           "northern mariana", "minor outlying", "プエルトリコ", "グアム",
                           "ヴァージン", "バージン", "サモア", "マリアナ", "小離島"],
        "sentinels": [
            ("プエルトリコ (サンフアン)", -66.10, 18.42, None),
            ("米領ヴァージン諸島", -64.93, 18.34, None),
            ("グアム", 144.79, 13.44, None),
            ("首都ワシントン", -77.03, 38.90, "US-DC"),
        ],
        "insets": ["US-AK", "US-HI"],
    },
    "gb": {
        "country": "GB", "denominator": 46, "status": "released",
        "codes": GB_ITL2_2025,
        "required": ["TLN0"],
        "excluded_codes": GB_ITL2_2021_ONLY + [
            "GB", "UK", "GB-ENG", "GB-SCT", "GB-WLS", "GB-NIR",
            "E92000001", "S92000003", "W92000004", "N92000002", "IM", "JE", "GG"],
        "excluded_code_patterns": [r"^UK[C-N]", r"^TL[C-N]$"],
        "excluded_names": ["isle of man", "jersey", "guernsey", "マン島", "ジャージー",
                           "ガーンジー"],
        "sentinels": [
            ("北アイルランド (ベルファスト)", -5.93, 54.60, "TLN0"),
            ("マン島 (ダグラス)", -4.48, 54.15, None),
            ("ジャージー (セントヘリア)", -2.11, 49.19, None),
            ("アイルランド共和国 (ダブリン)", -6.26, 53.35, None),
        ],
    },
    "kr": {
        "country": "KR", "denominator": 16, "status": "released",
        # 2026-07-01 に KR-29 (光州) と KR-46 (全南) が統合。新区分は ISO 未割当のため
        # 韓国の行政区域コード 12 を使った KR-12
        "codes": [f"KR-{n}" for n in (11, 26, 27, 28, 30, 31, 41, 42, 43, 44, 45, 47, 48, 49,
                                      50, 12)],
        "excluded_codes": ["KR-29", "KR-46", "KR", "KR-KR"],
        "excluded_names_exact": ["gwangju", "south jeolla", "jeollanam-do", "gwangju-gwangyeoksi",
                                 "光州広域市", "全羅南道", "광주광역시", "전라남도"],
        "excluded_names": ["north korea", "북한", "北朝鮮", "pyongyang", "평양", "平壌"],
        "sentinels": [
            ("旧光州広域市 (光州市庁)", 126.851, 35.160, "KR-12"),
            ("旧全羅南道 (務安・道庁)", 126.463, 34.816, "KR-12"),
            ("軍威郡 (2023-07-01 に大邱へ編入)", 128.573, 36.243, "KR-27"),
            ("開城 (北朝鮮)", 126.555, 37.970, None),
            ("対馬 (日本)", 129.290, 34.200, None),
        ],
    },
    "cn": {
        "country": "CN", "denominator": 31, "status": "released",
        # ISO 3166-2:CN の 34 件から CN-TW・CN-HK・CN-MO を除いた 31 件
        "codes": [f"CN-{s}" for s in
                  "AH BJ CQ FJ GD GS GX GZ HA HB HE HI HL HN JL JS JX LN NM NX QH SC SD SH "
                  "SN SX TJ XJ XZ YN ZJ".split()],
        "excluded_codes": ["CN-TW", "CN-HK", "CN-MO", "TW", "HK", "MO", "CN", "CN-X01~"],
        "excluded_names": ["taiwan", "hong kong", "macau", "macao", "paracel", "台湾", "臺灣",
                           "臺湾", "香港", "マカオ", "澳門", "澳门", "パラセル", "西沙"],
        "sentinels": [
            ("台北", 121.56, 25.04, None),
            ("高雄", 120.30, 22.62, None),
            ("金門 (台湾)", 118.35, 24.44, None),
            ("香港 (尖沙咀)", 114.17, 22.30, None),
            ("香港 (ランタオ島)", 113.94, 22.26, None),
            ("マカオ", 113.55, 22.19, None),
            ("西沙諸島 (永興島)", 112.34, 16.83, None),
            ("北京", 116.40, 39.90, "CN-BJ"),
            ("上海", 121.47, 31.23, "CN-SH"),
            ("広州", 113.26, 23.13, "CN-GD"),
            ("海口 (海南島)", 110.33, 20.03, "CN-HI"),
            ("フフホト", 111.75, 40.84, "CN-NM"),
            ("ウルムチ", 87.62, 43.83, "CN-XJ"),
            ("ラサ", 91.13, 29.65, "CN-XZ"),
        ],
    },
    "ca": {
        "country": "CA", "denominator": 13, "status": "released",
        "codes": [f"CA-{s}" for s in "AB BC MB NB NL NS NT NU ON PE QC SK YT".split()],
        "excluded_names": ["saint-pierre", "miquelon", "サンピエール"],
        "sentinels": [("サンピエール島 (仏領)", -56.18, 46.78, None)],
    },
    "au": {
        "country": "AU", "denominator": 8, "status": "released",
        "codes": [f"AU-{s}" for s in "NSW VIC QLD SA WA TAS NT ACT".split()],
        "excluded_codes": ["AU-X02~", "AU-JBT", "CX", "CC", "NF", "HM", "AU-CX", "AU-CC",
                           "AU-NF", "AU-HM"],
        "excluded_names": ["christmas island", "cocos", "keeling", "norfolk", "heard island",
                           "mcdonald", "ashmore", "cartier", "coral sea", "jervis bay",
                           "antarctic", "クリスマス島", "ココス", "キーリング", "ノーフォーク",
                           "ハード島", "マクドナルド", "アシュモア", "カルティエ", "珊瑚海",
                           "コーラル・シー", "ジャービス", "ジャーヴィス", "南極"],
        "sentinels": [
            ("クリスマス島", 105.69, -10.45, None),
            ("ココス (キーリング) 諸島", 96.87, -12.17, None),
            ("ノーフォーク島", 167.95, -29.03, None),
            ("キャンベラ", 149.13, -35.28, "AU-ACT"),
        ],
    },
    "nz": {
        "country": "NZ", "denominator": 16, "status": "released",
        "codes": [f"NZ-{s}" for s in
                  "AUK BOP CAN GIS HKB MBH MWT NSN NTL OTA STL TAS TKI WGN WKO WTC".split()],
        "excluded_codes": ["NZ-CIT"],
        "excluded_names": ["chatham", "wharekauri", "kermadec", "tokelau", "チャタム",
                           "ケルマデック", "トケラウ"],
        "sentinels": [
            ("チャタム諸島 (ワイタンギ)", -176.56, -43.95, None),
            ("ケルマデック諸島 (ラウル島)", -177.92, -29.27, None),
        ],
    },
    "ie": {
        "country": "IE", "denominator": 26, "status": "released",
        "codes": [f"IE-{s}" for s in
                  "CW CN CE CO DL D G KY KE KK LS LM LK LD LH MO MH MN OY RN SO TA WD WH "
                  "WX WW".split()],
        "excluded_codes": ["TLN0", "GB-NIR", "N92000002", "IE-C", "IE-L", "IE-M", "IE-U"],
        "excluded_code_patterns": [r"^GB-", r"^UK"],
        "excluded_names_exact": [
            "northern ireland", "antrim", "armagh", "down", "fermanagh", "londonderry",
            "derry", "tyrone", "fingal", "south dublin", "dún laoghaire–rathdown",
            "dun laoghaire-rathdown", "dublin city", "north tipperary", "south tipperary",
            "cork city", "galway city", "limerick city", "waterford city",
            "北アイルランド", "アントリム県", "アーマー県", "ダウン県", "ファーマナ県",
            "ロンドンデリー県", "ティロン県", "タイロン県"],
        "sentinels": [
            ("ベルファスト", -5.93, 54.60, None),
            ("エニスキレン", -7.64, 54.34, None),
            ("オマー", -7.30, 54.60, None),
            ("デリー/ロンドンデリー", -7.31, 55.00, None),
            ("アーマー", -6.65, 54.35, None),
            ("ダブリン", -6.26, 53.35, "IE-D"),
            ("ティペラリー (クロンメル)", -7.70, 52.36, "IE-TA"),
            ("ティペラリー (ネナー)", -8.20, 52.86, "IE-TA"),
        ],
    },
    "sg": {
        "country": "SG", "denominator": 5, "status": "released",
        "codes": ["SG-CR", "SG-ER", "SG-NR", "SG-NE", "SG-WR"],
        "excluded_names_exact": [n.lower() for n in SG_PLANNING_AREAS],
        "sentinels": [("ジョホールバル (マレーシア)", 103.76, 1.47, None)],
    },
}


# ---------------------------------------------------------------- 投影 (前方のみ)

def conic_equal_area_raw(parallels):
    """d3-geo の conicEqualArea と同じ式。parallels が赤道対称なら円筒正積。"""
    p0, p1 = (math.radians(v) for v in parallels)
    sy0 = math.sin(p0)
    n = (sy0 + math.sin(p1)) / 2
    if abs(n) < 1e-6:
        cp0 = math.cos(p0)
        return lambda lam, phi: (lam * cp0, math.sin(phi) / cp0)
    c = 1 + sy0 * (2 * n - sy0)
    r0 = math.sqrt(c) / n

    def f(lam, phi):
        r = math.sqrt(max(0.0, c - 2 * n * math.sin(phi))) / n
        lam *= n
        return r * math.sin(lam), r0 - r * math.cos(lam)
    return f


def make_projector(p):
    """regions.json の projection 1 件から (lon, lat) -> viewBox 座標の関数を作る。"""
    raw = conic_equal_area_raw(p["parallels"])
    rot = p["rotate"]
    cx, cy = raw(math.radians(p["center"][0]), math.radians(p["center"][1]))
    k, tx, ty = p["scale"], p["translate"][0], p["translate"][1]

    def f(lon, lat):
        lam = ((lon + rot + 540.0) % 360.0) - 180.0
        x, y = raw(math.radians(lam), math.radians(lat))
        return tx + k * (x - cx), ty - k * (y - cy)
    return f


# ---------------------------------------------------------------- SVG 解析

PATH_OK = re.compile(r"(?:[MLZ]|-?\d+(?:\.\d+)?|[\s,])+")
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def parse_subpaths(d):
    """M/L/Z のみのパスをサブパス (点列) のリストにする。"""
    subpaths = []
    for chunk in re.split(r"(?=M)", d.strip()):
        if not chunk.strip():
            continue
        vals = [float(v) for v in NUM.findall(chunk)]
        pts = list(zip(vals[0::2], vals[1::2]))
        if pts:
            subpaths.append(pts)
    return subpaths


def ring_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def bbox_of(pts_list):
    xs = [p[0] for pts in pts_list for p in pts]
    ys = [p[1] for pts in pts_list for p in pts]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def point_in_evenodd(x, y, subpaths):
    inside = False
    for pts in subpaths:
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xi > x:
                    inside = not inside
    return inside


def segments_cross(a, b, c, d):
    """線分 ab と cd が端点以外で交差するか (共有境界の接触は除外)。"""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def analyze_svg(path):
    tree = ET.parse(path)
    root = tree.getroot()
    info = {"root": root, "errors": [], "regions": {}, "dup": [], "all_codes": []}
    vb = [float(v) for v in (root.get("viewBox") or "0 0 0 0").split()]
    info["viewBox"] = vb
    for el in root.iter():
        cls = (el.get("class") or "").split()
        if "country" in cls or "country-marker" in cls:
            info["errors"].append(f"class=\"country\" 系が混入: <{el.tag.split('}')[-1]} "
                                  f"class=\"{el.get('class')}\">")
        if el.tag == f"{{{SVG_NS}}}path":
            d = el.get("d", "")
            if not PATH_OK.fullmatch(d):
                bad = sorted(set(re.findall(r"[A-Za-z]", d)) - {"M", "L", "Z"})
                info["errors"].append(f"M/L/Z 以外のパスコマンド {bad}")
    info["boundary_lines"] = [
        sp for g in root.iter(f"{{{SVG_NS}}}g") if "boundary-line" in (g.get("class") or "").split()
        for p in g.findall("svg:path", NS) for sp in parse_subpaths(p.get("d", ""))]
    for g in root.iter(f"{{{SVG_NS}}}g"):
        code = g.get("data-code")
        if code is None:
            continue
        info["all_codes"].append(code)
        classes = (g.get("class") or "").split()
        title_el = g.find("svg:title", NS)
        paths = [p.get("d", "") for p in g.findall("svg:path", NS)]
        subpaths = [sp for d in paths for sp in parse_subpaths(d)]
        markers = g.findall("svg:circle", NS)
        r = {
            "classes": classes,
            "country": g.get("data-country"),
            "fill_rule": g.get("fill-rule"),
            "title": title_el.text if title_el is not None else None,
            "n_paths": len(paths),
            "subpaths": subpaths,
            "n_vertices": sum(len(sp) for sp in subpaths),
            "markers": [{
                "cls": (c.get("class") or "").split(),
                "cx": float(c.get("cx", "nan")), "cy": float(c.get("cy", "nan")),
                "r": float(c.get("r", "0")),
                "has_fill": c.get("fill") is not None or "fill" in (c.get("style") or ""),
            } for c in markers],
            "path_has_fill": any(p.get("fill") is not None for p in g.findall("svg:path", NS)),
            "stroke_width": float(g.get("stroke-width", "0")),
        }
        if code in info["regions"]:
            info["dup"].append(code)
        info["regions"][code] = r
    return info


# ---------------------------------------------------------------- 検証本体

def name_hits(text, spec):
    t = (text or "").strip().casefold()
    hits = []
    for n in spec.get("excluded_names", []):
        if n.casefold() in t:
            hits.append(n)
    for n in spec.get("excluded_names_exact", []):
        if t == n.casefold():
            hits.append(n)
    return hits


def code_hits(code, spec):
    if code in spec.get("excluded_codes", []):
        return True
    return any(re.search(p, code) for p in spec.get("excluded_code_patterns", []))


def validate_country(key, spec):
    errors = []
    summary = {"key": key, "country": spec["country"], "denominator": spec["denominator"]}
    d = os.path.join(SUBDIR, key)
    expected = spec["codes"]
    if len(expected) != spec["denominator"] or len(set(expected)) != len(expected):
        errors.append(f"検証表の不整合: 期待コード {len(set(expected))} 件 != 分母 "
                      f"{spec['denominator']}")
    exp_set = set(expected)
    a2 = spec["country"]

    # ---- regions.json
    rj_path = os.path.join(d, "regions.json")
    if not os.path.exists(rj_path):
        return [f"regions.json が無い"], summary
    with open(rj_path) as f:
        rj = json.load(f)
    if not isinstance(rj, dict) or not isinstance(rj.get("regions"), list):
        return ["regions.json は {\"regions\": [...]} を持つオブジェクトであること"], summary
    regions = rj["regions"]
    summary["regions_json"] = len(regions)
    if rj.get("country") != a2:
        errors.append(f"regions.json country={rj.get('country')} != {a2}")
    if rj.get("denominator") != spec["denominator"]:
        errors.append(f"regions.json denominator={rj.get('denominator')} != {spec['denominator']}")
    if len(regions) != spec["denominator"]:
        errors.append(f"区分数: regions.json {len(regions)} != 分母 {spec['denominator']}")
    src = rj.get("source") or {}
    for k in ("name", "url", "version", "license"):
        if not src.get(k):
            errors.append(f"regions.json source.{k} が無い (出典の注記)")
    rj_codes = []
    by_code = {}
    for i, r in enumerate(regions):
        for k in ("code", "country", "name_ja", "name_en", "included_in_svg"):
            if k not in r:
                errors.append(f"regions.json[{i}] に {k} が無い")
        code = r.get("code")
        if not code:
            errors.append(f"regions.json[{i}] の code が空")
            continue
        rj_codes.append(code)
        by_code[code] = r
        if r.get("country") != a2:
            errors.append(f"{code}: country={r.get('country')} != {a2}")
        if code == a2:
            errors.append(f"{code}: 国コードそのものを区分コードにしている")
        if r.get("included_in_svg") is not True:
            errors.append(f"{code}: included_in_svg が true でない (塗れない区分)")
        if code_hits(code, spec):
            errors.append(f"除外領域が分母に入っている: code={code}")
        for field in ("name_ja", "name_en"):
            for h in name_hits(r.get(field), spec):
                errors.append(f"除外領域が分母に入っている: {code} {field}='{r.get(field)}' ({h})")
    dups = sorted({c for c in rj_codes if rj_codes.count(c) > 1})
    if dups:
        errors.append(f"regions.json の code 重複: {dups}")
    if set(rj_codes) != exp_set:
        errors.append(f"regions.json と安定 ID の不一致: 欠落 {sorted(exp_set - set(rj_codes))} "
                      f"/ 余剰 {sorted(set(rj_codes) - exp_set)}")
    for c in spec.get("required", []):
        if c not in rj_codes:
            errors.append(f"必須区分 {c} が無い")

    # ---- SVG
    proj = rj.get("projection") or {}
    infos = {}
    for v in VARIANTS:
        p = os.path.join(d, v)
        if not os.path.exists(p):
            errors.append(f"{v} が無い")
            continue
        try:
            info = analyze_svg(p)
        except ET.ParseError as e:
            errors.append(f"{v}: XML パース失敗 {e}")
            continue
        infos[v] = info
        tag = v
        errors.extend(f"{tag}: {e}" for e in info["errors"])
        root = info["root"]
        if root.get("data-country") != a2:
            errors.append(f"{tag}: <svg data-country> が {a2} でない")
        regs = info["regions"]
        if info["dup"]:
            errors.append(f"{tag}: data-code 重複 {sorted(set(info['dup']))}")
        if len(info["all_codes"]) != spec["denominator"]:
            errors.append(f"{tag}: 区分数 {len(info['all_codes'])} != 分母 {spec['denominator']}")
        svg_codes = set(regs)
        if svg_codes != set(rj_codes):
            errors.append(f"{tag}: regions.json との不一致: SVG のみ "
                          f"{sorted(svg_codes - set(rj_codes))} / JSON のみ "
                          f"{sorted(set(rj_codes) - svg_codes)}")
        if svg_codes != exp_set:
            errors.append(f"{tag}: 安定 ID の不一致: 欠落 {sorted(exp_set - svg_codes)} / "
                          f"余剰 {sorted(svg_codes - exp_set)}")
        vx, vy, vw, vh = info["viewBox"]
        for code, r in sorted(regs.items()):
            if "region" not in r["classes"]:
                errors.append(f"{tag}: {code} に class=\"region\" が無い")
            if r["country"] != a2:
                errors.append(f"{tag}: {code} data-country={r['country']} != {a2}")
            if r["fill_rule"] != "evenodd":
                errors.append(f"{tag}: {code} fill-rule が evenodd でない")
            if code_hits(code, spec):
                errors.append(f"{tag}: 除外領域が分母に入っている: data-code={code}")
            for part in (r["title"] or "").split(" / "):
                for h in name_hits(part, spec):
                    errors.append(f"{tag}: 除外領域が分母に入っている: {code} "
                                  f"title='{r['title']}' ({h})")
            jr = by_code.get(code)
            if jr:
                expected_title = f"{jr.get('name_ja')} / {jr.get('name_en')}"
                if r["title"] != expected_title:
                    errors.append(f"{tag}: {code} title '{r['title']}' != '{expected_title}'")
            if r["n_paths"] > 1:
                errors.append(f"{tag}: {code} の <path> が {r['n_paths']} 個 "
                              "(飛び地と穴は 1 つの <path> に入れる)")
            if r["path_has_fill"]:
                errors.append(f"{tag}: {code} の <path> に fill がある (親から継承させる)")
            good_sub = [sp for sp in r["subpaths"] if len(sp) >= 3]
            markers = [m for m in r["markers"] if "region-marker" in m["cls"] and m["r"] > 0]
            for m in r["markers"]:
                if "region-marker" not in m["cls"]:
                    errors.append(f"{tag}: {code} に region-marker 以外の <circle>")
                if m["has_fill"]:
                    errors.append(f"{tag}: {code} のマーカーに fill がある (親から継承させる)")
                if not (vx <= m["cx"] <= vx + vw and vy <= m["cy"] <= vy + vh):
                    errors.append(f"{tag}: {code} のマーカーが viewBox の外")
            if not good_sub and not markers:
                errors.append(f"{tag}: 塗れない区分 {code} (パスもマーカーも無い)")
                continue
            size = 0.0
            bb = bbox_of(good_sub)
            if bb:
                size = max(bb[2] - bb[0], bb[3] - bb[1])
                if bb[0] < vx - 0.5 or bb[1] < vy - 0.5 or bb[2] > vx + vw + 0.5 \
                        or bb[3] > vy + vh + 0.5:
                    errors.append(f"{tag}: {code} のパスが viewBox の外にはみ出す")
            if markers:
                size = max(size, 2 * max(m["r"] for m in markers))
            if size < MIN_PAINTABLE:
                errors.append(f"{tag}: 塗れない区分 {code} (実用サイズ {size:.1f} < "
                              f"{MIN_PAINTABLE} でマーカーも無い)")

        # 代表地点 (除外領域が塗れる形で含まれていないか / 含まれるべき区分にあるか)
        if proj.get("main"):
            fwd = make_projector(proj["main"])
            for label, lon, lat, want in spec.get("sentinels", []):
                x, y = fwd(lon, lat)
                hits = [c for c, r in regs.items()
                        if point_in_evenodd(x, y, [sp for sp in r["subpaths"] if len(sp) >= 3])]
                if want is None and hits:
                    errors.append(f"{tag}: 除外領域 {label} が {hits} に含まれている")
                if want is not None and want not in hits:
                    # 小さい区分はマーカーで代替されることがあるので、マーカー内も許容
                    r = regs.get(want)
                    near = r and any(math.hypot(m["cx"] - x, m["cy"] - y) <= max(m["r"], 6)
                                     for m in r["markers"])
                    if not near:
                        errors.append(f"{tag}: {label} が {want} に含まれていない (hits={hits})")
        elif spec.get("sentinels"):
            errors.append("regions.json projection.main が無い (代表地点の検証ができない)")

        # 米国のはめ込み (アラスカ・ハワイ) は図の中にあり、他の区分と重ならない
        for inset in spec.get("insets", []):
            r = regs.get(inset)
            if not r:
                continue
            ins = [sp for sp in r["subpaths"] if len(sp) >= 3]
            ib = bbox_of(ins)
            for oc, orr in regs.items():
                if oc in spec["insets"]:
                    continue
                osp = [sp for sp in orr["subpaths"] if len(sp) >= 3]
                ob = bbox_of(osp)
                if not ob or ob[2] < ib[0] or ob[0] > ib[2] or ob[3] < ib[1] or ob[1] > ib[3]:
                    continue
                overlap = any(point_in_evenodd(x, y, osp) for sp in ins for x, y in sp) or \
                    any(point_in_evenodd(x, y, ins) for sp in osp for x, y in sp)
                if not overlap:
                    for sp in ins:
                        for i in range(len(sp)):
                            a, b = sp[i], sp[(i + 1) % len(sp)]
                            for osub in osp:
                                for j in range(len(osub)):
                                    if segments_cross(a, b, osub[j], osub[(j + 1) % len(osub)]):
                                        overlap = True
                                        break
                                if overlap:
                                    break
                            if overlap:
                                break
                        if overlap:
                            break
                if overlap:
                    errors.append(f"{tag}: はめ込みの {inset} が {oc} と重なっている")

        # はめ込みの区切り線 (boundary-line) が区分を横切らない
        for line in info["boundary_lines"]:
            for i in range(len(line) - 1):
                a, b = line[i], line[i + 1]
                for oc, orr in regs.items():
                    if any(segments_cross(a, b, sp[j], sp[(j + 1) % len(sp)])
                           for sp in orr["subpaths"] if len(sp) >= 3 for j in range(len(sp))):
                        errors.append(f"{tag}: 区切り線 (boundary-line) が {oc} を横切っている")

    # ---- full / mobile の関係
    if len(infos) == 2:
        full, mob = infos["map-full.svg"], infos["map-mobile.svg"]
        if full["viewBox"] != mob["viewBox"]:
            errors.append("full と mobile の viewBox が違う")
        fv = sum(r["n_vertices"] for r in full["regions"].values())
        mv = sum(r["n_vertices"] for r in mob["regions"].values())
        summary["vertices"] = (fv, mv)
        if not mv < fv:
            errors.append(f"mobile が簡略化されていない (頂点数 full {fv} / mobile {mv})")
        fsw = max((r["stroke_width"] for r in full["regions"].values()), default=0)
        msw = min((r["stroke_width"] for r in mob["regions"].values()), default=0)
        if not msw > fsw:
            errors.append(f"mobile の線が太くない (full {fsw} / mobile {msw})")
        fm = {c for c, r in full["regions"].items() if r["markers"]}
        mm = {c for c, r in mob["regions"].items() if r["markers"]}
        summary["markers"] = (sorted(fm), sorted(mm))
        if fm - mm:
            errors.append(f"full にあるマーカーが mobile に無い: {sorted(fm - mm)}")
        for c in fm & mm:
            if not max(m["r"] for m in mob["regions"][c]["markers"]) > \
                    max(m["r"] for m in full["regions"][c]["markers"]):
                errors.append(f"{c}: mobile のマーカーが full より大きくない")
        for c, fr in full["regions"].items():
            mr = mob["regions"].get(c)
            if not mr:
                continue
            fa = max((ring_area(sp) for sp in fr["subpaths"] if len(sp) >= 3), default=0)
            ma = max((ring_area(sp) for sp in mr["subpaths"] if len(sp) >= 3), default=0)
            if fa >= 1.0 and ma < 0.5 * fa:
                errors.append(f"{c}: mobile で最大ポリゴンが失われている "
                              f"(面積 full {fa:.1f} / mobile {ma:.1f})")
    return errors, summary


def main():
    all_errors = {}
    summaries = {}
    lines_out = []
    if os.path.isdir(SUBDIR):
        unknown = sorted(n for n in os.listdir(SUBDIR)
                         if os.path.isdir(os.path.join(SUBDIR, n)) and n not in SPEC)
        if unknown:
            all_errors["_"] = [f"検証表に無い国ディレクトリ: {unknown}"]
    for key, spec in SPEC.items():
        present = os.path.isdir(os.path.join(SUBDIR, key))
        if spec["status"] == "pending" and not present:
            summaries[key] = {"pending": True}
            lines_out.append(f"{key}: 未完了 (未収録) - {spec['pending_reason']}")
            continue
        if not present:
            all_errors[key] = [f"subdivisions/{key}/ が無い"]
            lines_out.append(f"{key}: 1 errors")
            lines_out.append(f"  - subdivisions/{key}/ が無い")
            continue
        errors, summary = validate_country(key, spec)
        all_errors[key] = errors
        summaries[key] = summary
        status = "OK" if not errors else f"{len(errors)} errors"
        lines_out.append(f"{key}: {status} ({spec['country']} 分母 {spec['denominator']})")
        lines_out.extend(f"  - {e}" for e in errors[:40])
        if len(errors) > 40:
            lines_out.append(f"  ... ほか {len(errors) - 40} 件")
    for e in all_errors.get("_", []):
        lines_out.append(f"_: {e}")

    ok = not any(all_errors.values())
    write_report(summaries, all_errors, ok)
    print("\n".join(lines_out))
    print("report -> reports/subdivisions-coverage.md")
    sys.exit(0 if ok else 1)


def write_report(summaries, all_errors, ok):
    lines = ["# 国の中の区画 検証レポート", ""]
    lines.append(f"- 判定: **{'合格' if ok else '不合格'}**"
                 "（`python3 scripts/validate_subdivisions.py`）")
    lines.append("")
    lines.append("| 国 | ディレクトリ | 分母 | 区分数 | 頂点数 full / mobile | マーカー full / mobile | 状態 |")
    lines.append("|---|---|---|---|---|---|---|")
    for key, spec in SPEC.items():
        s = summaries.get(key, {})
        if s.get("pending"):
            lines.append(f"| {spec['country']} | `{key}` | {spec['denominator']} | － | － | － | "
                         "未完了（未収録） |")
            continue
        v = s.get("vertices", ("－", "－"))
        m = s.get("markers", ([], []))
        state = "OK" if not all_errors.get(key) else f"{len(all_errors[key])} errors"
        lines.append(
            f"| {spec['country']} | `{key}` | {spec['denominator']} | "
            f"{s.get('regions_json', '－')} | {v[0]} / {v[1]} | "
            f"{', '.join(m[0]) or 'なし'} / {', '.join(m[1]) or 'なし'} | {state} |")
    lines.append("")
    pend = [(k, s) for k, s in SPEC.items() if s["status"] == "pending"]
    if pend:
        lines.append("## 未完了の国")
        lines.append("")
        for k, s in pend:
            lines.append(f"- **{s['country']}（`{k}`）**: {s['pending_reason']}")
        lines.append("")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "reports", "subdivisions-coverage.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
