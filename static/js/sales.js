document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('salesTableBody')) return;
  const tbody = document.getElementById('salesTableBody');
  const toPHT = (s) => { try { const d = new Date(s); return d.toLocaleString('en-PH', {timeZone:'Asia/Manila', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:true}); } catch(e){ return s; } };
  async function load() {
    const period = document.getElementById('salesPeriod').value;
    const start = document.getElementById('salesStart').value;
    const end = document.getElementById('salesEnd').value;
    const r = await api.get(`/sales/api/list?period=${period}&start=${start}&end=${end}`);
    tbody.innerHTML = '';
    r.items.forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${s.sale_number}</td><td class="p-3">${toPHT(s.created_at)}</td><td class="p-3">${s.cashier||''}</td><td class="p-3 text-right">${money(s.total)}</td><td class="p-3 text-right">${money(s.gross_profit)}</td><td class="p-3 ${s.status==='completed'?'text-nasa-green':'text-nasa-red'}">${s.status}</td><td class="p-3 text-center"><a href="/sales/receipt/${s.id}" class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-cyan text-[10px] hover:bg-nasa-cyan hover:text-black">Receipt</a></td>`;
      tbody.appendChild(tr);
    });
  }
  load();
  document.getElementById('btnSalesFilter').onclick = load;
});
