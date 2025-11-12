document.addEventListener('DOMContentLoaded', async () => {
  const c = document.getElementById('timelineChart');
  if (!c) return;
  try {
    const res = await fetch('/memory/insights');
    const data = await res.json();
    const stats = data && data.stats ? data.stats : data;
    const tags = (stats && stats.tags) || [];
    // Build a simple series using tag counts as a stand-in for timeseries
    const labels = tags.map(t => t.tag);
    const values = tags.map(t => t.count);
    const ctx = c.getContext('2d');
    // eslint-disable-next-line no-undef
    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Entries (by top tags)',
          data: values,
          borderColor: 'rgb(34,197,94)',
          backgroundColor: 'rgba(34,197,94,0.2)',
          tension: 0.3,
          fill: true,
        }]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: true }
        },
        scales: {
          x: { title: { display: true, text: 'Tag' } },
          y: { title: { display: true, text: 'Count' }, beginAtZero: true }
        }
      }
    });
  } catch (e) {
    if (window.toast) toast(`Timeline load error: ${e}`, 'error');
  }
});
