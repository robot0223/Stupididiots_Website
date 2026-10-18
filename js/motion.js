/* Optional movement. Nothing starts hidden, and the site works without this file. */
(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('.motion-toggle');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const pointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const visual = document.querySelector('.intro-visual');
  const intro = document.querySelector('.home-intro');
  const reveals = new Set();
  const storageKey = 'stupididiots-motion-paused';
  let paused = false;
  let frame = 0;

  try { paused = localStorage.getItem(storageKey) === 'true'; } catch (_) { /* Storage is optional. */ }
  const enabled = () => Boolean(toggle) && !paused && !preference.matches && !document.hidden;
  const resetPointer = () => {
    if (!visual) return;
    visual.style.removeProperty('--orbit-x');
    visual.style.removeProperty('--orbit-y');
  };
  const updateMotion = () => {
    root.classList.toggle('motion-enabled', Boolean(toggle) && !preference.matches);
    root.classList.toggle('motion-paused', !enabled());
    if (toggle) {
      toggle.hidden = preference.matches;
      toggle.textContent = paused ? 'Resume motion' : 'Pause motion';
      toggle.setAttribute('aria-label', paused ? 'Resume animations' : 'Pause animations');
      toggle.setAttribute('aria-pressed', String(paused));
      toggle.title = paused ? 'Resume animations' : 'Pause animations';
    }
    if (!enabled()) {
      resetPointer();
      reveals.forEach(animation => animation.cancel());
      reveals.clear();
    }
  };
  if (toggle) toggle.addEventListener('click', () => {
    paused = !paused;
    try { localStorage.setItem(storageKey, String(paused)); } catch (_) { /* Ignore unavailable storage. */ }
    updateMotion();
  });
  preference.addEventListener('change', updateMotion);
  document.addEventListener('visibilitychange', updateMotion);
  updateMotion();

  if (intro && visual) {
    intro.addEventListener('pointermove', event => {
      if (!enabled() || !pointer.matches || frame) return;
      const bounds = intro.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width - .5) * 16;
      const y = ((event.clientY - bounds.top) / bounds.height - .5) * 12;
      frame = requestAnimationFrame(() => {
        if (enabled()) {
          visual.style.setProperty('--orbit-x', `${x.toFixed(2)}px`);
          visual.style.setProperty('--orbit-y', `${y.toFixed(2)}px`);
        }
        frame = 0;
      });
    }, { passive: true });
    intro.addEventListener('pointerleave', resetPointer);
  }

  // Reveal is a short, one-time enhancement, never a visibility requirement.
  if ('IntersectionObserver' in window && typeof Element.prototype.animate === 'function') {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        if (!enabled()) return;
        const animation = entry.target.animate([
          { opacity: .72, transform: 'translateY(15px)' },
          { opacity: 1, transform: 'translateY(0)' }
        ], { duration: 650, easing: 'cubic-bezier(.22,1,.36,1)' });
        reveals.add(animation);
        animation.onfinish = () => reveals.delete(animation);
        animation.oncancel = () => reveals.delete(animation);
      });
    }, { threshold: .07, rootMargin: '0px 0px -25px 0px' });
    document.querySelectorAll('[data-reveal], .project-card, .project-row, .about-preview, .notes-preview, .journal-card').forEach(element => observer.observe(element));
  }
})();
