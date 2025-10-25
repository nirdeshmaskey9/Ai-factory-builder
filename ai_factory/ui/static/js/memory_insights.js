document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('learn-now');
  const res = document.getElementById('learn-res');
  if (btn) {
    btn.addEventListener('click', async ()=>{
      res.textContent = ' learning...';
      try {
        const r = await fetch('/memory/learn', {method:'POST', headers:{'Content-Type':'application/json'}, body: '{}'});
        const j = await r.json();
        res.textContent = ` added ${j.added}, linked ${j.linked}`;
      } catch(e) {
        res.textContent = ' error';
      }
    });
  }
});

