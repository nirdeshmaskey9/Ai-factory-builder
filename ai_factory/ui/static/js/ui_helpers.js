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

