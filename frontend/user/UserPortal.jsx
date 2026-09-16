import { lazy, Suspense, useEffect, useState } from 'react';
import { getProjectFeatures, getProjects } from '../admin/api';

const ProjectMap = lazy(() => import('../shared/ProjectMap'));

const layerLabels = { imagery: 'Aerial imagery', parcels: 'Parcel outlines', buildings: 'Building footprints', roads: 'Road network' };

export default function UserPortal() {
<<<<<<< HEAD
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [featureData, setFeatureData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [layers, setLayers] = useState({ building: true, road: true, parcel: true });
  const selectedProject = projects.find(project => project.project_id === projectId);

  useEffect(() => {
    getProjects().then(items => {
      const published = items.filter(project => project.status === 'published');
      setProjects(published);
      setProjectId(published[0]?.project_id || '');
    }).catch(apiError => setError(apiError.message)).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    if (!projectId) return undefined;
    setFeatureData(null);
    getProjectFeatures(projectId, { publishedOnly: true }).then(setFeatureData).catch(apiError => setError(`Could not load published features: ${apiError.message}`));
    return undefined;
  }, [projectId]);

  return <section><div className="portal-heading"><div><span className="eyebrow">Public data explorer</span><h2>Published project map</h2><p>Only reviewed and published physical mapping features are shown. Indicative parcels are not legal cadastral boundaries.</p></div></div>
    {error && <p className="notice" role="alert">{error}</p>}
    {loading ? <p className="notice">Loading published projects…</p> : projects.length === 0 ? <div className="panel empty-state"><h3>No published projects</h3><p>Published GIS data will appear here once it has completed review.</p></div> : <div className="map-layout"><aside className="panel"><label>Project<select value={projectId} onChange={event => setProjectId(event.target.value)}>{projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label><h3>Map layers</h3>{Object.entries(layers).map(([name, enabled]) => <label className="toggle" key={name}><input type="checkbox" checked={enabled} onChange={() => setLayers(current => ({ ...current, [name]: !current[name] }))} />{name === 'parcel' ? 'indicative parcels' : `${name}s`}</label>)}<hr /><h3>Data status</h3><p className="success">● {selectedProject?.status || 'published'}</p></aside><Suspense fallback={<div className="map-empty">Loading map viewer…</div>}><ProjectMap project={selectedProject} featureData={featureData} layers={layers} /></Suspense></div>}
    {selectedProject && <section className="data-section panel"><span className="eyebrow">Project information</span><h3>{selectedProject.project_name}</h3><p>{selectedProject.description || 'No project description provided.'}</p><p>{selectedProject.location || 'No location label provided.'}</p></section>}
=======
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
>>>>>>> 0f0e1eda2bfed970d4f86c46662fb09721e2fda5
  </section>;
}
