import { useEffect, useState } from 'react';
import { projects, features } from '../shared/mockData';
import { createProject, getProjects, getUploadStatus, uploadDroneImage } from './api';

export default function AdminPortal() {
  const [projectName, setProjectName] = useState('');
  const [file, setFile] = useState(null);
  const [upload, setUpload] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [apiProjects, setApiProjects] = useState([]);
  const [projectForm, setProjectForm] = useState({ name: '', description: '', location: '' });
  const [projectMessage, setProjectMessage] = useState('');

  const displayedProjects = apiProjects.length ? apiProjects : projects;

  async function loadProjects() {
    try {
      setApiProjects(await getProjects());
    } catch {
      setProjectMessage('Could not load live projects. Showing the sample project list.');
    }
  }

  useEffect(() => { loadProjects(); }, []);

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
    if (!file || !projectName) return setUploadError('Add a project name and drone image first.');
    setUploading(true);
    setUploadError('');
    setUpload(null);
    try {
      const result = await uploadDroneImage(file, projectName);
      setUpload(result);
      setProjectName('');
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
    try {
      const project = await createProject(projectForm);
      setApiProjects(current => [project, ...current]);
      setProjectForm({ name: '', description: '', location: '' });
      setProjectMessage(`Created ${project.project_name}.`);
    } catch (error) {
      setProjectMessage(error.message);
    }
  }

  return <section className="portal admin-portal"><div className="portal-heading admin-heading"><div><span className="eyebrow">Operations workspace</span><h1>Turn imagery into<br /><em>map-ready insight.</em></h1><p>Bring in survey imagery, follow processing, and review AI-assisted physical feature layers in one place.</p></div><div className="workspace-summary"><span>Active projects</span><strong>{displayedProjects.length}</strong><small>Across your workspace</small></div></div>
    <div className="admin-grid"><form className="panel upload-panel" onSubmit={submit}><div className="panel-title"><span className="panel-icon">↑</span><div><small>Step 01</small><h2>New imagery upload</h2></div></div><p className="panel-copy">Start a mapping run by connecting its project to a drone image.</p><label>Project name<input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. East Ward Survey" /></label><label className="file-label">Drone image<input type="file" accept="image/*,.tif,.tiff" onChange={e => setFile(e.target.files[0])} /><span>{file ? file.name : 'Choose an image or TIFF file'}<small>JPG, PNG, WEBP or TIFF</small></span></label><button className="primary" disabled={uploading}>{uploading ? 'Uploading image…' : 'Start upload'} <span>→</span></button>{uploadError && <p className="notice">{uploadError}</p>}{upload && <div className="notice upload-result"><strong>Upload {upload.status}</strong><span>Job ID: {upload.job_id}</span><span>File: {upload.filename} · {upload.size} bytes</span></div>}</form>
      <aside className="panel review-panel"><div className="panel-title"><span className="panel-icon">✦</span><div><small>Feature inventory</small><h2>Ready for review</h2></div></div><p className="panel-copy">A clear overview of extracted physical map layers.</p><div className="metrics">{features.map((feature, index) => <div className="metric" key={feature.type}><span className={`metric-icon metric-${index}`}>{index === 0 ? '⌁' : index === 1 ? '□' : '—'}</span><span>{feature.type}</span><strong>{feature.count}</strong></div>)}</div><button className="secondary">Open review queue <span>→</span></button></aside></div>
    <section className="data-section"><div className="section-heading"><div><span className="eyebrow">Project management</span><h2>Mapping activity</h2></div><span className="status-summary"><i />{displayedProjects.length} projects tracked</span></div><div className="project-section"><form className="panel upload-panel project-form" onSubmit={submitProject}><h3>Create a project</h3><label>Project name<input value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} placeholder="e.g. East Ward Survey" /></label><label>Description<input value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Optional survey details" /></label><label>Location<input value={projectForm.location} onChange={e => setProjectForm({ ...projectForm, location: e.target.value })} placeholder="Optional ward or area" /></label><button className="secondary">Create project <span>→</span></button>{projectMessage && <p className="notice">{projectMessage}</p>}</form><div className="project-list">{displayedProjects.map(project => { const liveProject = Boolean(project.project_id); const id = liveProject ? project.project_id : project.id; const name = liveProject ? project.project_name : project.name; const date = liveProject ? new Date(project.created_timestamp).toLocaleDateString() : project.date; const status = project.status; const progress = liveProject ? 0 : project.progress; return <article className="project" key={id}><div className="project-code">{name.split(' ').map(word => word[0]).slice(0, 2).join('')}</div><div className="project-details"><h3>{name}</h3><p>{id} · {date} · {liveProject ? (project.location || 'No location') : `${project.parcels || '—'} parcels`}</p></div><div className="progress-wrap"><span className={`status ${status.toLowerCase()}`}>{status}</span><div className="progress"><i style={{ width: `${progress}%` }} /></div><small>{liveProject ? 'Awaiting imagery upload' : `${progress}% complete`}</small></div></article>; })}</div></div></section>
  </section>;
}
