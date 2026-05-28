/* Utilities */
function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* Modals: open, close, Escape, click-outside */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-backdrop')) {
    e.target.classList.add('hidden');
  }
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop:not(.hidden)').forEach(m => m.classList.add('hidden'));
  }
});

/* Toasts */
function ensureToastContainer() {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-container';
    c.className = 'toast-container';
    document.body.appendChild(c);
  }
  return c;
}
function showToast(title, subtitle = '', type = 'info', timeout = 3500) {
  const c = ensureToastContainer();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<div><strong>${escapeHtml(title)}</strong>${subtitle ? `<small>${escapeHtml(subtitle)}</small>` : ''}</div>`;
  c.appendChild(t);
  setTimeout(() => {
    t.classList.add('removing');
    setTimeout(() => t.remove(), 220);
  }, timeout);
}

/* Table row state change */
function changeRowState(btn, newBadgeClass, newBadgeText, replaceActions) {
  const row = btn.closest('tr');
  if (!row) return;
  const badge = row.querySelector('.badge');
  if (badge) {
    badge.className = `badge ${newBadgeClass}`;
    badge.textContent = newBadgeText;
  }
  if (replaceActions !== undefined) {
    const actions = row.querySelector('.actions');
    if (actions) actions.innerHTML = replaceActions;
  }
}

/* Destructive confirmation */
function confirmAction(message, onYes) {
  if (window.confirm(message)) onYes();
}

/* Sidebar — rendered from config */
const SIDEBAR_CONFIG = {
  doctor: {
    user: { initials: 'JP', name: 'Dr. Juan Pérez', role: 'Médico' },
    pills: [
      { id: 'panel-medico', icon: '🏠', label: 'Panel Médico', href: 'panel-medico.html' }
    ]
  },
  pharmacy: {
    user: { initials: 'MG', name: 'María González', role: 'Funcionario de Farmacia' },
    pills: [
      { id: 'panel-farmacia',  icon: '🏠', label: 'Panel Farmacia',   href: 'panel-farmacia.html' },
      { id: 'recetas',         icon: '📑', label: 'Recetas',          href: 'recetas.html' },
      { id: 'buscar-paciente', icon: '🔎', label: 'Buscar Paciente',  href: 'buscar-paciente.html' },
      { id: 'gestion-stock',   icon: '📦', label: 'Gestión de Stock', href: 'gestion-stock.html' }
    ]
  }
};

function renderSidebar() {
  const aside = document.getElementById('sidebar');
  if (!aside) return;
  const config = SIDEBAR_CONFIG[aside.dataset.role];
  if (!config) return;

  const active = aside.dataset.active
    || window.location.pathname.split('/').pop().replace('.html', '')
    || 'index';

  const pills = config.pills.map(p =>
    `<a class="nav-pill${p.id === active ? ' active' : ''}" href="${escapeHtml(p.href)}">` +
    `<span class="icon">${p.icon}</span> ${escapeHtml(p.label)}</a>`
  ).join('');

  aside.innerHTML = `
    <div class="brand">
      <div class="brand-logo">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7V3z"/></svg>
      </div>
      <div class="brand-text">
        <strong>CESFAM</strong>
        <small>Sistema de Salud CESFAM<br>Centro de Atención Primaria</small>
      </div>
    </div>
    <div class="user-chip">
      <div class="avatar">${escapeHtml(config.user.initials)}</div>
      <div class="user-chip-text">
        <strong>${escapeHtml(config.user.name)}</strong>
        <small>${escapeHtml(config.user.role)}</small>
      </div>
    </div>
    ${pills}
    <div class="sidebar-footer">
      <a class="logout-link" href="login.html"><span>🚪</span> Cerrar sesión</a>
    </div>
  `;
}

/* Shared modals — injected on pages that opt in */
const SHARED_MODALS = {
  'confirm-pickup': `
<div id="mConfirmPickup" class="modal-backdrop hidden">
  <div class="modal modal-lg">
    <h2>Confirmar Retiro</h2>
    <p class="modal-sub" id="pickup-info">—</p>

    <div class="input-group">
      <label>¿Quién retira?</label>
      <div class="radio-list">
        <label class="radio-row"><input type="radio" name="picker-type" value="patient" checked> El propio paciente</label>
        <label class="radio-row"><input type="radio" name="picker-type" value="guardian"> Un apoderado autorizado</label>
        <select id="pickup-guardian" class="select subfield-indent disabled" disabled>
          <option>Pedri González (hijo) — 18.434.915-K</option>
          <option>Gustavo González (esposo) — 13.464.215-7</option>
        </select>
        <label class="radio-row"><input type="radio" name="picker-type" value="third-party"> Un tercero autorizado verbalmente</label>
        <div class="grid grid-2 subfield-indent disabled" id="pickup-third-party-fields">
          <div class="input-group"><label>RUT del tercero</label><input id="pickup-third-party-rut" class="input" type="text" placeholder="12.345.678-9"></div>
          <div class="input-group"><label>Nombre completo</label><input id="pickup-third-party-name" class="input" type="text" placeholder="Nombre Apellido"></div>
        </div>
      </div>
    </div>

    <div class="input-group mt-3">
      <label>Partida a entregar (FEFO — vence primero)</label>
      <select id="pickup-batch" class="select">
        <option>P-2026-001 — vence 2026-12-15 — disponible: 200</option>
        <option>P-2026-003 — vence 2027-09-22 — disponible: 250</option>
      </select>
    </div>

    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal('mConfirmPickup')">Cancelar</button>
      <button class="btn btn-success" onclick="submitConfirmPickup()">Confirmar Retiro</button>
    </div>
  </div>
</div>`,

  'out-of-stock': `
<div id="mOutOfStock" class="modal-backdrop hidden">
  <div class="modal">
    <h2>Sin stock disponible</h2>
    <p class="modal-sub" id="oos-info">—</p>

    <div class="input-group">
      <label>¿Qué hacer con la receta?</label>
      <div class="radio-card-list">
        <label class="radio-card">
          <input type="radio" name="oos-decision" value="reserve" checked>
          <span><strong>Reservar</strong><br><small>El paciente espera. Se le avisará por SMS/Email cuando llegue stock.</small></span>
        </label>
        <label class="radio-card">
          <input type="radio" name="oos-decision" value="external">
          <span><strong>Comprará en farmacia externa</strong><br><small>No se reserva. Se registra el evento para auditoría interna.</small></span>
        </label>
        <textarea id="oos-notes" class="textarea subfield-indent disabled" placeholder="Observaciones (opcional)" style="min-height:60px;"></textarea>
        <label class="radio-card">
          <input type="radio" name="oos-decision" value="cancel">
          <span><strong>Anular receta</strong><br><small>El paciente desistió del tratamiento.</small></span>
        </label>
      </div>
    </div>

    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal('mOutOfStock')">Cancelar</button>
      <button class="btn btn-primary" onclick="submitOutOfStock()">Confirmar decisión</button>
    </div>
  </div>
</div>`
};

function injectSharedModals() {
  const container = document.getElementById('shared-modals');
  if (!container) return;
  const names = (container.dataset.modals || '').split(',').map(s => s.trim()).filter(Boolean);
  container.innerHTML = names.map(n => SHARED_MODALS[n] || '').join('\n');
}

/* Dependent fields toggled by radio selection */
function toggleDependents(radioName, rules) {
  const v = document.querySelector(`input[name="${radioName}"]:checked`)?.value;
  rules.forEach(({ id, activeOn }) => {
    const el = document.getElementById(id);
    if (!el) return;
    const inactive = activeOn !== v;
    el.classList.toggle('disabled', inactive);
    if (['SELECT', 'INPUT', 'TEXTAREA', 'BUTTON'].includes(el.tagName)) {
      el.disabled = inactive;
    }
  });
}

const togglePickupDependents = () => toggleDependents('picker-type', [
  { id: 'pickup-guardian',           activeOn: 'guardian'    },
  { id: 'pickup-third-party-fields', activeOn: 'third-party' }
]);
const toggleOutOfStockDependents = () => toggleDependents('oos-decision', [
  { id: 'oos-notes', activeOn: 'external' }
]);

document.addEventListener('change', (e) => {
  if (e.target.name === 'picker-type')   togglePickupDependents();
  if (e.target.name === 'oos-decision')  toggleOutOfStockDependents();
});

/* Feature: Confirm Pickup */
let pickupCtx = null;
function openConfirmPickup(btn) {
  pickupCtx = {
    btn,
    prescriptionId: btn.dataset.prescription || '—',
    patient:        btn.dataset.patient      || '—',
    rut:            btn.dataset.rut          || '—',
    medicine:       btn.dataset.medicine     || '—',
    quantity:       btn.dataset.quantity     || '—'
  };
  const info = document.getElementById('pickup-info');
  if (info) {
    info.innerHTML =
      `<strong>${escapeHtml(pickupCtx.patient)}</strong> (${escapeHtml(pickupCtx.rut)})<br>` +
      `Receta <strong>${escapeHtml(pickupCtx.prescriptionId)}</strong> — ${escapeHtml(pickupCtx.medicine)} — ${escapeHtml(pickupCtx.quantity)} unidades`;
  }

  document.querySelectorAll('input[name="picker-type"]').forEach((r, i) => r.checked = i === 0);
  togglePickupDependents();
  openModal('mConfirmPickup');
}
function submitConfirmPickup() {
  if (!pickupCtx) return;
  const v = document.querySelector('input[name="picker-type"]:checked')?.value;
  let pickedUpBy;
  if (v === 'patient') {
    pickedUpBy = `${pickupCtx.patient} (paciente)`;
  } else if (v === 'guardian') {
    pickedUpBy = `${document.getElementById('pickup-guardian').value} (apoderado)`;
  } else {
    const rut  = document.getElementById('pickup-third-party-rut').value  || '?';
    const name = document.getElementById('pickup-third-party-name').value || '?';
    pickedUpBy = `${name} — ${rut} (tercero)`;
  }
  const batch = (document.getElementById('pickup-batch')?.value || '—').split(' — ')[0];
  prescriptionMarkPickedUp(pickupCtx.btn);
  closeModal('mConfirmPickup');
  showToast('Retiro confirmado', `Retiró: ${pickedUpBy} · Partida: ${batch}`, 'success', 5000);
}

/* Feature: Out of Stock */
let outOfStockCtx = null;
function openOutOfStock(btn) {
  outOfStockCtx = {
    btn,
    prescriptionId: btn.dataset.prescription || '—',
    patient:        btn.dataset.patient      || '—',
    medicine:       btn.dataset.medicine     || '—',
    quantity:       btn.dataset.quantity     || '—'
  };
  const info = document.getElementById('oos-info');
  if (info) {
    info.innerHTML =
      `No hay stock de <strong>${escapeHtml(outOfStockCtx.medicine)}</strong> ` +
      `(${escapeHtml(outOfStockCtx.quantity)} requeridas) ` +
      `para la receta <strong>${escapeHtml(outOfStockCtx.prescriptionId)}</strong> de ${escapeHtml(outOfStockCtx.patient)}.`;
  }
  document.querySelectorAll('input[name="oos-decision"]').forEach((r, i) => r.checked = i === 0);
  toggleOutOfStockDependents();
  openModal('mOutOfStock');
}
function submitOutOfStock() {
  if (!outOfStockCtx) return;
  const v = document.querySelector('input[name="oos-decision"]:checked')?.value;
  const btn = outOfStockCtx.btn;

  if (v === 'reserve') {
    changeRowState(btn, 'warning', 'Reservado', '<span class="text-soft" style="font-size:12px;">Esperando partida</span>');
    showToast('Receta reservada', 'Se avisará al paciente cuando llegue stock de este medicamento.', 'warning', 5000);
  } else if (v === 'external') {
    const notes = document.getElementById('oos-notes')?.value || '';
    changeRowState(btn, 'muted', 'Compra externa', '<span class="text-soft" style="font-size:12px;">Cerrada (externa)</span>');
    showToast('Evento registrado', notes ? `"${notes}"` : 'Receta cerrada por compra externa.', 'info', 5000);
  } else {
    changeRowState(btn, 'danger', 'Anulada', '<span class="text-soft" style="font-size:12px;">Anulada</span>');
    showToast('Receta anulada', 'La receta ya no podrá retirarse.', 'danger', 4000);
  }
  closeModal('mOutOfStock');
}

/* Pharmacy prescription queue */
function prescriptionPrepare(btn) {
  const d = btn.dataset;
  const dataAttrs = ['prescription','patient','rut','medicine','quantity']
    .map(k => `data-${k}="${escapeHtml(d[k] || '')}"`).join(' ');
  const newBtn =
    `<button class="btn btn-success btn-sm" ${dataAttrs} onclick="openConfirmPickup(this)">Entregar</button>`;
  changeRowState(btn, 'info', 'Preparado', newBtn);
  showToast('Receta preparada', `${d.medicine || 'Medicamento'} lista para retiro en ventanilla.`, 'info');
}

/* Medicine detail */
function viewMedicineDetail(name) {
  const el = document.getElementById('md-name');
  if (el && name) el.textContent = name;
  openModal('mMedicineDetail');
}

/* Prescription state actions (table) */
function prescriptionMarkPickedUp(btn) {
  changeRowState(btn, 'muted', 'Retirado', '<span class="text-soft" style="font-size:12px;">Retirado ✓</span>');
  showToast('Retiro confirmado', 'Medicamento entregado al paciente. Stock descontado.', 'success');
}
function prescriptionMarkAvailable(btn) {
  changeRowState(btn, 'success', 'Disponible', '<button class="btn btn-success btn-sm" onclick="prescriptionMarkPickedUp(this)">Confirmar Retiro</button>');
  showToast('Receta marcada como disponible', 'Se notificará al paciente vía SMS/Email.', 'info');
}
function prescriptionReserve(btn) {
  changeRowState(btn, 'warning', 'Reservado', '<button class="btn btn-success btn-sm" onclick="prescriptionMarkAvailable(this)">Marcar disponible</button>');
  showToast('Receta reservada', 'Se avisará al paciente cuando llegue stock.', 'warning');
}
function prescriptionCancel(btn) {
  confirmAction('¿Anular esta receta?', () => {
    changeRowState(btn, 'danger', 'Anulada', '<span class="text-soft" style="font-size:12px;">Anulada</span>');
    showToast('Receta anulada', 'La receta no se podrá retirar.', 'danger');
  });
}

/* Bootstrap */
document.addEventListener('DOMContentLoaded', () => {
  renderSidebar();
  injectSharedModals();
});
