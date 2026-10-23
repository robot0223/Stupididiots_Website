// Webflow scroll interactions reproduced without the Webflow runtime.
// CSS artwork and radio controls are copied directly from the saved page.
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const ribbon = document.querySelector(".flow-ribbon-layer");
  const track = document.querySelector(".alive-drift-track");
  const reveals = [
    ...document.querySelectorAll(
      ".alive-intro-copy,.alive-play-heading,.alive-together,.alive-manifesto,.alive-notes",
    ),
  ];
  const items = reveals.map((el) => ({ el, p: 0, target: 0, top: 0 }));
  let frame = 0,
    last = 0,
    ribbonP = 0,
    ribbonTarget = 0,
    typeP = 0,
    typeTarget = 0;
  const clamp = (n) => Math.max(0, Math.min(1, n));
  function measure() {
    items.forEach(
      (i) =>
        (i.top =
          i.el.getBoundingClientRect().top +
          scrollY -
          (parseFloat(i.el.dataset.shift) || 0)),
    );
  }
  function targets() {
    const vh = innerHeight;
    items.forEach(
      (i) => (i.target = clamp((scrollY + vh * 0.88 - i.top) / (vh * 0.43))),
    );
    ribbonTarget = clamp(
      scrollY / Math.max(1, document.documentElement.scrollHeight - vh),
    );
    const r = track.getBoundingClientRect();
    typeTarget = clamp((vh - r.top) / (vh + r.height));
  }
  function tick(time) {
    const dt = Math.min((time - last) / 1000 || 0.016, 0.064);
    last = time;
    let moving = false;
    items.forEach((i) => {
      i.p += (i.target - i.p) * (1 - Math.exp(-dt / 0.22));
      const shift = 34 * (1 - i.p);
      i.el.dataset.shift = shift;
      i.el.style.transform = "translateY(" + shift + "px)";
      i.el.style.opacity = 0.55 + 0.45 * i.p;
      moving ||= Math.abs(i.target - i.p) > 0.0001;
    });
    ribbonP += (ribbonTarget - ribbonP) * (1 - Math.exp(-dt / 0.4));
    typeP += (typeTarget - typeP) * (1 - Math.exp(-dt / 0.33));
    ribbon.style.transform =
      "translate(" +
      (-18 + 36 * ribbonP) +
      "px," +
      (-35 + 70 * ribbonP) +
      "px)";
    track.style.transform = "translateX(" + (40 - 260 * typeP) + "px)";
    moving ||=
      Math.abs(ribbonP - ribbonTarget) > 0.0001 ||
      Math.abs(typeP - typeTarget) > 0.0001;
    frame = moving ? requestAnimationFrame(tick) : 0;
  }
  function update() {
    if (reduce.matches) return;
    targets();
    if (!frame) {
      last = performance.now();
      frame = requestAnimationFrame(tick);
    }
  }
  function reset() {
    cancelAnimationFrame(frame);
    frame = 0;
    items.forEach((i) => {
      i.el.style.transform = "";
      i.el.style.opacity = "";
      delete i.el.dataset.shift;
    });
    ribbon.style.transform = "";
    track.style.transform = "";
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
  new ResizeObserver(() => {
    measure();
    update();
  }).observe(document.body);
  reset();
})();
