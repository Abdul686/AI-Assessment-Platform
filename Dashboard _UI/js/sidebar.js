// (function injectSidebar() {
//   const mount = document.getElementById('sidebar-mount');
//   if (!mount) return;
//   const page = window.location.pathname.split('/').pop();
//   function navItem(href, icon, label, badge) {
//     const active = (href.endsWith(page)) ? 'active' : '';
//     const badgeHtml = badge ? `<span class="nav-badge">${badge}</span>` : '';
//     return `<a href="${href}" class="nav-item ${active}">${icon}${label}${badgeHtml}</a>`;
//   }
//   const icons = {
//     dashboard:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="14" y="3" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="3" y="14" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="14" y="14" width="7" height="7" rx="1.5" stroke-width="2"/></svg>`,
//     create:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke-width="2" stroke-linecap="round"/></svg>`,
//     tests:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke-width="2" stroke-linecap="round"/></svg>`,
//     eval:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke-width="2"/></svg>`,
//     reports:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" stroke-width="2"/><path d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" stroke-width="2"/></svg>`,
//     settings:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" stroke-width="2"/><circle cx="12" cy="12" r="3" stroke-width="2"/></svg>`,
//     logout:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h5a2 2 0 012 2v1" stroke-width="2" stroke-linecap="round"/></svg>`
//   };
//   // Aziro-style logo — matches the hexagon mark from Aziro brand
//   const logoSVG = `<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:26px;height:26px">
//     <path d="M16 2L4 9V23L16 30L28 23V9L16 2Z" fill="white" opacity="0.15"/>
//     <path d="M16 2L4 9L16 16L28 9L16 2Z" fill="white" opacity="0.9"/>
//     <path d="M4 9V23L16 30V16L4 9Z" fill="white" opacity="0.6"/>
//     <path d="M28 9V23L16 30V16L28 9Z" fill="white" opacity="0.35"/>
//   </svg>`;
//   let user = { name: 'HR Admin', role: 'Training Team · L&D', email: '' };
//   try { user = JSON.parse(localStorage.getItem('trainiq_user')) || user; } catch(_) {}
//   const initials = (user.name || 'H').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
//   mount.innerHTML = `
//     <aside class="sidebar">
//       <div class="sidebar-logo">
//         <div class="logo-mark">${logoSVG}</div>
//         <div>
//           <div class="logo-text"><span style="font-weight:400;opacity:0.85">aziro</span> <span style="font-size:10px;opacity:0.6;font-weight:400;letter-spacing:1px">L&D</span></div>
//           <div class="logo-sub">Assessment Platform</div>
//         </div>
//       </div>
//       <div class="sidebar-section">
//         <div class="sidebar-label">Main</div>
//         ${navItem('dashboard.html',       icons.dashboard, 'Dashboard')}
//         ${navItem('create_test.html',     icons.create,    'Create Test')}
//         ${navItem('generated_tests.html', icons.tests,     'Generated Tests', '6')}
//       </div>
//       <div class="sidebar-section">
//         <div class="sidebar-label">Analytics</div>
//         ${navItem('evaluation.html', icons.eval,    'Evaluation')}
//         ${navItem('reports.html',    icons.reports, 'Reports')}
//       </div>
//       <div class="sidebar-section">
//         <div class="sidebar-label">System</div>
//         ${navItem('#', icons.settings, 'Settings')}
//         <a href="#" class="nav-item" onclick="window.logout();return false;">${icons.logout}Logout</a>
//       </div>
//       <div class="sidebar-footer">
//         <div class="user-card">
//           <div class="user-avatar">${initials}</div>
//           <div class="user-info">
//             <div class="user-name">${user.name||'HR Admin'}</div>
//             <div class="user-role">${user.role||'Training Team · L&D'}</div>
//           </div>
//         </div>
//       </div>
//     </aside>`;
// })();

(function injectSidebar() {
  const mount = document.getElementById('sidebar-mount');
  if (!mount) return;
  const page = window.location.pathname.split('/').pop();
  function navItem(href, icon, label, badge) {
    const active = (href.endsWith(page)) ? 'active' : '';
    const badgeHtml = badge ? `<span class="nav-badge">${badge}</span>` : '';
    return `<a href="${href}" class="nav-item ${active}">${icon}${label}${badgeHtml}</a>`;
  }
  const icons = {
    dashboard:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="14" y="3" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="3" y="14" width="7" height="7" rx="1.5" stroke-width="2"/><rect x="14" y="14" width="7" height="7" rx="1.5" stroke-width="2"/></svg>`,
    create:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke-width="2" stroke-linecap="round"/></svg>`,
    tests:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke-width="2" stroke-linecap="round"/></svg>`,
    eval:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke-width="2"/></svg>`,
    reports:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" stroke-width="2"/><path d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" stroke-width="2"/></svg>`,
    settings:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" stroke-width="2"/><circle cx="12" cy="12" r="3" stroke-width="2"/></svg>`,
    logout:`<svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h5a2 2 0 012 2v1" stroke-width="2" stroke-linecap="round"/></svg>`
  };
  // Real Aziro logo from assets
  let user = { name: 'HR Admin', role: 'Training Team · L&D', email: '' };
  try { user = JSON.parse(localStorage.getItem('trainiq_user')) || user; } catch(_) {}
  const initials = (user.name || 'H').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
  mount.innerHTML = `
    <aside class="sidebar">
      <div class="sidebar-logo">
        <img src="../assets/images/logo.avif" alt="Aziro" style="width:42px;height:42px;object-fit:contain;border-radius:8px;flex-shrink:0">
        <div>
          <div class="logo-text" style="font-size:16px;font-weight:700;letter-spacing:-0.3px">aziro <span style="font-size:11px;font-weight:600;color:var(--accent);letter-spacing:0.5px">L&D</span></div>
          <div class="logo-sub">Assessment Platform</div>
        </div>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">Main</div>
        ${navItem('dashboard.html',       icons.dashboard, 'Dashboard')}
        ${navItem('create_test.html',     icons.create,    'Create Test')}
        ${navItem('generated_tests.html', icons.tests,     'Generated Tests', '6')}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">Analytics</div>
        ${navItem('evaluation.html', icons.eval,    'Evaluation')}
        ${navItem('reports.html',    icons.reports, 'Reports')}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">System</div>
        ${navItem('#', icons.settings, 'Settings')}
        <a href="#" class="nav-item" onclick="window.logout();return false;">${icons.logout}Logout</a>
      </div>
      <div class="sidebar-footer">
        <div class="user-card">
          <div class="user-avatar">${initials}</div>
          <div class="user-info">
            <div class="user-name">${user.name||'HR Admin'}</div>
            <div class="user-role">${user.role||'Training Team · L&D'}</div>
          </div>
        </div>
      </div>
    </aside>`;
})();