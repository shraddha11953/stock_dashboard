// app/static/js/dashboard.js
let priceChart = null;
let compareChart = null;

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status} - ${txt}`);
  }
  return res.json();
}

async function loadCompanies() {
  try {
    const json = await fetchJSON('/api/companies');
    const companies = json.companies || [];
    const list = document.getElementById('companyList');
    const select = document.getElementById('symbolSelect');
    const compareA = document.getElementById('compareA');
    const compareB = document.getElementById('compareB');

    list.innerHTML = '';
    select.innerHTML = '';
    compareA.innerHTML = '';
    compareB.innerHTML = '';

    companies.forEach(sym => {
      const li = document.createElement('li');
      li.textContent = sym;
      li.addEventListener('click', () => onSelectCompany(sym));
      list.appendChild(li);

      const opt = document.createElement('option');
      opt.value = sym; opt.textContent = sym;
      select.appendChild(opt);

      const optA = opt.cloneNode(true);
      const optB = opt.cloneNode(true);
      compareA.appendChild(optA);
      compareB.appendChild(optB);
    });

    // initial load
    if (companies.length) {
      const initial = companies[0];
      document.getElementById('symbolSelect').value = initial;
      onSelectCompany(initial);
    }
  } catch (e) {
    console.error('Failed to load companies', e);
  }
}

async function onSelectCompany(symbol) {
  const days = parseInt(document.getElementById('rangeSelect').value || '90');
  try {
    const json = await fetchJSON(`/api/data?symbol=${encodeURIComponent(symbol)}&days=${days}`);
    renderPriceChart(json.symbol, json.data);
    updateSummary(json.data);
    document.getElementById('chartTitle').textContent = `${json.symbol} — last ${days} days`;
  } catch (e) {
    console.error('Failed to load data', e);
    alert('Failed to load data: ' + e.message);
  }
}

function formatDate(d) {
  const dt = new Date(d);
  return dt.toISOString().slice(0,10);
}

function renderPriceChart(symbol, data) {
  const labels = data.map(d => formatDate(d.date));
  const closes = data.map(d => d.close);
  const ma7 = data.map(d => d.ma_7);

  const ctx = document.getElementById('priceChart').getContext('2d');
  if (priceChart) priceChart.destroy();

  priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: symbol + ' Close', data: closes, borderWidth: 2, tension: 0.2 },
        { label: '7-day MA', data: ma7, borderWidth: 1, tension: 0.2, borderDash: [6,4] }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index' },
      plugins: { legend: { display: true } }
    }
  });
}

function updateSummary(data) {
  if (!data || data.length === 0) return;
  const last = data[data.length - 1];
  document.getElementById('maValue').textContent = (last.ma_7 ? last.ma_7.toFixed(2) : '-');
  document.getElementById('lastClose').textContent = (last.close ? last.close.toFixed(2) : '-');
  document.getElementById('lastReturn').textContent = (last.daily_return ? (last.daily_return*100).toFixed(2) + '%' : '-');
}

async function compareStocks() {
  const a = document.getElementById('compareA').value;
  const b = document.getElementById('compareB').value;
  const days = parseInt(document.getElementById('rangeSelect').value || '90');
  if (!a || !b) return;
  try {
    const pa = await fetchJSON(`/api/data?symbol=${encodeURIComponent(a)}&days=${days}`);
    const pb = await fetchJSON(`/api/data?symbol=${encodeURIComponent(b)}&days=${days}`);
    const labels = pa.data.map(d => formatDate(d.date));
    const ctx = document.getElementById('compareChart').getContext('2d');
    if (compareChart) compareChart.destroy();
    compareChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: a, data: pa.data.map(d => d.close), borderWidth: 2, tension: 0.2 },
          { label: b, data: pb.data.map(d => d.close), borderWidth: 2, tension: 0.2 }
        ]
      },
      options: { responsive: true }
    });
  } catch (e) {
    console.error('Compare failed', e);
  }
}

async function triggerRefresh() {
  try {
    document.getElementById('refreshBtn').disabled = true;
    const res = await fetch('/refresh', { method: 'POST' });
    if (!res.ok) throw new Error('Refresh failed');
    alert('Refresh started on server. It may take a few minutes.');
  } catch (e) {
    alert('Refresh error: ' + e.message);
  } finally {
    document.getElementById('refreshBtn').disabled = false;
  }
}

// events
document.addEventListener('DOMContentLoaded', () => {
  loadCompanies();
  document.getElementById('rangeSelect').addEventListener('change', () => {
    const sym = document.getElementById('symbolSelect').value;
    if (sym) onSelectCompany(sym);
  });
  document.getElementById('symbolSelect').addEventListener('change', (ev) => {
    onSelectCompany(ev.target.value);
  });
  document.getElementById('compareBtn').addEventListener('click', compareStocks);
  document.getElementById('refreshBtn').addEventListener('click', triggerRefresh);
});
