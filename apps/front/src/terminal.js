// Prefix an /api/* path with the runtime-configured API base (config.js).
// Empty API_BASE -> same-origin relative path, proxied by Nginx (default).
function apiUrl(path) {
  const base = (window.API_BASE || '').replace(/\/$/, '');
  return base + path;
}

// Fill any [data-api-endpoint] element with the active API endpoint (config.js ·
// API_BASE), and toggle a green dot on [data-api-dot] when an explicit override
// is set. Empty API_BASE means same-origin requests proxied by Nginx (default).
document.addEventListener('DOMContentLoaded', () => {
  const base = (window.API_BASE || '').trim();
  const label = base || 'same-origin · /api/* (proxied by Nginx)';
  document.querySelectorAll('[data-api-endpoint]').forEach(el => { el.textContent = label; });
  document.querySelectorAll('[data-api-dot]').forEach(el => { el.style.background = base ? '#22c55e' : '#555'; });
});

function ts() { return new Date().toTimeString().slice(0, 8); }

function log(html) {
  const t = document.getElementById('term');
  t.insertAdjacentHTML('beforeend', html);
  t.scrollTop = t.scrollHeight;
}

function clearTerminal() { document.getElementById('term').innerHTML = ''; }

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function logReq(method, path) {
  const cls = { GET:'log-get', POST:'log-post', DELETE:'log-del' }[method] || 'log-info';
  log(`<div class="log"><span class="log-ts">${ts()}</span><span class="${cls}">${method}</span><span class="log-json"> ${escHtml(path)}</span></div>`);
}

function logRes(status, detail) {
  const ok = typeof status === 'number' && status >= 200 && status < 300;
  const cls = ok ? 'log-ok' : 'log-err';
  log(`<div class="log"><span class="log-ts">${ts()}</span><span class="${cls}">${status}</span><span class="log-json"> ${escHtml(String(detail))}</span></div>`);
}
