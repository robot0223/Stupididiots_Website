/* Every page and link works without JavaScript; this adds the compact mobile menu. */
const menuButton = document.querySelector('.menu-toggle');
const menu = document.querySelector('#site-navigation');

if (menuButton && menu) {
  document.documentElement.classList.add('js');
  const closeMenu = (focusButton = false) => {
    menuButton.setAttribute('aria-expanded', 'false');
    menu.classList.remove('is-open');
    if (focusButton) menuButton.focus();
  };
  menuButton.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') !== 'true';
    menuButton.setAttribute('aria-expanded', String(open));
    menu.classList.toggle('is-open', open);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') closeMenu(true);
  });
  document.addEventListener('click', (event) => {
    if (!menu.contains(event.target) && !menuButton.contains(event.target)) closeMenu();
  });
  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });
  window.matchMedia('(min-width: 601px)').addEventListener('change', () => closeMenu());
  window.addEventListener('pageshow', () => closeMenu());
}
