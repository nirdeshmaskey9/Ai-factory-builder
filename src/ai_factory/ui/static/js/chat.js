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
    try { 
      const j = JSON.parse(ev.data); 
      // Clean content - remove any internal debug markers
      let content = j.content || '';
      // Remove [Local], [External] prefixes if present
      content = content.replace(/\[Local\]\s*/gi, '').replace(/\[External\]\s*/gi, '');
      append(j.role || 'assistant', content); 
    } catch(e) { 
      // Fallback: clean raw text
      let content = ev.data || '';
      content = content.replace(/\[Local\]\s*/gi, '').replace(/\[External\]\s*/gi, '');
      append('assistant', content); 
    }
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

