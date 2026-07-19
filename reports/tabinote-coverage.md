# tabiNote 国マスタ突合レポート

- マスタ正本: `tabinote-countries.json` (194 カ国, 取得日 2026-07-19)
- 判定: **合格 (欠落 0 / code 不一致 0 / 名前解決不能 0)**

## map-full.svg

- マスタ対応 country グループ: 194 / 194
- マスタ外 territory グループ: 4 (TW 台湾 / XK コソボ / EH 西サハラ / AM アルメニア)
- 極小国マーカー付与: 31 カ国
  - AD, AG, BB, BH, BN, DM, FM, GD, KI, KM, KN, LC, LI, LU, MC, MH, MT, MU, MV, NR, PS, PW, SC, SG, SM, ST, TO, TT, TV, VA, VC
- エラー: なし

## map-mobile.svg

- マスタ対応 country グループ: 194 / 194
- マスタ外 territory グループ: 4 (TW 台湾 / XK コソボ / EH 西サハラ / AM アルメニア)
- 極小国マーカー付与: 45 カ国
  - AD, AG, BB, BH, BN, CV, CY, DJ, DM, FM, GD, JM, KI, KM, KN, KW, LB, LC, LI, LU, MC, ME, MH, MK, MT, MU, MV, NR, PS, PW, QA, RW, SC, SG, SM, ST, SV, SZ, TL, TO, TT, TV, VA, VC, WS
- エラー: なし

## map-full-japan-center.svg

- マスタ対応 country グループ: 194 / 194
- マスタ外 territory グループ: 4 (TW 台湾 / XK コソボ / EH 西サハラ / AM アルメニア)
- 極小国マーカー付与: 31 カ国
  - AD, AG, BB, BH, BN, DM, FM, GD, KI, KM, KN, LC, LI, LU, MC, MH, MT, MU, MV, NR, PW, SC, SG, SM, ST, TO, TT, TV, VA, VC, WS
- エラー: なし

## map-mobile-japan-center.svg

- マスタ対応 country グループ: 194 / 194
- マスタ外 territory グループ: 4 (TW 台湾 / XK コソボ / EH 西サハラ / AM アルメニア)
- 極小国マーカー付与: 43 カ国
  - AD, AG, BB, BH, BN, CV, DJ, DM, FM, GD, JM, KI, KM, KN, KW, LB, LC, LI, LU, MC, ME, MH, MT, MU, MV, NR, PS, PW, QA, RW, SC, SG, SM, ST, SV, SZ, TL, TO, TT, TV, VA, VC, WS
- エラー: なし

## 特記事項

- **アルメニア (AM)**: 国連加盟国だが tabiNote 国マスタ 194 件に存在しないため、マスタ正の原則に従い色塗り対象外の `territory` として収録。マスタに追加された場合は `scripts/build.py` の `TERRITORIES` から `ARM` を削除して再ビルドすれば `country` に昇格する。
- マスタ外 territory (TW/XK/EH/AM) は `class="territory"` `data-master="false"` を持ち、`.country` セレクタでは選択されない。
- 属領・海外領土 (グリーンランド、プエルトリコ、ニューカレドニア等) は本国のグループに吸収済み。
- 除外: 南極大陸 (マスタに AQ が無い)、ビル・タウィール (無主地)、南シナ海の岩礁等。

