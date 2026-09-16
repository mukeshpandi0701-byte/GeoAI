const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function readResponse(response) {
  if (response.ok) return response.json();
  const payload = await response.json().catch(() => ({}));
  throw new Error(payload.detail || `Request failed with status ${response.status}.`);
}

async function request(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error('Could not reach the backend. Start it and check VITE_API_URL.');
  }
}

export async function uploadDroneImage(file, projectName, projectId = '') {
  const body = new FormData();
  body.append('file', file);
  body.append('project_name', projectName);
  if (projectId) body.append('project_id', projectId);
  const response = await request(`${API_URL}/api/uploads/drone-image`, { method: 'POST', body });
  return readResponse(response);
}

export async function getUploadStatus(jobId) {
  return readResponse(await request(`${API_URL}/api/uploads/${jobId}`));
}

export async function getProjects() {
  return readResponse(await request(`${API_URL}/api/projects`));
}

export async function createProject(project) {
  return readResponse(await request(`${API_URL}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  }));
}

export async function getReviewQueue(status = 'review') {
  return readResponse(await request(`${API_URL}/api/review-queue?status=${status}`));
}

export async function updateReviewStatus(jobId, decision) {
  return readResponse(await request(
    `${API_URL}/api/review-queue/${jobId}?decision=${decision}`,
    { method: 'PATCH' },
  ));
}

export async function getProjectUploads(projectId) {
  return readResponse(await request(`${API_URL}/api/projects/${projectId}/uploads`));
}


export async function getProjectFeatures(projectId) {
  return readResponse(await request(
    `${API_URL}/api/features?project_id=${encodeURIComponent(projectId)}`,
  ));

// GIS feature endpoints are intentionally kept behind this small adapter. The GIS
// service owns persistence and publication decisions; the UI never infers them.
export async function getProjectFeatures(projectId, { publishedOnly = false } = {}) {
  const query = publishedOnly ? '?published=true' : '';
  return readResponse(await fetch(`${API_URL}/api/projects/${projectId}/features${query}`));
}

export async function updateFeatureReview(featureId, { decision, notes, geometry }) {
  return readResponse(await fetch(`${API_URL}/api/features/${featureId}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes, ...(geometry ? { geometry } : {}) }),
  }));

}
