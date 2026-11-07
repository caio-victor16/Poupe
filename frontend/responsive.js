document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.app-sidebar');
  if (!sidebar) return;
  const nav = sidebar.querySelector('.nav-container');
  const brand = sidebar.querySelector('.brand-wrapper');
  if (!nav || !brand) return;
  nav.id = nav.id || 'site-navigation';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'navigation-toggle';
  toggle.setAttribute('aria-controls', nav.id);
  toggle.setAttribute('aria-label', 'Abrir menu de navegação');
  toggle.setAttribute('aria-expanded', 'false');
  toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
  brand.appendChild(toggle);
  function fechar(devolverFoco = false) {
    sidebar.classList.remove('navigation-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Abrir menu de navegação');
    if (devolverFoco) toggle.focus();
  }
  toggle.addEventListener('click', () => {
    const aberto = sidebar.classList.toggle('navigation-open');
    toggle.setAttribute('aria-expanded', String(aberto));
    toggle.setAttribute('aria-label', aberto ? 'Fechar menu de navegação' : 'Abrir menu de navegação');
  });
  document.addEventListener('click', event => { if (!sidebar.contains(event.target)) fechar(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && sidebar.classList.contains('navigation-open')) fechar(true);
  });
  sidebar.addEventListener('focusout', event => {
    if (event.relatedTarget && !sidebar.contains(event.relatedTarget)) fechar();
  });
  matchMedia('(max-width: 900px)').addEventListener('change', () => fechar());
});
