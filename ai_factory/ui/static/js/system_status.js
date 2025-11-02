(() => {
  async function refresh(){
    try{
      const r = await fetch('/ui/system_status');
      const j = await r.json();
      const verEl = document.getElementById('ver');
      const msEl = document.getElementById('ms');
      const bridgeEl = document.getElementById('bridge');
      const trioEl = document.getElementById('trio');
      if (verEl) verEl.textContent = j.version || '';
      if (msEl) msEl.textContent = j.milestone || '';
      if (bridgeEl) bridgeEl.textContent = j.bridge_mode || 'hybrid';
      if (trioEl) trioEl.textContent = JSON.stringify(j.trio_health || {}, null, 2);
    } catch(e){}
  }

  async function refreshControl(){
    try{
      const r = await fetch('/ui/control_state');
      const d = await r.json();
      const m = document.getElementById('mockModeStatus');
      const u = document.getElementById('usageStats');
      if (m) m.textContent = d.mock_mode ? 'ON (Mock)' : 'OFF (Live)';
      if (u) u.textContent = `${d.tokens} tokens ≈ $${Number(d.usd || 0).toFixed(4)}`;
    } catch(e){}
  }

  window.toggleMock = async function toggleMock(){
    try{
      await fetch('/ui/toggle_mock', { method: 'POST' });
      refreshControl();
    } catch(e){}
  }

  function loop(){ refresh(); refreshControl(); }
  loop();
  setInterval(loop, 10000);
})();
