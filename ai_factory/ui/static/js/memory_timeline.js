document.addEventListener('DOMContentLoaded', async () => {
  // Simple placeholder: draw counts over time if needed; here, no-op.
  const c = document.getElementById('timelineChart');
  if (!c) return;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#ddd';
  ctx.fillRect(0,0,c.width,c.height);
  ctx.fillStyle = '#333';
  ctx.fillText('Memory timeline (placeholder)', 20, 20);
});

