import { lazy, Suspense, useEffect, useState } from 'react';
import { getProjectFeatures, getProjects } from '../admin/api';

const ProjectMap = lazy(() => import('../shared/ProjectMap'));

export default function UserPortal() {
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
  </section>;
}
