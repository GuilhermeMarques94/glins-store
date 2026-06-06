/* ═══════════════════════════════════════
   GLINS STORE — UTILS
═══════════════════════════════════════ */

// ── Toast ──────────────────────────────
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Format ─────────────────────────────
function formatPrice(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency', currency: 'BRL'
  }).format(value);
}

function formatDate(dateStr) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  }).format(new Date(dateStr));
}

// ── Status badge ───────────────────────
function statusBadge(status) {
  const map = {
    pending:   ['badge-muted',   '⏳ Aguardando'],
    paid:      ['badge-success', '✅ Pago'],
    preparing: ['badge-gold',    '🔨 Preparando'],
    shipped:   ['badge-gold',    '🚚 Enviado'],
    delivered: ['badge-success', '📦 Entregue'],
    cancelled: ['badge-danger',  '❌ Cancelado'],
  };
  const [cls, label] = map[status] || ['badge-muted', status];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Guard: redireciona se não logado ───
function requireAuth() {
  if (!Auth.isLogged()) {
    window.location.href = '/pages/login.html';
    return false;
  }
  return true;
}

// ── Guard: redireciona se não admin ────
function requireAdmin() {
  if (!Auth.isLogged() || !Auth.isAdmin()) {
    window.location.href = '/pages/login.html';
    return false;
  }
  return true;
}

// ── Atualiza navbar cart badge ─────────
async function updateCartBadge() {
  if (!Auth.isLogged()) return;
  try {
    const cart = await API.cart.get();
    const badge = document.getElementById('cart-badge');
    if (badge) {
      badge.textContent = cart.quantity || 0;
      badge.style.display = cart.quantity > 0 ? 'flex' : 'none';
    }
  } catch (_) {}
}

// ══════════════════════════════════════════
//  AUTO-PREENCHER ENDEREÇO via ViaCEP
// ══════════════════════════════════════════

/**
 * Inicializa o auto-preenchimento de endereço via ViaCEP.
 * @param {string} cepId       - ID do input de CEP
 * @param {string} streetId    - ID do input de rua
 * @param {string} cityId      - ID do input de cidade
 * @param {string} stateId     - ID do input de estado
 * @param {string} [numberId]  - ID do input de número (recebe foco após preencher)
 */
function initViaCEP(cepId, streetId, cityId, stateId, numberId = null) {
  const cepInput = document.getElementById(cepId);
  if (!cepInput) return;

  cepInput.addEventListener('input', (e) => {
    // Mantém só números
    let val = e.target.value.replace(/\D/g, '');

    // Formata 00000-000
    if (val.length > 5) val = val.slice(0, 5) + '-' + val.slice(5, 8);
    e.target.value = val;

    // Dispara busca quando tiver 8 dígitos
    if (val.replace('-', '').length === 8) fetchViaCEP(val, streetId, cityId, stateId, numberId);
  });
}

async function fetchViaCEP(cep, streetId, cityId, stateId, numberId) {
  const clean = cep.replace(/\D/g, '');
  try {
    const res  = await fetch(`https://viacep.com.br/ws/${clean}/json/`);
    const data = await res.json();

    if (data.erro) {
      showToast('CEP não encontrado', 'error');
      return;
    }

    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el && val) el.value = val;
    };

    set(streetId, data.logradouro);
    set(cityId,   data.localidade);
    set(stateId,  data.uf);

    // Foca no campo de número para o usuário preencher
    if (numberId) {
      const numEl = document.getElementById(numberId);
      if (numEl) numEl.focus();
    }

    showToast('✅ Endereço preenchido!', 'success');

  } catch (_) {
    showToast('Erro ao buscar CEP', 'error');
  }
}
