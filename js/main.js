// Scroll-linked text entrances. Settled text does no animation work until its target changes.
// Content and native <details> remain usable without JavaScript.
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const items = [...document.querySelectorAll(".hub-reveal")].map((el) => ({
    el,
    progress: 0,
    target: 0,
    top: 0,
    shift: 0,
  }));
  let frame = 0,
    last = 0;
  const active = new Set();
  const epsilon = 0.0001;
  const clamp = (n) => Math.max(0, Math.min(1, n));
  function measure() {
    items.forEach(
      (item) =>
        (item.top = item.el.getBoundingClientRect().top + scrollY - item.shift),
    );
  }
  function targets() {
    for (const item of items) {
      const target = clamp(
        (scrollY + innerHeight * 0.9 - item.top) / (innerHeight * 0.25),
      );
      if (target === item.target) continue;
      item.target = target;
      if (target !== item.progress) active.add(item);
    }
  }
  function tick(time) {
    const dt = Math.min((time - last) / 1000 || 0.016, 0.064);
    last = time;
    for (const item of active) {
      item.progress +=
        (item.target - item.progress) * (1 - Math.exp(-dt / 0.18));
      if (Math.abs(item.target - item.progress) <= epsilon) {
        item.progress = item.target;
        active.delete(item);
      }
      item.shift = 20 * (1 - item.progress);
      item.el.style.transform = item.progress === 1
        ? "none"
        : "translateY(" + item.shift + "px)";
      item.el.style.opacity = 0.72 + 0.28 * item.progress;
    }
    frame = active.size ? requestAnimationFrame(tick) : 0;
  }
  function update() {
    if (reduce.matches) return;
    targets();
    if (!frame && active.size) {
      last = performance.now();
      frame = requestAnimationFrame(tick);
    }
  }
  function reset() {
    cancelAnimationFrame(frame);
    frame = 0;
    active.clear();
    items.forEach((item) => {
      item.progress = 1;
      item.target = 1;
      item.shift = 0;
      item.el.style.transform = "";
      item.el.style.opacity = "";
    });
    measure();
    update();
  }
  addEventListener("scroll", update, { passive: true });
  addEventListener("resize", () => {
    measure();
    update();
  });
  addEventListener("load", reset);
  reduce.addEventListener("change", reset);
  if ("ResizeObserver" in window)
    new ResizeObserver(() => {
      measure();
      update();
    }).observe(document.body);
  reset();
})();

