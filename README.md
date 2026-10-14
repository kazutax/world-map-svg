# SVG Map of the World（world-map-svg）

[geolonia/japanese-prefectures](https://github.com/geolonia/japanese-prefectures)（SVG 日本地図）の**世界地図版**です。
訪問した国を色塗りする「制覇マップ」等のユースケースを想定した、国ごとにグループ化された SVG 世界地図を提供します。

Demo: https://kazutax.github.io/world-map-svg/demo/

国の中の区画（米国の州、英国の ITL2 地域など 9 か国）の SVG もあります → [国の中の区画](#国の中の区画subdivisions)（Demo: https://kazutax.github.io/world-map-svg/demo/subdivisions.html）

![map-full.svg](map-full.svg)

## 仕様

* 国ごとに `<g>` でグループ化してあり、国名スラッグ（例: `japan`）と大陸名（`asia` / `europe` / `africa` / `north-america` / `south-america` / `oceania`）を `class` 属性の値としてセットしてありますので、CSS で国別・大陸別に色分けすることができます。
* 各国のグループは `country` class を持ちます（日本地図版の `.prefecture` に相当）。
* `data-code` という属性をもっており、**ISO 3166-1 alpha-2 コード（大文字）** が格納されています。（日本の例: `data-code="JP"`）
* 各グループは `<title>日本語名 / English name</title>` を持ちます。（例: `<title>日本 / Japan</title>`）
* 投影法は **Equal Earth 図法**（面積比が保たれ、スマホでの実績マップ表示に向く）。
* 極小の国（シンガポール、バチカン市国、モルディブ等）には、クリック・色塗りを可能にするための円マーカー `<circle class="country-marker">` をグループ内に付与してあります。マーカーはグループの `fill` を継承するため、国と同時に塗り替わります。
* 4 種類の SVG ファイルがありますので、好みで使い分けてください。
  * [map-full.svg](map-full.svg) - フルサイズの地図です（簡略化弱め・マーカー小さめ）。
  * [map-mobile.svg](map-mobile.svg) - モバイルデバイス用にアレンジした地図です（パス簡略化強め・極小国マーカー大きめ・線太め）。
  * [map-full-japan-center.svg](map-full-japan-center.svg) - **日本中心（太平洋中心）版**。中央経線 150°E。
  * [map-mobile-japan-center.svg](map-mobile-japan-center.svg) - 日本中心版のモバイル向けアレンジです。

### 日本中心版について

![map-full-japan-center.svg](map-full-japan-center.svg)

* 中央経線 150°E で再投影しており、日本がほぼ中央、アメリカ大陸が右側に配置されます。
* 地図の切れ目は西経 30 度です。この経線をまたぐ**グリーンランド（デンマーク領）のみ左右両端に分割**されますが、どちらも同じ `DK` グループに属するため塗り分けには影響しません。
* 元データが日付変更線（180 度線）で分割されているロシア（チュクチ半島・ウランゲリ島）とフィジーは、継ぎ目の境界線が見えないように接合しています（該当箇所のパスは `Z` で閉じず、塗りは暗黙の閉路で成立させています）。

### SVG の構造

```xml
<svg class="world-svg-map" viewBox="0 0 2000 894" xmlns="http://www.w3.org/2000/svg">
  <title>World Countries</title>
  <g class="svg-map">
    <g class="countries">
      <g class="japan asia country" data-code="JP" fill="#EEEEEE" fill-rule="evenodd"
         stroke="#000000" stroke-width="0.5" stroke-linejoin="round">
        <title>日本 / Japan</title>
        <path d="M... Z"/>
      </g>
      <!-- 極小国はマーカー付き -->
      <g class="singapore asia country" data-code="SG" ...>
        <title>シンガポール / Singapore</title>
        <path d="M... Z"/>
        <circle class="country-marker" cx="..." cy="..." r="4"/>
      </g>
    </g>
  </g>
</svg>
```

## tabiNote 国マスタ完全対応（必須要件）

この SVG は、tabiNote アプリの国マスタ（`location_tags` の `type = 'country'`、**195 カ国**）への完全対応を必須要件としています。

* 正本: [tabinote-countries.json](tabinote-countries.json)（`name` / `name_en` / `country_code` / `continent`）
* マスタ全 195 カ国について、SVG 上に `country` グループが存在し、`data-code` が `country_code` と一致し、`<title>` の日本語名がマスタの `name` と一致します。
* 突合結果: [reports/tabinote-coverage.md](reports/tabinote-coverage.md)（**欠落 0 / code 不一致 0 / 名前解決不能 0**）

### 検証手順

```console
$ python3 scripts/validate.py
map-full.svg: OK
map-mobile.svg: OK
map-full-japan-center.svg: OK
map-mobile-japan-center.svg: OK
report -> reports/tabinote-coverage.md
```

`validate.py` は次を機械検証します: マスタ全件の存在 / `data-code` の一致と重複なし / `<title>` の一致 / 全マスタ国が塗り可能（可視ジオメトリまたはマーカーを持つ）/ マスタ外地域が `.country` セレクタを汚染しないこと / `countries.json` との整合。

## 使い方（例）

### JavaScript

JavaScript で以下のように読み込んでください。

```javascript
const map = "./map-full.svg" // Or "./map-mobile.svg"
const container = document.querySelector( '#map' )

const res = await fetch( map )

if ( res.ok ) {
  const svg = await res.text()
  container.innerHTML = svg
  const countries = document.querySelectorAll( '.world-svg-map .country' )

  countries.forEach( ( country ) => {
    // マウスオーバーで色を変える
    country.addEventListener( 'mouseover', ( event ) => {
      event.currentTarget.style.fill = "#ff0000"
    } )

    // マウスが離れたら色をもとに戻す
    country.addEventListener( 'mouseleave', ( event ) => {
      event.currentTarget.style.fill = ""
    } )

    // マウスクリック時のイベント
    country.addEventListener( 'click', ( event ) => {
      location.href = `https://example.com/${event.currentTarget.dataset.code}` // 例（日本）: https://example.com/JP
    } )
  } )
}
```

訪問済みの国を塗る例:

```javascript
const visitedCodes = [ "JP", "US", "FR" ] // ISO 3166-1 alpha-2

