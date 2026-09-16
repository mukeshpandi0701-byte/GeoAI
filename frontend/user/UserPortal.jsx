import { useEffect, useState } from 'react';
import MapCanvas from '../shared/MapCanvas';
import { getProjectFeatures, getProjects } from '../admin/api';

const layerLabels = { imagery: 'Aerial imagery', parcels: 'Parcel outlines', buildings: 'Building footprints', roads: 'Road network' };

export default function UserPortal() {
  const [layers, setLayers] = useState({ imagery: true, parcels: true, buildings: true, roads: true });
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [features, setFeatures] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [featuresLoading, setFeaturesLoading] = useState(false);
  const [featureError, setFeatureError] = useState('');
  const [selectedFeature, setSelectedFeature] = useState(null);

  useEffect(() => {
    let active = true;
    getProjects()
      .then(result => {
        if (!active) return;
        setProjects(result);
        setSelectedProjectId(result[0]?.project_id || '');
      })
      .catch(error => active && setFeatureError(`Could not load projects: ${error.message}`))
      .finally(() => active && setProjectsLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedProjectId) {
      setFeatures([]);
      return undefined;
    }
    let active = true;
    setFeaturesLoading(true);
    setFeatureError('');
    setSelectedFeature(null);
    getProjectFeatures(selectedProjectId)
      .then(result => active && setFeatures(result))
      .catch(error => active && setFeatureError(`Could not load mapped features: ${error.message}`))
      .finally(() => active && setFeaturesLoading(false));
    return () => { active = false; };
  }, [selectedProjectId]);

  const selectedProject = projects.find(project => project.project_id === selectedProjectId);
  const parcelFeatures = features.filter(feature => feature.properties?.feature_type === 'parcel');

  return <section className="portal user-portal">
    <div className="portal-heading hero-heading">
      <div><span className="eyebrow">Public map explorer</span><h1>See the shape of<br /><em>the neighbourhood.</em></h1><p>Browse AI-assisted physical feature mapping for Central Ward. Published features are for visual exploration and are not official land records.</p></div>
      <label className="search-field"><span aria-hidden="true">⌕</span><select aria-label="Select project" value={selectedProjectId} onChange={event => setSelectedProjectId(event.target.value)} disabled={projectsLoading || !projects.length}><option value="">{projectsLoading ? 'Loading projects…' : 'Select a project'}</option>{projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label>
    </div>
    <div className="map-layout">
      <aside className="layer-panel">
        <div className="panel-title"><span className="panel-icon">◈</span><div><small>Map controls</small><h2>Layers</h2></div></div>
        <div className="layer-list">{Object.entries(layers).map(([name, enabled]) => <label className="toggle" key={name}><span><input type="checkbox" checked={enabled} onChange={() => setLayers({ ...layers, [name]: !enabled })}/><i /></span>{layerLabels[name]}</label>)}</div>
        <div className="data-status"><span className="live-dot" /><div><small>Dataset status</small><strong>{selectedProject ? `${features.length} mapped features` : 'Select a project'}</strong></div></div>
        {selectedFeature && <div className="feature-details"><small>Selected feature</small><strong>{selectedFeature.properties?.feature_type}</strong><span>ID: {selectedFeature.id}</span><span>Project: {selectedFeature.project_id}</span><span>Upload: {selectedFeature.upload_job_id || 'Not recorded'}</span><span>Geometry: {selectedFeature.geometry?.type}</span></div>}
      </aside>
      <MapCanvas layers={layers} features={features} loading={featuresLoading || projectsLoading} error={featureError} projectName={selectedProject?.project_name} onFeatureSelect={setSelectedFeature} />
    </div>
    <section className="data-section">
      <div className="section-heading"><div><span className="eyebrow">Available records</span><h2>Mapped parcel features</h2></div></div>
      {!featuresLoading && selectedProject && parcelFeatures.length === 0 && <p className="notice">No parcel features are available for this project.</p>}
      <div className="cards">{parcelFeatures.map((feature, index) => <article className="card" key={feature.id}><div className="card-top"><span className="parcel-number">{String(index + 1).padStart(2, '0')}</span><span className="tag">{feature.review_status}</span></div><h3>{feature.id}</h3><p>Project: {feature.project_id}</p><dl><div><dt>Geometry</dt><dd>{feature.geometry?.type}</dd></div><div><dt>Upload</dt><dd>{feature.upload_job_id || 'Not recorded'}</dd></div></dl></article>)}</div>
    </section>
  </section>;
}
