(() => {
  const input = () => document.getElementById('chatInput');
  async function summarize(){
    try{ const r = await fetch('/dialogue/close?dry-run=true', {method: 'POST'}); const j = await r.json(); alert('Summary: '+ (j.topic||'')); window.dispatchEvent(new CustomEvent('jp:memory-pulse')); }catch(e){}
  }
  async function recall(){
    try{ const r = await fetch('/dialogue/recent?n=15'); const j = await r.json(); alert('Recent turns: '+ j.length); window.dispatchEvent(new CustomEvent('jp:memory-pulse')); }catch(e){}
  }
  function clearBox(){ const el = input(); if (el) el.value = ''; }
  function saveNote(){ fetch('/dialogue/recent'); /* placeholder to ensure route works */ }
  function toggleVoice(){ window.dispatchEvent(new CustomEvent('jp:voice-toggle')); }
  window.jpCommandHook = function(e){
    const el = input();
    if (!el) return;
    const v = el.value || '';
    if (v.startsWith('/')){
      if (v.startsWith('/summarize')){ e.preventDefault(); summarize(); }
      else if (v.startsWith('/recall')){ e.preventDefault(); recall(); }
      else if (v.startsWith('/clear')){ e.preventDefault(); clearBox(); }
      else if (v.startsWith('/toggle voice')){ e.preventDefault(); toggleVoice(); }
    }
  }
})();

