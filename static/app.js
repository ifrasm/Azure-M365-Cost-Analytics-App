async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch('/import-excel', { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

function renderChart(ctx, labels, values, label) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{ label: label, data: values, backgroundColor: 'rgba(54,162,235,0.6)' }]
    },
    options: { responsive: true }
  });
}

document.getElementById('upload').addEventListener('click', async () => {
  const fileEl = document.getElementById('file');
  const status = document.getElementById('status');
  if (!fileEl.files.length) { status.textContent = 'Select a file first'; return; }
  status.textContent = 'Uploading...';
  try {
    const result = await uploadFile(fileEl.files[0]);
    status.textContent = 'Rendered charts from uploaded file';

    const monthly = result.monthly || [];
    const quarterly = result.quarterly || [];

    const mLabels = monthly.map(r => r.month);
    const mValues = monthly.map(r => r._cost || r._cost === 0 ? r._cost : (r[Object.keys(r)[1]] || 0));

    const qLabels = quarterly.map(r => r.quarter);
    const qValues = quarterly.map(r => r._cost || r._cost === 0 ? r._cost : (r[Object.keys(r)[1]] || 0));

    // Destroy previous charts if exist
    if (window._monthlyChart) window._monthlyChart.destroy();
    if (window._quarterlyChart) window._quarterlyChart.destroy();

    const mCtx = document.getElementById('monthlyChart').getContext('2d');
    const qCtx = document.getElementById('quarterlyChart').getContext('2d');

    window._monthlyChart = renderChart(mCtx, mLabels, mValues, 'Monthly Cost');
    window._quarterlyChart = renderChart(qCtx, qLabels, qValues, 'Quarterly Cost');

  } catch (e) {
    status.textContent = 'Error: ' + e.message;
  }
});

// If the site is served statically (e.g. GitHub Pages), fetch sample data
async function loadSampleIfNoBackend() {
  const status = document.getElementById('status');
  try {
    // Try health check
    const h = await fetch('/health');
    if (h.ok) return; // backend present
  } catch (_) {
    // no backend; load sample data
  }

  status.textContent = 'No backend detected — loading sample data';
  try {
    const resp = await fetch('/static/sample-data.json');
    const result = await resp.json();

    const monthly = result.monthly || [];
    const quarterly = result.quarterly || [];

    const mLabels = monthly.map(r => r.month);
    const mValues = monthly.map(r => r._cost || r.cost || Object.values(r)[1] || 0);

    const qLabels = quarterly.map(r => r.quarter);
    const qValues = quarterly.map(r => r._cost || r.cost || Object.values(r)[1] || 0);

    if (window._monthlyChart) window._monthlyChart.destroy();
    if (window._quarterlyChart) window._quarterlyChart.destroy();

    const mCtx = document.getElementById('monthlyChart').getContext('2d');
    const qCtx = document.getElementById('quarterlyChart').getContext('2d');

    window._monthlyChart = renderChart(mCtx, mLabels, mValues, 'Monthly Cost (sample)');
    window._quarterlyChart = renderChart(qCtx, qLabels, qValues, 'Quarterly Cost (sample)');
    status.textContent = 'Displayed sample data';
  } catch (e) {
    status.textContent = 'No sample data available';
  }
}

// Run fallback on load
window.addEventListener('load', loadSampleIfNoBackend);
