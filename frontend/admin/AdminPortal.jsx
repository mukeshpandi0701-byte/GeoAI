import { useEffect, useState } from 'react';
import MapCanvas from '../shared/MapCanvas';
import { createProject, getProjectFeatures, getProjectUploads, getProjects, getUploadStatus, retryUploadProcessing, reviewGISFeature, uploadDroneImage } from './api';

const blankSummary = { total: 0, building: 0, road: 0, parcel: 0, pending: 0, approved: 0, rejected: 0 };
const formatTime = value => value ? new Date(value).toLocaleString() : 'Not recorded';
function summarize(features) {
  return features.reduce((counts, feature) => {
    const type = feature.properties?.feature_type;
    const status = feature.review_status;
    return { ...counts, total: counts.total + 1, [type]: type in counts ? counts[type] + 1 : counts[type], [status]: status in counts ? counts[status] + 1 : counts[status] };
  }, blankSummary);
}

export default function AdminPortal() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [history, setHistory] = useState([]);
  const [features, setFeatures] = useState([]);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [upload, setUpload] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [projectForm, setProjectForm] = useState({ name: '', description: '', location: '' });
  const [projectMessage, setProjectMessage] = useState('');
  const [reviewError, setReviewError] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const [retryingJobId, setRetryingJobId] = useState('');
  const selectedProject = projects.find(project => project.project_id === projectId);
  const summary = summarize(features);

  async function loadProjects() {
    try {
      const result = await getProjects();
      setProjects(result);
      setProjectId(current => current || result[0]?.project_id || '');
    } catch (error) { setHistoryError(`Unable to load projects: ${error.message}`); }
  }
  async function loadDetail(id = projectId) {
    if (!id) { setHistory([]); setFeatures([]); return; }
    setHistoryLoading(true); setHistoryError(''); setSelectedFeature(null);
    try {
      const [jobs, mapped] = await Promise.all([getProjectUploads(id), getProjectFeatures(id)]);
      setHistory(jobs); setFeatures(mapped);
    } catch (error) {
      setHistory([]); setFeatures([]); setHistoryError(`Unable to load processing history. ${error.message}`);
    } finally { setHistoryLoading(false); }
  }
  useEffect(() => { loadProjects(); }, []);
  useEffect(() => { loadDetail(projectId); }, [projectId]);
  useEffect(() => {
    if (!upload?.job_id || !['queued', 'processing'].includes(upload.status)) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const current = await getUploadStatus(upload.job_id);
        setUpload(current);
        if (current.project_id === projectId) loadDetail(projectId);
      } catch (error) { setUploadError(`Unable to refresh upload status. ${error.message}`); }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [upload?.job_id, upload?.status, projectId]);

  async function submitUpload(event) {
    event.preventDefault();
    if (!projectName.trim() || !file) { setUploadError('Enter a project name and choose an image before uploading.'); return; }
    setUploading(true); setUploadError('');
    try {
      const created = await uploadDroneImage(file, projectName, projectId);
      setUpload(created); setFile(null); event.target.reset();
      if (created.project_id) { setProjectId(created.project_id); await loadDetail(created.project_id); }
    } catch (error) { setUploadError(error.message); } finally { setUploading(false); }
  }
  async function submitProject(event) {
    event.preventDefault();
    if (!projectForm.name.trim()) { setProjectMessage('Enter a project name before creating a project.'); return; }
    try {
      const created = await createProject(projectForm);
      setProjects(current => [created, ...current]); setProjectId(created.project_id); setProjectName(created.project_name);
      setProjectForm({ name: '', description: '', location: '' }); setProjectMessage(`Created ${created.project_name}.`);
    } catch (error) { setProjectMessage(error.message); }
  }
  async function reviewFeature(decision) {
    if (!selectedFeature) return;
    setReviewing(true); setReviewError('');
    try {
      const updated = await reviewGISFeature(selectedFeature.id, decision);
      setFeatures(current => current.map(feature => feature.id === updated.id ? updated : feature)); setSelectedFeature(updated);
    } catch (error) { setReviewError(`Unable to ${decision} this feature. ${error.message}`); } finally { setReviewing(false); }
  }
  async function retryJob(jobId) {
    setRetryingJobId(jobId); setHistoryError('');
    try {
      const updated = await retryUploadProcessing(jobId);
      setUpload(updated);
      await loadDetail(projectId);
    } catch (error) { setHistoryError(`Unable to retry processing. ${error.message}`); }
    finally { setRetryingJobId(''); }
  }

  return <section>
    <div className="portal-heading"><div><span className="eyebrow">Administration workspace</span><h2>Mapping projects</h2><p>Track imagery processing, inspect history, and review extracted GIS features.</p></div></div>
    <div className="admin-grid">
      <form className="panel upload-panel" onSubmit={submitUpload}><h3>New imagery upload</h3><label>Project name<input value={projectName} onChange={event => setProjectName(event.target.value)} /></label><label>Link to project<select value={projectId} onChange={event => setProjectId(event.target.value)}><option value="">No linked project</option>{projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label><label>Drone image<input type="file" accept="image/*,.tif,.tiff" onChange={event => setFile(event.target.files[0])} /></label><button className="primary" disabled={uploading}>{uploading ? 'Uploading image…' : 'Upload image'}</button>{uploadError && <p className="notice" role="alert">{uploadError}</p>}{upload && <p className="notice">Latest upload: {upload.filename} — {upload.status}</p>}</form>
      <form className="panel upload-panel" onSubmit={submitProject}><h3>Create project</h3><label>Project name<input value={projectForm.name} onChange={event => setProjectForm({ ...projectForm, name: event.target.value })} /></label><label>Description<input value={projectForm.description} onChange={event => setProjectForm({ ...projectForm, description: event.target.value })} /></label><label>Location<input value={projectForm.location} onChange={event => setProjectForm({ ...projectForm, location: event.target.value })} /></label><button className="primary">Create project</button>{projectMessage && <p className="notice" role="alert">{projectMessage}</p>}</form>
    </div>
    <section className="data-section panel"><span className="eyebrow">Processing status and history</span><h2>Project activity</h2><label className="feature-project-select">Selected project<select value={projectId} onChange={event => setProjectId(event.target.value)}><option value="">Select a project</option>{projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label>{historyLoading && <p className="notice">Loading processing history...</p>}{historyError && <p className="notice" role="alert">{historyError}</p>}{projectId && !historyLoading && !historyError && (history.length ? <div className="history-list">{history.map((job, index) => <article className="history-item" key={job.job_id}><div><strong>{job.filename}</strong>{index === 0 && <small>Newest</small>}<p>{job.job_id} · <span className={`status ${job.status}`}>{job.status}</span></p></div><div><p>Created: {formatTime(job.timestamp)}</p><p>Started: {formatTime(job.processing_started_timestamp)}</p><p>Completed: {formatTime(job.processing_completed_timestamp)}</p><p>Features: {job.feature_count} · Retries: {job.retry_count}</p>{job.failure_reason && <p className="notice">Failure: {job.failure_reason}</p>}{job.status === 'failed' && <button type="button" disabled={retryingJobId === job.job_id} onClick={() => retryJob(job.job_id)}>{retryingJobId === job.job_id ? 'Retrying…' : 'Retry processing'}</button>}</div></article>)}</div> : <p>No processing history available.</p>)}</section>
    <section className="data-section"><span className="eyebrow">Persisted GIS features</span><h2>Feature summary</h2><div className="admin-grid"><aside className="panel">{[['Total features', summary.total], ['Buildings', summary.building], ['Roads', summary.road], ['Parcels', summary.parcel], ['Pending review', summary.pending], ['Approved', summary.approved], ['Rejected', summary.rejected]].map(([label, count]) => <div className="metric" key={label}><span>{label}</span><strong>{count}</strong></div>)}</aside><div className="feature-review-layout"><MapCanvas layers={{ imagery: true, parcels: true, buildings: true, roads: true }} features={features} projectName={selectedProject?.project_name} onFeatureSelect={setSelectedFeature} /><aside className="panel feature-review-details">{selectedFeature ? <><span className={`status feature-status-${selectedFeature.review_status}`}>{selectedFeature.review_status}</span><h3>{selectedFeature.properties?.feature_type}</h3><p>ID: {selectedFeature.id}</p><p>Upload: {selectedFeature.upload_job_id || 'Not recorded'}</p><p>Geometry: {selectedFeature.geometry?.type}</p>{selectedFeature.review_status === 'pending' && <div className="review-actions"><button type="button" className="primary" disabled={reviewing} onClick={() => reviewFeature('approve')}>Approve</button><button type="button" className="danger-button" disabled={reviewing} onClick={() => reviewFeature('reject')}>Reject</button></div>}{reviewError && <p className="notice" role="alert">{reviewError}</p>}</> : <p>Select a feature from the map to review it.</p>}</aside></div></div></section>
  </section>;
}
