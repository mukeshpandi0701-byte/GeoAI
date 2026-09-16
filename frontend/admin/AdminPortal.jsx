import { useEffect, useState } from 'react';
import { projects, features } from '../shared/mockData';
import { createProject, getProjectFeatures, getProjectUploads, getProjects, getReviewQueue, getUploadStatus, updateFeatureReview, updateReviewStatus, uploadDroneImage } from './api';

export default function AdminPortal() {
const [projectName, setProjectName] = useState('');
const [selectedProjectId, setSelectedProjectId] = useState('');
  const [file, setFile] = useState(null);
  const [upload, setUpload] = useState(null);
const [uploadError, setUploadError] = useState('');
const [uploadFieldError, setUploadFieldError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [apiProjects, setApiProjects] = useState([]);
  const [projectForm, setProjectForm] = useState({ name: '', description: '', location: '' });
const [projectMessage, setProjectMessage] = useState('');
const [creatingProject, setCreatingProject] = useState(false);
const [reviewQueue, setReviewQueue] = useState([]);
const [reviewedItems, setReviewedItems] = useState([]);
const [reviewOpen, setReviewOpen] = useState(false);
const [reviewLoading, setReviewLoading] = useState(false);
const [reviewError, setReviewError] = useState('');
const [reviewFeatures, setReviewFeatures] = useState(features);
const [detailProjectId, setDetailProjectId] = useState('');
const [detailUploads, setDetailUploads] = useState([]);
const [gisFeatures, setGisFeatures] = useState([]);
const [detailLoading, setDetailLoading] = useState(false);
const [detailError, setDetailError] = useState('');
const [featureNotes, setFeatureNotes] = useState({});
  const displayedProjects = apiProjects.length ? apiProjects : projects;
const handleOpenReviewQueue = async () => {
  setReviewOpen(true);
  setReviewLoading(true);
  setReviewError('');

try {
const [queue, approved, rejected] = await Promise.all([
  getReviewQueue(),
  getReviewQueue('approved'),
  getReviewQueue('rejected'),
]);
setReviewQueue(queue);
setReviewedItems([...approved, ...rejected].sort(
  (left, right) => new Date(right.timestamp) - new Date(left.timestamp),
));
  } catch (error) {
    console.error('Review queue error:', error);
    setReviewError(error.message);
  } finally {
    setReviewLoading(false);
  }
};
const closeReviewQueue = () => {
  setReviewOpen(false);
};

const handleReviewDecision = async (jobId, decision) => {
  try {
    const updatedJob = await updateReviewStatus(jobId, decision);

    setReviewQueue(currentQueue =>
      currentQueue.filter(job => job.job_id !== updatedJob.job_id)
    );
    setReviewedItems(currentItems => [updatedJob, ...currentItems]);

    if (decision === 'approved') {
      setReviewFeatures(currentFeatures =>
        currentFeatures.map(feature => {
          if (feature.type === 'Parcel boundaries') {
            return {
              ...feature,
              count: feature.count + 1,
            };
          }

          return feature;
        })
      );
    }
  } catch (error) {
    console.error('Review decision error:', error);
    setReviewError(error.message);
  }
};
  async function loadProjects() {
    try {
      setApiProjects(await getProjects());
    } catch {
      setProjectMessage('Could not load live projects. Showing the sample project list.');
    }
  }

  useEffect(() => { loadProjects(); }, []);

  useEffect(() => {
    if (!detailProjectId) return undefined;
    setDetailLoading(true); setDetailError('');
    Promise.all([getProjectUploads(detailProjectId), getProjectFeatures(detailProjectId)])
      .then(([uploads, response]) => { setDetailUploads(uploads); setGisFeatures(response.features || response || []); })
      .catch(error => setDetailError(error.message))
      .finally(() => setDetailLoading(false));
    return undefined;
  }, [detailProjectId]);

  const reviewFeature = async (feature, decision) => {
    try {
      const featureId = feature.id || feature.properties?.id;
      const updated = await updateFeatureReview(featureId, { decision, notes: featureNotes[featureId] || '' });
      setGisFeatures(current => current.map(item => (item.id || item.properties?.id) === (updated.id || updated.properties?.id) ? updated : item));
    } catch (error) { setDetailError(error.message); }
  };

  useEffect(() => {
    if (!upload?.job_id || upload.status !== 'queued') return undefined;
    const timer = window.setInterval(async () => {
      try {
        setUpload(await getUploadStatus(upload.job_id));
      } catch (error) {
        setUploadError(`Could not check job status: ${error.message}`);
        setUpload(current => ({ ...current, status: 'error' }));
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [upload?.job_id, upload?.status]);

  async function submit(event) {
    event.preventDefault();
    const supportedFile = file && /\.(jpe?g|png|gif|webp|tiff?)$/i.test(file.name);
    if (!projectName.trim()) {
      setUploadFieldError('Enter a project name before uploading imagery.');
      return;
    }
    if (!file) {
      setUploadFieldError('Choose an image file before uploading.');
      return;
    }
    if (!supportedFile) {
      setUploadFieldError('Choose a JPG, PNG, GIF, WEBP, or TIFF image file.');
      return;
    }
    setUploading(true);
    setUploadError('');
    setUploadFieldError('');
    setUpload(null);
    try {
      const result = await uploadDroneImage(file, projectName, selectedProjectId);
      setUpload(result);
      setProjectName('');
      setSelectedProjectId('');
      setFile(null);
      event.target.reset();
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
    }
  }

  async function submitProject(event) {
    event.preventDefault();
    setProjectMessage('');
    if (!projectForm.name.trim()) {
      setProjectMessage('Enter a project name before creating a project.');
      return;
    }
    setCreatingProject(true);
    try {
      const project = await createProject(projectForm);
      setApiProjects(current => [project, ...current]);
      setProjectForm({ name: '', description: '', location: '' });
      setProjectMessage(`Created ${project.project_name}.`);
    } catch (error) {
      setProjectMessage(error.message);
    } finally {
      setCreatingProject(false);
    }
  }

  return <section><div className="portal-heading"><div><span className="eyebrow">Administration workspace</span><h2>Mapping projects</h2><p>Upload imagery, monitor mock processing, and review extracted cadastral features.</p></div></div>
    <div className="admin-grid"><form className="panel upload-panel" onSubmit={submit}><h3>New imagery upload</h3><label>Project name<input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. East Ward Survey" aria-invalid={Boolean(uploadFieldError)} /></label><label>Link to project<select value={selectedProjectId} onChange={e => setSelectedProjectId(e.target.value)}><option value="">No linked project</option>{apiProjects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label><label>Drone image<input type="file" accept="image/*,.tif,.tiff" onChange={e => setFile(e.target.files[0])} aria-invalid={Boolean(uploadFieldError)} /></label><button className="primary" disabled={uploading}>{uploading ? 'Uploading image…' : 'Upload image'}</button>{uploadFieldError && <p className="notice" role="alert">{uploadFieldError}</p>}{uploadError && <p className="notice" role="alert">{uploadError}</p>}{upload && <div className="notice upload-result"><strong>Upload {upload.status}</strong><span>Job ID: {upload.job_id}</span><span>File: {upload.filename} · {upload.size} bytes</span><span>Status: {upload.status}</span>{upload.project_id && <span>Linked project: {upload.project_id}</span>}</div>}</form>
      <aside className="panel"><h3>Feature review</h3>{reviewFeatures.map(feature => (
  <div className="metric" key={feature.type}>
    <span>{feature.type}</span>
    <strong>{feature.count}</strong>
  </div>
))}<button type="button" onClick={handleOpenReviewQueue}>
  Open review queue
</button></aside></div>
    {reviewOpen && (
  <div className="review-overlay">
    <div className="review-modal">
      <div className="review-modal-header">
        <div>
          <span className="eyebrow">Administration</span>
          <h2>Review queue</h2>
          <p>Review uploaded drone imagery before publishing.</p>
        </div>

        <button
          type="button"
          className="close-button"
          onClick={closeReviewQueue}
        >
          ✕
        </button>
      </div>

      {reviewLoading && (
        <p className="notice">Loading review items...</p>
      )}

      {reviewError && (
        <p className="notice">{reviewError}</p>
      )}

      {!reviewLoading && !reviewError && reviewQueue.length === 0 && (
        <div className="empty-review">
          <h3>No images waiting for review</h3>
          <p>Upload a drone image to create a new review item.</p>
        </div>
      )}

      {!reviewLoading && reviewQueue.length > 0 && (
        <div className="review-list">
          {reviewQueue.map(job => (
            <article className="review-card" key={job.job_id}>
              <div className="review-card-icon">
                🛰️
              </div>

              <div className="review-card-content">
                <h3>{job.project_name}</h3>

                <p className="review-filename">
                  {job.filename}
                </p>

                <div className="review-meta">
                  <span>
                    <strong>Job ID:</strong> {job.job_id}
                  </span>

                  <span>
                    <strong>File size:</strong>{' '}
                    {(job.size / 1024).toFixed(2)} KB
                  </span>

                  <span>
                    <strong>Uploaded:</strong>{' '}
                    {new Date(job.timestamp).toLocaleString()}
                  </span>
                </div>

                <span className="review-status">
                  {job.status}
                </span>

                <div className="review-actions">
                  <button
                    type="button"
                    className="primary"
                    onClick={() =>
                      handleReviewDecision(job.job_id, 'approved')
                    }
                  >
                    ✓ Approve
                  </button>

                  <button
                    type="button"
                    className="danger-button"
                    onClick={() =>
                      handleReviewDecision(job.job_id, 'rejected')
                    }
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {!reviewLoading && reviewedItems.length > 0 && (
        <section className="review-history">
          <h3>Reviewed imagery</h3>
          <p>Approved and rejected items remain available here after a decision.</p>
          <div className="review-list">
            {reviewedItems.map(job => (
              <article className="review-card" key={job.job_id}>
                <div className="review-card-icon">🛰️</div>
                <div className="review-card-content">
                  <h3>{job.project_name}</h3>
                  <p className="review-filename">{job.filename}</p>
                  <span className="review-status">{job.status}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  </div>
)}

    <section className="data-section"><span className="eyebrow">Project management</span><h2>Processing status</h2><form className="panel upload-panel" onSubmit={submitProject}><h3>Create project</h3><label>Project name<input value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} placeholder="e.g. East Ward Survey" /></label><label>Description<input value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Optional survey details" /></label><label>Location<input value={projectForm.location} onChange={e => setProjectForm({ ...projectForm, location: e.target.value })} placeholder="Optional ward or area" /></label><button className="primary">Create project</button>{projectMessage && <p className="notice">{projectMessage}</p>}</form><div className="project-list">{displayedProjects.map(project => { const liveProject = Boolean(project.project_id); const id = liveProject ? project.project_id : project.id; const name = liveProject ? project.project_name : project.name; const date = liveProject ? new Date(project.created_timestamp).toLocaleDateString() : project.date; const status = project.status; const progress = liveProject ? 0 : project.progress; const uploadSummary = project.upload_summary; return <article className="project" key={id}><div><h3>{name}</h3><p>{id} · {date} · {liveProject ? (project.location || 'No location') : `${project.parcels || '—'} parcels`}</p>{uploadSummary && <small>{uploadSummary.total} uploads · {uploadSummary.review} awaiting review · {uploadSummary.approved} approved · {uploadSummary.rejected} rejected</small>}</div><div className="progress-wrap"><span className={`status ${status.toLowerCase()}`}>{status}</span><div className="progress"><i style={{ width: `${progress}%` }} /></div><small>{liveProject ? 'View upload history in the review queue' : `${progress}% complete`}</small></div></article>; })}</div></section>

    <section className="data-section panel"><span className="eyebrow">Project detail and history</span><h2>Review a project</h2><label>Selected project<select value={detailProjectId} onChange={event => setDetailProjectId(event.target.value)}><option value="">Select a live project</option>{apiProjects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select></label>{detailLoading && <p className="notice">Loading project history…</p>}{detailError && <p className="notice" role="alert">{detailError}</p>}{detailProjectId && !detailLoading && <><h3>Upload decisions</h3>{detailUploads.length ? <div className="history-list">{detailUploads.map(upload => <p key={upload.job_id}><strong>{upload.filename}</strong> — <span className={`status ${upload.status}`}>{upload.status}</span> {upload.reviewed_timestamp && `reviewed ${new Date(upload.reviewed_timestamp).toLocaleString()}`}</p>)}</div> : <p>No uploads have been linked to this project.</p>}<h3>Individual GIS feature review</h3><p className="notice">Feature decisions are persisted by the GIS API. Geometry editing appears only when that API accepts a geometry update.</p>{gisFeatures.length ? <div className="feature-review-list">{gisFeatures.map((feature, index) => { const id = feature.id || feature.properties?.id || `${feature.properties?.feature_type}-${index}`; const type = feature.properties?.feature_type || feature.feature_type || 'feature'; const status = feature.properties?.review_status || feature.review_status || 'review'; return <article className="feature-review" key={id}><div><strong>{type[0].toUpperCase() + type.slice(1)} #{index + 1}</strong><p>Decision: {status}</p></div><textarea aria-label={`Notes for ${type} ${index + 1}`} value={featureNotes[id] || ''} onChange={event => setFeatureNotes(current => ({ ...current, [id]: event.target.value }))} placeholder="Reviewer notes" /><div className="review-actions"><button type="button" className="primary" onClick={() => reviewFeature(feature, 'accepted')}>Accept</button><button type="button" className="danger-button" onClick={() => reviewFeature(feature, 'rejected')}>Reject</button></div></article>; })}</div> : <p>No GIS features are ready for individual review.</p>}</>}</section>
  </section>;
=======
</section>;
=======
    <section className="data-section"><span className="eyebrow">Project management</span><h2>Processing status</h2><form className="panel upload-panel" onSubmit={submitProject}><h3>Create project</h3><label>Project name<input value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} placeholder="e.g. East Ward Survey" aria-invalid={projectMessage.startsWith('Enter a project name')} /></label><label>Description<input value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Optional survey details" /></label><label>Location<input value={projectForm.location} onChange={e => setProjectForm({ ...projectForm, location: e.target.value })} placeholder="Optional ward or area" /></label><button className="primary" disabled={creatingProject}>{creatingProject ? 'Creating project…' : 'Create project'}</button>{projectMessage && <p className="notice" role="alert">{projectMessage}</p>}</form><div className="project-list">{displayedProjects.map(project => { const liveProject = Boolean(project.project_id); const id = liveProject ? project.project_id : project.id; const name = liveProject ? project.project_name : project.name; const date = liveProject ? new Date(project.created_timestamp).toLocaleDateString() : project.date; const status = project.status; const progress = liveProject ? 0 : project.progress; const uploadSummary = project.upload_summary; return <article className="project" key={id}><div><h3>{name}</h3><p>{id} · {date} · {liveProject ? (project.location || 'No location') : `${project.parcels || '—'} parcels`}</p>{uploadSummary && <small>{uploadSummary.total} uploads · {uploadSummary.review} awaiting review · {uploadSummary.approved} approved · {uploadSummary.rejected} rejected</small>}</div><div className="progress-wrap"><span className={`status ${status.toLowerCase()}`}>{status}</span><div className="progress"><i style={{ width: `${progress}%` }} /></div><small>{liveProject ? 'View upload history in the review queue' : `${progress}% complete`}</small></div></article>; })}</div></section>
  </section>;

}
