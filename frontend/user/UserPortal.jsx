import { useState } from 'react';
import MapCanvas from '../shared/MapCanvas';
import { parcels } from '../shared/mockData';

export default function UserPortal() {
  const [layers, setLayers] = useState({ imagery: true, parcels: true, buildings: true, roads: true });
  return <section><div className="portal-heading"><div><span className="eyebrow">Public data explorer</span><h2>Published parcel map</h2><p>Browse verified cadastral information. Processing controls are available only to administrators.</p></div><input aria-label="Search parcel" placeholder="Search parcel ID" /></div>
    <div className="map-layout"><aside className="panel"><h3>Map layers</h3>{Object.entries(layers).map(([name, enabled]) => <label className="toggle" key={name}><input type="checkbox" checked={enabled} onChange={() => setLayers({ ...layers, [name]: !enabled })}/>{name}</label>)}<hr/><h3>Data status</h3><p className="success">● Published · 14 Sep 2026</p></aside><MapCanvas layers={layers}/></div>
    <section className="data-section"><div><span className="eyebrow">Available records</span><h2>Parcel information</h2></div><div className="cards">{parcels.map(parcel => <article className="card" key={parcel.id}><span className="tag">{parcel.status}</span><h3>{parcel.id}</h3><p>{parcel.owner}</p><dl><div><dt>Area</dt><dd>{parcel.area}</dd></div><div><dt>Land use</dt><dd>{parcel.use}</dd></div></dl></article>)}</div></section>
  </section>;
}
