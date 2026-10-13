#!/usr/bin/env python3
"""国の中の区画 SVG (subdivisions/{code}/map-full.svg, map-mobile.svg, regions.json) の生成。

ベースデータ (data/ に無ければダウンロード):
  - Natural Earth 1:10m Admin 1 (大きな湖を除いた版) v5.1.2 (パブリックドメイン)
      us / ca / au / nz / ie
  - ONS International Territorial Level 2 (January 2025) Boundaries UK BUC
      gb (Open Government Licence v3.0)
  - URA Master Plan 2025 Region Boundary (No Sea) (data.gov.sg)
      sg (Singapore Open Data Licence v1.0)

使い方:
    python3 scripts/build_subdivisions.py          # 全か国
    python3 scripts/build_subdivisions.py us ie    # 指定した国だけ
依存: Python 3.9+ 標準ライブラリのみ
"""
import datetime
import hashlib
import json
import math
import os
import sys
import time
import unicodedata
import urllib.request
from collections import defaultdict
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import dp_simplify, ring_area, slugify  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "subdivisions")
UA = {"User-Agent": "world-map-svg-build (+https://github.com/kazutax/world-map-svg)"}

DEFAULT_FILL = "#EEEEEE"
STROKE = "#000000"
LONG_SIDE = 1000  # viewBox の長辺
PAD = 12  # viewBox の余白

# (ファイル名, 簡略化許容誤差, 最小ポリゴン面積, マーカー閾値, マーカー半径, 線幅)
# マーカー閾値は「最大ポリゴンの面積の平方根」。細長い区分 (PEI 等) も指せない側に数える
VARIANTS = [
    ("map-full.svg", 0.3, 0.8, 7.0, 5.0, 0.5),
    ("map-mobile.svg", 0.8, 3.0, 14.0, 10.0, 1.0),
]

NE_VERSION = "v5.1.2"
SOURCES = {
    "ne": {
        "name": "Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces "
                "(large lakes removed)",
        "publisher": "Natural Earth",
        "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/"
               "10m-admin-1-states-provinces/",
        "download_url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
                        f"{NE_VERSION}/geojson/ne_10m_admin_1_states_provinces_lakes.geojson",
        "version": f"{NE_VERSION} (ne_10m_admin_1_states_provinces_lakes)",
        "license": "Public Domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
        "attribution": "Made with Natural Earth. Free vector and raster map data @ "
                       "naturalearthdata.com.",
        "file": "ne_10m_admin_1_states_provinces_lakes.geojson",
    },
    "ons": {
        "name": "International Territorial Level 2 (January 2025) Boundaries UK BUC",
        "publisher": "Office for National Statistics (Open Geography Portal)",
        "url": "https://geoportal.statistics.gov.uk/search?q=ITL2_JAN_2025_UK_BUC",
        "download_url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
                        "ITL2_JAN_2025_UK_BUC/FeatureServer/0/query?where=1%3D1&"
                        "outFields=ITL225CD,ITL225NM&outSR=4326&f=geojson",
        "version": "ITL 2025 (January 2025), ITL2, BUC (ultra generalised 500m, clipped "
                   "to the coastline)",
        "license": "Open Government Licence v3.0",
        "license_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/"
                       "version/3/",
        "attribution": "Source: Office for National Statistics licensed under the Open "
                       "Government Licence v.3.0. Contains OS data © Crown copyright and "
                       "database right 2025.",
        "file": "ons_itl2_jan2025_uk_buc.geojson",
    },
    "ura": {
        "name": "Master Plan 2025 Region Boundary (No Sea)",
        "publisher": "Urban Redevelopment Authority (data.gov.sg)",
        "url": "https://data.gov.sg/datasets/d_4ce0038f7ac689652350bb91b7fb92ed/view",
        "download_url": "https://api-open.data.gov.sg/v1/public/api/datasets/"
                        "d_4ce0038f7ac689652350bb91b7fb92ed/poll-download",
        "version": "URA Master Plan 2025 (gazetted 2025-12-01), dataset updated 2026-02-27",
        "license": "Singapore Open Data Licence v1.0",
        "license_url": "https://data.gov.sg/open-data-licence",
        "attribution": "Contains information from Master Plan 2025 Region Boundary (No Sea) "
                       "accessed on {retrieved} from data.gov.sg which is made available "
                       "under the terms of the Singapore Open Data Licence version 1.0 "
                       "https://data.gov.sg/open-data-licence",
        "file": "ura_mp2025_region_boundary_no_sea.geojson",
    },
}

