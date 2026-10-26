/* Food stories: scroll-driven "from bowl to cake" animation. Loaded only on /stories/ pages. */
(function () {
  "use strict";
  const sc = document.getElementById("fs");
  if (!sc) return;
  const $ = s => sc.querySelector(s);
  const track = $(".fs-track"), sticky = $(".fs-sticky"), stage = $(".fs-stage");
  const bowl = $(".fs-bowl"), bowlImg = bowl.querySelector("img");
  const pour = $(".fs-pour"), pourImg = pour.querySelector("img");
  const layers = $(".fs-layers"), lw = $(".fs-lw"), b1 = $(".fs-b1"), b2 = $(".fs-b2");
  const finalS = $(".fs-final"), finalImg = finalS.querySelector("img");
  const icons = [...sc.querySelectorAll(".fs-ic")], steps = [...sc.querySelectorAll(".fs-steps li")];
  const n = icons.length;
  const hdr = document.getElementById("hdr");
  const setHdr = () => document.documentElement.style.setProperty("--hdr", (hdr ? hdr.offsetHeight : 78) + "px");
  setHdr();

  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    sc.classList.add("static", "end");
    return;
  }
  /* Load every frame up front so nothing pops in mid-scroll */
  sc.querySelectorAll("img[loading]").forEach(i => { i.loading = "eager"; });

  const clamp = v => Math.min(1, Math.max(0, v));
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const range = (a, b, v) => ease(clamp((v - a) / (b - a)));
  let target = 0, current = 0, running = false;

  function measure() {
    const r = track.getBoundingClientRect();
    const top = parseFloat(getComputedStyle(sticky).top) || 0;
    target = clamp((top - r.top) / Math.max(1, r.height - sticky.offsetHeight));
    if (!running) { running = true; requestAnimationFrame(tick); }
  }

  function draw(p) {
    sc.style.setProperty("--p", p.toFixed(4));
    const W = stage.clientWidth, R = W * 0.37;
    /* 1. ingredients rest around the bowl */
    stage.style.setProperty("--lab", (1 - range(0.08, 0.15, p)).toFixed(3));
    const drift = p * 0.4;
    /* 2. they glide into the bowl one after another */
    icons.forEach((ic, i) => {
      const start = 0.1 + i * 0.022, t = range(start, start + 0.11, p);
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / n + drift;
      const rr = R * (1 - t), lift = Math.sin(t * Math.PI) * -W * 0.05;
      ic.style.transform = `translate(-50%,-50%) translate(${(Math.cos(a) * rr).toFixed(1)}px,${(Math.sin(a) * rr + lift).toFixed(1)}px) scale(${(1 - 0.75 * t).toFixed(3)})`;
      ic.style.opacity = (1 - range(start + 0.075, start + 0.11, p)).toFixed(3);
    });
    const mix = range(0.1, 0.42, p);
    bowlImg.style.transform = `rotate(${(mix * 200).toFixed(1)}deg) scale(1.06)`;
    stage.style.setProperty("--glow", (Math.sin(mix * Math.PI) * 0.9).toFixed(3));
    /* the bowl opens into the pour, and the camera eases closer */
    const open = range(0.38, 0.52, p);
    bowl.style.transform = `translate(-50%,-50%) scale(${(1 + open * 0.8).toFixed(3)})`;
    bowl.style.opacity = (1 - range(0.46, 0.52, p)).toFixed(3);
    pour.style.opacity = range(0.37, 0.4, p).toFixed(3);
    pour.style.setProperty("--r", (24 * (1 - open) + 78 * open).toFixed(2) + "%");
    pourImg.style.transform = `scale(${(1.18 - 0.18 * range(0.38, 0.66, p)).toFixed(3)})`;
    /* 3. the layers float in, then press down onto the base */
    const lin = range(0.6, 0.67, p);
    layers.style.opacity = lin.toFixed(3);
    layers.style.transform = `scale(${(1.06 - 0.06 * lin).toFixed(3)})`;
    pour.style.transform = `scale(${(1 + 0.05 * lin).toFixed(3)})`;
    const press = range(0.67, 0.84, p);
    b1.style.transform = `translateY(${(press * 8.6).toFixed(2)}%)`;
    b2.style.transform = `translateY(${(press * 4.2).toFixed(2)}%)`;
    lw.style.transform = `scale(${(1 + 0.1 * press).toFixed(3)})`;
    /* 4. the finished cake */
    finalS.style.opacity = range(0.82, 0.9, p).toFixed(3);
    finalImg.style.transform = `scale(${(1.08 - 0.08 * range(0.82, 1, p)).toFixed(3)})`;
    const idx = p < 0.12 ? 0 : p < 0.6 ? 1 : p < 0.84 ? 2 : 3;
    steps.forEach((s, i) => s.classList.toggle("on", i === idx));
    sc.classList.toggle("end", idx === 3);
  }

  function tick() {
    current += (target - current) * 0.1;
    if (Math.abs(target - current) < 0.0005) current = target;
    draw(current);
    if (current !== target) requestAnimationFrame(tick); else running = false;
  }

  addEventListener("scroll", measure, { passive: true });
  addEventListener("resize", () => { setHdr(); measure(); });
  measure(); current = target; draw(current);
})();
