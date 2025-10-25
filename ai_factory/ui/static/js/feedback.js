window.Feedback = (function(){
  async function vote(runId, rating){ try{ await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:runId,rating,comment:''})}); document.getElementById('fb-status').textContent='Saved '+rating; }catch(e){}}
  async function submit(runId){ const c=document.getElementById('fb-comment').value; try{ await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:runId,rating:'up',comment:c})}); document.getElementById('fb-status').textContent='Comment saved'; }catch(e){}}
  return { vote, submit };
})();

