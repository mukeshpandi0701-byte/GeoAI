import { useEffect, useState } from 'react';
import MapCanvas from '../shared/MapCanvas';
import { getProjectFeatures, getProjects } from '../admin/api';

const layerLabels = { imagery: 'Aerial imagery', parcels: 'Parcel outlines', buildings: 'Building footprints', roads: 'Road network' };

export default function UserPortal() {
  const [layers, setLayers] = useState({ imagery: true, parcels: true, buildings: true, roads: true });
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getProjects().then(result => {
      setProjects(result);
      setProjectId(result[0]?.project_id || '');
    }).catch(apiError => setError(`Could not load projects: ${apiError.message}`)).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getProjectFeatures(projectId).then(setFeatures).catch(apiError => setError(`Could not load mapped features: ${apiError.message}`)).finally(() => setLoading(false));
  }, [projectId]);

  const selectedProject = projects.find(project => project.project_id === projectId);
  return <section className="portal user-portal"><div className="portal-heading hero-heading"><div><span className="eyebrow">Public map explorer</span><h1>See the shape of<br /><em>the neighbourhood.</em></h1><p>Browse AI-assisted physical feature mapping. These are not official cadastral boundaries.</p></div><label className="search-field"><select aria-label="Select project" value={projectId} onChange={event => setProjectId(event.target.value)}><option value="">Select a project</option>{projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label></div>{error && <p className="notice" role="alert">{error}</p>}<div className="map-layout"><aside className="layer-panel"><div className="panel-title"><span className="panel-icon">◈</span><div><small>Map controls</small><h2>Layers</h2></div></div><div className="layer-list">{Object.entries(layers).map(([name, enabled]) => <label className="toggle" key={name}><span><input type="checkbox" checked={enabled} onChange={() => setLayers(current => ({ ...current, [name]: !enabled }))} /><i /></span>{layerLabels[name]}</label>)}</div></aside><MapCanvas layers={layers} features={features} loading={loading} error={error} projectName={selectedProject?.project_name} /></div></section>;
}
