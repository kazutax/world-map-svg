const maps = [
  "../map-full.svg",
  "../map-mobile.svg",
  "../map-full-japan-center.svg",
  "../map-mobile-japan-center.svg",
]
const containers = document.querySelectorAll( '.map' )

const visited = new Set()

const updateCount = () => {
  document.querySelector( '#visited-count' ).textContent = visited.size
}

maps.forEach( async ( map, index ) => {
  const res = await fetch( map )

  if ( res.ok ) {
    const svg = await res.text()
    containers[ index ].innerHTML = svg
    const countries = containers[ index ].querySelectorAll( '.world-svg-map .country' )

    countries.forEach( ( country ) => {
      // マウスオーバーで国名と ISO コードを表示
      country.addEventListener( 'mouseover', ( event ) => {
        const g = event.currentTarget
        const title = g.querySelector( 'title' ).textContent
        document.querySelector( '#hover-info' ).textContent = `${title} (${g.dataset.code})`
      } )

      // クリックで訪問済みをトグル (両方の地図に同期)
      country.addEventListener( 'click', ( event ) => {
        const code = event.currentTarget.dataset.code
        if ( visited.has( code ) ) {
          visited.delete( code )
        } else {
          visited.add( code )
        }
        document.querySelectorAll( `.world-svg-map [data-code="${code}"]` ).forEach( ( el ) => {
          el.classList.toggle( 'visited', visited.has( code ) )
        } )
        updateCount()
      } )
    } )
  }
} )
