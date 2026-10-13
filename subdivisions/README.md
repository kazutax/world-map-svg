# 国の中の区画 コード表

`scripts/build_subdivisions.py` が生成します。手で編集しないでください。

## アメリカ合衆国（`us`）: 50 州とコロンビア特別区、分母 51

- ID: ISO 3166-2:US
- 出典: [Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces (large lakes removed)](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)（v5.1.2 (ne_10m_admin_1_states_provinces_lakes)、Public Domain）
- アラスカ州とハワイ州は本土の左下にはめ込みで配置（d3-geo の geoAlbersUsa と同じ配置。アラスカは面積 0.35 倍）。はめ込みの区切り線は `<g class="boundary-line">` に入っており、data-code を持たない。
- ハワイ州の北西ハワイ諸島（西経 161 度以西）は小島のため描画を省略（区分としてはハワイ州）。
- 分母に含めない: プエルトリコ（US-PR）、グアム（US-GU）、米領ヴァージン諸島（US-VI）、米領サモア（US-AS）、北マリアナ諸島（US-MP）、合衆国領有小離島（US-UM）

| data-code | 日本語名 | English name | 元データの ID |
|---|---|---|---|
| `US-AK` | アラスカ州 | Alaska | USA-3563 |
| `US-AL` | アラバマ州 | Alabama | USA-3541 |
| `US-AR` | アーカンソー州 | Arkansas | USA-3528 |
| `US-AZ` | アリゾナ州 | Arizona | USA-3520 |
| `US-CA` | カリフォルニア州 | California | USA-3521 |
| `US-CO` | コロラド州 | Colorado | USA-3522 |
| `US-CT` | コネチカット州 | Connecticut | USA-3537 |
| `US-DC` | ワシントンD.C. | District of Columbia | USA-3556 |
| `US-DE` | デラウェア州 | Delaware | USA-3555 |
| `US-FL` | フロリダ州 | Florida | USA-3542 |
| `US-GA` | ジョージア州 | Georgia | USA-3543 |
| `US-HI` | ハワイ州 | Hawaii | USA-3517 |
| `US-IA` | アイオワ州 | Iowa | USA-3529 |
| `US-ID` | アイダホ州 | Idaho | USA-3518 |
| `US-IL` | イリノイ州 | Illinois | USA-3546 |
| `US-IN` | インディアナ州 | Indiana | USA-3547 |
| `US-KS` | カンザス州 | Kansas | USA-3530 |
| `US-KY` | ケンタッキー州 | Kentucky | USA-3548 |
| `US-LA` | ルイジアナ州 | Louisiana | USA-3535 |
| `US-MA` | マサチューセッツ州 | Massachusetts | USA-3513 |
| `US-MD` | メリーランド州 | Maryland | USA-3557 |
| `US-ME` | メイン州 | Maine | USA-3561 |
| `US-MI` | ミシガン州 | Michigan | USA-3562 |
| `US-MN` | ミネソタ州 | Minnesota | USA-3514 |
| `US-MO` | ミズーリ州 | Missouri | USA-3531 |
| `US-MS` | ミシシッピ州 | Mississippi | USA-3544 |
| `US-MT` | モンタナ州 | Montana | USA-3515 |
| `US-NC` | ノースカロライナ州 | North Carolina | USA-3549 |
| `US-ND` | ノースダコタ州 | North Dakota | USA-3516 |
| `US-NE` | ネブラスカ州 | Nebraska | USA-3532 |
| `US-NH` | ニューハンプシャー州 | New Hampshire | USA-3538 |
| `US-NJ` | ニュージャージー州 | New Jersey | USA-3558 |
| `US-NM` | ニューメキシコ州 | New Mexico | USA-3524 |
| `US-NV` | ネバダ州 | Nevada | USA-3523 |
| `US-NY` | ニューヨーク州 | New York | USA-3559 |
| `US-OH` | オハイオ州 | Ohio | USA-3550 |
| `US-OK` | オクラホマ州 | Oklahoma | USA-3533 |
| `US-OR` | オレゴン州 | Oregon | USA-3525 |
| `US-PA` | ペンシルベニア州 | Pennsylvania | USA-3560 |
| `US-RI` | ロードアイランド州 | Rhode Island | USA-3539 |
| `US-SC` | サウスカロライナ州 | South Carolina | USA-3545 |
| `US-SD` | サウスダコタ州 | South Dakota | USA-3534 |
| `US-TN` | テネシー州 | Tennessee | USA-3551 |
| `US-TX` | テキサス州 | Texas | USA-3536 |
| `US-UT` | ユタ州 | Utah | USA-3526 |
| `US-VA` | バージニア州 | Virginia | USA-3552 |
| `US-VT` | バーモント州 | Vermont | USA-3540 |
| `US-WA` | ワシントン州 | Washington | USA-3519 |
| `US-WI` | ウィスコンシン州 | Wisconsin | USA-3553 |
| `US-WV` | ウェストバージニア州 | West Virginia | USA-3554 |
| `US-WY` | ワイオミング州 | Wyoming | USA-3527 |

