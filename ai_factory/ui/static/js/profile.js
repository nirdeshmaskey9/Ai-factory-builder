(() => {
  async function load(){
    try{ const r = await fetch('/ui/user_snapshot'); const j = await r.json(); const el = document.getElementById('miniProfile'); if (el){ el.textContent = (j.name||'You') + ' — ' + (j.mood||'neutral'); }}catch(e){}
  }
  window.addEventListener('DOMContentLoaded', load);
})();

