class ApiClient {
  constructor() {
    this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  }
  headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    if (this.csrfToken) h['X-CSRFToken'] = this.csrfToken;
    return h;
  }
  async request(method, url, body = null) {
    const opts = { method, headers: this.headers(), credentials: 'same-origin' };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    let data = null;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) data = await res.json();
    else data = await res.text();
    if (!res.ok) {
      const msg = (data && data.error) ? data.error : (typeof data === 'string' ? data : 'Request failed');
      throw new Error(msg);
    }
    return data;
  }
  get(url) { return this.request('GET', url); }
  post(url, body) { return this.request('POST', url, body); }
  put(url, body) { return this.request('PUT', url, body); }
  delete(url) { return this.request('DELETE', url); }
}
window.api = new ApiClient();
