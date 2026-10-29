const toPHT = (s) => { try { const d = new Date(s); return d.toLocaleString('en-PH', {timeZone:'Asia/Manila', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:true}); } catch(e){ return s; } };

document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('expenseTableBody')) return;
  const tbody = document.getElementById('expenseTableBody');
  let page = 1;
  async function loadCats() {
    const cats = await api.get('/expenses/api/categories');
    const sel = document.getElementById('expenseCategorySelect');
    cats.forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; sel.appendChild(o); });
  }
  await loadCats();
  async function load() {
    const r = await api.get(`/expenses/api/list?page=${page}`);
    tbody.innerHTML = '';
    r.items.forEach(e => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${e.expense_date}</td><td class="p-3">${e.description}</td><td class="p-3">${e.category_name||''}</td><td class="p-3 text-right">${money(e.amount)}</td><td class="p-3">${e.payment_method}</td><td class="p-3 ${e.status==='recorded'?'text-nasa-green':'text-nasa-red'}">${e.status}</td><td class="p-3 text-center"><button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-red text-[10px] hover:bg-nasa-red hover:text-white" data-void="${e.id}">Void</button></td>`;
      tbody.appendChild(tr);
    });
  }
  load();
  const modal = document.getElementById('expenseModal');
  document.getElementById('btnAddExpense').onclick = () => modal.classList.remove('hidden');
  document.getElementById('expenseClose').onclick = () => modal.classList.add('hidden');
  document.getElementById('expenseForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try {
      await api.post('/expenses/api/create', {
        description: f.description.value,
        category_id: f.category_id.value,
        amount: parseFloat(f.amount.value),
        expense_date: f.expense_date.value,
        payment_method: f.payment_method.value,
        notes: f.notes.value
      });
      modal.classList.add('hidden');
      load();
    } catch (err) { showToast(err.message, 'error'); }
  };
  tbody.addEventListener('click', async (e) => {
    if (e.target.dataset.void) {
      if (!(await showConfirm('Void this expense?'))) return;
      await api.post('/expenses/api/' + e.target.dataset.void + '/void', {});
      load();
    }
  });
});
