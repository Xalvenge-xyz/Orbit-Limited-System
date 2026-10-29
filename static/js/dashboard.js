document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('kpiGrid')) return;
  async function load() {
    try {
      const m = await api.get('/dashboard/api/metrics');
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = money(v); };
      set('kpiToday', m.today_sales);
      set('kpiGrossSales', m.gross_sales);
      set('kpiGrossProfit', m.gross_profit);
      set('kpiNetProfit', m.net_profit);
      set('kpiOpex', m.operating_expenses);
      set('kpiInvVal', m.inventory_value);
      set('kpiInvProfit', m.estimated_inventory_profit);
      set('kpiCash', m.cash);
      set('kpiRecv', m.receivables);
      set('kpiPay', m.payables);
      set('kpiCapital', m.capital);
      set('kpiSafe', m.safe_spend);
      const low = document.getElementById('kpiLow'); if (low) low.textContent = m.low_stock_count;
      // charts
      if (window.Chart) {
        const c1 = document.getElementById('chartCapitalProfit');
        if (c1) {
          window.chartManager.create('capitalProfit', c1.getContext('2d'), {
            type: 'doughnut',
            data: {
              labels: ['Invested Capital', 'Realized Net Profit'],
              datasets: [{ data: [m.capital, m.net_profit], backgroundColor: ['#6366F1', '#10B981'] }]
            },
            options: { plugins: { legend: { labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary') } } } }
          });
        }
        const c2 = document.getElementById('chartTelemetry');
        if (c2) {
          window.chartManager.create('telemetry', c2.getContext('2d'), {
            type: 'bar',
            data: {
              labels: ['Invested Capital', 'Gross Sales', 'Net Profit'],
              datasets: [{ label: 'Amount', data: [m.capital, m.gross_sales, m.net_profit], backgroundColor: ['#6366F1', '#00F0FF', '#10B981'] }]
            },
            options: { scales: { x: { ticks: { color: '#9bb0cc' } }, y: { ticks: { color: '#9bb0cc' } } } }
          });
        }
      }
    } catch (e) { console.error(e); }
  }
  load();
});
