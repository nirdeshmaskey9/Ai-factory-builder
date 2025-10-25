window.Analytics = (function(){
  const $ = (id) => document.getElementById(id);
  async function fetchJSON(url){ try{ const r=await fetch(url); return await r.json(); }catch(e){ return {}; } }
  async function refresh(){
    const s = await fetchJSON('/analytics/stats');
    if ($('mc-total')) $('mc-total').textContent = s.total_runs ?? 0;
    if ($('mc-success')) $('mc-success').textContent = ((s.success_rate ?? 0)*100).toFixed(1)+'%';
    if ($('mc-duration')) $('mc-duration').textContent = (s.avg_duration ?? 0).toFixed(2)+'s';
    if ($('mc-logsize')) $('mc-logsize').textContent = (s.log_dir_size_mb ?? 0).toFixed(1)+' MB';
    try{
      if (window.Chart){
        const t = await fetchJSON('/analytics/trends?limit=20');
        const ctx1 = document.getElementById('chart-line');
        if (ctx1){ new Chart(ctx1,{type:'line',data:{labels:t.map(x=>x.run_id),datasets:[{label:'Score',data:t.map(x=>x.score||0),borderColor:'#22d3ee'}]},options:{responsive:true}}); }
        const ctx2 = document.getElementById('chart-pie');
        if (ctx2){ new Chart(ctx2,{type:'pie',data:{labels:['success','failed','deployed','partial'],datasets:[{data:[s.success||0,s.failed||0,s.deployed||0,(s.total_runs-(s.success||0)-(s.failed||0)-(s.deployed||0))],backgroundColor:['#10b981','#ef4444','#3b82f6','#f59e0b']}]}}); }
        const ctx3 = document.getElementById('chart-bar');
        if (ctx3){ const tu=s.templates_usage||{}; new Chart(ctx3,{type:'bar',data:{labels:Object.keys(tu),datasets:[{label:'count',data:Object.values(tu),backgroundColor:'#a78bfa'}]},options:{responsive:true}}); }
      }
    }catch(e){ }
  }
  function init(){ refresh(); setInterval(refresh, 30000); }
  return { init };
})();

