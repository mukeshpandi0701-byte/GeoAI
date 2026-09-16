export default function MapCanvas({ layers }) {
  return <div className="map" role="img" aria-label="Map of Central Ward showing parcel outlines, buildings and roads">
    <div className="map-toolbar"><button aria-label="Zoom in">+</button><button aria-label="Zoom out">−</button><button aria-label="Center map">⌾</button></div>
    <div className="north"><b>N</b><span>↑</span></div><div className="scale"><i />50 m</div>
    <svg viewBox="0 0 720 430" preserveAspectRatio="none">
      {layers.imagery && <><rect width="720" height="430" className="terrain" /><path className="contour" d="M-20 85 Q155 30 315 90T740 62M-15 292 Q110 242 280 303T735 263M82 -10Q128 98 50 212T73 440M640 -15Q581 112 651 212T618 450" /></>}
      {layers.roads && <><path d="M0 170 L720 105" className="road"/><path d="M435 0 L390 430" className="road"/></>}
      {layers.parcels && <g className="parcel"><path d="M45 44L245 27 263 148 80 164Z"/><path d="M267 26L422 14 411 137 264 148Z"/><path d="M460 22L661 8 680 98 431 135Z"/><path d="M85 186L253 174 270 336 54 358Z"/><path d="M281 167L421 155 404 328 276 340Z"/><path d="M443 151L670 121 689 302 422 335Z"/><path d="M74 373L273 350 326 429 43 429Z"/><path d="M337 354L670 318 703 429 333 429Z"/></g>}
      {layers.buildings && <g className="building"><rect x="108" y="72" width="71" height="48"/><rect x="295" y="53" width="75" height="56"/><rect x="504" y="47" width="98" height="43"/><rect x="116" y="224" width="80" height="64"/><rect x="306" y="210" width="62" height="77"/><rect x="504" y="203" width="100" height="70"/></g>}
    </svg><span className="map-label"><i />Central Ward <small>Published view</small></span>
  </div>;
}
