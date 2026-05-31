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
