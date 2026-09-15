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

  return <section><div className="portal-heading"><div><span className="eyebrow">Administration workspace</span><h2>Mapping projects</h2><p>Upload imagery, monitor mock processing, and review extracted cadastral features.</p></div></div>
    <div className="admin-grid"><form className="panel upload-panel" onSubmit={submit}><h3>New imagery upload</h3><label>Project name<input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. East Ward Survey" /></label><label>Drone image<input type="file" accept="image/*,.tif,.tiff" onChange={e => setFile(e.target.files[0])} /></label><button className="primary" disabled={uploading}>{uploading ? 'Uploading image…' : 'Upload image'}</button>{uploadError && <p className="notice">{uploadError}</p>}{upload && <div className="notice upload-result"><strong>Upload {upload.status}</strong><span>Job ID: {upload.job_id}</span><span>File: {upload.filename} · {upload.size} bytes</span><span>Status: {upload.status}</span></div>}</form>
      <aside className="panel"><h3>Feature review</h3>{features.map(feature => <div className="metric" key={feature.type}><span>{feature.type}</span><strong>{feature.count}</strong></div>)}<button>Open review queue</button></aside></div>
    <section className="data-section"><span className="eyebrow">Project management</span><h2>Processing status</h2><form className="panel upload-panel" onSubmit={submitProject}><h3>Create project</h3><label>Project name<input value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} placeholder="e.g. East Ward Survey" /></label><label>Description<input value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Optional survey details" /></label><label>Location<input value={projectForm.location} onChange={e => setProjectForm({ ...projectForm, location: e.target.value })} placeholder="Optional ward or area" /></label><button className="primary">Create project</button>{projectMessage && <p className="notice">{projectMessage}</p>}</form><div className="project-list">{displayedProjects.map(project => { const liveProject = Boolean(project.project_id); const id = liveProject ? project.project_id : project.id; const name = liveProject ? project.project_name : project.name; const date = liveProject ? new Date(project.created_timestamp).toLocaleDateString() : project.date; const status = project.status; const progress = liveProject ? 0 : project.progress; return <article className="project" key={id}><div><h3>{name}</h3><p>{id} · {date} · {liveProject ? (project.location || 'No location') : `${project.parcels || '—'} parcels`}</p></div><div className="progress-wrap"><span className={`status ${status.toLowerCase()}`}>{status}</span><div className="progress"><i style={{ width: `${progress}%` }} /></div><small>{liveProject ? 'Awaiting imagery upload' : `${progress}% complete`}</small></div></article>; })}</div></section>
  </section>;
}
