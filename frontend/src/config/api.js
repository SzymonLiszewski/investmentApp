/**
 * API root for axios/fetch. Override with VITE_API_BASE_URL when needed.
 *
 * In dev we default to Django on port 8000 so the browser calls the API directly
 * (avoids Vite /api proxy issues, e.g. multipart uploads). Production builds use
 * same-origin relative URLs (e.g. behind nginx).
 */
export function getApiRoot() {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw != null && String(raw).trim() !== '') {
    return String(raw).replace(/\/$/, '');
  }
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }
  return '';
}

/** Path must start with / (e.g. /api/token/). Returns absolute URL when getApiRoot() is set. */
export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  const root = getApiRoot();
  return root ? `${root}${p}` : p;
}
