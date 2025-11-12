(function(){
  const input = document.querySelector('textarea, input[type="text"], #chat-input') || document.querySelector('textarea');
  const usageTokens = document.getElementById('jp-usage-tokens');
  const usageUsd = document.getElementById('jp-usage-usd');
  const dot = document.getElementById('jp-memory-dot');

  async function refreshUsage(){
    try{
      const r = await fetch('/ui/control_state'); const j = await r.json();
      if(usageTokens) usageTokens.textContent = (j.tokens||0);
      if(usageUsd) usageUsd.textContent = (j.usd && j.usd.toFixed) ? j.usd.toFixed(4) : (j.usd||0);
      if(j.persona_mode){
        document.querySelectorAll('.jp-persona .jp-pill').forEach(b=>{
          b.classList.toggle('active', b.dataset.persona===j.persona_mode);
        });
      }
    }catch(e){}
  }

  function pulse(){ if(!dot) return; dot.classList.add('active'); setTimeout(()=>dot.classList.remove('active'), 1800); }
  window.jpPulse = pulse;

  async function handleCommand(cmd){
    if(cmd==='/summarize'){ const r=await fetch('/dialogue/close',{method:'POST'}); pulse(); return await r.json(); }
    if(cmd==='/recall'){ const r=await fetch('/dialogue/recent?session=current&n=20'); pulse(); return await r.json(); }
    if(cmd==='/clear'){ await fetch('/dialogue/close?dry-run=true',{method:'POST'}); pulse(); return {ok:true,cleared:true}; }
    if(cmd==='/toggle-voice'){ const evt=new CustomEvent('jp-voice-toggle'); window.dispatchEvent(evt); return {ok:true,voiceToggled:true}; }
    return null;
  }

  function attachInputHook(){
    if(!input) return;
    input.addEventListener('keydown', async (e)=>{
      if(e.key==='Enter' && (e.ctrlKey||e.metaKey)){
        const v=(input.value||'').trim();
        if(v.startsWith('/')){
          e.preventDefault();
          const res=await handleCommand(v.split(' ')[0]);
          console.debug('Slash cmd result:',res);
          input.value='';
        }
      }
    });
  }

  document.querySelectorAll('.jp-persona .jp-pill').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const persona = btn.dataset.persona;
      await fetch('/ui/control_state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona_mode: persona})});
      refreshUsage();
    });
  });

  refreshUsage(); attachInputHook();
  setInterval(refreshUsage, 4000);
})();

