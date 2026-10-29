class POSController {
  constructor() {
    this.cart = [];
    this.searchInput = document.getElementById('posSearch');
    this.results = document.getElementById('posResults');
    this.cartItems = document.getElementById('cartItems');
    this.totalEl = document.getElementById('cartTotal');
    this.bind();
  }
  bind() {
    if (this.searchInput) {
      let t;
      this.searchInput.addEventListener('input', () => {
        clearTimeout(t);
        t = setTimeout(() => this.search(this.searchInput.value), 250);
      });
    }
    const checkoutBtn = document.getElementById('btnCheckout');
    if (checkoutBtn) checkoutBtn.addEventListener('click', () => this.checkout());
    const clearBtn = document.getElementById('btnClearCart');
    if (clearBtn) clearBtn.addEventListener('click', async () => { if (await showConfirm('Clear cart?')) { this.cart = []; this.renderCart(); } });
    // load all products initially
    this.search('');
    // event delegation for product cards
    if (this.results) {
      this.results.addEventListener('click', (e) => {
        const card = e.target.closest('[data-product]');
        if (!card) return;
        if (card.classList.contains('cursor-not-allowed')) return;
        try {
          const p = JSON.parse(card.dataset.product);
          this.addToCart(p);
        } catch (err) { console.error(err); }
      });
    }
  }
  async search(q) {
    try {
      const data = await api.get('/pos/api/search?q=' + encodeURIComponent(q || ''));
      this.lastProducts = data;
      this.renderProducts();
    } catch (e) { console.error(e); }
  }
  renderProducts() {
    this.results.innerHTML = '';
    const cartQty = {};
    this.cart.forEach(c => { cartQty[c.id] = (cartQty[c.id] || 0) + c.qty; });
    (this.lastProducts || []).forEach(p => {
      const availableStock = p.stock - (cartQty[p.id] || 0);
      const available = p.available !== false && (availableStock > 0);
      const lowStock = available && (availableStock <= 3);
      const div = document.createElement('div');
      div.className = 'nasa-border bg-nasa-panel p-3 rounded flex flex-col justify-between relative ' + (available ? 'cursor-pointer hover:border-nasa-cyan transition' : 'opacity-40 cursor-not-allowed');
      div.dataset.productId = p.id;
      div.dataset.product = JSON.stringify(p);
      div.innerHTML = `
        ${lowStock ? '<span class="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-nasa-red text-white text-[8px] font-mono font-bold">LOW</span>' : ''}
        <div><span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-nasa-card text-nasa-cyan border border-nasa-border">${p.sku||''}</span><h4 class="font-bold text-white text-xs mt-2">${p.name}</h4></div>
        <div class="mt-2 font-mono text-[10px]"><p class="text-nasa-cyan">${money(p.price)}</p><p class="${!available ? 'text-nasa-red' : (lowStock ? 'text-nasa-red font-bold' : 'text-slate-400')}">${available ? 'stock ' + availableStock : 'OUT OF STOCK'}</p></div>
      `;
      this.results.appendChild(div);
    });
    if (window.lucide) lucide.createIcons();
  }
  addToCart(p) {
    const existing = this.cart.find(c => c.id === p.id);
    if (existing) {
      if (existing.qty + 1 > p.stock) { showToast('Insufficient stock', 'warning'); return; }
      existing.qty += 1;
    } else {
      this.cart.push({ id: p.id, name: p.name, cost: p.cost, price: p.price, min_price: p.min_price, selectedPrice: p.price, qty: 1, stock: p.stock });
    }
    this.renderProducts();
    this.renderCart();
  }
  renderCart() {
    this.cartItems.innerHTML = '';
    let total = 0;
    this.cart.forEach((c, idx) => {
      const line = c.selectedPrice * c.qty;
      total += line;
      const below = c.selectedPrice < c.min_price;
      const row = document.createElement('div');
      row.className = 'nasa-border bg-nasa-bg p-3 rounded space-y-2 font-mono text-xs' + (below ? ' border-nasa-red' : '');
      row.innerHTML = `
        <div class="flex justify-between items-start">
          <span class="font-bold text-white">${c.name}</span>
          <button class="remBtn text-nasa-red hover:text-white" data-idx="${idx}"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
        </div>
        <div class="grid grid-cols-2 gap-2 items-center">
          <div class="flex items-center gap-1">
            <button class="qtyBtn w-6 h-6 bg-nasa-card border border-nasa-border rounded text-white" data-idx="${idx}" data-delta="-1">-</button>
            <span class="px-2 font-bold text-nasa-cyan">${c.qty}</span>
            <button class="qtyBtn w-6 h-6 bg-nasa-card border border-nasa-border rounded text-white" data-idx="${idx}" data-delta="1">+</button>
          </div>
          <div>
            <label class="text-[9px] text-slate-400 block">Unit Selling Price / Tawad:</label>
            <select class="priceSelect w-full p-1 bg-nasa-panel border ${below?'border-nasa-red text-nasa-red':'border-nasa-border text-nasa-green'} rounded text-right font-bold focus:outline-none" data-idx="${idx}">
              <option value="${c.price}" ${c.selectedPrice==c.price?'selected':''}>Regular ${money(c.price)}</option>
              <option value="${c.min_price}" ${c.selectedPrice==c.min_price?'selected':''}>Min ${money(c.min_price)}</option>
            </select>
          </div>
        </div>
        ${below ? '<div class="text-nasa-red text-[10px]">Warning: Below last price limit</div>' : ''}
      `;
      this.cartItems.appendChild(row);
    });
    this.totalEl.textContent = money(total);
    if (window.lucide) lucide.createIcons();
    this.renderProducts();
    // bind events
    this.cartItems.querySelectorAll('.priceSelect').forEach(s => {
      s.addEventListener('change', (e) => {
        const idx = parseInt(s.dataset.idx);
        this.cart[idx].selectedPrice = parseFloat(s.value);
        this.renderCart();
      });
    });
    this.cartItems.querySelectorAll('.qtyBtn').forEach(b => {
      b.addEventListener('click', () => {
        const idx = parseInt(b.dataset.idx);
        const delta = parseInt(b.dataset.delta);
        const c = this.cart[idx];
        const newQty = c.qty + delta;
        if (newQty < 1) return;
        if (newQty > c.stock) { showToast('Insufficient stock', 'warning'); return; }
        c.qty = newQty;
        this.renderCart();
      });
    });
    this.cartItems.querySelectorAll('.remBtn').forEach(b => {
      b.addEventListener('click', () => {
        const idx = parseInt(b.dataset.idx);
        this.cart.splice(idx, 1);
        this.renderCart();
      });
    });
  }
  async checkout() {
    if (this._checking) return;
    this._checking = true;
    const btn = document.getElementById('btnCheckout');
    if (btn) btn.disabled = true;
    if (this.cart.length === 0) { showToast('Cart is empty', 'warning'); this._checking = false; if (btn) btn.disabled = false; return; }
    const payment_method = document.getElementById('paymentMethod').value;
    const cash = parseFloat(document.getElementById('cashTendered').value || 0);
    const customer_name = document.getElementById('customerName').value;
    const payload = {
      items: this.cart.map(c => ({ product_id: c.id, quantity: c.qty, selected_price: c.selectedPrice })),
      payment_method,
      cash_tendered: cash,
      customer_name,
      idempotency_key: 'idem-' + Date.now() + '-' + Math.random().toString(36).slice(2)
    };
    try {
      const r = await api.post('/pos/api/checkout', payload);
      const res = document.getElementById('checkoutResult');
      res.classList.remove('hidden');
      res.className = 'nasa-border bg-nasa-panel p-3 rounded font-mono text-xs text-nasa-green mt-2';
      res.textContent = `Sale ${r.sale_number} completed. Total ${money(r.total)}. Change ${money(r.change)}.`;
      this.cart = [];
      this.renderCart();
      this.search(this.searchInput ? this.searchInput.value : '');
    } catch (e) {
      const res = document.getElementById('checkoutResult');
      res.classList.remove('hidden');
      res.className = 'nasa-border bg-nasa-panel p-3 rounded font-mono text-xs text-nasa-red mt-2';
      res.textContent = e.message;
    } finally {
      this._checking = false;
      if (btn) btn.disabled = false;
    }
  }
}
document.addEventListener('DOMContentLoaded', () => { if (document.getElementById('posSearch')) window.pos = new POSController(); });
