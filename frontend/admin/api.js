const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function readResponse(response) {
  if (response.ok) return response.json();
  const payload = await response.json().catch(() => ({}));
  throw new Error(payload.detail || `Request failed with status ${response.status}.`);
}

export async function uploadDroneImage(file, projectName) {
  const body = new FormData();
  body.append('file', file);
  body.append('project_name', projectName);
  const response = await fetch(`${API_URL}/api/uploads/drone-image`, { method: 'POST', body });
  return readResponse(response);
}

export async function getUploadStatus(jobId) {
  return readResponse(await fetch(`${API_URL}/api/uploads/${jobId}`));
}

export async function getProjects() {
  return readResponse(await fetch(`${API_URL}/api/projects`));
}

export async function createProject(project) {
  return readResponse(await fetch(`${API_URL}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  }));
}
