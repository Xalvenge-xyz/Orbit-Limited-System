document.addEventListener('DOMContentLoaded', async () => {
  if (!document.getElementById('empTableBody')) return;
  const tbody = document.getElementById('empTableBody');
  async function load() {
    const users = await api.get('/employees/api/list');
    const roles = await api.get('/employees/api/roles');
    tbody.innerHTML = '';
    users.forEach(u => {
      const tr = document.createElement('tr');
      const roleOpts = roles.map(r => `<option value="${r.id}" ${r.name===u.role?'selected':''}>${r.name}</option>`).join('');
      tr.innerHTML = `<td class="p-3">${u.full_name}</td><td class="p-3">${u.email}</td><td class="p-3"><select data-role="${u.id}" class="bg-nasa-bg border border-nasa-border rounded text-white text-[10px] p-1">${roleOpts}</select></td><td class="p-3 ${u.status==='approved'?'text-nasa-green':'text-nasa-red'}">${u.status}</td>
        <td class="p-3 text-center space-x-1">
          ${u.status!=='approved'?`<button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-green text-[10px] hover:bg-nasa-green hover:text-black" data-approve="${u.id}">Approve</button>`:''}
          ${u.status!=='suspended'?`<button class="px-2 py-1 bg-nasa-bg border border-nasa-border rounded text-nasa-red text-[10px] hover:bg-nasa-red hover:text-white" data-suspend="${u.id}">Suspend</button>`:''}
        </td>`;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('select[data-role]').forEach(sel => {
      sel.addEventListener('change', async () => {
        try { await api.post('/employees/api/' + sel.dataset.role + '/role', { role_id: parseInt(sel.value) }); } catch(e){ showToast(e.message, 'error'); }
      });
    });
    tbody.querySelectorAll('button[data-approve]').forEach(b => {
      b.onclick = async () => { await api.post('/employees/api/' + b.dataset.approve + '/approve', {}); load(); };
    });
    tbody.querySelectorAll('button[data-suspend]').forEach(b => {
      b.onclick = async () => { if(!(await showConfirm('Suspend this account?'))) return; await api.post('/employees/api/' + b.dataset.suspend + '/suspend', {}); load(); };
    });
  }
  load();
});
