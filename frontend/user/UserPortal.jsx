import { useState } from 'react';
import MapCanvas from '../shared/MapCanvas';
import { parcels } from '../shared/mockData';

const layerLabels = { imagery: 'Aerial imagery', parcels: 'Parcel outlines', buildings: 'Building footprints', roads: 'Road network' };

export default function UserPortal() {
  const [layers, setLayers] = useState({ imagery: true, parcels: true, buildings: true, roads: true });

  return <section className="portal user-portal">
    <div className="portal-heading hero-heading">
      <div><span className="eyebrow">Public map explorer</span><h1>See the shape of<br /><em>the neighbourhood.</em></h1><p>Browse AI-assisted physical feature mapping for Central Ward. Published features are for visual exploration and are not official land records.</p></div>
      <label className="search-field"><span aria-hidden="true">⌕</span><input aria-label="Search parcel" placeholder="Search parcel ID" /><kbd>⌘ K</kbd></label>
    </div>
    <div className="map-layout">
      <aside className="layer-panel">
        <div className="panel-title"><span className="panel-icon">◈</span><div><small>Map controls</small><h2>Layers</h2></div></div>
        <div className="layer-list">{Object.entries(layers).map(([name, enabled]) => <label className="toggle" key={name}><span><input type="checkbox" checked={enabled} onChange={() => setLayers({ ...layers, [name]: !enabled })}/><i /></span>{layerLabels[name]}</label>)}</div>
        <div className="data-status"><span className="live-dot" /><div><small>Dataset status</small><strong>Published · 14 Sep 2026</strong></div></div>
      </aside>
      <MapCanvas layers={layers} />
    </div>
    <section className="data-section">
      <div className="section-heading"><div><span className="eyebrow">Available records</span><h2>Parcel snapshots</h2></div><button className="text-button">View all parcels <span>→</span></button></div>
      <div className="cards">{parcels.map((parcel, index) => <article className="card" key={parcel.id}><div className="card-top"><span className="parcel-number">{String(index + 1).padStart(2, '0')}</span><span className="tag">{parcel.status}</span></div><h3>{parcel.id}</h3><p>{parcel.owner}</p><dl><div><dt>Area</dt><dd>{parcel.area}</dd></div><div><dt>Land use</dt><dd>{parcel.use}</dd></div></dl></article>)}</div>
    </section>
  </section>;
}