# ------------------------------------------------------------------ 区分名
US_NAMES = {
    "US-AL": ("アラバマ州", "Alabama"), "US-AK": ("アラスカ州", "Alaska"),
    "US-AZ": ("アリゾナ州", "Arizona"), "US-AR": ("アーカンソー州", "Arkansas"),
    "US-CA": ("カリフォルニア州", "California"), "US-CO": ("コロラド州", "Colorado"),
    "US-CT": ("コネチカット州", "Connecticut"), "US-DE": ("デラウェア州", "Delaware"),
    "US-FL": ("フロリダ州", "Florida"), "US-GA": ("ジョージア州", "Georgia"),
    "US-HI": ("ハワイ州", "Hawaii"), "US-ID": ("アイダホ州", "Idaho"),
    "US-IL": ("イリノイ州", "Illinois"), "US-IN": ("インディアナ州", "Indiana"),
    "US-IA": ("アイオワ州", "Iowa"), "US-KS": ("カンザス州", "Kansas"),
    "US-KY": ("ケンタッキー州", "Kentucky"), "US-LA": ("ルイジアナ州", "Louisiana"),
    "US-ME": ("メイン州", "Maine"), "US-MD": ("メリーランド州", "Maryland"),
    "US-MA": ("マサチューセッツ州", "Massachusetts"), "US-MI": ("ミシガン州", "Michigan"),
    "US-MN": ("ミネソタ州", "Minnesota"), "US-MS": ("ミシシッピ州", "Mississippi"),
    "US-MO": ("ミズーリ州", "Missouri"), "US-MT": ("モンタナ州", "Montana"),
    "US-NE": ("ネブラスカ州", "Nebraska"), "US-NV": ("ネバダ州", "Nevada"),
    "US-NH": ("ニューハンプシャー州", "New Hampshire"),
    "US-NJ": ("ニュージャージー州", "New Jersey"),
    "US-NM": ("ニューメキシコ州", "New Mexico"), "US-NY": ("ニューヨーク州", "New York"),
    "US-NC": ("ノースカロライナ州", "North Carolina"),
    "US-ND": ("ノースダコタ州", "North Dakota"), "US-OH": ("オハイオ州", "Ohio"),
    "US-OK": ("オクラホマ州", "Oklahoma"), "US-OR": ("オレゴン州", "Oregon"),
    "US-PA": ("ペンシルベニア州", "Pennsylvania"),
    "US-RI": ("ロードアイランド州", "Rhode Island"),
    "US-SC": ("サウスカロライナ州", "South Carolina"),
    "US-SD": ("サウスダコタ州", "South Dakota"), "US-TN": ("テネシー州", "Tennessee"),
    "US-TX": ("テキサス州", "Texas"), "US-UT": ("ユタ州", "Utah"),
    "US-VT": ("バーモント州", "Vermont"), "US-VA": ("バージニア州", "Virginia"),
    "US-WA": ("ワシントン州", "Washington"),
    "US-WV": ("ウェストバージニア州", "West Virginia"),
    "US-WI": ("ウィスコンシン州", "Wisconsin"), "US-WY": ("ワイオミング州", "Wyoming"),
    "US-DC": ("ワシントンD.C.", "District of Columbia"),
}
CA_NAMES = {
    "CA-AB": ("アルバータ州", "Alberta"),
    "CA-BC": ("ブリティッシュコロンビア州", "British Columbia"),
    "CA-MB": ("マニトバ州", "Manitoba"),
    "CA-NB": ("ニューブランズウィック州", "New Brunswick"),
    "CA-NL": ("ニューファンドランド・ラブラドール州", "Newfoundland and Labrador"),
    "CA-NS": ("ノバスコシア州", "Nova Scotia"),
    "CA-NT": ("ノースウェスト準州", "Northwest Territories"),
    "CA-NU": ("ヌナブト準州", "Nunavut"),
    "CA-ON": ("オンタリオ州", "Ontario"),
    "CA-PE": ("プリンスエドワードアイランド州", "Prince Edward Island"),
    "CA-QC": ("ケベック州", "Quebec"),
    "CA-SK": ("サスカチュワン州", "Saskatchewan"),
    "CA-YT": ("ユーコン準州", "Yukon"),
}
AU_NAMES = {
    "AU-NSW": ("ニューサウスウェールズ州", "New South Wales"),
    "AU-VIC": ("ビクトリア州", "Victoria"),
    "AU-QLD": ("クイーンズランド州", "Queensland"),
    "AU-SA": ("南オーストラリア州", "South Australia"),
    "AU-WA": ("西オーストラリア州", "Western Australia"),
    "AU-TAS": ("タスマニア州", "Tasmania"),
    "AU-NT": ("北部準州", "Northern Territory"),
    "AU-ACT": ("オーストラリア首都特別地域", "Australian Capital Territory"),
}
# (日本語名, 英語名, Stats NZ 地方コード REGC2025)
NZ_NAMES = {
    "NZ-NTL": ("ノースランド地方", "Northland", "01"),
    "NZ-AUK": ("オークランド地方", "Auckland", "02"),
    "NZ-WKO": ("ワイカト地方", "Waikato", "03"),
    "NZ-BOP": ("ベイ・オブ・プレンティ地方", "Bay of Plenty", "04"),
    "NZ-GIS": ("ギズボーン地方", "Gisborne", "05"),
    "NZ-HKB": ("ホークスベイ地方", "Hawke's Bay", "06"),
    "NZ-TKI": ("タラナキ地方", "Taranaki", "07"),
    "NZ-MWT": ("マナワツ・ワンガヌイ地方", "Manawatū-Whanganui", "08"),
    "NZ-WGN": ("ウェリントン地方", "Wellington", "09"),
    "NZ-WTC": ("ウェストコースト地方", "West Coast", "12"),
    "NZ-CAN": ("カンタベリー地方", "Canterbury", "13"),
    "NZ-OTA": ("オタゴ地方", "Otago", "14"),
    "NZ-STL": ("サウスランド地方", "Southland", "15"),
    "NZ-TAS": ("タスマン地方", "Tasman", "16"),
    "NZ-NSN": ("ネルソン地方", "Nelson", "17"),
    "NZ-MBH": ("マールボロ地方", "Marlborough", "18"),
}
# (日本語名, 英語名, アイルランド語名, 地方)
IE_NAMES = {
    "IE-CW": ("カーロウ県", "Carlow", "Ceatharlach", "Leinster"),
    "IE-CN": ("キャバン県", "Cavan", "An Cabhán", "Ulster"),
    "IE-CE": ("クレア県", "Clare", "An Clár", "Munster"),
    "IE-CO": ("コーク県", "Cork", "Corcaigh", "Munster"),
    "IE-DL": ("ドニゴール県", "Donegal", "Dún na nGall", "Ulster"),
    "IE-D": ("ダブリン県", "Dublin", "Baile Átha Cliath", "Leinster"),
    "IE-G": ("ゴールウェイ県", "Galway", "Gaillimh", "Connacht"),
    "IE-KY": ("ケリー県", "Kerry", "Ciarraí", "Munster"),
    "IE-KE": ("キルデア県", "Kildare", "Cill Dara", "Leinster"),
    "IE-KK": ("キルケニー県", "Kilkenny", "Cill Chainnigh", "Leinster"),
    "IE-LS": ("リーシュ県", "Laois", "Laois", "Leinster"),
    "IE-LM": ("リートリム県", "Leitrim", "Liatroim", "Connacht"),
    "IE-LK": ("リムリック県", "Limerick", "Luimneach", "Munster"),
    "IE-LD": ("ロングフォード県", "Longford", "An Longfort", "Leinster"),
    "IE-LH": ("ラウス県", "Louth", "Lú", "Leinster"),
    "IE-MO": ("メイヨー県", "Mayo", "Maigh Eo", "Connacht"),
    "IE-MH": ("ミース県", "Meath", "An Mhí", "Leinster"),
    "IE-MN": ("モナハン県", "Monaghan", "Muineachán", "Ulster"),
    "IE-OY": ("オファリー県", "Offaly", "Uíbh Fhailí", "Leinster"),
    "IE-RN": ("ロスコモン県", "Roscommon", "Ros Comáin", "Connacht"),
    "IE-SO": ("スライゴ県", "Sligo", "Sligeach", "Connacht"),
    "IE-TA": ("ティペラリー県", "Tipperary", "Tiobraid Árann", "Munster"),
    "IE-WD": ("ウォーターフォード県", "Waterford", "Port Láirge", "Munster"),
    "IE-WH": ("ウェストミース県", "Westmeath", "An Iarmhí", "Leinster"),
    "IE-WX": ("ウェックスフォード県", "Wexford", "Loch Garman", "Leinster"),
    "IE-WW": ("ウィックロー県", "Wicklow", "Cill Mhantáin", "Leinster"),
}
# 英語名は ONS の ITL225NM と完全一致させる (ビルド時に照合)
GB_NAMES = {
    "TLC3": ("ティーズ・バレー", "Tees Valley"),
    "TLC4": ("ノーサンバーランド、ダラム、タイン・アンド・ウィア",
             "Northumberland, Durham and Tyne & Wear"),
    "TLD1": ("カンブリア", "Cumbria"),
    "TLD3": ("グレーター・マンチェスター", "Greater Manchester"),
    "TLD4": ("ランカシャー", "Lancashire"),
    "TLD6": ("チェシャー", "Cheshire"),
    "TLD7": ("マージーサイド", "Merseyside"),
    "TLE1": ("イースト・ヨークシャー、ノーザン・リンカンシャー",
             "East Yorkshire and Northern Lincolnshire"),
    "TLE2": ("ノース・ヨークシャー", "North Yorkshire"),
    "TLE3": ("サウス・ヨークシャー", "South Yorkshire"),
    "TLE4": ("ウェスト・ヨークシャー", "West Yorkshire"),
    "TLF1": ("ダービーシャー、ノッティンガムシャー", "Derbyshire and Nottinghamshire"),
    "TLF2": ("レスターシャー、ラトランド、ノーサンプトンシャー",
             "Leicestershire, Rutland and Northamptonshire"),
    "TLF3": ("リンカンシャー", "Lincolnshire"),
    "TLG1": ("ヘレフォードシャー、ウスターシャー、ウォリックシャー",
             "Herefordshire, Worcestershire and Warwickshire"),
    "TLG2": ("シュロップシャー、スタッフォードシャー", "Shropshire and Staffordshire"),
    "TLG3": ("ウェスト・ミッドランズ", "West Midlands"),
    "TLH2": ("ベッドフォードシャー、ハートフォードシャー", "Bedfordshire and Hertfordshire"),
    "TLH3": ("エセックス", "Essex"),
    "TLH4": ("ケンブリッジシャー、ピーターバラ", "Cambridgeshire and Peterborough"),
    "TLH5": ("ノーフォーク", "Norfolk"),
    "TLH6": ("サフォーク", "Suffolk"),
    "TLI3": ("インナー・ロンドン西部", "Inner London - West"),
    "TLI4": ("インナー・ロンドン東部", "Inner London - East"),
    "TLI5": ("アウター・ロンドン東部・北東部", "Outer London - East and North East"),
    "TLI6": ("アウター・ロンドン南部", "Outer London - South"),
    "TLI7": ("アウター・ロンドン西部・北西部", "Outer London - West and North West"),
    "TLJ1": ("バークシャー、バッキンガムシャー、オックスフォードシャー",
             "Berkshire, Buckinghamshire and Oxfordshire"),
    "TLJ2": ("サリー、イースト・サセックス、ウェスト・サセックス",
             "Surrey, East and West Sussex"),
    "TLJ3": ("ハンプシャー、ワイト島", "Hampshire and Isle of Wight"),
    "TLJ4": ("ケント", "Kent"),
    "TLK3": ("コーンウォール、シリー諸島", "Cornwall and Isles of Scilly"),
    "TLK4": ("デヴォン", "Devon"),
    "TLK5": ("ウェスト・オブ・イングランド", "West of England"),
    "TLK6": ("ノース・サマセット、サマセット、ドーセット",
             "North Somerset, Somerset and Dorset"),
    "TLK7": ("グロスターシャー、ウィルトシャー", "Gloucestershire and Wiltshire"),
    "TLL3": ("北ウェールズ", "North Wales"),
    "TLL4": ("中部・南西ウェールズ", "Mid and South West Wales"),
    "TLL5": ("南東ウェールズ", "South East Wales"),
    "TLM0": ("東部スコットランド", "Eastern Scotland"),
    "TLM1": ("中東部スコットランド", "East Central Scotland"),
    "TLM2": ("ハイランド・アンド・アイランズ", "Highlands and Islands"),
    "TLM3": ("中西部スコットランド", "West Central Scotland"),
    "TLM5": ("北東部スコットランド", "North Eastern Scotland"),
    "TLM9": ("南部スコットランド", "Southern Scotland"),
    "TLN0": ("北アイルランド", "Northern Ireland"),
}
# URA の REGION_C -> 安定 ID
SG_NAMES = {
    "SG-CR": ("中央地域", "Central Region", "CR"),
    "SG-ER": ("東部地域", "East Region", "ER"),
    "SG-NR": ("北部地域", "North Region", "NR"),
    "SG-NE": ("北東部地域", "North-East Region", "NER"),
    "SG-WR": ("西部地域", "West Region", "WR"),
}


