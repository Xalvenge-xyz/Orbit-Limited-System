document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('debtTableBody')) return;
  const tbody = document.getElementById('debtTableBody');
  let page = 1;
  async function load() {
    const type = document.getElementById('debtType').value;
    const status = document.getElementById('debtStatus').value;
    const r = await api.get(`/debts/api/list?type=${type}&status=${status}&page=${page}`);
    tbody.innerHTML = '';
    r.items.forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${d.name}</td><td class="p-3">${d.debt_type}</td><td class="p-3 text-right">${money(d.amount)}</td><td class="p-3 text-right">${money(d.paid_amount)}</td><td class="p-3 text-right">${money(d.balance)}</td><td class="p-3 ${d.status==='paid'?'text-nasa-green':'text-nasa-red'}">${d.status}</td><td class="p-3">${d.due_date||''}</td><td class="p-3 text-center"><button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-cyan text-[10px] hover:bg-nasa-cyan hover:text-black" data-pay="${d.id}">Pay</button></td>`;
      tbody.appendChild(tr);
    });
  }
  load();
  document.getElementById('debtType').addEventListener('change', () => { page=1; load(); });
  document.getElementById('debtStatus').addEventListener('change', () => { page=1; load(); });
  const modal = document.getElementById('debtModal');
  document.getElementById('btnAddDebt').onclick = () => modal.style.display='flex';
  document.getElementById('debtClose').onclick = () => modal.style.display='none';
  document.getElementById('debtForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try {
      await api.post('/debts/api/create', {
        name: f.name.value,
        debt_type: f.debt_type.value,
        amount: parseFloat(f.amount.value),
        debt_date: f.debt_date.value,
        due_date: f.due_date.value,
        notes: f.notes.value
      });
      modal.style.display='none';
      load();
    } catch (err) { showToast(err.message, 'error'); }
  };
  const payModal = document.getElementById('paymentModal');
  document.getElementById('paymentClose').onclick = () => payModal.style.display='none';
  document.getElementById('paymentForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try {
      await api.post(`/debts/api/${f.debt_id.value}/payment`, {
        amount: parseFloat(f.amount.value),
        payment_date: f.payment_date.value,
        method: f.method.value,
        notes: f.notes.value
      });
      payModal.style.display='none';
      load();
    } catch (err) { showToast(err.message, 'error'); }
  };
  tbody.addEventListener('click', (e) => {
    if (e.target.dataset.pay) {
      const f = document.getElementById('paymentForm');
      f.debt_id.value = e.target.dataset.pay;
      payModal.style.display='flex';
    }
  });
});
