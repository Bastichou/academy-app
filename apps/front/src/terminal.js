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
