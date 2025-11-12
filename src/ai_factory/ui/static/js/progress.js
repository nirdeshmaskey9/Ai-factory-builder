window.Progress = (function(){
  function stageFrom(text, status){
    const t=(text||'').toLowerCase();
    if(/deployed|deploy/.test(t) || status==='deployed') return {pct:100,label:'Deploying',cls:'bg-green-500'};
    if(/evaluate|score/.test(t)) return {pct:75,label:'Evaluating',cls:'bg-blue-500'};
    if(/build|rebuild/.test(t)) return {pct:50,label:'Building',cls:'bg-blue-500'};
    if(/plan|planning/.test(t)) return {pct:25,label:'Planning',cls:'bg-blue-500'};
    if(status==='failed') return {pct:100,label:'Failed',cls:'bg-red-600'};
    if(status==='success') return {pct:100,label:'Completed',cls:'bg-green-500'};
    return {pct:0,label:'Pending',cls:'bg-blue-500'};
  }
  function updateFromPayload(payload){
    try{
      const inner=document.getElementById('progress-inner');
      const label=document.getElementById('progress-label');
      if(!inner||!label) return;
      const run = payload.run||{}; const sup = payload.supervisor||{};
      const text = (sup.result||'') + ' ' + (run.status||'');
      const st = stageFrom(text, run.status);
      inner.style.width = st.pct+'%';
      inner.className = `h-2 rounded transition-all duration-700 ${st.cls}`;
      label.textContent = `Stage: ${st.label}`;
    }catch(e){}
  }
  return { updateFromPayload };
})();