def conic(parallels, rotate, center):
    return {"type": "conicEqualArea", "parallels": list(parallels), "rotate": rotate,
            "center": list(center)}


COUNTRIES = {
    "us": {
        "country": "US", "name_ja": "アメリカ合衆国", "name_en": "United States",
        "division_ja": "50 州とコロンビア特別区", "division_en": "50 states and the District of Columbia",
        "id_scheme": "ISO 3166-2:US", "source": "ne", "ne_adm0": "USA",
        "names": {k: v for k, v in US_NAMES.items()},
        # d3-geo の geoAlbersUsa と同じ配置 (本土 Albers + アラスカ 0.35 倍 + ハワイ等倍)
        "projection": dict(conic((29.5, 45.5), 96, (-0.6, 38.7)), k=1070, t=(480, 250)),
        "insets": {
            "US-AK": dict(conic((55, 65), 154, (-2, 58.5)), k=1070 * 0.35,
                          t=(480 - 0.307 * 1070, 250 + 0.201 * 1070)),
            "US-HI": dict(conic((8, 18), 157, (-3, 19.9)), k=1070,
                          t=(480 - 0.205 * 1070, 250 + 0.212 * 1070)),
        },
        # 北西ハワイ諸島 (西経 161 度以西) は本島から 2,000 km 以上離れた小島のため描画しない
        "polygon_filter": {"US-HI": lambda poly: centroid_lon(poly) > -161.0},
        "region_notes": {
            "US-AK": "本土の左下にはめ込み（面積 0.35 倍）",
            "US-HI": "本土の左下にはめ込み。北西ハワイ諸島は描画を省略",
        },
        "excluded": [
            ("プエルトリコ", "Puerto Rico", "US-PR", "海外領域（州・DC ではない）"),
            ("グアム", "Guam", "US-GU", "海外領域"),
            ("米領ヴァージン諸島", "United States Virgin Islands", "US-VI", "海外領域"),
            ("米領サモア", "American Samoa", "US-AS", "海外領域"),
            ("北マリアナ諸島", "Northern Mariana Islands", "US-MP", "海外領域"),
            ("合衆国領有小離島", "United States Minor Outlying Islands", "US-UM", "海外領域"),
        ],
        "notes": [
            "アラスカ州とハワイ州は本土の左下にはめ込みで配置（d3-geo の geoAlbersUsa と同じ配置。"
            "アラスカは面積 0.35 倍）。はめ込みの区切り線は `<g class=\"boundary-line\">` に入っており、"
            "data-code を持たない。",
            "ハワイ州の北西ハワイ諸島（西経 161 度以西）は小島のため描画を省略（区分としてはハワイ州）。",
        ],
    },
    "gb": {
        "country": "GB", "name_ja": "イギリス", "name_en": "United Kingdom",
        "division_ja": "ITL2 (2025) の 46 地域", "division_en": "46 ITL2 regions (ITL 2025)",
        "id_scheme": "ONS ITL 2025 code (ITL225CD)", "source": "ons",
        "names": GB_NAMES,
        "projection": dict(conic((51, 58), 3, (0, 54.5))),
        "excluded": [
            ("マン島", "Isle of Man", "IM", "王室属領（英国の ITL 外）"),
            ("ジャージー", "Jersey", "JE", "王室属領（英国の ITL 外）"),
            ("ガーンジー", "Guernsey", "GG", "王室属領（英国の ITL 外）"),
            ("英国の海外領土", "British Overseas Territories", "", "ITL 外"),
        ],
        "notes": [
            "ONS の ITL 2025 年分類（2025 年 1 月）の ITL2。England の細分を含む 46 地域。"
            "4 構成国、ITL1 の 12 地域、ITL 2021 / NUTS の 41 地域のいずれでもない。",
            "北アイルランドは TLN0 として gb に含む（ie には含めない）。",
        ],
    },
    "ca": {
        "country": "CA", "name_ja": "カナダ", "name_en": "Canada",
        "division_ja": "10 州と 3 準州", "division_en": "10 provinces and 3 territories",
        "id_scheme": "ISO 3166-2:CA", "source": "ne", "ne_adm0": "CAN",
        "names": CA_NAMES,
        "projection": dict(conic((50, 70), 96, (0, 62))),
        "excluded": [],
        "notes": [],
    },
    "au": {
        "country": "AU", "name_ja": "オーストラリア", "name_en": "Australia",
        "division_ja": "6 州と 2 準州（ACT・NT）", "division_en": "6 states, ACT and NT",
        "id_scheme": "ISO 3166-2:AU", "source": "ne", "ne_adm0": "AUS",
        "names": AU_NAMES,
        "projection": dict(conic((-18, -36), -134, (0, -27))),
        # NE ではロードハウ島 (NSW) が別フィーチャになっている。本土から約 600 km 離れた小島のため描画しない
        "ne_drop": {"AUS-2659": "Lord Howe Island"},
        "region_notes": {
            "AU-NSW": "ロードハウ島は描画を省略",
            "AU-TAS": "マッコーリー島は描画を省略",
        },
        "excluded": [
            ("ジャービス湾特別地域", "Jervis Bay Territory", "",
             "連邦直轄の特別地域。6 州・ACT・NT のいずれでもない（ABS では Other Territories）"),
            ("クリスマス島", "Christmas Island", "CX", "海外領域"),
            ("ココス（キーリング）諸島", "Cocos (Keeling) Islands", "CC", "海外領域"),
            ("ノーフォーク島", "Norfolk Island", "NF", "海外領域"),
            ("ハード島とマクドナルド諸島", "Heard Island and McDonald Islands", "HM", "海外領域"),
            ("アシュモア・カルティエ諸島", "Ashmore and Cartier Islands", "", "海外領域"),
            ("コーラル・シー諸島", "Coral Sea Islands", "", "海外領域"),
            ("オーストラリア南極領土", "Australian Antarctic Territory", "", "海外領域"),
        ],
        "notes": [
            "ロードハウ島（ニューサウスウェールズ州）とマッコーリー島（タスマニア州）は本土から"
            "遠い小島のため描画を省略（区分としてはそれぞれの州）。",
        ],
    },
    "nz": {
        "country": "NZ", "name_ja": "ニュージーランド", "name_en": "New Zealand",
        "division_ja": "16 の地方（regional council の区域）", "division_en": "16 regions",
        "id_scheme": "ISO 3166-2:NZ（Stats NZ の地方コード REGC2025 を stats_nz_code に併記）",
        "source": "ne", "ne_adm0": "NZL",
        "names": {k: v[:2] for k, v in NZ_NAMES.items()},
        "projection": dict(conic((-37, -45), -173, (0, -41))),
        "excluded": [
            ("チャタム諸島", "Chatham Islands Territory", "NZ-CIT",
             "地方（regional council）に属さない特別区域（Stats NZ の 99 Area Outside Region）"),
            ("ケルマデック諸島・亜南極諸島など", "Kermadec, Three Kings and sub-Antarctic islands",
             "", "地方に属さない区域（Area Outside Region）"),
            ("トケラウ", "Tokelau", "TK", "海外領域"),
        ],
        "notes": [],
    },
    "ie": {
        "country": "IE", "name_ja": "アイルランド", "name_en": "Ireland",
        "division_ja": "伝統的な 26 県", "division_en": "26 traditional counties",
        "id_scheme": "ISO 3166-2:IE（県）", "source": "ne", "ne_adm0": "IRL",
        "names": {k: v[:2] for k, v in IE_NAMES.items()},
        "projection": dict(conic((52, 55), 8, (0, 53.4))),
        "dissolve": True,
        "excluded": [
            ("北アイルランド（アントリム、アーマー、ダウン、ファーマナ、ロンドンデリー、ティロン）",
             "Northern Ireland (Antrim, Armagh, Down, Fermanagh, Londonderry, Tyrone)", "",
             "英国。gb の TLN0 に含む"),
        ],
        "notes": [
            "Natural Earth の地方自治体単位（34）を ISO 3166-2:IE の県へ統合して 26 県にした。"
            "ダブリン（Dublin City・Dún Laoghaire–Rathdown・Fingal・South Dublin）は 1 県、"
            "ティペラリー（North / South Tipperary）は 1 県、コーク・ゴールウェイ・リムリック・"
            "ウォーターフォードは市と県を 1 県にまとめている。",
        ],
    },
    "sg": {
        "country": "SG", "name_ja": "シンガポール", "name_en": "Singapore",
        "division_ja": "URA の 5 地域", "division_en": "5 URA planning regions",
        "id_scheme": "SG-{URA の地域コード}（NER は SG-NE）。ISO 3166-2:SG（CDC の 01〜05）とは別",
        "source": "ura",
        "names": {k: v[:2] for k, v in SG_NAMES.items()},
        "projection": dict(conic((1.2, 1.5), -103.82, (0, 1.35))),
        "excluded": [
            ("計画区域（55）", "Planning areas (55)", "", "地域の下位区分。分母に使わない"),
        ],
        "notes": [
            "URA Master Plan 2025 の地域境界（海域を除く）。離島（セントーサ、ジュロン島、"
            "ウビン島、テコン島など）は所属する地域に含む。",
        ],
    },
}


