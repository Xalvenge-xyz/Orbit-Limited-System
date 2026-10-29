const toPHT = (s) => { try { const d = new Date(s); return d.toLocaleString('en-PH', {timeZone:'Asia/Manila', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:true}); } catch(e){ return s; } };

document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('movementTableBody')) return;
  const tbody = document.getElementById('movementTableBody');
  let page = 1;
  async function loadProducts() {
    try {
      const r = await api.get('/products/api/list?per_page=200&status=active');
      const sel = document.getElementById('adjustProductSelect');
      sel.innerHTML = '';
      (r.items || []).forEach(p => {
        const o = document.createElement('option');
        o.value = p.id;
        o.textContent = `${p.name} (stock: ${p.stock})`;
        sel.appendChild(o);
      });
    } catch (e) { console.error(e); }
  }
  await loadProducts();
  async function load() {
    const r = await api.get(`/inventory/api/movements?page=${page}`);
    tbody.innerHTML = '';
    r.items.forEach(m => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="p-3">${toPHT(m.created_at)}</td><td class="p-3">${m.product_name||''}</td><td class="p-3 text-right font-bold ${m.quantity_change>=0?'text-nasa-green':'text-nasa-red'}">${m.quantity_change}</td><td class="p-3">${m.movement_type}</td><td class="p-3">${m.reason||''}</td><td class="p-3">${m.user||''}</td>`;
      tbody.appendChild(tr);
    });
  }
  load();
  // low stock
  try {
    const ls = await api.get('/inventory/api/low-stock');
    const box = document.getElementById('lowStockList');
    if (ls.length) {
      box.innerHTML = '<strong>Low stock:</strong> ' + ls.map(p => `${p.name} (${p.stock})`).join(', ');
    } else {
      box.innerHTML = '<strong>No low-stock items.</strong>';
    }
  } catch(e){}
  const modal = document.getElementById('adjustModal');
  document.getElementById('btnAdjust').onclick = () => modal.style.display='flex';
  document.getElementById('adjustClose').onclick = () => modal.style.display='none';
  document.getElementById('adjustForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    try {
      await api.post('/inventory/api/adjust', {
        product_id: parseInt(f.product_id.value),
        quantity_change: parseInt(f.quantity_change.value),
        movement_type: f.movement_type.value,
        reason: f.reason.value
      });
      modal.style.display='none';
      load();
    } catch (err) { showToast(err.message, 'error'); }
  };
});
