(() => {
  const log = document.getElementById('chatLog');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');

  function append(role, content){
    const div = document.createElement('div');
    div.className = 'p-2 rounded border border-slate-800';
    div.innerHTML = `<span class="accent">${role}:</span> ${content}`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws/chat');
  ws.onmessage = (ev) => {
    try { const j = JSON.parse(ev.data); append(j.role || 'assistant', j.content || ''); } catch(e) { append('assistant', ev.data); }
  };
  ws.onopen = () => { /* nop */ };
  ws.onerror = () => { append('system', 'Connection error.'); };
  ws.onclose = () => { append('system', 'Disconnected.'); };

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = (input.value || '').trim();
    if(!text){ return; }
    ws.send(JSON.stringify({ user_input: text }));
    input.value = '';
  });
})();

