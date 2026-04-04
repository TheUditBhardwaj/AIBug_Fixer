import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE, timeout: 300_000 });

export async function analyzeCode(code, filename, useRag = true) {
  const { data } = await api.post('/analyze-code', { code, filename, use_rag: useRag });
  return data;
}

export async function analyzeFile(file) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/analyze-file', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function analyzeRepo(repoUrl, branch = 'main') {
  const { data } = await api.post('/analyze-repo', { repo_url: repoUrl, branch });
  return data;
}

export async function checkHealth() {
  const { data } = await api.get('/health', { timeout: 5000 });
  return data;
}
