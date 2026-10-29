document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('finGrid')) return;
  async function load() {
    const period = document.getElementById('finPeriod').value;
    const start = document.getElementById('finStart').value;
    const end = document.getElementById('finEnd').value;
    const percent = document.getElementById('finPercent').value;
    const m = await api.get(`/finance/api/overview?period=${period}&start=${start}&end=${end}&percent=${percent}`);
    const grid = document.getElementById('finGrid');
    grid.innerHTML = '';
    const items = [
      ['Gross Sales', m.gross_sales], ['COGS', m.cogs], ['Gross Profit', m.gross_profit],
      ['Operating Expenses', m.operating_expenses], ['Net Profit', m.net_profit],
      ['Inventory Value', m.inventory_value], ['Est. Inventory Profit', m.estimated_inventory_profit],
      ['Cash', m.cash], ['Capital', m.capital], ['Receivables', m.receivables],
      ['Payables', m.payables], ['Safe to Spend', m.safe_spend], ['Protected Buffer', m.protected_buffer],
      ['Capital Contributions', m.capital_contributions], ['Withdrawals', m.withdrawals],
    ];
    items.forEach(([label, val]) => {
      const div = document.createElement('div');
      div.className = 'nasa-border bg-nasa-panel p-4 rounded-lg';
      div.innerHTML = `<p class="text-[10px] font-mono text-slate-400 uppercase tracking-widest">${label}</p><h3 class="text-xl font-orbitron font-bold text-white mt-1">${money(val)}</h3>`;
      grid.appendChild(div);
    });
  }
  load();
  document.getElementById('btnFinFilter').onclick = load;
  // capital list
  try {
    const caps = await api.get('/finance/api/capital');
    const tbody = document.getElementById('capitalTableBody');
    caps.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${c.date}</td><td class="p-3">${c.type}</td><td class="p-3 text-right">${money(c.amount)}</td><td class="p-3">${c.description||''}</td>`;
      tbody.appendChild(tr);
    });
  } catch(e){}
  const modal = document.getElementById('capitalModal');
  document.getElementById('btnAddCapital').onclick = () => modal.classList.remove('hidden');
  document.getElementById('capitalClose').onclick = () => modal.classList.add('hidden');
  document.getElementById('capitalForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try {
      await api.post('/finance/api/capital', {
        transaction_type: f.transaction_type.value,
        amount: parseFloat(f.amount.value),
        transaction_date: f.transaction_date.value,
        description: f.description.value
      });
      modal.classList.add('hidden');
      location.reload();
    } catch (err) { showToast(err.message, 'error'); }
  };
});
