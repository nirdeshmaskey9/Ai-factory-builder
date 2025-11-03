window.renderMemoryPeek = function(items){
  try{
    const root = document.getElementById('memGrid');
    if (!root) return;
    const list = (items||[]).slice(0,6);
    root.innerHTML = '';
    list.forEach((it)=>{
      const topic = (it.summary && it.summary.topic) || '(no topic)';
      const el = document.createElement('div');
      el.className = 'p-3 border border-slate-700 rounded bg-slate-900';
      el.innerHTML = `<div class="font-semibold text-slate-100">${topic}</div>
        <button class="mt-2 px-2 py-1 bg-slate-700 rounded" data-id="${it.id}">Reinject</button>`;
      el.querySelector('button')?.addEventListener('click', async () => {
        try{
          const r = await fetch('/dialogue/reinject', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({summary: it.summary, summary_id: it.id})});
          const j = await r.json();
          window.dispatchEvent(new CustomEvent('jp:memory-pulse'));
          alert('Context ready: '+ (j.context||''));
        }catch(e){}
      });
      root.appendChild(el);
    });
  }catch(e){}
}