visitedCodes.forEach( ( code ) => {
  const el = document.querySelector( `.world-svg-map .country[data-code="${code}"]` )
  if ( el ) el.style.fill = "#e8927c"
} )
```

### CSS

以下は CSS の記述例です。

```css
.world-svg-map
{
  width: 100%;
}

.world-svg-map .country
{
  fill: #f7f7f7;
  stroke: #666666;
  cursor: pointer;
}

/* 訪問済み */
.world-svg-map .country.visited
{
  fill: #e8927c;
}

/* マスタ外の中立地域 (色塗り対象外) */
.world-svg-map .territory
{
  fill: #e0e0e0;
  stroke: #999999;
}

/* 大陸単位の色分けも可能 */
.world-svg-map .country.asia { fill: #fff3e0; }
```

### SwiftUI 等でのパース

各国は `data-code` を持つ `<g>` 単位で完結しており、パスは `M` / `L` / `Z` のみで構成された単純なポリゴンです（曲線コマンドなし）。座標は `viewBox`（例: `0 0 2000 894`）基準の絶対座標なので、XML パーサで `<g data-code>` ごとに `<path d>` と `<circle>` を取り出せばネイティブ描画できます。

* 1 つの `<path>` に複数のサブパス（`M ... Z M ... Z`）が含まれる場合があります。2 つ目以降は飛び地または穴（例: 南アフリカの中のレソト）で、`fill-rule="evenodd"` で解釈してください。
* 日本中心版には `Z` で閉じないサブパスが少数あります（継ぎ目の線を消すための意図的なもの）。塗りつぶし時は始点と終点を結んで閉じてください（SVG の fill と同じ挙動）。

## 国の定義・収録範囲

* **採用集合は tabiNote 国マスタ（195 カ国）に一致させています。** 国連の一般定義ではなくマスタが正です。
  * マスタには国連加盟 193 カ国すべて + パレスチナ (PS) + バチカン市国 (VA) が含まれます。
* **マスタ外の中立地域（3 件）**: 地図上の空白（穴）を避けるため、以下は `class="territory"` `data-master="false"` として収録していますが、`.country` セレクタでは選択されず、マスタの塗り分けを阻害しません。
  * 台湾 (TW) / コソボ (XK) / 西サハラ (EH)
  * アルメニア (AM) は当初マスタに欠落しており territory 扱いでしたが、2026-07-19 のマスタ更新（194 → 195 カ国）に伴い色塗り対象の `country` に昇格しました。
* **属領・海外領土は本国に含めています。** 例: グリーンランド→デンマーク (DK)、プエルトリコ→アメリカ (US)、ニューカレドニア・仏領ポリネシア→フランス (FR)、フォークランド諸島→イギリス (GB)。マスタ外の独立パスは追加していません。
* 実効支配地域の扱い: 北キプロス→キプロス (CY)、ソマリランド→ソマリア (SO) に吸収。
* **省略**: 南極大陸（マスタに AQ が無く、縦横比と塗り UX を優先）、ビル・タウィール（無主地）、南シナ海の岩礁等。
* 国別の収録状況と突合結果は [countries.json](countries.json)（`code` / `name_ja` / `name_en` / `region` / `included_in_svg` / `tabinote_matched` / `notes`）を参照してください。

## 極小国の扱い

日本地図版が沖縄を別枠配置しているのと同様の配慮として、投影後の描画サイズが閾値未満の国（map-full で 31 カ国、map-mobile で 45 カ国）には円マーカーを付与し、「見えない・触れない・塗れない」状態を防いでいます。対象国の一覧は [reports/tabinote-coverage.md](reports/tabinote-coverage.md) に記載しています。

## ビルド・再生成

```console
$ python3 scripts/build.py     # Natural Earth データを取得し SVG / countries.json を再生成
$ python3 scripts/validate.py  # tabiNote 国マスタ完全対応チェック
```

依存は Python 3.9+ の標準ライブラリのみです。ベースデータ（約 13MB）はリポジトリに含めず、初回実行時にダウンロードします。

## ライセンス・出典

* **地理データ**: [Natural Earth](https://www.naturalearthdata.com/)（1:10m Admin 0 - Countries）。Natural Earth はパブリックドメインで、商用利用・改変・再配布・アプリへの同梱がすべて自由です。クレジット表記も不要ですが、本リポジトリでは出典として明記します。
* **本リポジトリの SVG・スクリプト・メタデータ**: [MIT License](LICENSE)。商用アプリへの同梱が可能です。
* 国の中の区画（`subdivisions/`）の地理データの出典とライセンスは、[国の中の区画](#国の中の区画subdivisions) の節を参照してください（英国・韓国・シンガポールは帰属表示が必要です）。
* 参考元（仕様の正）: [geolonia/japanese-prefectures](https://github.com/geolonia/japanese-prefectures)（同リポジトリの SVG データ自体は GFDL のため流用しておらず、属性設計・使い勝手のみを踏襲しています）。

## 免責事項

本リポジトリの地図は「訪問国の塗り分け」を目的とした簡略化された表現であり、国境線・地域区分・名称は [Natural Earth](https://www.naturalearthdata.com/) のデフォルト解釈に基づきます。**国家の承認・帰属・領土に関するいかなる政治的立場も表明するものではありません。**係争地・地位未確定の地域（台湾・コソボ・西サハラ等）は、地図の連続性のために中立地域（`territory`）として描画しているものであり、その地位に関する見解を示すものではありません。

## 既知の制約

* 国境線は Natural Earth のデフォルト解釈に基づく簡略表現であり、厳密な地政学地図ではありません（「制覇塗り絵」用途を優先）。
* パス簡略化（Douglas-Peucker）により、小さな島嶼の一部は省略されています（各国最大のポリゴンは必ず保持）。
* カリブ海・南太平洋の極小国マーカーは近接して重なる場合があります。
* 縦横比の都合上、南極大陸は収録していません。

## 国の中の区画（subdivisions）

訪問した州・地域を塗る「国の中の達成地図」用に、国ごとの区画 SVG を `subdivisions/` に置いています。世界地図（`map-*.svg`）とは別ファイルで、世界地図の `<g class="country">` には手を加えていません。日本の 47 都道府県は収録しません（[geolonia/japanese-prefectures](https://github.com/geolonia/japanese-prefectures) を使ってください）。

Demo: https://kazutax.github.io/world-map-svg/demo/subdivisions.html

### ファイルの場所

```text
subdivisions/
  {code}/map-mobile.svg   アプリ向け（簡略化強め・線太め・マーカー大きめ）
  {code}/map-full.svg     フル版
  {code}/regions.json     区分の一覧（分母・ID・名称・出典・投影・除外した領域）
  README.md               国ごとのコード表（自動生成）
```

### 収録国と分母

分母は下表で固定です。より細かい行政界への分割や、より粗い統合はしません。件数は `scripts/validate_subdivisions.py` で機械検証しています。

| 国 | `{code}` | 区分 | 分母 | `data-code`（安定 ID） | 出典 | 地理データのライセンス |
|---|---|---|---|---|---|---|
| アメリカ | `us` | 50 州とコロンビア特別区。アラスカ・ハワイを含み、プエルトリコなどの海外領域は含めない | 51 | ISO 3166-2:US（`US-CA`、`US-DC`） | Natural Earth Admin 1 v5.1.2 | パブリックドメイン |
| イギリス | `gb` | ONS の ITL2（2025 年 1 月の分類）。England の細分を含み、北アイルランド（`TLN0`）を含む | 46 | ONS の ITL 2025 コード（`TLC3` … `TLN0`） | ONS ITL2 (January 2025) BUC | Open Government Licence v3.0 |
| 韓国 | `kr` | 第 1 級の 16 区分（特別市、広域市、特別自治市、統合特別市、道、特別自治道。2026-07-01 の光州・全南統合後） | 16 | ISO 3166-2:KR（`KR-11`）。ISO 未割当の全南光州統合特別市は `KR-12`（下記） | vuski/admdongkor 行政洞境界 ver20260701（統計庁 SGIS を加工） | CC BY 4.0（原資料は公共ヌリ第 1 類型） |
| 中国 | `cn` | 22 省、5 自治区、4 直轄市。台湾・香港・マカオは含めない | 31 | ISO 3166-2:CN（`CN-BJ`、`CN-GD`）。`CN-TW`・`CN-HK`・`CN-MO` は使わない | Natural Earth Admin 1 v5.1.2 | パブリックドメイン |
| カナダ | `ca` | 10 州と 3 準州 | 13 | ISO 3166-2:CA（`CA-ON`） | Natural Earth Admin 1 v5.1.2 | パブリックドメイン |
| オーストラリア | `au` | 6 州、ACT、NT。クリスマス島などの海外領域とジャービス湾特別地域は含めない | 8 | ISO 3166-2:AU（`AU-NSW`） | Natural Earth Admin 1 v5.1.2 | パブリックドメイン |
| ニュージーランド | `nz` | 16 の地方（regional council の区域）。チャタム諸島は含めない | 16 | ISO 3166-2:NZ（`NZ-AUK`）。Stats NZ の地方コードを `stats_nz_code` に併記 | Natural Earth Admin 1 v5.1.2 | パブリックドメイン |
| アイルランド | `ie` | 伝統的な 26 県。ダブリン・ティペラリーは各 1 県。北アイルランドは含めない | 26 | ISO 3166-2:IE（`IE-D`、`IE-TA`） | Natural Earth Admin 1 v5.1.2（自治体単位を県へ統合） | パブリックドメイン |
| シンガポール | `sg` | URA の 5 地域。計画区域（55）は使わない | 5 | `SG-CR` / `SG-ER` / `SG-NR` / `SG-NE` / `SG-WR` | URA Master Plan 2025 Region Boundary (No Sea) | Singapore Open Data Licence v1.0 |

* 北アイルランドは `gb` にだけ入っています（`ie` には入れていません）。
* 各国の区分の一覧（`data-code`・日本語名・英語名）は [subdivisions/README.md](subdivisions/README.md) と各 `regions.json` にあります。
* **韓国の `KR-12` について**: 2026-07-01 に光州広域市（`KR-29`）と全羅南道（`KR-46`）が統合されて「全南光州統合特別市」が発足しました。ISO 3166-2:KR は 2023-11-23 以降更新がなく、この区分のコードはまだありません（2026-10 時点。Debian iso-codes・Unicode CLDR・Wikidata でも未登録）。そこで、韓国政府が割り当てた行政区域コード（行政標準コード・法定洞コードの市道 2 桁）`12` を、他の区分と同じ `KR-` 形式にして `KR-12` としています。**`KR-12` は ISO コードではありません。** ISO がコードを割り当てても `data-code` は変えず、`regions.json` の `iso_3166_2` に記録します（他の 15 区分は `iso_3166_2` が `data-code` と同じ値、`KR-12` は `null`）。韓国の行政区域コードは `kr_admin_code` に併記しています（江原 `51`・全北 `52`・済州 `50`・世宗 `36` などは ISO の番号と違うので注意）。
* 韓国の境界は行政洞（3,558）を市道単位に統合したもので、2023-07-01 に大邱へ編入された軍威郡も反映しています。
* **中国（`cn`）について**: Natural Earth の第 1 級行政界のうち ISO 3166-2:CN の 31 件に当たるフィーチャをそのまま使っています（台湾・香港・マカオは Natural Earth でも中国とは別のフィーチャで、中国側には入っていません）。31 区分を合わせた外形は、世界地図の `CN` の元データ（Natural Earth Admin 0 の CHN）と一致します。九段線、台湾、香港、マカオは描きません。西沙（パラセル）諸島は 31 区分に属さない別フィーチャのため、海南省へ吸収せず描画もしていません（世界地図でも描画されない大きさです）。
  * 世界地図（`map-*.svg`）では、Natural Earth で主権国が中国の香港とマカオは `CN` のグループに含まれています（台湾は `TW` の `territory` として別）。区画では香港とマカオを描かないため、この 2 か所だけ世界地図の `CN` と外形が異なります。

### SVG の構造

世界地図と同じ読み方（`data-code` を持つ `<g>` ごとに `<title>`・`<path>`・`<circle>`）でパースできます。

```xml
<svg class="subdivision-svg-map" data-country="US" viewBox="0 0 1000 594" xmlns="http://www.w3.org/2000/svg">
  <title>アメリカ合衆国：50 州とコロンビア特別区 / United States: 50 states and the District of Columbia</title>
  <desc>（出典とライセンスの表示）</desc>
  <g class="svg-map">
    <g class="regions">
      <g class="california region" data-code="US-CA" data-country="US" fill="#EEEEEE" fill-rule="evenodd"
         stroke="#000000" stroke-width="1.0" stroke-linejoin="round">
        <title>カリフォルニア州 / California</title>
        <path d="M... Z M... Z"/>
      </g>
      <!-- 画面で指せないほど小さい区分はマーカー付き -->
      <g class="district-of-columbia region" data-code="US-DC" data-country="US" ...>
        <title>ワシントンD.C. / District of Columbia</title>
        <path d="M... Z"/>
        <circle class="region-marker" cx="..." cy="..." r="10.0" stroke-width="1.0"/>
      </g>
    </g>
    <!-- us のみ: アラスカ・ハワイのはめ込みの区切り線（data-code を持たない） -->
    <g class="boundary-line" fill="none" stroke="#999999" ...>
      <path d="M... L..."/>
    </g>
  </g>
</svg>
```

* 1 区分が 1 つの `<g class="region">` です。`class="country"` は付けていないので、世界地図の `.country` セレクタとは混ざりません。
* `data-code` は上表の安定 ID、`data-country` は国の ISO 3166-1 alpha-2 です。区分は `[data-code]` または `.region` で取得してください（`boundary-line` は区分ではありません）。
* `<title>` は「日本語名 / English name」です（例: `<title>カリフォルニア州 / California</title>`）。
* パスは `M` / `L` / `Z` のみ（曲線なし）。1 区分につき `<path>` は 1 つで、飛び地と穴は同じ `<path>` のサブパスです。`fill-rule="evenodd"` で解釈してください。
* 隣り合う区分の共有境界は同じ簡略化結果を使っているので、区分の間に隙間や重なりはできません。
* 小さい区分（最大ポリゴンの面積の平方根が mobile で 14、full で 7 未満）には `<circle class="region-marker">` を付けています。マーカーは `fill` を持たず親の `<g>` から継承するので、区分と同時に塗られます。マーカー同士が重なる場合は半径を縮めています。
  * mobile: `US-DC`, `US-RI`, `TLI3`, `TLI4`, `CA-PE`, `AU-ACT`, `NZ-NSN`
  * full: `US-DC`, `TLI3`
* 投影は国ごとの正積円錐図法（Albers）で、その国が viewBox（長辺 1000）いっぱいに収まります。世界地図の Equal Earth は使っていません。投影のパラメータは `regions.json` の `projection` にあります。
* アメリカは本土の左下にアラスカ（面積 0.35 倍）とハワイをはめ込んでいます（d3-geo の `geoAlbersUsa` と同じ配置）。日本地図の沖縄の別枠と同じ配慮で、本土とは重ねていません。
* full と mobile は同じ viewBox です。mobile はパスの簡略化を強め、線を太く、マーカーを大きくしています。各区分の最大のポリゴンは必ず残しています。

### regions.json

```jsonc
{
  "country": "US", "denominator": 51, "id_scheme": "ISO 3166-2:US",
  "source": { "name": "...", "url": "...", "version": "...", "license": "...", "attribution": "...", "retrieved": "...", "sha256": "..." },
  "projection": { "main": { ... }, "insets": { "US-AK": { ... }, "US-HI": { ... } }, "viewBox": [0, 0, 1000, 594] },
  "excluded": [ { "name_ja": "プエルトリコ", "name_en": "Puerto Rico", "code": "US-PR", "reason": "..." } ],
  "notes": [ "..." ],
  "regions": [
    { "code": "US-CA", "country": "US", "name_ja": "カリフォルニア州", "name_en": "California",
      "included_in_svg": true, "source_ids": ["USA-3521"], "marker": { "full": false, "mobile": false }, "notes": "" }
  ]
}
```

`regions` の長さは分母と一致します。`excluded` は分母に数えないと決めた領域、`notes` は統合や描画の省略など国ごとの判断の記録です。

### 検証

```console
$ python3 scripts/validate_subdivisions.py
us: OK (US 分母 51)
gb: OK (GB 分母 46)
kr: OK (KR 分母 16)
cn: OK (CN 分母 31)
ca: OK (CA 分母 13)
au: OK (AU 分母 8)
nz: OK (NZ 分母 16)
ie: OK (IE 分母 26)
sg: OK (SG 分母 5)
report -> reports/subdivisions-coverage.md
```

期待値（分母・安定 ID の集合・除外する領域）は検証スクリプトの中に独立して持っており、次のどれかがあると失敗します（終了コード 1）。

* 区分数が分母と違う
* `data-code` の欠落・重複、安定 ID の期待集合や `regions.json` との不一致
* `<title>` が `regions.json` の「name_ja / name_en」と違う
* 塗れない区分（パスもマーカーも無い、または小さすぎてマーカーも無い）
* 区画ファイルに `class="country"` が混ざっている
* 除外すると決めた領域（米国・豪州の海外領域、チャタム諸島、`ie` に入った北アイルランド、シンガポールの計画区域 55、英国の旧 41 地域のコード、統合前の光州広域市・全羅南道、中国の `CN-TW`・`CN-HK`・`CN-MO` と台湾・香港・マカオなど）が分母に数えられている。代表地点（サンフアン、ベルファスト、旧光州市庁、軍威郡、台北、香港、マカオなど）を投影して、入るべき区分に入り、除外した領域はどの区分にも含まれないことも確かめます
* `M` / `L` / `Z` 以外のパスコマンド、`evenodd` でない、マーカーが親の `fill` を継承しない
* mobile が簡略化されていない・線が太くない・マーカーが大きくない、各区分の最大ポリゴンが失われている
* アメリカのはめ込み（アラスカ・ハワイ）が本土と重なる、区切り線が区分を横切る

世界地図の検証（`python3 scripts/validate.py`）とは別のスクリプトです。両方とも成功する状態を保っています。

### ビルド・再生成

```console
$ python3 scripts/build_subdivisions.py         # 全 9 か国（data/ に元データが無ければダウンロード）
$ python3 scripts/build_subdivisions.py us ie   # 指定した国だけ
$ python3 scripts/validate_subdivisions.py
```

依存は Python 3.9+ の標準ライブラリのみです。元データ（約 80MB）はリポジトリに含めません。

### 出典・ライセンス（区画）

本リポジトリのファイル（SVG・JSON・スクリプト）は [MIT License](LICENSE) です。ただし区画の境界は次の地理データに由来し、その利用条件は MIT とは別にかかります。いずれも商用アプリへの同梱と改変が認められています。

| 国 | データ | 版（取得日） | ライセンス | 帰属表示 |
|---|---|---|---|---|
| `us` `ca` `au` `nz` `ie` `cn` | [Natural Earth](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/) 1:10m Admin 1 – States, Provinces（大きな湖を除いた版） | v5.1.2（2026-10-13） | パブリックドメイン | 不要（本リポジトリでは出典として明記） |
| `gb` | [ONS](https://geoportal.statistics.gov.uk/) International Territorial Level 2 (January 2025) Boundaries UK BUC | ITL 2025（2026-10-13） | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | 必要: 「Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right 2025」 |
| `kr` | [vuski/admdongkor](https://github.com/vuski/admdongkor) 行政洞境界 ver20260701（原資料: [統計庁 SGIS](https://sgis.kostat.go.kr)） | 2026-07-01 時点（2026-10-13） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)（原資料は[公共ヌリ第 1 類型](https://www.kogl.or.kr/info/licenseType1.do)） | 必要: 「This data is derived from administrative-dong boundaries released by Statistics Korea SGIS (https://sgis.kostat.go.kr) under KOGL Type 1, modified by vuski/admdongkor (https://github.com/vuski/admdongkor), distributed under CC BY 4.0. Dissolved into 16 first-level divisions by kazutax/world-map-svg.」 |
| `sg` | [URA](https://data.gov.sg/datasets/d_4ce0038f7ac689652350bb91b7fb92ed/view) Master Plan 2025 Region Boundary (No Sea)（data.gov.sg） | Master Plan 2025（2026-10-13） | [Singapore Open Data Licence v1.0](https://data.gov.sg/open-data-licence) | 必要: 「Contains information from Master Plan 2025 Region Boundary (No Sea) accessed on 2026-10-13 from data.gov.sg which is made available under the terms of the Singapore Open Data Licence version 1.0 https://data.gov.sg/open-data-licence」 |

* `gb`・`kr`・`sg` を使うアプリやサイトでは、上の帰属表示を利用者に見える場所（クレジット画面など）に出してください。Singapore Open Data Licence は、URA などの公的機関が推奨・承認しているように見せることも禁じています。
* 帰属表示の文言は各 SVG の `<desc>` と `regions.json` の `source.attribution` にも入れています。

### 免責事項（区画）

区画の地図は「訪問した地域の塗り分け」のための簡略図です。境界線・区分・名称は上記の出典データの解釈に基づき、**国家・地域の境界、帰属、地位に関するいかなる政治的立場も表明するものではありません。**北アイルランドを `gb` に収めているのは英国統計局の地域区分（ITL）に、アイルランドの 26 県は ISO 3166-2:IE に従った、塗り分けの都合による整理です。離島の一部（北西ハワイ諸島、ロードハウ島、マッコーリー島など）は、区分には属したまま描画を省略しています。リアンクール岩礁（独島/竹島）も、この縮尺では表示できない小島のため描画していません。帰属についての立場を示すものではありません。

中国の区画も同じ趣旨の、塗り分けのための簡略図です。台湾・香港・マカオを描かないこと、九段線や南シナ海の島しょを描かないこと、国境の線の引き方は、本リポジトリの世界地図（Natural Earth のデフォルト解釈）にそろえた表示上の整理であり、**いかなる政治的立場も表明するものではありません。**