# ------------------------------------------------------------------ データ取得

def http_get(url, timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def ensure_source(key):
    src = SOURCES[key]
    path = os.path.join(DATA, src["file"])
    if os.path.exists(path):
        return path
    os.makedirs(DATA, exist_ok=True)
    print(f"downloading {src['name']} ...", file=sys.stderr)
    url = src["download_url"]
    if key == "ura":
        for _ in range(8):
            meta = json.load(http_get(url))
            if meta.get("data") and meta["data"].get("url"):
                url = meta["data"]["url"]
                break
            time.sleep(12)  # data.gov.sg のレート制限
        else:
            raise SystemExit("data.gov.sg からダウンロード URL を取得できない")
    with http_get(url) as r, open(path + ".part", "wb") as f:
        f.write(r.read())
    os.replace(path + ".part", path)
    return path


def source_meta(key):
    src = dict(SOURCES[key])
    path = os.path.join(DATA, src.pop("file"))
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    retrieved = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    src["retrieved"] = retrieved
    src["sha256"] = digest
    src["attribution"] = src["attribution"].replace("{retrieved}", retrieved)
    return src


# ------------------------------------------------------------------ ジオメトリ読み込み

def geom_polygons(geom):
    """GeoJSON geometry -> [polygon], polygon = [ring], ring = [(lon, lat), ...] (閉じない)"""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for poly in polys:
        rings = []
        for ring in poly:
            pts = [(float(c[0]), float(c[1])) for c in ring]
            if len(pts) > 1 and pts[0] == pts[-1]:
                pts = pts[:-1]
            if len(pts) >= 3:
                rings.append(pts)
        if rings:
            out.append(rings)
    return out


def signed_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2


def centroid_lon(poly):
    pts = poly[0]
    return sum(p[0] for p in pts) / len(pts)


def point_in_ring(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
                inside = not inside
    return inside


def dissolve(polys):
    """辺を共有するポリゴン群を 1 つにまとめる (共有辺の打ち消し)。

    元データの位相が整合している (共有境界の頂点が一致する) ことが前提。
    外周を反時計回り・穴を時計回りにそろえ、逆向きの同じ辺を打ち消してから辺をつなぎ直す。
    """
    edges = defaultdict(int)
    for poly in polys:
        for ri, ring in enumerate(poly):
            ccw = signed_area(ring) > 0
            r = ring if ccw == (ri == 0) else ring[::-1]
            for a, b in zip(r, r[1:] + r[:1]):
                if edges.get((b, a), 0) > 0:
                    edges[(b, a)] -= 1
                else:
                    edges[(a, b)] += 1
    out_edges = defaultdict(list)
    for (a, b), n in edges.items():
        for _ in range(n):
            out_edges[a].append(b)
    rings = []
    while out_edges:
        start = next(iter(out_edges))
        ring = [start]
        cur = start
        while True:
            nxt = out_edges[cur].pop()
            if not out_edges[cur]:
                del out_edges[cur]
            if nxt == start:
                break
            ring.append(nxt)
            cur = nxt
            if cur not in out_edges:
                raise ValueError("dissolve: 辺がつながらない (位相が不整合)")
        if len(ring) >= 3:
            rings.append(ring)
    outers = [r for r in rings if signed_area(r) > 0]
    holes = [r for r in rings if signed_area(r) <= 0]
    result = [[o] for o in outers]
    for h in holes:
        x, y = h[0]
        cands = [i for i, o in enumerate(outers) if point_in_ring(x, y, o)]
        if not cands:
            raise ValueError("dissolve: 穴の外周が見つからない")
        best = min(cands, key=lambda i: abs(signed_area(outers[i])))
        result[best].append(h)
    return result


def load_regions(key, cfg):
    """区分コード -> {"polys": [...], "source_ids": [...]} (経緯度)"""
    regions = {code: {"polys": [], "source_ids": []} for code in cfg["names"]}
    src = cfg["source"]
    with open(ensure_source(src)) as f:
        features = json.load(f)["features"]
    if src == "ne":
        drop = cfg.get("ne_drop", {})
        for feat in features:
            p = feat["properties"]
            if p["adm0_a3"] != cfg["ne_adm0"] or p["adm1_code"] in drop:
                continue
            code = p["iso_3166_2"]
            if code not in regions:
                continue
            regions[code]["polys"].append(geom_polygons(feat["geometry"]))
            regions[code]["source_ids"].append(p["adm1_code"])
            regions[code].setdefault("source_names", []).append(f"{p['name']} ({p['type_en']})")
    elif src == "ons":
        for feat in features:
            p = feat["properties"]
            code = p["ITL225CD"]
            if code not in regions:
                raise SystemExit(f"gb: 名前表に無い ONS コード {code}")
            if p["ITL225NM"] != cfg["names"][code][1]:
                raise SystemExit(f"gb: {code} の英語名が ONS と違う: {p['ITL225NM']!r}")
            regions[code]["polys"].append(geom_polygons(feat["geometry"]))
            regions[code]["source_ids"].append(code)
    elif src == "ura":
        by_ura = {v[2]: k for k, v in SG_NAMES.items()}
        for feat in features:
            p = feat["properties"]
            code = by_ura[p["REGION_C"]]
            regions[code]["polys"].append(geom_polygons(feat["geometry"]))
            regions[code]["source_ids"].append(f"{p['REGION_C']} ({p['REGION_N']})")

    out = {}
    for code, r in regions.items():
        if not r["polys"]:
            raise SystemExit(f"{key}: {code} のジオメトリが無い")
        if cfg.get("dissolve") and len(r["polys"]) > 1:
            polys = dissolve([poly for member in r["polys"] for poly in member])
        else:
            polys = [poly for member in r["polys"] for poly in member]
        keep = cfg.get("polygon_filter", {}).get(code)
        if keep:
            polys = [poly for poly in polys if keep(poly)]
        out[code] = {"polys": polys, "source_ids": r["source_ids"],
                     "source_names": r.get("source_names", [])}
    return out


# ------------------------------------------------------------------ 投影

def conic_equal_area_raw(parallels):
    """d3-geo の conicEqualArea と同じ式。"""
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


class Projection:
    def __init__(self, spec, k=1.0, t=(0.0, 0.0)):
        self.spec = spec
        self.raw = conic_equal_area_raw(spec["parallels"])
        self.rot = spec["rotate"]
        self.cx, self.cy = self.raw(math.radians(spec["center"][0]),
                                    math.radians(spec["center"][1]))
        self.k, self.tx, self.ty = k, t[0], t[1]

    def __call__(self, lon, lat):
        lam = ((lon + self.rot + 540.0) % 360.0) - 180.0
        x, y = self.raw(math.radians(lam), math.radians(lat))
        return self.tx + self.k * (x - self.cx), self.ty - self.k * (y - self.cy)

    def refit(self, s, ox, oy):
        """出力座標に一様拡大 s と平行移動 (ox, oy) をかけた投影を返す。"""
        return Projection(self.spec, self.k * s, (ox + s * self.tx, oy + s * self.ty))

    def as_json(self):
        return {"type": self.spec["type"], "parallels": self.spec["parallels"],
                "rotate": self.spec["rotate"], "center": self.spec["center"],
                "scale": round(self.k, 6), "translate": [round(self.tx, 6), round(self.ty, 6)]}


def project_country(cfg, regions):
    """区分ごとに投影し、長辺 LONG_SIDE の viewBox に収める。"""
    p = cfg["projection"]
    main = Projection(p, p.get("k", 1.0), p.get("t", (0.0, 0.0)))
    insets = {c: Projection(s, s["k"], s["t"]) for c, s in cfg.get("insets", {}).items()}
    raw = {}
    for code, r in regions.items():
        proj = insets.get(code, main)
        raw[code] = [[[proj(lon, lat) for lon, lat in ring] for ring in poly]
                     for poly in r["polys"]]
    xs = [x for polys in raw.values() for poly in polys for x, _ in poly[0]]
    ys = [y for polys in raw.values() for poly in polys for _, y in poly[0]]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    s = (LONG_SIDE - 2 * PAD) / max(maxx - minx, maxy - miny)
    ox, oy = PAD - minx * s, PAD - miny * s
    width = round((maxx - minx) * s + 2 * PAD)
    height = round((maxy - miny) * s + 2 * PAD)
    out = {code: [[[(ox + s * x, oy + s * y) for x, y in ring] for ring in poly]
                  for poly in polys] for code, polys in raw.items()}
    projections = {"main": main.refit(s, ox, oy).as_json()}
    if insets:
        projections["insets"] = {c: pr.refit(s, ox, oy).as_json() for c, pr in insets.items()}
    return out, width, height, projections


# ------------------------------------------------------------------ 位相を保った簡略化

class Topology:
    """共有境界を 1 本の弧として持ち、隣り合う区分で同じ簡略化結果を使う (隙間・重なり防止)。"""

    def __init__(self, regions):
        self.rings = []  # (code, pi, ri, [(arc_id, forward)])
        self.arcs = []  # 点列
        self.closed = []  # 弧が閉路か
        index = {}
        ring_pts = []
        for code, polys in regions.items():
            for pi, poly in enumerate(polys):
                for ri, ring in enumerate(poly):
                    pts = [ring[0]]
                    for q in ring[1:]:
                        if q != pts[-1]:
                            pts.append(q)
                    while len(pts) > 1 and pts[-1] == pts[0]:
                        pts.pop()
                    if len(pts) >= 3:
                        ring_pts.append((code, pi, ri, pts))
        # TopoJSON と同じ考え方: 前後の点が一致しない点を接合点とする
        seen = {}
        junctions = set()
        for _, _, _, pts in ring_pts:
            n = len(pts)
            for i in range(n):
                p = pts[i]
                if p in junctions:
                    continue
                a, b = pts[i - 1], pts[(i + 1) % n]
                if p not in seen:
                    seen[p] = (a, b)
                elif seen[p] != (a, b) and seen[p] != (b, a):
                    junctions.add(p)
            # 同じリングが同じ点を 2 回通る (くびれ) 場合も接合点
            counts = defaultdict(int)
            for p in pts:
                counts[p] += 1
            junctions.update(p for p, c in counts.items() if c > 1)

        for code, pi, ri, pts in ring_pts:
            n = len(pts)
            js = [i for i in range(n) if pts[i] in junctions]
            refs = []
            if not js:
                i0 = min(range(n), key=lambda i: pts[i])
                fwd = pts[i0:] + pts[:i0]
                rev = pts[::-1]
                j0 = min(range(n), key=lambda i: rev[i])
                rev = rev[j0:] + rev[:j0]
                canon = min(fwd, rev)
                key = ("c", tuple(canon))
                if key not in index:
                    index[key] = len(self.arcs)
                    self.arcs.append(list(canon))
                    self.closed.append(True)
                refs.append((index[key], canon == fwd))
            else:
                for k in range(len(js)):
                    s, e = js[k], js[(k + 1) % len(js)]
                    seg = pts[s:e + 1] if e > s else pts[s:] + pts[:e + 1]
                    t = tuple(seg)
                    if ("o", t) in index:
                        refs.append((index[("o", t)], True))
                    elif ("o", t[::-1]) in index:
                        refs.append((index[("o", t[::-1])], False))
                    else:
                        index[("o", t)] = len(self.arcs)
                        self.arcs.append(seg)
                        self.closed.append(False)
                        refs.append((index[("o", t)], True))
            self.rings.append((code, pi, ri, refs))
        self.arc_users = defaultdict(set)
        for code, pi, ri, refs in self.rings:
            for a, _ in refs:
                self.arc_users[a].add((code, pi, ri))

    @staticmethod
    def simplify_loop(pts, tol):
        """閉路の簡略化。始点と、始点から最も遠い点は必ず残す。"""
        n = len(pts)
        if n <= 3:
            return list(pts)
        x0, y0 = pts[0]
        k = max(range(n), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        a = dp_simplify(pts[:k + 1], tol)
        b = dp_simplify(pts[k:] + [pts[0]], tol)
        out = a[:-1] + b[:-1]
        if len(out) < 3:
            (ax, ay), (bx, by) = pts[0], pts[k]
            j = max((i for i in range(n) if i not in (0, k)),
                    key=lambda i: abs((bx - ax) * (pts[i][1] - ay) - (by - ay) * (pts[i][0] - ax)))
            out = [pts[0], pts[j], pts[k]] if j < k else [pts[0], pts[k], pts[j]]
        return out

    def simplify_arc(self, i, tol):
        pts = self.arcs[i]
        if self.closed[i]:
            return self.simplify_loop(pts, tol)
        if pts[0] == pts[-1]:
            return self.simplify_loop(pts[:-1], tol) + [pts[0]]
        return dp_simplify(pts, tol)

    def ring_points(self, refs, simplified):
        out = []
        for a, fwd in refs:
            s = simplified[a] if fwd else simplified[a][::-1]
            if self.closed[a]:
                out.extend(s)
            else:
                out.extend(s[:-1])
        return out

    def original_ring(self, refs):
        return self.ring_points(refs, self.arcs)


def simplify_country(regions, tol, min_area):
    """簡略化したポリゴン (区分 -> [ [ring, ...] ]) を返す。各区分の最大ポリゴンは必ず残す。"""
    topo = Topology(regions)
    rings = defaultdict(dict)  # code -> pi -> {ri: refs}
    for code, pi, ri, refs in topo.rings:
        rings[code].setdefault(pi, {})[ri] = refs
    largest = {}
    orig_area = {}
    for code, polys in rings.items():
        areas = {pi: ring_area(topo.original_ring(rs[0])) for pi, rs in polys.items() if 0 in rs}
        largest[code] = max(areas, key=areas.get)
        orig_area[code] = areas[largest[code]]

    arc_tol = [tol] * len(topo.arcs)
    simplified = [topo.simplify_arc(i, tol) for i in range(len(topo.arcs))]
    # 小さな区分の最大ポリゴンが潰れたり大きく歪んだりしたら、その弧だけ許容誤差を下げる
    for _ in range(10):
        changed = False
        for code, pi in largest.items():
            refs = rings[code][pi][0]
            pts = topo.ring_points(refs, simplified)
            area = ring_area(pts) if len(set(pts)) >= 3 else 0.0
            oa = orig_area[code]
            if len(set(pts)) >= 3 and abs(area - oa) <= 0.15 * oa:
                continue
            for a, _ in refs:
                if arc_tol[a] > 1e-3:
                    arc_tol[a] /= 2
                    simplified[a] = topo.simplify_arc(a, arc_tol[a])
                    changed = True
        if not changed:
            break

    def ring_of(code, pi, ri):
        pts = topo.ring_points(rings[code][pi][ri], simplified)
        return pts if len(set(pts)) >= 3 else None

    kept_outer = set()
    result = {}
    for code, polys in rings.items():
        for pi, rs in polys.items():
            if 0 not in rs:
                continue
            outer = ring_of(code, pi, 0)
            if outer is None:
                continue
            if pi == largest[code] or ring_area(outer) >= min_area:
                kept_outer.add((code, pi))
    for code, polys in rings.items():
        out = []
        for pi in sorted(polys):
            if (code, pi) not in kept_outer:
                continue
            poly = [ring_of(code, pi, 0)]
            for ri in sorted(polys[pi]):
                if ri == 0:
                    continue
                hole = ring_of(code, pi, ri)
                if hole is None:
                    continue
                # 他の区分が埋めている穴 (飛び地を囲む穴) は面積によらず残す
                filled = any((u[0], u[1]) in kept_outer and u[2] == 0 and u[0] != code
                             for a, _ in polys[pi][ri] for u in topo.arc_users[a])
                if filled or ring_area(hole) >= min_area:
                    poly.append(hole)
            out.append(poly)
        result[code] = out
    return result


# ------------------------------------------------------------------ 出力

def fmt_ring(pts):
    coords = []
    for x, y in pts:
        c = f"{x:.1f} {y:.1f}"
        if not coords or coords[-1] != c:
            coords.append(c)
    while len(coords) > 1 and coords[-1] == coords[0]:
        coords.pop()
    if len(set(coords)) < 3:
        return None
    return "M" + "L".join(coords) + "Z"


def marker_point(poly):
    """ポリゴン (外周 + 穴) の内側で、境界から最も遠い点 (到達不能極の近似)。

    重心は三日月形の区分で外に出たり隣の区分の近くに寄ったりするため使わない。
    """
    edges = [(r[i], r[(i + 1) % len(r)]) for r in poly for i in range(len(r))]

    def inside(x, y):
        return sum(point_in_ring(x, y, r) for r in poly) % 2 == 1

    def clearance(x, y):
        best = math.inf
        for (ax, ay), (bx, by) in edges:
            dx, dy = bx - ax, by - ay
            seg2 = dx * dx + dy * dy
            t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / seg2))
            best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
        return best

    xs = [p[0] for p in poly[0]]
    ys = [p[1] for p in poly[0]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    step = max(x1 - x0, y1 - y0) / 32
    best, best_d = None, -1.0
    for _ in range(3):
        nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
        for i in range(nx + 1):
            for j in range(ny + 1):
                x, y = x0 + i * step, y0 + j * step
                if inside(x, y):
                    d = clearance(x, y)
                    if d > best_d:
                        best, best_d = (x, y), d
        if best is None:
            break
        x0, y0, x1, y1 = best[0] - step, best[1] - step, best[0] + step, best[1] + step
        step /= 8
    if best is None:  # 格子に掛からないほど細い場合は外周の頂点平均
        best = (sum(xs) / len(xs), sum(ys) / len(ys))
    return best


def region_slug(name_en):
    return slugify(unicodedata.normalize("NFKD", name_en).encode("ascii", "ignore").decode())


def inset_frame(geoms, inset_codes, height):
    """はめ込みの区切り線。左から順に各はめ込みの上を通り、最後のはめ込みの右で下へ降りる階段状の線。

    d3-geo の geoAlbersUsa の区切り (アラスカ枠とハワイ枠) と同じ形。
    """
    m = 6.0
    boxes = []
    for c in inset_codes:
        pts = [p for poly in geoms[c] for p in poly[0]]
        boxes.append((min(p[0] for p in pts), min(p[1] for p in pts),
                      max(p[0] for p in pts), max(p[1] for p in pts)))
    boxes.sort()
    pts = [(PAD / 2, boxes[0][1] - m)]
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        top = y0 - m
        if i:
            step = (boxes[i - 1][2] + x0) / 2
            pts += [(step, pts[-1][1]), (step, top)]
        else:
            pts[-1] = (pts[-1][0], top)
    pts += [(boxes[-1][2] + m, pts[-1][1]), (boxes[-1][2] + m, height - PAD / 2)]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def render(key, cfg, projected, width, height, variant, meta):
    fname, tol, min_area, mth, mr, sw = variant
    geoms = simplify_country(projected, tol, min_area)
    a2 = cfg["country"]
    items = []
    for code in sorted(geoms):
        d_parts = []
        for poly in geoms[code]:
            sub = [fmt_ring(r) for r in poly]
            if sub[0] is None:
                continue
            d_parts.append("".join(s for s in sub if s))
        if not d_parts:
            raise SystemExit(f"{key}: {code} のパスが空になった")
        big = max(geoms[code], key=lambda poly: ring_area(poly[0]))
        size = math.sqrt(ring_area(big[0]))
        marker = marker_point(big) if size < mth else None
        items.append({"code": code, "d": "".join(d_parts), "marker": marker, "size": size})
    # マーカー同士が重ならないよう半径を詰める (下限は既定の 6 割。full より小さくしない)
    radii = {}
    mk = [it for it in items if it["marker"]]
    for it in mk:
        r = mr
        for other in mk:
            if other is it:
                continue
            dist = math.dist(it["marker"], other["marker"])
            r = min(r, max(mr * 0.6, dist / 2))
        radii[it["code"]] = r
    # マーカー付きの区分を後に描き、隣の区分に隠れないようにする
    items.sort(key=lambda it: (it["marker"] is not None, it["code"]))

    names = cfg["names"]
    lines = ['<?xml version="1.0" encoding="utf-8"?>']
    lines.append(f'<svg class="subdivision-svg-map" data-country="{a2}" '
                 f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f"  <title>{escape(cfg['name_ja'])}：{escape(cfg['division_ja'])} / "
                 f"{escape(cfg['name_en'])}: {escape(cfg['division_en'])}</title>")
    lines.append(f"  <desc>{escape(meta['attribution'])} Simplified map for coloring; "
                 "no political position is implied. Generated for "
                 "https://github.com/kazutax/world-map-svg</desc>")
    lines.append('  <g class="svg-map">')
    lines.append('    <g class="regions">')
    for it in items:
        code = it["code"]
        name_ja, name_en = names[code]
        lines.append(
            f'      <g class="{region_slug(name_en)} region" data-code="{code}" '
            f'data-country="{a2}" fill="{DEFAULT_FILL}" fill-rule="evenodd" '
            f'stroke="{STROKE}" stroke-width="{sw}" stroke-linejoin="round">')
        lines.append(f"        <title>{escape(name_ja)} / {escape(name_en)}</title>")
        lines.append(f'        <path d="{it["d"]}"/>')
        if it["marker"]:
            cx, cy = it["marker"]
            lines.append(f'        <circle class="region-marker" cx="{cx:.1f}" cy="{cy:.1f}" '
                         f'r="{radii[code]:.1f}" stroke-width="{sw}"/>')
        lines.append("      </g>")
    lines.append("    </g>")
    if cfg.get("insets"):
        frame = inset_frame(geoms, list(cfg["insets"]), height)
        lines.append(f'    <g class="boundary-line" fill="none" stroke="#999999" '
                     f'stroke-width="{sw}" stroke-linejoin="round">')
        lines.append(f'      <path d="{frame}"/>')
        lines.append("    </g>")
    lines.append("  </g>")
    lines.append("</svg>")
    with open(os.path.join(OUT, key, fname), "w") as f:
        f.write("\n".join(lines) + "\n")
    return {it["code"]: it for it in items}


def build_country(key):
    cfg = COUNTRIES[key]
    regions = load_regions(key, cfg)
    meta = source_meta(cfg["source"])
    projected, width, height, projections = project_country(cfg, regions)
    os.makedirs(os.path.join(OUT, key), exist_ok=True)
    results = {}
    for variant in VARIANTS:
        results[variant[0]] = render(key, cfg, projected, width, height, variant, meta)

    rows = []
    for code in sorted(cfg["names"]):
        name_ja, name_en = cfg["names"][code]
        row = {"code": code, "country": cfg["country"], "name_ja": name_ja, "name_en": name_en,
               "included_in_svg": all(code in results[v[0]] for v in VARIANTS)}
        if key == "nz":
            row["stats_nz_code"] = NZ_NAMES[code][2]
        if key == "ie":
            row["name_ga"], row["province"] = IE_NAMES[code][2], IE_NAMES[code][3]
        row["source_ids"] = regions[code]["source_ids"]
        row["marker"] = {v[0].replace("map-", "").replace(".svg", ""):
                         results[v[0]][code]["marker"] is not None for v in VARIANTS}
        notes = []
        if cfg.get("dissolve") and len(regions[code]["source_ids"]) > 1:
            notes.append("Natural Earth の " + "・".join(regions[code]["source_names"])
                         + " を 1 県に統合")
        if code in cfg.get("region_notes", {}):
            notes.append(cfg["region_notes"][code])
        row["notes"] = "。".join(notes)
        rows.append(row)
    doc = {
        "country": cfg["country"],
        "country_name_ja": cfg["name_ja"],
        "country_name_en": cfg["name_en"],
        "division_ja": cfg["division_ja"],
        "division_en": cfg["division_en"],
        "denominator": len(cfg["names"]),
        "id_scheme": cfg["id_scheme"],
        "source": meta,
        "projection": dict(projections, viewBox=[0, 0, width, height]),
        "excluded": [{"name_ja": e[0], "name_en": e[1], "code": e[2], "reason": e[3]}
                     for e in cfg["excluded"]],
        "notes": cfg["notes"],
        "regions": rows,
    }
    with open(os.path.join(OUT, key, "regions.json"), "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    markers = {v[0]: sorted(c for c, it in results[v[0]].items() if it["marker"])
               for v in VARIANTS}
    print(f"{key}: {len(rows)} regions, viewBox 0 0 {width} {height}, "
          f"markers full={markers['map-full.svg']} mobile={markers['map-mobile.svg']}")
    return doc


def write_code_tables(docs):
    """subdivisions/README.md (国ごとのコード表) を書く。"""
    lines = ["# 国の中の区画 コード表", "",
             "`scripts/build_subdivisions.py` が生成します。手で編集しないでください。", ""]
    for key in COUNTRIES:
        doc = docs.get(key)
        if doc is None:
            path = os.path.join(OUT, key, "regions.json")
            if not os.path.exists(path):
                continue
            with open(path) as f:
                doc = json.load(f)
        src = doc["source"]
        lines.append(f"## {doc['country_name_ja']}（`{key}`）: {doc['division_ja']}、"
                     f"分母 {doc['denominator']}")
        lines.append("")
        lines.append(f"- ID: {doc['id_scheme']}")
        lines.append(f"- 出典: [{src['name']}]({src['url']})（{src['version']}、"
                     f"{src['license']}）")
        for n in doc["notes"]:
            lines.append(f"- {n}")
        if doc["excluded"]:
            ex = "、".join(e["name_ja"] + (f"（{e['code']}）" if e["code"] else "")
                          for e in doc["excluded"])
            lines.append(f"- 分母に含めない: {ex}")
        lines.append("")
        extra = {"nz": "Stats NZ コード", "ie": "アイルランド語名 / 地方"}.get(key, "元データの ID")
        lines.append(f"| data-code | 日本語名 | English name | {extra} |")
        lines.append("|---|---|---|---|")
        for r in doc["regions"]:
            if key == "nz":
                ex = r["stats_nz_code"]
            elif key == "ie":
                ex = f"{r['name_ga']} / {r['province']}"
            else:
                ex = ", ".join(r["source_ids"])
            lines.append(f"| `{r['code']}` | {r['name_ja']} | {r['name_en']} | {ex} |")
        lines.append("")
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    keys = sys.argv[1:] or list(COUNTRIES)
    unknown = [k for k in keys if k not in COUNTRIES]
    if unknown:
        raise SystemExit(f"unknown country: {unknown} (choose from {list(COUNTRIES)})")
    docs = {k: build_country(k) for k in keys}
    write_code_tables(docs)


if __name__ == "__main__":
    main()
