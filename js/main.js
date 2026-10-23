// Lightweight equivalents of the Webflow ribbon and content scroll interactions.
// Content and native <details> remain usable without JavaScript.
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const ribbon = document.querySelector(".flow-ribbon-layer");
  const items = [...document.querySelectorAll(".hub-reveal")].map((el) => ({
    el,
    progress: 0,
    target: 0,
    top: 0,
    shift: 0,
  }));
  let frame = 0,
    last = 0,
    ribbonProgress = 0,
    ribbonTarget = 0;
  const clamp = (n) => Math.max(0, Math.min(1, n));
  function measure() {
    items.forEach(
      (item) =>
        (item.top = item.el.getBoundingClientRect().top + scrollY - item.shift),
    );
  }
  function targets() {
    items.forEach(
      (item) =>
        (item.target = clamp(
          (scrollY + innerHeight * 0.9 - item.top) / (innerHeight * 0.25),
        )),
    );
    ribbonTarget = clamp(
      scrollY /
        Math.max(1, document.documentElement.scrollHeight - innerHeight),
    );
  }
  function tick(time) {
    const dt = Math.min((time - last) / 1000 || 0.016, 0.064);
    last = time;
    let moving = false;
    items.forEach((item) => {
      item.progress +=
        (item.target - item.progress) * (1 - Math.exp(-dt / 0.18));
      item.shift = 20 * (1 - item.progress);
      item.el.style.transform = "translateY(" + item.shift + "px)";
      item.el.style.opacity = 0.72 + 0.28 * item.progress;
      moving ||= Math.abs(item.target - item.progress) > 0.0001;
    });
    if (ribbon) {
      ribbonProgress +=
        (ribbonTarget - ribbonProgress) * (1 - Math.exp(-dt / 0.4));
      ribbon.style.transform =
        "translate(" +
        (-18 + 36 * ribbonProgress) +
        "px," +
        (-35 + 70 * ribbonProgress) +
        "px)";
      moving ||= Math.abs(ribbonTarget - ribbonProgress) > 0.0001;
    }
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
    items.forEach((item) => {
      item.shift = 0;
      item.el.style.transform = "";
      item.el.style.opacity = "";
    });
    if (ribbon) ribbon.style.transform = "";
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
