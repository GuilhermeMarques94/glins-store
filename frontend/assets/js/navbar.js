/* ═══════════════════════════════════════
   GLINS STORE — NAVBAR (injetada em todas as páginas)
═══════════════════════════════════════ */

function renderNavbar() {
  const user    = Auth.getUser();
  const isAdmin = Auth.isAdmin();

  const nav = document.createElement('nav');
  nav.className = 'navbar';
  nav.innerHTML = `
    <div class="container nav-inner">
      <a href="/index.html" class="nav-logo">
        <span class="logo-icon">⚔️</span>
        <span>Glins<span class="logo-accent">Store</span></span>
      </a>

      <button class="nav-toggle" id="navToggle">☰</button>

      <ul class="nav-links" id="navLinks">
        <li><a href="/index.html">🏰 Início</a></li>
        <li><a href="/pages/products.html">⚔️ Produtos</a></li>
        ${user ? `
          <li><a href="/pages/cart.html" class="nav-cart">
            🛒 Carrinho
            <span class="cart-badge" id="cart-badge" style="display:none">0</span>
          </a></li>
          <li><a href="/pages/profile.html">🧙 ${user.name.split(' ')[0]}</a></li>
          ${isAdmin ? `<li><a href="/pages/admin/dashboard.html">👑 Admin</a></li>` : ''}
          <li><a href="#" id="logoutBtn">🚪 Sair</a></li>
        ` : `
          <li><a href="/pages/login.html">🔐 Entrar</a></li>
          <li><a href="/pages/register.html" class="btn btn-primary btn-sm">📜 Cadastrar</a></li>
        `}
      </ul>
    </div>
  `;

  document.body.prepend(nav);

  // Toggle mobile
  document.getElementById('navToggle')?.addEventListener('click', () => {
    document.getElementById('navLinks').classList.toggle('open');
  });

  // Logout
  document.getElementById('logoutBtn')?.addEventListener('click', async (e) => {
    e.preventDefault();
    try { await API.auth.logout(); } catch (_) {}
    Auth.clear();
    window.location.href = '/index.html';
  });

  updateCartBadge();
}

// CSS da navbar inline (evita arquivo extra)
const navStyle = document.createElement('style');
navStyle.textContent = `
  .navbar {
    position: sticky; top: 0; z-index: 1000;
    background: rgba(15,10,6,0.97);
    border-bottom: 1px solid var(--border-gold);
    backdrop-filter: blur(10px);
  }
  .nav-inner {
    display: flex; align-items: center;
    justify-content: space-between;
    height: 64px;
  }
  .nav-logo {
    font-family: var(--font-title);
    font-size: 1.4rem;
    font-weight: 900;
    color: var(--primary) !important;
    display: flex; align-items: center; gap: 8px;
    letter-spacing: 0.05em;
  }
  .logo-accent { color: var(--primary-light); }
  .logo-icon { font-size: 1.6rem; }
  .nav-links {
    display: flex; align-items: center;
    gap: 6px; list-style: none;
  }
  .nav-links a {
    color: var(--text-light);
    padding: 6px 12px;
    border-radius: var(--radius);
    font-size: 0.88rem;
    transition: var(--transition);
    white-space: nowrap;
  }
  .nav-links a:hover { color: var(--primary); background: rgba(201,162,39,0.08); }
  .nav-cart { position: relative; }
  .cart-badge {
    position: absolute; top: -6px; right: -6px;
    background: var(--primary); color: var(--text-dark);
    border-radius: 50%; width: 18px; height: 18px;
    font-size: 0.7rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }
  .nav-toggle { display: none; background: none; border: none; color: var(--primary); font-size: 1.5rem; cursor: pointer; }
  @media (max-width: 768px) {
    .nav-toggle { display: block; }
    .nav-links {
      display: none; flex-direction: column; align-items: flex-start;
      position: absolute; top: 64px; left: 0; right: 0;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
      padding: 16px;
      gap: 4px;
    }
    .nav-links.open { display: flex; }
    .nav-links a { width: 100%; padding: 10px 16px; }
  }
`;
document.head.appendChild(navStyle);

document.addEventListener('DOMContentLoaded', renderNavbar);
