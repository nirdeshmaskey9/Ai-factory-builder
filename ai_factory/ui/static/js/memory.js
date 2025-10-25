document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('learn-btn');
  const status = document.getElementById('learn-status');
  if (btn) {
    btn.addEventListener('click', async () => {
      status.textContent = ' learning...';
      try {
        const resp = await fetch('/memory/learn', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})});
        const data = await resp.json();
        status.textContent = ` added ${data.added}, linked ${data.linked}`;
        setTimeout(()=> window.location.reload(), 600);
      } catch (e) {
        status.textContent = ' error';
      }
    });
  }
});

