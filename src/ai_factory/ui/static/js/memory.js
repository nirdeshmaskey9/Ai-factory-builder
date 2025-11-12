document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('learn-btn');
  const status = document.getElementById('learn-status');
  if (btn) {
    btn.addEventListener('click', async () => {
      status.textContent = ' learning...';
      try {
        const resp = await fetch('/memory/learn', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})});
        const data = await resp.json();
        status.textContent = ` added ${data.added}, linked ${data.linked}`;
        if (window.toast) toast('Memory learn completed', 'info');
        setTimeout(()=> window.location.reload(), 600);
      } catch (e) {
        status.textContent = ' error';
        if (window.toast) toast('Memory learn failed', 'error');
      }
    });
  }

  // Admin actions
  const exportJsonBtn = document.getElementById('mem-export-json');
  const exportCsvBtn = document.getElementById('mem-export-csv');
  const importFile = document.getElementById('mem-import-file');
  const backupBtn = document.getElementById('mem-backup');
  const restoreBtn = document.getElementById('mem-restore');

  async function callExport(fmt) {
    try {
      const r = await fetch(`/memory/export?fmt=${encodeURIComponent(fmt)}`);
      const j = await r.json();
      if (r.ok) {
        if (window.toast) toast(`Exported ${j.count || 0} items to ${j.path}`, 'info');
      } else {
        if (window.toast) toast(`Export failed: ${j.detail || r.status}`, 'error');
      }
    } catch(e) {
      if (window.toast) toast(`Export error: ${e}`, 'error');
    }
  }
  exportJsonBtn && exportJsonBtn.addEventListener('click', () => callExport('json'));
  exportCsvBtn && exportCsvBtn.addEventListener('click', () => callExport('csv'));

  importFile && importFile.addEventListener('change', async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      let payload;
      if (file.type.includes('json') || file.name.endsWith('.json')) {
        const parsed = JSON.parse(text);
        const items = Array.isArray(parsed) ? parsed : (parsed.items || []);
        payload = { items };
      } else if (file.type.includes('csv') || file.name.endsWith('.csv')) {
        // naive CSV -> items with minimal fields
        const lines = text.split(/\r?\n/).filter(Boolean);
        const header = lines.shift();
        const cols = header ? header.split(',') : [];
        const items = lines.map(line => {
          const vals = line.split(',');
          const obj = {};
          cols.forEach((c, i) => obj[c.trim()] = vals[i]);
          return obj;
        });
        payload = { items };
      } else {
        if (window.toast) toast('Unsupported file type', 'error');
        return;
      }
      const r = await fetch('/memory/import', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
      const j = await r.json();
      if (r.ok) {
        if (window.toast) toast(`Imported ${j.added || 0} items`, 'info');
      } else {
        if (window.toast) toast(`Import failed: ${j.detail || r.status}`, 'error');
      }
    } catch(e) {
      if (window.toast) toast(`Import error: ${e}`, 'error');
    } finally {
      ev.target.value = '';
    }
  });

  async function callSimple(method, url, okMsg) {
    try {
      const r = await fetch(url, { method });
      const j = await r.json();
      if (r.ok) {
        if (window.toast) toast(`${okMsg}: ${j.path || 'ok'}`, 'info');
      } else {
        if (window.toast) toast(`${okMsg} failed: ${j.detail || r.status}`, 'error');
      }
    } catch(e) {
      if (window.toast) toast(`${okMsg} error: ${e}`, 'error');
    }
  }
  backupBtn && backupBtn.addEventListener('click', () => callSimple('GET', '/memory/backup', 'Backup'));
  restoreBtn && restoreBtn.addEventListener('click', () => callSimple('POST', '/memory/restore', 'Restore'));
});
