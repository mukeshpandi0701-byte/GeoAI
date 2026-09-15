const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function uploadDroneImage(file, projectName) {
  const body = new FormData(); body.append('file', file); body.append('project_name', projectName);
  const response = await fetch(`${API_URL}/api/uploads/drone-image`, { method: 'POST', body });
  if (!response.ok) throw new Error('Upload failed. Is the backend running?');
  return response.json();
}
