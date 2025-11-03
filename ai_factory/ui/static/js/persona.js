(() => {
  async function setMode(mode){
    try{
      await fetch('/ui/control_state', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({persona_mode: mode})});
    }catch(e){}
  }
  window.jpPersonaInit = function(){
    const sel = document.getElementById('personaMode');
    if (!sel) return;
    sel.addEventListener('change', ()=> setMode(sel.value));
  }
})();

