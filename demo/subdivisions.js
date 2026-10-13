const countries = [
  { key: "us", label: "アメリカ" },
  { key: "gb", label: "イギリス" },
  { key: "ca", label: "カナダ" },
  { key: "au", label: "オーストラリア" },
  { key: "nz", label: "ニュージーランド" },
  { key: "ie", label: "アイルランド" },
  { key: "sg", label: "シンガポール" },
]

const state = { country: "us", variant: "mobile" }
// 国ごとの訪問済み data-code (full / mobile を切り替えても保持する)
const visited = {}

const countryBox = document.querySelector( '#countries' )
countries.forEach( ( c ) => {
  const button = document.createElement( 'button' )
  button.type = 'button'
  button.dataset.country = c.key
  button.textContent = `${c.label} (${c.key})`
  countryBox.appendChild( button )
} )

const setPressed = ( selector, attr, value ) => {
  document.querySelectorAll( selector ).forEach( ( b ) => {
    b.setAttribute( 'aria-pressed', String( b.dataset[ attr ] === value ) )
  } )
}

const updateCount = () => {
  document.querySelector( '#visited-count' ).textContent = visited[ state.country ].size
}

const render = async () => {
  const { country, variant } = state
  visited[ country ] = visited[ country ] || new Set()
  setPressed( '#countries button', 'country', country )
  setPressed( '#variants button', 'variant', variant )

  const file = `../subdivisions/${country}/map-${variant}.svg`
  const [ svgRes, jsonRes ] = await Promise.all( [
    fetch( file ),
    fetch( `../subdivisions/${country}/regions.json` ),
  ] )
  if ( !svgRes.ok || !jsonRes.ok ) return
  const meta = await jsonRes.json()
  const container = document.querySelector( '#map' )
  container.innerHTML = await svgRes.text()

  document.querySelector( '#map-title' ).textContent =
    `${meta.country_name_ja}：${meta.division_ja}（分母 ${meta.denominator}）`
  document.querySelector( '#map-file' ).textContent =
    `subdivisions/${country}/map-${variant}.svg ／ ID: ${meta.id_scheme}`
  document.querySelector( '#map-source' ).textContent =
    `出典: ${meta.source.name}（${meta.source.version}、${meta.source.license}）`
  document.querySelector( '#total-count' ).textContent = meta.denominator
  document.querySelector( '#hover-info' ).textContent = '－'
  document.querySelector( '#clicked-code' ).textContent = '－'
  updateCount()

  container.querySelectorAll( '.subdivision-svg-map .region' ).forEach( ( region ) => {
    region.classList.toggle( 'visited', visited[ country ].has( region.dataset.code ) )

    // マウスオーバーで区分名と data-code を表示
    region.addEventListener( 'mouseover', ( event ) => {
      const g = event.currentTarget
      const title = g.querySelector( 'title' ).textContent
      document.querySelector( '#hover-info' ).textContent = `${title} (${g.dataset.code})`
    } )

    // クリックで data-code を表示し、訪問済みをトグル
    region.addEventListener( 'click', ( event ) => {
      const g = event.currentTarget
      const code = g.dataset.code
      document.querySelector( '#clicked-code' ).textContent = code
      if ( visited[ country ].has( code ) ) {
        visited[ country ].delete( code )
      } else {
        visited[ country ].add( code )
      }
      g.classList.toggle( 'visited', visited[ country ].has( code ) )
      updateCount()
    } )
  } )
}

document.querySelectorAll( '#countries button' ).forEach( ( b ) => {
  b.addEventListener( 'click', () => {
    state.country = b.dataset.country
    render()
  } )
} )
document.querySelectorAll( '#variants button' ).forEach( ( b ) => {
  b.addEventListener( 'click', () => {
    state.variant = b.dataset.variant
    render()
  } )
} )

render()
