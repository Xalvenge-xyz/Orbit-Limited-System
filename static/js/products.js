document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('productTableBody')) return;
  let page = 1;
  const tbody = document.getElementById('productTableBody');
  async function loadCategories() {
    try {
      const cats = await api.get('/products/api/categories');
      const sel = document.getElementById('productCategory');
      sel.innerHTML = '<option value="">All categories</option>';
      cats.forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; sel.appendChild(o); });
      // populate modal supplier select
      const sups = await api.get('/products/api/suppliers');
      const ssel = document.getElementById('productSupplierSelect');
      if (ssel) {
        ssel.innerHTML = '<option value="">-- none --</option>';
        sups.forEach(s => { const o = document.createElement('option'); o.value = s.id; o.textContent = s.name; ssel.appendChild(o); });
      }
    } catch (e) { console.error(e); }
  }
  await loadCategories();
  async function load() {
    const search = document.getElementById('productSearch').value;
    const category_id = document.getElementById('productCategory').value;
    const status = document.getElementById('productStatus').value;
    const stock_status = document.getElementById('productStock').value;
    const r = await api.get(`/products/api/list?search=${encodeURIComponent(search)}&category_id=${category_id}&status=${status}&stock_status=${stock_status}&page=${page}`);
    tbody.innerHTML = '';
    r.items.forEach(p => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="p-3">${p.name}</td>
        <td class="p-3">${p.sku||''}</td>
        <td class="p-3">${p.category_name||''}</td>
        <td class="p-3 text-right">${p.cost!==undefined?money(p.cost):'-'}</td>
        <td class="p-3 text-right">${money(p.price)}</td>
        <td class="p-3 text-right">${money(p.min_price)}</td>
        <td class="p-3 text-center">${p.stock}</td>
        <td class="p-3">${p.status}</td>
        <td class="p-3 text-center">
          <div class="flex gap-1 justify-center">
            <button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-cyan text-[10px] hover:bg-nasa-cyan hover:text-black" data-edit="${p.id}">Edit</button>
            <button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-red text-[10px] hover:bg-nasa-red hover:text-white" data-archive="${p.id}">Archive</button>
          </div>
        </td>`;
      tbody.appendChild(tr);
    });
    // pagination
    const pag = document.getElementById('productPagination');
    pag.innerHTML = '';
    for (let i=1;i<=r.pages;i++){
      const b=document.createElement('button'); b.textContent=i; b.onclick=()=>{page=i;load();}; pag.appendChild(b);
    }
  }
  load();
  document.getElementById('productSearch').addEventListener('input', () => { page=1; load(); });
  document.getElementById('productCategory').addEventListener('change', () => { page=1; load(); });
  document.getElementById('productStatus').addEventListener('change', () => { page=1; load(); });
  document.getElementById('productStock').addEventListener('change', () => { page=1; load(); });
  // modal
  const modal = document.getElementById('productModal');
  document.getElementById('btnAddProduct').onclick = () => { document.getElementById('productModalTitle').textContent='Add Product'; document.getElementById('productForm').reset(); const hid=document.querySelector('input[name="id"]'); if(hid) hid.value=''; modal.classList.remove('hidden'); };
  document.getElementById('productModalClose').onclick = () => modal.classList.add('hidden');
  document.getElementById('productForm').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    const payload = {
      name: f.elements.name.value, sku: f.elements.sku.value,
      category: f.elements.category.value, supplier_id: f.elements.supplier_id.value,
      cost: parseFloat(f.elements.cost.value), price: parseFloat(f.elements.price.value), min_price: parseFloat(f.elements.min_price.value),
      target_gross_margin: f.elements.target_gross_margin.value || null,
      stock: parseInt(f.elements.stock.value||0), reorder_level: parseInt(f.elements.reorder_level.value||3)
    };
    const id = f.querySelector('input[name="id"]').value;
    try {
      if (id) {
        await api.post(`/products/api/${id}/update`, payload);
      } else {
        await api.post('/products/api/create', payload);
      }
      modal.classList.add('hidden');
      load();
    } catch (err) { showToast(err.message, 'error'); alert(err.message); }
  };
  tbody.addEventListener('click', async (e) => {
    if (e.target.dataset.edit) {
      const p = await api.get('/products/api/' + e.target.dataset.edit);
      const f = document.getElementById('productForm');
      f.querySelector('input[name="id"]').value = p.id;
      f.name.value = p.name;
      f.sku.value = p.sku || '';
      f.category.value = p.category_name || '';
      f.supplier_id.value = p.supplier_id || '';
      f.cost.value = p.cost;
      f.price.value = p.price;
      f.min_price.value = p.min_price;
      f.target_gross_margin.value = p.target_gross_margin || '';
      f.stock.value = p.stock;
      f.reorder_level.value = p.reorder_level;
      document.getElementById('productModalTitle').textContent='Edit Product';
      modal.classList.remove('hidden');
    }
    if (e.target.dataset.archive) {
      if (!(await showConfirm('Archive this product?'))) return;
      await api.post('/products/api/' + e.target.dataset.archive + '/archive', {});
      load();
    }
  });
});
