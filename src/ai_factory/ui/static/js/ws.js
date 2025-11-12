window.WS = (function(){
  const ind = () => document.getElementById('ws-indicator');
  function setOnline(on){ if(ind()) ind().style.backgroundColor = on ? '#10b981' : '#ef4444'; }
  function backoff(i){ return Math.min(30000, 1000 * Math.pow(2, i)); }

  function connectRuns(onUpdate){ let tries=0; async function loop(){ try{ const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws/runs'); ws.onopen=()=>{ setOnline(true); tries=0; }; ws.onmessage=(ev)=>{ if(onUpdate) onUpdate(JSON.parse(ev.data)); }; ws.onclose=()=>{ setOnline(false); setTimeout(loop, backoff(++tries)); }; }catch(e){ setOnline(false); setTimeout(loop, backoff(++tries)); } } loop(); }
  function connectLogs(runId, onUpdate){ let tries=0; async function loop(){ try{ const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+`/ws/logs/${runId}`); ws.onopen=()=>{ setOnline(true); tries=0; }; ws.onmessage=(ev)=>{ if(onUpdate) onUpdate(JSON.parse(ev.data)); }; ws.onclose=()=>{ setOnline(false); setTimeout(loop, backoff(++tries)); }; }catch(e){ setOnline(false); setTimeout(loop, backoff(++tries)); } } loop(); }
  return { connectRuns, connectLogs };
})();

