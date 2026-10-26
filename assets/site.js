/* Tasty Pakistan by Fatma: shared site behaviour */
(function () {
  "use strict";
  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => [...(c || document).querySelectorAll(s)];
  const TP = window.TP || { categories: [], collections: [], recipes: [], ui: {} };
  const U = TP.ui || {};
  const tr = (k, o) => String(U[k] || k).replace(/\{(\w+)\}/g, (m, n) => (o && n in o ? o[n] : m));
  const plural = (k, n, o) => tr(k + (n === 1 ? "_one" : "_other"), Object.assign({ n }, o));
  const low = s => (U.lower ? s.toLowerCase() : s);
  const ROOT = document.body.dataset.root || "/";
  const RTL = document.documentElement.dir === "rtl";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const img = id => "/images/" + id + ".jpg";
  const catOf = id => TP.categories.find(c => c.id === id);
  const colOf = id => TP.collections.find(c => c.id === id);
  const byId = id => TP.recipes.find(r => r.id === id);
  const quick = r => r.mins <= 45;

  /* ---------- Saved recipes (this browser) ---------- */
  let saved = new Set();
  try { saved = new Set(JSON.parse(localStorage.getItem("tp_saved") || "[]")); } catch (e) {}
  const persist = () => { try { localStorage.setItem("tp_saved", JSON.stringify([...saved])); } catch (e) {} };
  function syncSaved() {
    const n = saved.size;
    $$(".badge-count").forEach(b => { b.textContent = n; b.hidden = n === 0; });
    $$("[data-save]").forEach(b => b.setAttribute("aria-pressed", String(saved.has(b.dataset.save))));
    $$("[data-saved-n]").forEach(e => e.textContent = n);
  }
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-save]");
    if (!b) return;
    e.preventDefault();
    const id = b.dataset.save;
    saved.has(id) ? saved.delete(id) : saved.add(id);
    persist(); syncSaved();
    b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop");
    const lbl = b.querySelector("[data-save-label]");
    if (lbl) lbl.textContent = saved.has(id) ? tr("saved") : tr("save_recipe");
    if (window.__tpFilter) window.__tpFilter();
  });
  syncSaved();
  $$("[data-save-label]").forEach(l => { const b = l.closest("[data-save]"); if (b && saved.has(b.dataset.save)) l.textContent = tr("saved"); });

  /* ---------- Header, menu, dropdown ---------- */
  const hdr = $("#hdr");
  const menuBtn = $("#menuBtn");
  if (menuBtn) menuBtn.addEventListener("click", () => { const o = hdr.classList.toggle("open"); menuBtn.setAttribute("aria-expanded", String(o)); });
  const dd = $(".dd");
  if (dd) {
    const btn = $(".dd-btn", dd);
    const set = o => { dd.classList.toggle("open", o); btn.setAttribute("aria-expanded", String(o)); };
    btn.addEventListener("click", e => { e.stopPropagation(); set(!dd.classList.contains("open")); });
    const wide = () => matchMedia("(min-width:1181px)").matches;
    dd.addEventListener("mouseenter", () => wide() && set(true));
    dd.addEventListener("mouseleave", () => wide() && set(false));
    document.addEventListener("click", e => { if (!dd.contains(e.target)) set(false); });
    document.addEventListener("keydown", e => { if (e.key === "Escape") set(false); });
  }

  /* ---------- Language menu ---------- */
  const lang = $("#lang");
  if (lang) {
    const btn = $(".lang-btn", lang);
    const set = o => { lang.classList.toggle("open", o); btn.setAttribute("aria-expanded", String(o)); };
    btn.addEventListener("click", e => { e.stopPropagation(); set(!lang.classList.contains("open")); });
    document.addEventListener("click", e => { if (!lang.contains(e.target)) set(false); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && lang.classList.contains("open")) { set(false); btn.focus(); } });
  }
  /* Keep the current filter (for example #chicken) when switching language */
  $$("a[hreflang]").forEach(a => a.addEventListener("click", () => {
    try { localStorage.setItem("tp_lang", a.getAttribute("hreflang")); } catch (e) {}
    const h = location.hash;
    if (h && h.length > 1 && !a.href.includes("#")) a.href += h;
  }));

  /* ---------- Search forms go to the recipes page ---------- */
  $$("form[data-search]").forEach(f => f.addEventListener("submit", e => {
    e.preventDefault();
    const q = $("input", f).value.trim().toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "-").replace(/^-|-$/g, "");
    location.href = ROOT + "recipes.html#" + (q ? "search-" + q : "all");
  }));

  /* ---------- Steam that rises harder while you scroll ---------- */
  const visible = new Set();
  const io = "IntersectionObserver" in window ? new IntersectionObserver(es => es.forEach(en => en.isIntersecting ? visible.add(en.target) : visible.delete(en.target)), { rootMargin: "40px" }) : null;
  if (io) $$(".steam").forEach(s => io.observe(s));
  let boost = 0, lastY = scrollY, lastPuff = 0;
  function puff(st) {
    if (st.querySelectorAll(".puff").length > 5) return;
    const p = document.createElement("span");
    p.className = "puff";
    p.style.setProperty("--x", (10 + Math.random() * 55) + "%");
    p.style.setProperty("--sx", ((Math.random() - .5) * 40) + "%");
    p.addEventListener("animationend", () => p.remove());
    st.appendChild(p);
  }
  addEventListener("scroll", () => {
    const y = scrollY, dy = Math.abs(y - lastY); lastY = y;
    if (hdr) hdr.classList.toggle("scrolled", y > 10);
    if (reduce) return;
    boost = Math.min(1, boost + dy / 500);
    const now = performance.now();
    if (dy > 2 && now - lastPuff > 110) { lastPuff = now; visible.forEach(s => { if (s.offsetParent) puff(s); }); }
  }, { passive: true });
  const heroMedia = $("#heroMedia");
  (function tick() {
    boost *= 0.95;
    document.documentElement.style.setProperty("--boost", boost.toFixed(3));
    if (heroMedia && !reduce && scrollY < innerHeight * 1.2) heroMedia.style.transform = `translateY(${scrollY * 0.22}px)`;
    requestAnimationFrame(tick);
  })();

  /* ---------- Reveal: below-the-fold blocks drift up (always visible) ---------- */
  if (io && !reduce) {
    const rio = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { en.target.classList.remove("below"); rio.unobserve(en.target); } }), { rootMargin: "0px 0px -8% 0px" });
    $$(".rv").forEach(el => { if (el.getBoundingClientRect().top > innerHeight) { el.classList.add("below"); rio.observe(el); } });
  }

  /* ---------- Category rail arrows ---------- */
  const rail = $("#rail");
  if (rail) {
    const dirn = RTL ? -1 : 1;
    $("#railPrev").addEventListener("click", () => rail.scrollBy({ left: -380 * dirn, behavior: reduce ? "auto" : "smooth" }));
    $("#railNext").addEventListener("click", () => rail.scrollBy({ left: 380 * dirn, behavior: reduce ? "auto" : "smooth" }));
  }

  /* ---------- Home: featured slider ---------- */
  const feat = $("#featured");
  if (feat) {
    const ids = JSON.parse(feat.dataset.ids);
    let i = 0, timer = null;
    const show = n => {
      i = n; const r = byId(ids[n].id); if (!r) return;
      const im = $("#fImg");
      $("#f-title").textContent = r.name;
      $("#fBlurb").textContent = r.intro;
      $("#fEyebrow").textContent = tr("featured") + " · " + r.region;
      $("#fMeta").innerHTML = `<span><svg aria-hidden="true"><use href="#i-clock"/></svg>${esc(r.time)}</span><span><svg aria-hidden="true"><use href="#i-chef"/></svg>${esc(r.level)}</span><span><svg aria-hidden="true"><use href="#i-users"/></svg>${esc(r.serves)}</span>`;
      $("#fOpen").href = ROOT + "recipes/" + r.id + ".html";
      $("#fCat").href = ROOT + "recipes.html#" + r.cat;
      $("#fCat").textContent = tr("more_x", { name: low(catOf(r.cat).name) });
      im.style.opacity = 0;
      setTimeout(() => { im.src = img(ids[n].img || r.id); im.alt = r.name; im.style.opacity = 1; }, reduce ? 0 : 250);
      $$(".thumb").forEach((t, j) => t.setAttribute("aria-pressed", String(j === n)));
    };
    $$(".thumb").forEach((t, j) => t.addEventListener("click", () => { clearInterval(timer); show(j); }));
    if (!reduce) timer = setInterval(() => show((i + 1) % ids.length), 7000);
    feat.addEventListener("pointerenter", () => clearInterval(timer));
  }

  /* ---------- Today's special (rotates daily) ---------- */
  const sp = $("#special");
  if (sp && TP.recipes.length) {
    const r = TP.recipes[Math.floor(Date.now() / 864e5) % TP.recipes.length];
    sp.href = ROOT + "recipes/" + r.id + ".html";
    $("#spImg").src = img(r.id); $("#spImg").alt = r.name;
    $("#spName").textContent = r.name;
    $("#spSub").textContent = r.time + " · " + r.region;
  }

  /* ---------- Recipes page: filter by hash ---------- */
  const grid = $("#grid");
  if (grid) {
    const cards = $$(".card", grid);
    const state = { cat: "all", special: "", q: "" };
    const qInput = $("#q");
    function parse() {
      const h = decodeURIComponent(location.hash.slice(1));
      state.cat = "all"; state.special = ""; state.q = "";
      if (catOf(h)) state.cat = h;
      else if (["veg", "quick", "saved"].includes(h)) state.special = h;
      else if (h.startsWith("col-") && colOf(h.slice(4))) state.special = "col:" + h.slice(4);
      else if (h.startsWith("search-")) state.q = h.slice(7).replace(/-/g, " ");
      if (qInput) qInput.value = state.q;
    }
    function banner() {
      if (state.special === "saved") return { e: tr("b_saved_e"), t: tr("b_saved_t"), d: tr("b_saved_d"), i: "hero_biryani" };
      if (state.special === "veg") return { e: tr("b_quick_e"), t: tr("b_veg_t"), d: tr("b_veg_d"), i: "daal_masoor" };
      if (state.special === "quick") return { e: tr("b_quick_e"), t: tr("b_quick_t"), d: tr("b_quick_d"), i: "matar_pulao" };
      if (state.special.startsWith("col:")) { const c = colOf(state.special.slice(4)); return { e: tr("b_col_e"), t: c.name, d: c.desc, i: c.img }; }
      if (state.cat !== "all") { const c = catOf(state.cat); return { e: tr("b_cat_e"), t: tr("b_cat_t", { name: c.name }), d: c.desc, i: c.img }; }
      return null;
    }
    function apply() {
      let n = 0;
      cards.forEach(c => {
        const d = c.dataset, cols = d.cols ? d.cols.split(" ") : [];
        let ok = true;
        if (state.cat !== "all" && d.cat !== state.cat) ok = false;
        if (state.special === "veg" && d.veg !== "1") ok = false;
        if (state.special === "quick" && +d.mins > 45) ok = false;
        if (state.special === "saved" && !saved.has(d.id)) ok = false;
        if (state.special.startsWith("col:")) { const k = state.special.slice(4); if (k === "quick" ? +d.mins > 45 : !cols.includes(k)) ok = false; }
        if (state.q && !d.text.includes(state.q)) ok = false;
        c.hidden = !ok; if (ok) n++;
      });
      const b = banner(), host = $("#catBanner");
      host.innerHTML = b ? `<div class="cat-banner"><img src="${img(b.i)}" alt=""><div class="cb-body"><div><p class="eyebrow" style="color:var(--gold)">${esc(b.e)}</p><h3>${esc(b.t)}</h3><p class="d">${esc(b.d)}</p></div><a class="btn btn-line" href="#all"><svg aria-hidden="true"><use href="#i-left"/></svg>${esc(tr("all_recipes"))}</a></div></div>` : "";
      $("#count").textContent = state.q ? plural("n_results", n, { q: state.q }) : plural("n_recipes", n);
      $("#empty").hidden = n > 0;
      $("#empty").textContent = state.special === "saved" ? tr("empty_saved") : tr("empty");
      $$(".chip").forEach(c => c.setAttribute("aria-pressed", String(!state.special && !state.q && c.dataset.chip === state.cat)));
      $$("[data-qf]").forEach(b => { const k = b.dataset.qf; b.setAttribute("aria-pressed", String(k.startsWith("cat:") ? (!state.special && state.cat === k.slice(4)) : state.special === k)); });
      $$("[data-col]").forEach(b => b.setAttribute("aria-pressed", String(state.special === "col:" + b.dataset.col)));
    }
    window.__tpFilter = apply;
    function go(hash, scroll) {
      try { history.replaceState(null, "", hash === "all" ? location.pathname : "#" + hash); } catch (e) { location.hash = hash; }
      parse(); apply();
      if (scroll) $("#results").scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    }
    document.addEventListener("click", e => {
      const a = e.target.closest("[data-go]");
      if (!a) return;
      e.preventDefault(); go(a.dataset.go, true);
      if (hdr) hdr.classList.remove("open");
    });
    addEventListener("hashchange", () => { parse(); apply(); });
    if (qInput) qInput.addEventListener("input", () => {
      state.q = qInput.value.trim().toLowerCase(); state.cat = "all"; state.special = "";
      try { history.replaceState(null, "", location.pathname); } catch (e) {}
      apply();
    });
    parse(); apply();
    if (location.hash === "#find" && qInput) qInput.focus();
    else if (location.hash && location.hash !== "#all") setTimeout(() => $("#results").scrollIntoView({ block: "start" }), 50);
  }

  /* ---------- Recipe page: servings, checklist, steps ---------- */
  const serv = $("#serv");
  if (serv) {
    const base = +serv.dataset.base;
    let n = base;
    const FR = { "½": .5, "¼": .25, "¾": .75 };
    const num = t => { t = t.trim(); let m;
      if ((m = t.match(/^(\d+)?([½¼¾])$/))) return (+m[1] || 0) + FR[m[2]];
      if ((m = t.match(/^(\d+)\/(\d+)$/))) return m[1] / m[2];
      return parseFloat(t); };
    const fmt = v => { const w = Math.floor(v + 1e-9), f = v - w;
      const q = Math.round(f * 4) / 4; const part = { 0: "", .25: "¼", .5: "½", .75: "¾", 1: "" }[q];
      const whole = q === 1 ? w + 1 : w;
      if (v >= 10) return String(Math.round(v));
      return (whole ? whole : "") + part || "0"; };
    const NUM = "(\\d+\\s?[½¼¾]|\\d*[½¼¾]|\\d+\\/\\d+|\\d+(?:\\.\\d+)?)";
    const RE = new RegExp("^" + NUM + "(\\s*(?:to|til|سے|-|–)\\s*" + NUM + ")?");
    const lines = $$(".checklist [data-ing]");
    lines.forEach(l => l.dataset.orig = l.textContent);
    function render() {
      $("#servOut").textContent = n + " " + serv.dataset.unit;
      const f = n / base;
      lines.forEach(l => {
        const o = l.dataset.orig, m = o.match(RE);
        if (!m || f === 1) { l.innerHTML = m ? `<span class="q">${esc(m[0])}</span>${esc(o.slice(m[0].length))}` : esc(o); return; }
        let q = fmt(num(m[1].replace(/\s/g, "")) * f);
        if (m[3]) q += (serv.dataset.to || " to ") + fmt(num(m[3]) * f);
        l.innerHTML = `<span class="q">${esc(q)}</span>${esc(o.slice(m[0].length))}`;
      });
    }
    $("#servMinus").addEventListener("click", () => { if (n > 1) { n--; render(); } });
    $("#servPlus").addEventListener("click", () => { if (n < 40) { n++; render(); } });
    render();
  }
  $$(".method button").forEach(b => b.addEventListener("click", () => b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true"))));
  const pr = $("#printBtn");
  if (pr) pr.addEventListener("click", () => window.print());

  /* ---------- Forms ---------- */
  const emailOk = v => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
  const mini = $("#miniForm");
  if (mini) {
    mini.addEventListener("submit", e => {
      e.preventDefault();
      const v = $("#miniEmail").value.trim();
      if (!emailOk(v)) { $("#miniErr").textContent = tr("email_err"); $("#miniEmail").focus(); return; }
      mini.outerHTML = `<p class="mini-ok">${esc(tr("mini_ok"))}</p>`;
      $("#miniErr").textContent = "";
    });
    $("#miniEmail").addEventListener("input", () => { $("#miniErr").textContent = ""; });
  }
  const sub = $("#subForm");
  if (sub) {
    sub.addEventListener("submit", e => {
      e.preventDefault();
      const email = $("#sEmail").value.trim(), name = $("#sName").value.trim();
      if (!emailOk(email)) { $("#sErr").textContent = tr("email_err"); $("#sEmail").focus(); return; }
      const ints = $$('input[name="int"]:checked').map(i => i.value);
      const freq = tr($('input[name="freq"]:checked').value === "weekly" ? "freq_weekly" : "freq_fortnightly");
      $("#subMsg").textContent = tr(name ? "sub_named" : "sub_plain", { name, freq }) + (ints.length ? tr("sub_more", { ints: low(ints.join(U.list_sep || ", ")) }) : tr("sub_end"));
      sub.hidden = true; $("#subDone").hidden = false;
    });
    $("#sEmail").addEventListener("input", () => { $("#sErr").textContent = ""; });
    $("#subAgain").addEventListener("click", () => { $("#subDone").hidden = true; sub.hidden = false; });
  }
  const ask = $("#askForm");
  if (ask) {
    ask.addEventListener("submit", e => {
      e.preventDefault();
      const n = $("#aName").value.trim(), m = $("#aEmail").value.trim(), t = $("#aMsg").value.trim();
      $("#aNameErr").textContent = n ? "" : tr("name_err");
      $("#aEmailErr").textContent = emailOk(m) ? "" : tr("email_err2");
      $("#aMsgErr").textContent = t.length >= 10 ? "" : tr("msg_err");
      if (!n || !emailOk(m) || t.length < 10) { (!n ? $("#aName") : !emailOk(m) ? $("#aEmail") : $("#aMsg")).focus(); return; }
      const topic = $("#aTopic"), topicText = topic.options[topic.selectedIndex].text;
      const mail = "mailto:" + (U.mail_to || "fbrr11@yahoo.com") + "?subject=" + encodeURIComponent(topicText + " · " + n) + "&body=" + encodeURIComponent(t + "\n\n" + n + "\n" + m);
      location.href = mail;
      $("#askMsg").textContent = tr("ask_thanks", { name: n, topic: low(topicText) });
      ask.hidden = true; $("#askDone").hidden = false;
    });
    ["aName", "aEmail", "aMsg"].forEach(id => $("#" + id).addEventListener("input", () => { $("#" + id + "Err").textContent = ""; }));
    $("#askAgain").addEventListener("click", () => { ask.reset(); $("#askDone").hidden = true; ask.hidden = false; });
    const want = decodeURIComponent(location.hash.slice(1));
    if (want === "request" || want === "collab") $("#aTopic").value = want;
  }
})();

