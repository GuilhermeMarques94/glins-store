/* ═══════════════════════════════════════
   GLINS STORE — API CLIENT
═══════════════════════════════════════ */

const API_BASE = 'https://glins-store-api.onrender.com/api';

// ── Token helpers ──────────────────────
const Auth = {
  getAccess:  () => localStorage.getItem('access'),
  getRefresh: () => localStorage.getItem('refresh'),
  getUser:    () => JSON.parse(localStorage.getItem('user') || 'null'),
  isAdmin:    () => Auth.getUser()?.is_admin || false,
  isLogged:   () => !!Auth.getAccess(),

  save(data) {
    localStorage.setItem('access',  data.access);
    localStorage.setItem('refresh', data.refresh);
    localStorage.setItem('user',    JSON.stringify(data.user));
  },

  clear() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
  }
};

// ── Fetch wrapper ──────────────────────
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (Auth.isLogged()) {
    headers['Authorization'] = `Bearer ${Auth.getAccess()}`;
  }

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Token expirado → tenta refresh
  if (res.status === 401 && Auth.getRefresh()) {
    const refreshed = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: Auth.getRefresh() })
    });

    if (refreshed.ok) {
      const data = await refreshed.json();
      localStorage.setItem('access', data.access);
      headers['Authorization'] = `Bearer ${data.access}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      Auth.clear();
      window.location.href = '/pages/login.html';
      return;
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw err;
  }

  if (res.status === 204) return null;
  return res.json();
}

// ── API methods ────────────────────────
const API = {

  // ── Auth ──────────────────────────────
  auth: {
    register:       (data) => apiFetch('/auth/register/',        { method: 'POST', body: JSON.stringify(data) }),
    login:          (data) => apiFetch('/auth/login/',           { method: 'POST', body: JSON.stringify(data) }),
    logout:         ()     => apiFetch('/auth/logout/',          { method: 'POST', body: JSON.stringify({ refresh: Auth.getRefresh() }) }),
    profile:        ()     => apiFetch('/auth/profile/'),
    updateProfile:  (data) => apiFetch('/auth/profile/',         { method: 'PUT',  body: JSON.stringify(data) }),
    changePassword: (data) => apiFetch('/auth/change-password/', { method: 'POST', body: JSON.stringify(data) }),
  },

  // ── Products ──────────────────────────
  products: {
    list:      (params = {}) => apiFetch('/products/?' + new URLSearchParams(params)),
    detail:    (id)          => apiFetch(`/products/${id}/`),
    create:    (data)        => apiFetch('/products/',       { method: 'POST',   body: JSON.stringify(data) }),
    update:    (id, data)    => apiFetch(`/products/${id}/`, { method: 'PUT',    body: JSON.stringify(data) }),
    delete:    (id)          => apiFetch(`/products/${id}/`, { method: 'DELETE' }),
    adminList: ()            => apiFetch('/products/admin/all/'),

    // ── Galeria de imagens ──
    getImages:   (id)        => apiFetch(`/products/${id}/images/`),
    deleteImage: (id, imgId) => apiFetch(`/products/${id}/images/${imgId}/`, { method: 'DELETE' }),

    // ✅ Adiciona imagem por URL (JSON, não FormData)
    addImageFile: (id, file, order = 0) => {
      const form = new FormData();
      form.append('image', file);
      form.append('order', order);
      return apiFetch(`/products/${id}/images/`, {
        method: 'POST',
        headers: {}, // sem Content-Type para o browser setar o boundary do multipart
        body: form
      });
    },
  },

  // ── Categories ────────────────────────
  categories: {
    list:   ()      => apiFetch('/products/categories/').then(r => r.results ?? r),
    create: (data)  => apiFetch('/products/categories/',       { method: 'POST',   body: JSON.stringify(data) }),
    update: (id, d) => apiFetch(`/products/categories/${id}/`, { method: 'PUT',    body: JSON.stringify(d) }),
    delete: (id)    => apiFetch(`/products/categories/${id}/`, { method: 'DELETE' }),
  },

  // ── Cart ──────────────────────────────
  cart: {
    get:    ()        => apiFetch('/cart/'),
    add:    (data)    => apiFetch('/cart/',       { method: 'POST',   body: JSON.stringify(data) }),
    update: (id, qty) => apiFetch(`/cart/${id}/`, { method: 'PATCH',  body: JSON.stringify({ quantity: qty }) }),
    remove: (id)      => apiFetch(`/cart/${id}/`, { method: 'DELETE' }),
    clear:  ()        => apiFetch('/cart/',        { method: 'DELETE' }),
  },

  // ── Orders ────────────────────────────
  orders: {
    list:           ()       => apiFetch('/orders/'),
    detail:         (id)     => apiFetch(`/orders/${id}/`),
    create:         (data)   => apiFetch('/orders/', { method: 'POST', body: JSON.stringify(data) }),
    adminList:      (params) => apiFetch('/orders/admin/?' + new URLSearchParams(params || {})),

    // ✅ Detalhe pelo endpoint admin (evita "No Order matches" do endpoint de usuário)
    adminDetail:    (id)     => apiFetch(`/orders/admin/${id}/`),

    adminUpdate:    (id, d)  => apiFetch(`/orders/admin/${id}/`, { method: 'PATCH', body: JSON.stringify(d) }),
    calcShipping:   (data)   => apiFetch('/orders/shipping/',             { method: 'POST', body: JSON.stringify(data) }),
    mpPreference:   (data)   => apiFetch('/orders/payment/preference/',   { method: 'POST', body: JSON.stringify(data) }),
    processPayment: (data)   => apiFetch('/orders/payment/process/',      { method: 'POST', body: JSON.stringify(data) }),
  },
};