## イギリス（`gb`）: ITL2 (2025) の 46 地域、分母 46

- ID: ONS ITL 2025 code (ITL225CD)
- 出典: [International Territorial Level 2 (January 2025) Boundaries UK BUC](https://geoportal.statistics.gov.uk/search?q=ITL2_JAN_2025_UK_BUC)（ITL 2025 (January 2025), ITL2, BUC (ultra generalised 500m, clipped to the coastline)、Open Government Licence v3.0）
- ONS の ITL 2025 年分類（2025 年 1 月）の ITL2。England の細分を含む 46 地域。4 構成国、ITL1 の 12 地域、ITL 2021 / NUTS の 41 地域のいずれでもない。
- 北アイルランドは TLN0 として gb に含む（ie には含めない）。
- 分母に含めない: マン島（IM）、ジャージー（JE）、ガーンジー（GG）、英国の海外領土

| data-code | 日本語名 | English name | 元データの ID |
|---|---|---|---|
| `TLC3` | ティーズ・バレー | Tees Valley | TLC3 |
| `TLC4` | ノーサンバーランド、ダラム、タイン・アンド・ウィア | Northumberland, Durham and Tyne & Wear | TLC4 |
| `TLD1` | カンブリア | Cumbria | TLD1 |
| `TLD3` | グレーター・マンチェスター | Greater Manchester | TLD3 |
| `TLD4` | ランカシャー | Lancashire | TLD4 |
| `TLD6` | チェシャー | Cheshire | TLD6 |
| `TLD7` | マージーサイド | Merseyside | TLD7 |
| `TLE1` | イースト・ヨークシャー、ノーザン・リンカンシャー | East Yorkshire and Northern Lincolnshire | TLE1 |
| `TLE2` | ノース・ヨークシャー | North Yorkshire | TLE2 |
| `TLE3` | サウス・ヨークシャー | South Yorkshire | TLE3 |
| `TLE4` | ウェスト・ヨークシャー | West Yorkshire | TLE4 |
| `TLF1` | ダービーシャー、ノッティンガムシャー | Derbyshire and Nottinghamshire | TLF1 |
| `TLF2` | レスターシャー、ラトランド、ノーサンプトンシャー | Leicestershire, Rutland and Northamptonshire | TLF2 |
| `TLF3` | リンカンシャー | Lincolnshire | TLF3 |
| `TLG1` | ヘレフォードシャー、ウスターシャー、ウォリックシャー | Herefordshire, Worcestershire and Warwickshire | TLG1 |
| `TLG2` | シュロップシャー、スタッフォードシャー | Shropshire and Staffordshire | TLG2 |
| `TLG3` | ウェスト・ミッドランズ | West Midlands | TLG3 |
| `TLH2` | ベッドフォードシャー、ハートフォードシャー | Bedfordshire and Hertfordshire | TLH2 |
| `TLH3` | エセックス | Essex | TLH3 |
| `TLH4` | ケンブリッジシャー、ピーターバラ | Cambridgeshire and Peterborough | TLH4 |
| `TLH5` | ノーフォーク | Norfolk | TLH5 |
| `TLH6` | サフォーク | Suffolk | TLH6 |
| `TLI3` | インナー・ロンドン西部 | Inner London - West | TLI3 |
| `TLI4` | インナー・ロンドン東部 | Inner London - East | TLI4 |
| `TLI5` | アウター・ロンドン東部・北東部 | Outer London - East and North East | TLI5 |
| `TLI6` | アウター・ロンドン南部 | Outer London - South | TLI6 |
| `TLI7` | アウター・ロンドン西部・北西部 | Outer London - West and North West | TLI7 |
| `TLJ1` | バークシャー、バッキンガムシャー、オックスフォードシャー | Berkshire, Buckinghamshire and Oxfordshire | TLJ1 |
| `TLJ2` | サリー、イースト・サセックス、ウェスト・サセックス | Surrey, East and West Sussex | TLJ2 |
| `TLJ3` | ハンプシャー、ワイト島 | Hampshire and Isle of Wight | TLJ3 |
| `TLJ4` | ケント | Kent | TLJ4 |
| `TLK3` | コーンウォール、シリー諸島 | Cornwall and Isles of Scilly | TLK3 |
| `TLK4` | デヴォン | Devon | TLK4 |
| `TLK5` | ウェスト・オブ・イングランド | West of England | TLK5 |
| `TLK6` | ノース・サマセット、サマセット、ドーセット | North Somerset, Somerset and Dorset | TLK6 |
| `TLK7` | グロスターシャー、ウィルトシャー | Gloucestershire and Wiltshire | TLK7 |
| `TLL3` | 北ウェールズ | North Wales | TLL3 |
| `TLL4` | 中部・南西ウェールズ | Mid and South West Wales | TLL4 |
| `TLL5` | 南東ウェールズ | South East Wales | TLL5 |
| `TLM0` | 東部スコットランド | Eastern Scotland | TLM0 |
| `TLM1` | 中東部スコットランド | East Central Scotland | TLM1 |
| `TLM2` | ハイランド・アンド・アイランズ | Highlands and Islands | TLM2 |
| `TLM3` | 中西部スコットランド | West Central Scotland | TLM3 |
| `TLM5` | 北東部スコットランド | North Eastern Scotland | TLM5 |
| `TLM9` | 南部スコットランド | Southern Scotland | TLM9 |
| `TLN0` | 北アイルランド | Northern Ireland | TLN0 |

## 韓国（`kr`）: 第 1 級の 16 区分（2026-07-01 以降）、分母 16

- ID: ISO 3166-2:KR。ISO 未割当の全南光州統合特別市だけ、韓国の行政区域コード 12 を KR-12 とする（行政区域コードを kr_admin_code、ISO コードを iso_3166_2 に併記）
- 出典: [대한민국 행정동 경계 (admdongkor) HangJeongDong_ver20260701](https://github.com/vuski/admdongkor)（ver20260701 (2026-07-01 boundaries, commit 7360288277)、CC BY 4.0 (original data: Statistics Korea SGIS, KOGL Type 1)）
- 2026-07-01 の光州広域市と全羅南道の統合後の 16 区分（行政安全部の行政標準コード・国土交通部の法定洞コード 2026-06-30 版で 16 件を確認）。
- ISO 3166-2:KR は 2023-11-23 以降更新がなく、全南光州統合特別市のコードが無い。このため KR-12 は ISO コードではなく、韓国の行政区域コード（法定洞コードの市道 2 桁）12 を ISO と同じ形にしたもの。ISO がコードを割り当てても data-code は変えず、regions.json の iso_3166_2 に記録する。
- 行政洞（3,558）を市道単位に統合して作成。軍威郡（2023-07-01 に大邱へ編入）を反映。
- リアンクール岩礁（独島/竹島）は、この縮尺では表示できない小島のため描画しない。帰属についての立場を示すものではない。
- 分母に含めない: 光州広域市（KR-29）、全羅南道（KR-46）

| data-code | 日本語名 | English name | 韓国語名 / 行政区域コード / ISO 3166-2 |
|---|---|---|---|
| `KR-11` | ソウル特別市 | Seoul | 서울특별시 / 11 / KR-11 |
| `KR-12` | 全南光州統合特別市 | Jeonnam-Gwangju | 전남광주통합특별시 / 12 / 未割当 |
| `KR-26` | 釜山広域市 | Busan | 부산광역시 / 26 / KR-26 |
| `KR-27` | 大邱広域市 | Daegu | 대구광역시 / 27 / KR-27 |
| `KR-28` | 仁川広域市 | Incheon | 인천광역시 / 28 / KR-28 |
| `KR-30` | 大田広域市 | Daejeon | 대전광역시 / 30 / KR-30 |
| `KR-31` | 蔚山広域市 | Ulsan | 울산광역시 / 31 / KR-31 |
| `KR-41` | 京畿道 | Gyeonggi | 경기도 / 41 / KR-41 |
| `KR-42` | 江原特別自治道 | Gangwon | 강원특별자치도 / 51 / KR-42 |
| `KR-43` | 忠清北道 | North Chungcheong | 충청북도 / 43 / KR-43 |
| `KR-44` | 忠清南道 | South Chungcheong | 충청남도 / 44 / KR-44 |
| `KR-45` | 全北特別自治道 | Jeonbuk | 전북특별자치도 / 52 / KR-45 |
| `KR-47` | 慶尚北道 | North Gyeongsang | 경상북도 / 47 / KR-47 |
| `KR-48` | 慶尚南道 | South Gyeongsang | 경상남도 / 48 / KR-48 |
| `KR-49` | 済州特別自治道 | Jeju | 제주특별자치도 / 50 / KR-49 |
| `KR-50` | 世宗特別自治市 | Sejong | 세종특별자치시 / 36 / KR-50 |

## カナダ（`ca`）: 10 州と 3 準州、分母 13

- ID: ISO 3166-2:CA
- 出典: [Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces (large lakes removed)](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)（v5.1.2 (ne_10m_admin_1_states_provinces_lakes)、Public Domain）

| data-code | 日本語名 | English name | 元データの ID |
|---|---|---|---|
| `CA-AB` | アルバータ州 | Alberta | CAN-632 |
| `CA-BC` | ブリティッシュコロンビア州 | British Columbia | CAN-633 |
| `CA-MB` | マニトバ州 | Manitoba | CAN-630 |
| `CA-NB` | ニューブランズウィック州 | New Brunswick | CAN-684 |
| `CA-NL` | ニューファンドランド・ラブラドール州 | Newfoundland and Labrador | CAN-686 |
| `CA-NS` | ノバスコシア州 | Nova Scotia | CAN-685 |
| `CA-NT` | ノースウェスト準州 | Northwest Territories | CAN-635 |
| `CA-NU` | ヌナブト準州 | Nunavut | CAN-634 |
| `CA-ON` | オンタリオ州 | Ontario | CAN-682 |
| `CA-PE` | プリンスエドワードアイランド州 | Prince Edward Island | CAN-687 |
| `CA-QC` | ケベック州 | Quebec | CAN-683 |
| `CA-SK` | サスカチュワン州 | Saskatchewan | CAN-631 |
| `CA-YT` | ユーコン準州 | Yukon | CAN-636 |

## オーストラリア（`au`）: 6 州と 2 準州（ACT・NT）、分母 8

- ID: ISO 3166-2:AU
- 出典: [Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces (large lakes removed)](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)（v5.1.2 (ne_10m_admin_1_states_provinces_lakes)、Public Domain）
- ロードハウ島（ニューサウスウェールズ州）とマッコーリー島（タスマニア州）は本土から遠い小島のため描画を省略（区分としてはそれぞれの州）。
- 分母に含めない: ジャービス湾特別地域、クリスマス島（CX）、ココス（キーリング）諸島（CC）、ノーフォーク島（NF）、ハード島とマクドナルド諸島（HM）、アシュモア・カルティエ諸島、コーラル・シー諸島、オーストラリア南極領土

| data-code | 日本語名 | English name | 元データの ID |
|---|---|---|---|
| `AU-ACT` | オーストラリア首都特別地域 | Australian Capital Territory | AUS-2653 |
| `AU-NSW` | ニューサウスウェールズ州 | New South Wales | AUS-2654 |
| `AU-NT` | 北部準州 | Northern Territory | AUS-2650 |
| `AU-QLD` | クイーンズランド州 | Queensland | AUS-2657 |
| `AU-SA` | 南オーストラリア州 | South Australia | AUS-2655 |
| `AU-TAS` | タスマニア州 | Tasmania | AUS-2660 |
| `AU-VIC` | ビクトリア州 | Victoria | AUS-2656 |
| `AU-WA` | 西オーストラリア州 | Western Australia | AUS-2651 |

## ニュージーランド（`nz`）: 16 の地方（regional council の区域）、分母 16

- ID: ISO 3166-2:NZ（Stats NZ の地方コード REGC2025 を stats_nz_code に併記）
- 出典: [Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces (large lakes removed)](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)（v5.1.2 (ne_10m_admin_1_states_provinces_lakes)、Public Domain）
- 分母に含めない: チャタム諸島（NZ-CIT）、ケルマデック諸島・亜南極諸島など、トケラウ（TK）

| data-code | 日本語名 | English name | Stats NZ コード |
|---|---|---|---|
| `NZ-AUK` | オークランド地方 | Auckland | 02 |
| `NZ-BOP` | ベイ・オブ・プレンティ地方 | Bay of Plenty | 04 |
| `NZ-CAN` | カンタベリー地方 | Canterbury | 13 |
| `NZ-GIS` | ギズボーン地方 | Gisborne | 05 |
| `NZ-HKB` | ホークスベイ地方 | Hawke's Bay | 06 |
| `NZ-MBH` | マールボロ地方 | Marlborough | 18 |
| `NZ-MWT` | マナワツ・ワンガヌイ地方 | Manawatū-Whanganui | 08 |
| `NZ-NSN` | ネルソン地方 | Nelson | 17 |
| `NZ-NTL` | ノースランド地方 | Northland | 01 |
| `NZ-OTA` | オタゴ地方 | Otago | 14 |
| `NZ-STL` | サウスランド地方 | Southland | 15 |
| `NZ-TAS` | タスマン地方 | Tasman | 16 |
| `NZ-TKI` | タラナキ地方 | Taranaki | 07 |
| `NZ-WGN` | ウェリントン地方 | Wellington | 09 |
| `NZ-WKO` | ワイカト地方 | Waikato | 03 |
| `NZ-WTC` | ウェストコースト地方 | West Coast | 12 |

## アイルランド（`ie`）: 伝統的な 26 県、分母 26

- ID: ISO 3166-2:IE（県）
- 出典: [Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces (large lakes removed)](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)（v5.1.2 (ne_10m_admin_1_states_provinces_lakes)、Public Domain）
- Natural Earth の地方自治体単位（34）を ISO 3166-2:IE の県へ統合して 26 県にした。ダブリン（Dublin City・Dún Laoghaire–Rathdown・Fingal・South Dublin）は 1 県、ティペラリー（North / South Tipperary）は 1 県、コーク・ゴールウェイ・リムリック・ウォーターフォードは市と県を 1 県にまとめている。
- 分母に含めない: 北アイルランド（アントリム、アーマー、ダウン、ファーマナ、ロンドンデリー、ティロン）

| data-code | 日本語名 | English name | アイルランド語名 / 地方 |
|---|---|---|---|
| `IE-CE` | クレア県 | Clare | An Clár / Munster |
| `IE-CN` | キャバン県 | Cavan | An Cabhán / Ulster |
| `IE-CO` | コーク県 | Cork | Corcaigh / Munster |
| `IE-CW` | カーロウ県 | Carlow | Ceatharlach / Leinster |
| `IE-D` | ダブリン県 | Dublin | Baile Átha Cliath / Leinster |
| `IE-DL` | ドニゴール県 | Donegal | Dún na nGall / Ulster |
| `IE-G` | ゴールウェイ県 | Galway | Gaillimh / Connacht |
| `IE-KE` | キルデア県 | Kildare | Cill Dara / Leinster |
| `IE-KK` | キルケニー県 | Kilkenny | Cill Chainnigh / Leinster |
| `IE-KY` | ケリー県 | Kerry | Ciarraí / Munster |
| `IE-LD` | ロングフォード県 | Longford | An Longfort / Leinster |
| `IE-LH` | ラウス県 | Louth | Lú / Leinster |
| `IE-LK` | リムリック県 | Limerick | Luimneach / Munster |
| `IE-LM` | リートリム県 | Leitrim | Liatroim / Connacht |
| `IE-LS` | リーシュ県 | Laois | Laois / Leinster |
| `IE-MH` | ミース県 | Meath | An Mhí / Leinster |
| `IE-MN` | モナハン県 | Monaghan | Muineachán / Ulster |
| `IE-MO` | メイヨー県 | Mayo | Maigh Eo / Connacht |
| `IE-OY` | オファリー県 | Offaly | Uíbh Fhailí / Leinster |
| `IE-RN` | ロスコモン県 | Roscommon | Ros Comáin / Connacht |
| `IE-SO` | スライゴ県 | Sligo | Sligeach / Connacht |
| `IE-TA` | ティペラリー県 | Tipperary | Tiobraid Árann / Munster |
| `IE-WD` | ウォーターフォード県 | Waterford | Port Láirge / Munster |
| `IE-WH` | ウェストミース県 | Westmeath | An Iarmhí / Leinster |
| `IE-WW` | ウィックロー県 | Wicklow | Cill Mhantáin / Leinster |
| `IE-WX` | ウェックスフォード県 | Wexford | Loch Garman / Leinster |

## シンガポール（`sg`）: URA の 5 地域、分母 5

- ID: SG-{URA の地域コード}（NER は SG-NE）。ISO 3166-2:SG（CDC の 01〜05）とは別
- 出典: [Master Plan 2025 Region Boundary (No Sea)](https://data.gov.sg/datasets/d_4ce0038f7ac689652350bb91b7fb92ed/view)（URA Master Plan 2025 (gazetted 2025-12-01), dataset updated 2026-02-27、Singapore Open Data Licence v1.0）
- URA Master Plan 2025 の地域境界（海域を除く）。離島（セントーサ、ジュロン島、ウビン島、テコン島など）は所属する地域に含む。
- 分母に含めない: 計画区域（55）

| data-code | 日本語名 | English name | 元データの ID |
|---|---|---|---|
| `SG-CR` | 中央地域 | Central Region | CR (CENTRAL REGION) |
| `SG-ER` | 東部地域 | East Region | ER (EAST REGION) |
| `SG-NE` | 北東部地域 | North-East Region | NER (NORTH-EAST REGION) |
| `SG-NR` | 北部地域 | North Region | NR (NORTH REGION) |
| `SG-WR` | 西部地域 | West Region | WR (WEST REGION) |
