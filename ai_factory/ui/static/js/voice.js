(() => {
  function speak(text){
    try{
      if (!('speechSynthesis' in window)) return;
      const u = new SpeechSynthesisUtterance(text||'');
      speechSynthesis.speak(u);
    }catch(e){}
  }
  window.addEventListener('jp:voice-toggle', ()=>{
    /* placeholder - real toggle state omitted */
  });
  window.jpVoiceSpeak = speak;
})();

