window.toast = (msg, type='info') => {
  try{
    const c = document.getElementById('toast-container');
    if(!c) return; 
    const el = document.createElement('div');
    el.className = `px-4 py-2 rounded shadow text-white ${type==='error'?'bg-red-600':'bg-green-600'} fade-in`;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(()=>el.remove(), 3000);
  }catch(e){}
};


// Mood helpers and JoJo bubble (non-invasive additions)
(function(){
  const bubble = document.getElementById('jojoBubble');
  if (bubble) {
    bubble.addEventListener('click', fetchWhisper);
    setInterval(fetchWhisper, 60000);
    fetchWhisper();
  }
  async function fetchWhisper(){
    try{
      const r = await fetch('/memory/analytics'); const d = await r.json();
      const samples = [
        `Daily reflections: ${(d.daily_reflections||[]).slice(-1)[0]?.count || 0}.`,
        `Mood samples: ${(d.mood_trend||[]).length}.`,
        `Pinned memories: ${d.pinned_count || 0}.`
      ];
      const msg = samples[Math.floor(Math.random()*samples.length)] || 'All systems steady.';
      const t = document.getElementById('quickInsight') || bubble;
      t.textContent = msg;
      bubble.classList.add('soft-glow');
      setTimeout(()=>bubble.classList.remove('soft-glow'), 800);
    }catch(e){}
  }
  window.setMood = function(mode){
    try{
      document.body.classList.remove('mood-calm','mood-working','mood-reflecting');
      if(mode==='working') document.body.classList.add('mood-working');
      else if(mode==='reflecting') document.body.classList.add('mood-reflecting');
      else document.body.classList.add('mood-calm');
    }catch(e){}
  }
})();

// JP Statebar lightweight refresher
(function(){
  const pinSpan = document.getElementById('jp-pin');
  const lastSpan = document.getElementById('jp-last');
  if (pinSpan || lastSpan){
    async function refreshState(){
      try{
        const a = await fetch('/memory/analytics'); const aj = await a.json();
        if (pinSpan) pinSpan.textContent = 'Pins: ' + (aj.pinned_count||0);
      }catch(e){}
      try{
        const r = await fetch('/memory/reflections'); const d = await r.json();
        const arr = d.reflections||[]; const last = arr.length ? arr[arr.length-1].timestamp : '—';
        if (lastSpan) lastSpan.textContent = 'Last reflection: ' + last;
      }catch(e){}
    }
    refreshState();
    setInterval(refreshState, 60000);
  }
})();
