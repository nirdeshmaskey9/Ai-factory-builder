(() => {
  async function refresh(){
    try{
      const r = await fetch('/ui/system_status');
      const j = await r.json();
      document.getElementById('ver').textContent = j.version || '';
      document.getElementById('ms').textContent = j.milestone || '';
      document.getElementById('bridge').textContent = j.bridge_mode || 'hybrid';
      document.getElementById('trio').textContent = JSON.stringify(j.trio_health || {}, null, 2);
    } catch(e){}
  }
  refresh();
  setInterval(refresh, 10000);
})();

