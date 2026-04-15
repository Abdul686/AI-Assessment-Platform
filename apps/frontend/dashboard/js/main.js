/* ============================================================
   TrainIQ L&D Platform — main.js
   Shared across ALL pages. Loaded as <script src="../js/main.js">
   ============================================================ */

/* ── SIDEBAR NAV: auto-highlight active page ── */
(function setActiveNav() {
  const page = window.location.pathname.split('/').pop();
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href') || '';
    if (href === page || href.endsWith(page)) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
})();

/* ── TIME FILTER TABS ── */
document.querySelectorAll('.tf-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.time-filters')
       .querySelectorAll('.tf-btn')
       .forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // Hook: override window.onTimeFilterChange(period) in each page
    if (typeof window.onTimeFilterChange === 'function') {
      window.onTimeFilterChange(btn.textContent.trim());
    }
  });
});

/* ── TOAST ── */
/**
 * showToast(message, type = 'success' | 'error', duration = 3000)
 * Creates a toast if #toast exists, otherwise creates one dynamically.
 */
window.showToast = function(message, type = 'success', duration = 3000) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = 'toast' + (type === 'error' ? ' error' : '');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => toast.classList.add('show'));
  });
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), duration);
};

/* ── MODAL HELPERS ── */
window.openModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
};
window.closeModal = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
};
// Close modal on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});
// Close modal on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open')
            .forEach(m => m.classList.remove('open'));
  }
});

/* ── PILL TOGGLE (course selection) ── */
document.querySelectorAll('.pill[data-toggle]').forEach(pill => {
  pill.addEventListener('click', () => pill.classList.toggle('active'));
});

/* ── FILTER CARDS by search text ── */
window.filterByText = function(inputEl, cardSelector) {
  const q = inputEl.value.toLowerCase();
  document.querySelectorAll(cardSelector).forEach(card => {
    card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
};

/* ── FILTER CARDS by data-status ── */
window.filterByStatus = function(selectEl, cardSelector) {
  const val = selectEl.value;
  document.querySelectorAll(cardSelector).forEach(card => {
    card.style.display = (val === 'all' || card.dataset.status === val) ? '' : 'none';
  });
};

/* ── CHECKBOX "select all" helper ── */
window.setupSelectAll = function(masterCbId, childCbClass, counterId) {
  const master  = document.getElementById(masterCbId);
  const counter = document.getElementById(counterId);

  function refresh() {
    const all     = document.querySelectorAll('.' + childCbClass);
    const checked = document.querySelectorAll('.' + childCbClass + ':checked');
    if (master) {
      master.checked       = checked.length === all.length && all.length > 0;
      master.indeterminate = checked.length > 0 && checked.length < all.length;
    }
    if (counter) counter.textContent = `(${checked.length} selected)`;
  }

  if (master) {
    master.addEventListener('change', () => {
      document.querySelectorAll('.' + childCbClass)
              .forEach(cb => cb.checked = master.checked);
      refresh();
    });
  }
  document.querySelectorAll('.' + childCbClass).forEach(cb => {
    cb.addEventListener('change', refresh);
  });
  refresh();
};

/* ── COPY TO CLIPBOARD ── */
window.copyToClipboard = function(text, feedbackEl) {
  navigator.clipboard.writeText(text).then(() => {
    if (feedbackEl) {
      const orig = feedbackEl.textContent;
      feedbackEl.textContent = '✓ Copied';
      feedbackEl.style.color = 'var(--accent3)';
      setTimeout(() => {
        feedbackEl.textContent = orig;
        feedbackEl.style.color = '';
      }, 1500);
    } else {
      showToast('🔗 Link copied to clipboard!');
    }
  }).catch(() => showToast('Copy failed — please copy manually.', 'error'));
};

/* ── DYNAMIC "ADD CANDIDATE" ROW (Create Test page) ── */
window.addCandidateRow = function(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const idx = container.children.length + 1;
  const row = document.createElement('div');
  row.className = 'candidate-row anim-1';
  row.style.cssText = 'display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;padding:14px 16px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;';
  row.innerHTML = `
    <div class="form-group">
      <label class="form-label">Full Name</label>
      <input type="text" class="form-control" placeholder="Employee ${idx} name">
    </div>
    <div class="form-group">
      <label class="form-label">Work Email</label>
      <input type="email" class="form-control" placeholder="email@company.com">
    </div>
    <button onclick="this.closest('.candidate-row').remove()"
            style="width:32px;height:32px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#f87171;border-radius:7px;cursor:pointer;font-size:15px;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-bottom:1px;">✕</button>
  `;
  container.appendChild(row);
};

/* ── AUTH GUARD ── */
// If not on login page and no session token, redirect.
(function authGuard() {
  const loginPage  = window.location.pathname.includes('login.html');
  const publicTestPage = window.location.pathname.includes('take_test.html');
  const hasSession = localStorage.getItem('trainiq_user');
  if (!loginPage && !publicTestPage && !hasSession) {
    window.location.replace('login.html');
  }
})();

/* ── LOGOUT ── */
window.logout = function() {
  localStorage.removeItem('trainiq_user');
  window.location.replace('login.html');
};

/* ── LOAD USER IN SIDEBAR ── */
(function loadUserInSidebar() {
  const raw = localStorage.getItem('trainiq_user');
  if (!raw) return;
  try {
    const user = JSON.parse(raw);
    const nameEl   = document.querySelector('.user-name');
    const roleEl   = document.querySelector('.user-role');
    const avatarEl = document.querySelector('.user-avatar');
    if (nameEl)   nameEl.textContent   = user.name   || 'HR Admin';
    if (roleEl)   roleEl.textContent   = user.role   || 'Training Team';
    if (avatarEl) avatarEl.textContent = (user.name || 'H').charAt(0).toUpperCase();
  } catch (_) {}
})();

/* ── CHART.JS GLOBAL DEFAULTS ── */
if (typeof Chart !== 'undefined') {
  Chart.defaults.color          = '#5f738f';
  Chart.defaults.font.family    = "'DM Sans', sans-serif";
  Chart.defaults.font.size      = 12;
  Chart.defaults.plugins.legend.display = false;
  Chart.defaults.plugins.tooltip.backgroundColor = '#2d4f95';
  Chart.defaults.plugins.tooltip.borderColor      = 'rgba(255,255,255,0.12)';
  Chart.defaults.plugins.tooltip.borderWidth      = 1;
  Chart.defaults.plugins.tooltip.padding          = 10;
  Chart.defaults.plugins.tooltip.titleColor       = '#f5f9ff';
  Chart.defaults.plugins.tooltip.bodyColor        = '#dde8ff';
  Chart.defaults.scale.grid.color                 = 'rgba(53,92,168,0.12)';
  Chart.defaults.scale.ticks.color                = '#5f738f';
}

/* ── SIDEBAR NAV ICON SVGs (injected via JS to keep HTML DRY) ── */
// Not used here — icons are inline in each HTML file for clarity.

console.log('%cTrainIQ L&D Platform loaded ✓', 'color:#355ca8;font-weight:bold;font-size:13px');
