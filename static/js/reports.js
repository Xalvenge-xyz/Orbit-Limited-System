document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('repTableBody')) return;
  const tbody = document.getElementById('repTableBody');
  async function load() {
    const period = document.getElementById('repPeriod').value;
    const start = document.getElementById('repStart').value;
    const end = document.getElementById('repEnd').value;
    const r = await api.get(`/reports/api/sales?period=${period}&start=${start}&end=${end}`);
    tbody.innerHTML = '';
    r.forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${s.sale_number}</td><td class="p-3">${s.created_at}</td><td class="p-3 text-right">${money(s.total)}</td><td class="p-3 text-right">${money(s.gross_profit)}</td><td class="p-3 ${s.status==='completed'?'text-nasa-green':'text-nasa-red'}">${s.status}</td>`;
      tbody.appendChild(tr);
    });
    const summary = await api.get(`/reports/api/summary?period=${period}&start=${start}&end=${end}`);
    const el = document.getElementById('repSummary');
    let html = '<table class="w-full text-left font-mono text-xs"><thead><tr class="bg-nasa-card text-slate-400 uppercase text-[10px] border-b border-nasa-border"><th class="p-3">Metric</th><th class="p-3 text-right">Value</th></tr></thead><tbody class="divide-y divide-nasa-border">';
    const labels = {
      gross_sales:'Gross Sales', cogs:'COGS', gross_profit:'Gross Profit',
      operating_expenses:'Operating Expenses', net_profit:'Net Profit',
      capital_contributions:'Capital Contributions', withdrawals:'Withdrawals',
      receivables:'Receivables', payables:'Payables', sale_count:'Sale Count'
    };
    Object.keys(labels).forEach(k => {
      const v = summary[k];
      const val = (k === 'sale_count') ? v : money(v);
      html += `<tr><td class="p-3">${labels[k]}</td><td class="p-3 text-right">${val}</td></tr>`;
    });
    html += '</tbody></table>';
    el.innerHTML = html;
  }
  load();
  document.getElementById('btnRepFilter').onclick = load;
  document.getElementById('btnExportCsv').onclick = () => {
    const period = document.getElementById('repPeriod').value;
    const start = document.getElementById('repStart').value;
    const end = document.getElementById('repEnd').value;
    window.open(`/reports/api/sales?period=${period}&start=${start}&end=${end}&format=csv`, '_blank');
  };
});
