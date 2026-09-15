import { useState } from 'react';
import { projects, features } from '../shared/mockData';
import { uploadDroneImage } from './api';

export default function AdminPortal() {
  const [projectName, setProjectName] = useState(''); const [file, setFile] = useState(null); const [message, setMessage] = useState(''); const [uploading, setUploading] = useState(false);
  async function submit(event) { event.preventDefault(); if (!file || !projectName) return setMessage('Add a project name and drone image first.'); setUploading(true); setMessage(''); try { const result = await uploadDroneImage(file, projectName); setMessage(`Uploaded ${result.filename}. Processing has been queued (mock).`); setProjectName(''); setFile(null); event.target.reset(); } catch (error) { setMessage(`${error.message} You can still review the mock projects below.`); } finally { setUploading(false); } }
  return <section><div className="portal-heading"><div><span className="eyebrow">Administration workspace</span><h2>Mapping projects</h2><p>Upload imagery, monitor mock processing, and review extracted cadastral features.</p></div></div>
    <div className="admin-grid"><form className="panel upload-panel" onSubmit={submit}><h3>New imagery upload</h3><label>Project name<input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. East Ward Survey" /></label><label>Drone image<input type="file" accept="image/*,.tif,.tiff" onChange={e => setFile(e.target.files[0])} /></label><button className="primary" disabled={uploading}>{uploading ? 'Uploading…' : 'Upload image'}</button>{message && <p className="notice">{message}</p>}</form>
      <aside className="panel"><h3>Feature review</h3>{features.map(feature => <div className="metric" key={feature.type}><span>{feature.type}</span><strong>{feature.count}</strong></div>)}<button>Open review queue</button></aside></div>
    <section className="data-section"><span className="eyebrow">Project management</span><h2>Processing status</h2><div className="project-list">{projects.map(project => <article className="project" key={project.id}><div><h3>{project.name}</h3><p>{project.id} · {project.date} · {project.parcels || '—'} parcels</p></div><div className="progress-wrap"><span className={`status ${project.status.toLowerCase()}`}>{project.status}</span><div className="progress"><i style={{ width: `${project.progress}%` }} /></div><small>{project.progress}% complete</small></div></article>)}</div></section>
  </section>;
}
