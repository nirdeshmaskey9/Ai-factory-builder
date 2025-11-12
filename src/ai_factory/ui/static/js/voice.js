(() => {
  let enabled = false;
  function speak(text){
    try{
      if (!('speechSynthesis' in window) || !enabled) return;
      const u = new SpeechSynthesisUtterance(text||'');
      speechSynthesis.speak(u);
    }catch(e){}
  }
  // Support both legacy and new event names
  window.addEventListener('jp:voice-toggle', ()=>{ enabled = !enabled; console.log('Voice:', enabled); });
  window.addEventListener('jp-voice-toggle', ()=>{ enabled = !enabled; console.log('Voice:', enabled); });
  window.jpVoiceSpeak = speak;
})();
