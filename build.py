#!/usr/bin/env python3
"""Build the Tasty Pakistan by Fatma website in English, Danish and Urdu.

Content lives in data/:
  recipes.json, journal.json, spices.json   English source content
  i18n/ui.json                              interface text for every language
  i18n/<lang>/recipes.json, journal.json, spices.json
                                            translations, keyed by recipe id or slug

Shared page sections live in src/ (English) and src/<lang>/ (translations).

Run `python3 build.py` after editing any of these. English is written to the site
root, Danish to da/ and Urdu to ur/, with the same file names in each:

  index.html, recipes.html, story.html, ask.html, journal.html, spices.html
  recipes/<recipe-id>.html, journal/<slug>.html, spices/<slug>.html
  assets/data.js, assets/data.da.js, assets/data.ur.js   data for the recipe filters

Run `python3 build.py --strict` to stop the build if any translation is missing.
"""
import copy
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "Tasty Pakistan by Fatma"

# The live address, used for canonical links, hreflang, sitemap.xml and robots.txt.
SITE_URL = "https://tasty-pakistan.vercel.app"

# English stays at the site root. Each language has its own folder and settings.
LANGS = {
    "en": {"prefix": "", "dir": "ltr", "code": "EN", "flag": "flag-gb", "native": "English", "locale": "en_GB"},
    "da": {"prefix": "da/", "dir": "ltr", "code": "DA", "flag": "flag-dk", "native": "Dansk", "locale": "da_DK"},
    "ur": {"prefix": "ur/", "dir": "rtl", "code": "UR", "flag": "flag-pk", "native": "اردو", "locale": "ur_PK"},
}
ORDER = ["en", "da", "ur"]

# Words in a recipe's English ingredients that link to a spice guide.
SPICE_WORDS = {
    "haldi-turmeric": ["turmeric", "haldi"],
    "zeera-cumin": ["cumin", "zeera"],
    "dhaniya-coriander": ["coriander", "dhaniya"],
    "lal-mirch-red-chilli": ["red chilli", "chilli powder", "kashmiri chilli", "red chillies"],
    "kali-mirch-black-pepper": ["black pepper", "peppercorns"],
    "elaichi-cardamom": ["cardamom", "elaichi"],
    "dalchini-cinnamon": ["cinnamon"],
    "laung-cloves": ["cloves"],
    "adrak-ginger": ["ginger"],
    "lehsan-garlic": ["garlic"],
}

# Home page choices: change these ids to feature different dishes.
FEATURED = [{"id": "chicken_biryani", "img": "hero_biryani"}, {"id": "beef_nihari"}, {"id": "chicken_karahi"}, {"id": "zarda"}]
PICKS = ["chicken_karahi", "kabli_pulao", "beef_haleem", "golgappay", "chicken_qorma", "gulab_jamun"]
WEEK = "beef_nihari"
STORY_GALLERY = ["kabli_pulao", "golgappay", "beef_nihari", "gulab_jamun", "balochi_kaak", "chicken_qorma"]


def load(*p):
    path = os.path.join(HERE, "data", *p)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


EN_DATA = load("recipes.json")
EN_JOURNAL = load("journal.json")["posts"]
EN_SPICES = load("spices.json")["spices"]
EN_BY_ID = {r["id"]: r for r in EN_DATA["recipes"]}
UI = load("i18n", "ui.json")
MISSING = []
OPTIONAL = {"latin"}  # translated only where the English value needs it

e = lambda s: html.escape(str(s), quote=True)


def ver(path):
    """Short content hash, so browsers fetch a file again whenever it changes."""
    import hashlib
    return hashlib.md5(open(os.path.join(HERE, path.lstrip("/")), "rb").read()).hexdigest()[:8]


# ---------------------------------------------------------------- language state
class Lang:
    """Everything that changes between languages, set by use(lang)."""


L = Lang()


def overlay(items, tr, key, fields, kind):
    """Copy English items and replace text fields with the translation."""
    out = []
    for it in items:
        it = copy.deepcopy(it)
        t = tr.get(it[key])
        if t is None:
            if L.id != "en":
                MISSING.append(f"{L.id}: {kind} {it[key]}")
        else:
            for f in fields:
                if f in t:
                    it[f] = t[f]
                elif f in it and f not in OPTIONAL and L.id != "en":
                    MISSING.append(f"{L.id}: {kind} {it[key]}.{f}")
        out.append(it)
    return out


def use(lang):
    L.id = lang
    L.meta = LANGS[lang]
    L.root = "/" + L.meta["prefix"]          # this language's home folder
    L.ui = UI[lang]
    tr = load("i18n", lang, "recipes.json") if lang != "en" else {}
    L.cats = overlay(EN_DATA["categories"], tr.get("categories", {}), "id", ["name", "desc"], "category")
    L.cols = overlay(EN_DATA["collections"], tr.get("collections", {}), "id", ["name", "desc"], "collection")
    L.recipes = overlay(EN_DATA["recipes"], tr.get("recipes", {}), "id", ["name", "intro", "ing", "steps", "tip"], "recipe")
    for r in L.recipes:  # short labels come from the ui maps
        for f in ("time", "level", "serves", "region"):
            r[f] = label(f, EN_BY_ID[r["id"]][f])
    L.by_id = {r["id"]: r for r in L.recipes}
    L.cat = {c["id"]: c for c in L.cats}
    L.col = {c["id"]: c for c in L.cols}
    jt = load("i18n", lang, "journal.json") if lang != "en" else {}
    L.journal = overlay(EN_JOURNAL, jt, "slug", ["tag", "title", "read", "summary", "lead", "body"], "journal")
    st = load("i18n", lang, "spices.json") if lang != "en" else {}
    L.spices = overlay(EN_SPICES, st, "slug", ["name", "local", "latin", "title", "meta", "lead", "sections", "faq", "sources_label"], "spice")
    for s in L.spices:
        s.setdefault("name", s["urdu"])
        s.setdefault("local", s["english"])
    L.sprite = open(os.path.join(HERE, "src", "sprite.svg"), encoding="utf-8").read()


def t(key, **kw):
    v = L.ui.get(key)
    if v is None:
        if L.id != "en":
            MISSING.append(f"{L.id}: ui {key}")
        v = UI["en"][key]
    return v.format(**kw) if kw else v


def tn(key, n):
    """A count with the right singular or plural word, for example '1 recipe'."""
    return t(key + ("_one" if n == 1 else "_other"), n=n)


def label(kind, value):
    if L.id == "en":
        return value
    v = L.ui.get("map_" + kind, {}).get(value)
    if v is None:
        MISSING.append(f"{L.id}: {kind} {value!r}")
        return value
    return v


def src(name):
    p = os.path.join(HERE, "src", L.id, name)
    if L.id == "en" or not os.path.exists(p):
        if L.id != "en":
            MISSING.append(f"{L.id}: template {name}")
        p = os.path.join(HERE, "src", name)
    return open(p, encoding="utf-8").read()


def ico(i, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} aria-hidden="true"><use href="#{i}"/></svg>'


def steam(n):
    return '<div class="steam" aria-hidden="true">' + "<i></i>" * n + "</div>"


def img(name):
    return f"/images/{name}.jpg"


def quick(r):
    return r["mins"] <= 45


def in_col(r, cid):
    return quick(r) if cid == "quick" else cid in r.get("cols", [])


def count_cat(cid):
    return sum(1 for r in L.recipes if r["cat"] == cid)


def search_text(r):
    """Words the recipe filter searches: this language plus the English names."""
    en = EN_BY_ID[r["id"]]
    parts = [r["name"], r["region"], L.cat[r["cat"]]["name"], " ".join(r["ing"]), en["name"], " ".join(en["ing"])]
    return " ".join(parts).lower()


def url(path):
    return SITE_URL.rstrip("/") + "/" + LANGS[L.id]["prefix"] + ("" if path == "index.html" else path)


# ---------------------------------------------------------------- layout
def lang_switch(path):
    opts = ""
    for k in ORDER:
        m = LANGS[k]
        on = k == L.id
        href = "/" + m["prefix"] + ("" if path == "index.html" else path)
        cur = ' aria-current="true"' if on else ""
        opts += (f'<a class="lang-opt{" on" if on else ""}" href="{href}" hreflang="{k}" lang="{k}" data-lang="{k}"{cur}>'
                 f'<span class="flag">{ico(m["flag"])}</span><span class="lang-txt"><b>{e(m["native"])}</b>'
                 f'<small>{e(t("lang_" + k))}</small></span>{ico("i-check", "tick")}</a>')
    me = L.meta
    return f'''<div class="lang" id="lang">
        <button class="lang-btn" type="button" aria-expanded="false" aria-controls="langPanel" aria-label="{e(t("lang_label"))}: {e(me["native"])}">
          <span class="flag">{ico(me["flag"])}</span><b>{me["code"]}</b>{ico("i-chev", "car")}
        </button>
        <div class="lang-panel" id="langPanel">
          <p class="lang-h">{e(t("lang_choose"))}</p>
          {opts}
        </div>
      </div>'''


def header(active, path):
    R = L.root

    def link(href, label, key):
        on = ' class="on" aria-current="page"' if key == active else ""
        return f'<a href="{R}{href}"{on}>{label}</a>'
    dd = "".join(
        f'<a href="{R}recipes.html#{c["id"]}"><img src="{img(c["img"])}" alt="" loading="lazy"><span><b>{e(c["name"])}</b><small>{tn("n_recipes", count_cat(c["id"]))}</small></span></a>'
        for c in L.cats)
    return f'''<header class="site" id="hdr">
  <div class="wrap bar">
    <a class="brand" href="{R}" aria-label="{SITE}, {e(t("home"))}">
      <svg aria-hidden="true"><use href="#logo"/></svg>
      <span><b>Tasty Pakistan</b><small>by Fatma</small></span>
    </a>
    <nav class="links" id="nav" aria-label="{e(t("nav_main"))}">
      {link("", t("home"), "home")}
      {link("recipes.html", t("recipes"), "recipes")}
      <div class="dd">
        <button class="dd-btn" type="button" aria-expanded="false" aria-controls="ddPanel">{t("categories")} {ico("i-chev")}</button>
        <div class="dd-panel" id="ddPanel">{dd}<a class="dd-all" href="{R}recipes.html">{t("view_all_recipes")}</a></div>
      </div>
      {link("journal.html", t("journal"), "journal")}
      {link("story.html", t("fatmas_story"), "story")}
      {link("ask.html", t("ask_fatma"), "ask")}
    </nav>
    <div class="bar-actions">
      {lang_switch(path)}
      <a class="ico-btn" href="{R}recipes.html#find" aria-label="{e(t("search_recipes"))}">{ico("i-search")}</a>
      <a class="ico-btn" href="{R}recipes.html#saved" aria-label="{e(t("saved_recipes"))}">{ico("i-heart")}<span class="badge-count" hidden>0</span></a>
      <a class="btn btn-gold sub-btn" href="#subscribe">{t("subscribe")}</a>
      <button class="ico-btn menu-btn" id="menuBtn" type="button" aria-label="{e(t("open_menu"))}" aria-expanded="false" aria-controls="nav">{ico("i-menu")}</button>
    </div>
  </div>
</header>'''


def footer(path):
    R = L.root
    cats = "".join(f'<li><a href="{R}recipes.html#{c["id"]}">{e(c["name"])}</a></li>' for c in L.cats)
    cols = "".join(f'<li><a href="{R}recipes.html#col-{c["id"]}">{e(c["name"])}</a></li>' for c in L.cols)
    langs = "".join(
        f'<a href="/{LANGS[k]["prefix"]}{"" if path == "index.html" else path}" hreflang="{k}" lang="{k}"{" aria-current=true" if k == L.id else ""}>{e(LANGS[k]["native"])}</a>'
        for k in ORDER)
    return f'''<footer>
  <div class="wrap">
    <div class="foot-top">
      <a class="brand" href="{R}" aria-label="{SITE}, {e(t("home"))}"><svg aria-hidden="true"><use href="#logo"/></svg><span><b>Tasty Pakistan</b><small>by Fatma</small></span></a>
      <p>{t("foot_tagline")}</p>
      <a class="btn btn-gold" href="#subscribe">{t("get_letter")} {ico("i-arrow")}</a>
    </div>
    <div class="foot">
      <div><h4>{t("recipes")}</h4><ul>{cats}</ul></div>
      <div><h4>{t("collections")}</h4><ul>{cols}<li><a href="{R}recipes.html#veg">{t("vegetarian")}</a></li></ul></div>
      <div><h4>{t("read")}</h4><ul><li><a href="{R}journal.html">{t("journal")}</a></li><li><a href="{R}spices.html">{t("spice_guide")}</a></li><li><a href="{R}story.html">{t("fatmas_story")}</a></li><li><a href="#subscribe">{t("sunday_letter")}</a></li></ul></div>
      <div><h4>{t("talk")}</h4><ul><li><a href="{R}ask.html">{t("ask_fatma")}</a></li><li><a href="{R}ask.html#request">{t("recipe_requests")}</a></li><li><a href="{R}ask.html#collab">{t("collaborations")}</a></li></ul></div>
    </div>
    <div class="copyline"><span>© 2026 {SITE}</span><span class="foot-langs">{langs}</span><span>{t("made_with")}</span></div>
  </div>
</footer>'''


FONTS = {
    "base": "family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500&family=Great+Vibes",
    "ur": "&family=Noto+Nastaliq+Urdu:wght@400;500;600",
}


def page(path, title, desc, main, active="", image="hero_biryani", head_extra="", suffix=True, noindex=False):
    """Write one page. `path` is the same in every language, for example recipes/zarda.html."""
    full_title = title if (title == SITE or not suffix) else f"{title} · {SITE}"
    L.pages.append(path)
    head = ""
    if SITE_URL:
        head += f'<link rel="canonical" href="{url(path)}">\n'
        if not noindex:
            for k in ORDER:
                href = SITE_URL.rstrip("/") + "/" + LANGS[k]["prefix"] + ("" if path == "index.html" else path)
                head += f'<link rel="alternate" hreflang="{k}" href="{href}">\n'
            head += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL.rstrip("/")}/{"" if path == "index.html" else path}">\n'
    if noindex:
        head += '<meta name="robots" content="noindex">\n'
    fonts = FONTS["base"] + (FONTS["ur"] if L.id == "ur" else "")
    # Other languages load only the Nastaliq letters for the word اردو in the language menu.
    ur_word = "" if L.id == "ur" else '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&text=%D8%A7%D8%B1%D8%AF%D9%88&display=swap">\n'
    data_js = "/assets/data.js" if L.id == "en" else f"/assets/data.{L.id}.js"
    body = (L.sprite + "\n" + header(active, path) + f'\n<main id="top">\n{main}\n</main>\n'
            + src("sub.html") + "\n" + footer(path))
    doc = f'''<!doctype html>
<html lang="{L.id}" dir="{L.meta["dir"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0F2F23">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE_URL.rstrip("/")}/images/{image}.jpg">
<meta property="og:type" content="website">
<meta property="og:locale" content="{L.meta["locale"]}">
<meta property="og:site_name" content="{SITE}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
{ur_word}<link rel="stylesheet" href="/assets/style.css?v={ver("assets/style.css")}">
{head}{head_extra}</head>
<body data-root="{L.root}">
{body}
<script src="{data_js}?v={ver(data_js)}"></script>
<script src="/assets/site.js?v={ver("assets/site.js")}"></script>
</body>
</html>
'''
    doc = doc.replace("{{root}}", L.root).replace("{{img}}", "/images/")
    out = os.path.join(HERE, L.meta["prefix"], path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)


# ---------------------------------------------------------------- pieces
def card(r, rv=False):
    c = L.cat[r["cat"]]
    veg = f'<span>{ico("i-leaf")}{t("veg")}</span>' if r.get("veg") else ""
    return f'''<article class="card{' rv' if rv else ''}" data-id="{r["id"]}" data-cat="{r["cat"]}" data-veg="{1 if r.get("veg") else 0}" data-mins="{r["mins"]}" data-cols="{" ".join(r.get("cols", []))}" data-text="{e(search_text(r))}">
  <div class="media"><img src="{img(r["id"])}" alt="" loading="lazy">{steam(3)}<span class="tag">{e(c["name"])}</span>
    <button class="heart" type="button" data-save="{r["id"]}" aria-pressed="false" aria-label="{e(t("save_x", name=r["name"]))}">{ico("i-heart")}</button></div>
  <div class="card-body">
    <span class="region">{e(r["region"])}</span>
    <h3><a class="card-link" href="{L.root}recipes/{r["id"]}.html">{e(r["name"])}</a></h3>
    <span class="facts"><span>{ico("i-clock")}{e(r["time"])}</span><span>{ico("i-chef")}{e(r["level"])}</span>{veg}</span>
  </div>
</article>'''


def page_head(crumbs, title_html, sub, image, eyebrow=""):
    cr = f'<a href="{L.root}">{t("home")}</a>'
    for lbl, href in crumbs:
        cr += '<span aria-hidden="true" class="sep">/</span>' + (f'<a href="{href}">{e(lbl)}</a>' if href else f'<span>{e(lbl)}</span>')
    eb = f'<p class="eyebrow" style="margin-top:18px">{e(eyebrow)}</p>' if eyebrow else ""
    return f'''<section class="page-head">
  <div class="ph-img"><img src="{img(image)}" alt=""></div>
  <div class="wrap">
    <nav class="crumbs" aria-label="{e(t("breadcrumb"))}">{cr}</nav>
    {eb}
    <h1>{title_html}</h1>
    <p class="ph-sub">{e(sub)}</p>
  </div>
</section>'''


def post_card(p):
    return f'''<article class="post rv">
  <a class="stretch" href="{L.root}journal/{p["slug"]}.html">
    <div class="media"><span class="post-tag">{e(p["tag"])}</span><img src="{img(p["img"])}" alt="" loading="lazy">{steam(3)}</div>
    <h3 style="margin-top:14px">{e(p["title"])}</h3>
  </a>
  <p>{e(p["summary"])}</p>
  <span class="read">{e(p["read"])} {ico("i-arrow")}</span>
</article>'''


# ---------------------------------------------------------------- home
def build_home():
    R = L.root
    rail = "".join(
        f'<a class="cat" href="{R}recipes.html#{c["id"]}" aria-label="{e(c["name"])}, {tn("n_recipes", count_cat(c["id"]))}"><img src="{img(c["img"])}" alt="" loading="lazy"><span class="cat-body"><span><b>{e(c["name"])}</b><small>{tn("n_recipes", count_cat(c["id"]))}</small></span><span class="arrow-dot">{ico("i-arrow")}</span></span></a>'
        for c in L.cats)
    f0 = L.by_id[FEATURED[0]["id"]]
    thumbs = "".join(
        f'<button class="thumb" type="button" aria-label="{e(t("feature_x", name=L.by_id[f["id"]]["name"]))}" aria-pressed="{str(i == 0).lower()}"><img src="{img(f.get("img", f["id"]))}" alt="" loading="lazy"></button>'
        for i, f in enumerate(FEATURED))
    picks = "".join(card(L.by_id[i], rv=True) for i in PICKS)
    w = L.by_id[WEEK]
    posts = "".join(post_card(p) for p in L.journal[:3])
    main = src("hero.html") + f'''
<div class="wrap home">
  <section id="categories" aria-labelledby="cat-title">
    <div class="sec-head">
      <div><p class="eyebrow">{t("explore_kitchen")}</p><h2 id="cat-title">{t("flavours_h2")}</h2></div>
      <a class="link-more" href="{R}recipes.html">{t("all_recipes")} {ico("i-arrow")}</a>
    </div>
    <div class="rail-wrap">
      <button class="rail-btn prev" type="button" id="railPrev" aria-label="{e(t("scroll_left"))}">{ico("i-left")}</button>
      <div class="rail" id="rail">{rail}</div>
      <button class="rail-btn next" type="button" id="railNext" aria-label="{e(t("scroll_right"))}">{ico("i-arrow")}</button>
    </div>
  </section>

  <section class="featured rv" aria-labelledby="f-title" id="featured" data-ids='{json.dumps(FEATURED)}'>
    <div class="f-copy">
      <p class="eyebrow" id="fEyebrow">{t("featured_recipe")} · {e(f0["region"])}</p>
      <h2 id="f-title">{e(f0["name"])}</h2>
      <p class="blurb" id="fBlurb">{e(f0["intro"])}</p>
      <div class="f-meta" id="fMeta"><span>{ico("i-clock")}{e(f0["time"])}</span><span>{ico("i-chef")}{e(f0["level"])}</span><span>{ico("i-users")}{e(f0["serves"])}</span></div>
      <div class="f-actions">
        <a class="btn btn-gold" id="fOpen" href="{R}recipes/{f0["id"]}.html">{t("view_recipe")} {ico("i-arrow")}</a>
        <a class="btn btn-line ink" id="fCat" href="{R}recipes.html#{f0["cat"]}">{e(t("more_x", name=L.cat[f0["cat"]]["name"].lower()))}</a>
      </div>
    </div>
    <div class="f-media">
      <img id="fImg" src="{img(FEATURED[0].get("img", f0["id"]))}" alt="{e(f0["name"])}">
      {steam(4)}
      <div class="seal" aria-hidden="true"><span>{t("fatmas_pick_seal")}</span></div>
    </div>
    <div class="thumbs" role="group" aria-label="{e(t("choose_featured"))}">{thumbs}</div>
  </section>

  <section aria-labelledby="picks-title">
    <div class="sec-head">
      <div><p class="eyebrow">{t("fatmas_picks")}</p><h2 id="picks-title">{t("picks_h2")}</h2></div>
      <a class="link-more" href="{R}recipes.html">{t("see_all_n", n=len(L.recipes))} {ico("i-arrow")}</a>
    </div>
    <div class="picks">{picks}</div>
    <div class="center-cta"><a class="btn btn-green" href="{R}recipes.html">{t("browse_all")} {ico("i-arrow")}</a></div>
  </section>

  <section class="week rv" aria-labelledby="week-title">
    <a class="plate" href="{R}recipes/{w["id"]}.html" aria-label="{e(t("open_x", name=w["name"]))}"><img src="{img(w["id"])}" alt="{e(w["name"])}" loading="lazy">{steam(4)}</a>
    <div>
      <p class="eyebrow">{t("recipe_of_week")}</p>
      <h2 id="week-title">{e(w["name"])}</h2>
      <p class="copy">{e(w["intro"])}</p>
      <div class="mstats"><div><b>{e(w["time"])}</b><small>{t("time")}</small></div><div><b>{e(w["serves"])}</b><small>{t("serves")}</small></div><div><b>{e(w["level"])}</b><small>{t("level")}</small></div></div>
      <div class="week-actions">
        <a class="btn btn-green" href="{R}recipes/{w["id"]}.html">{t("cook_tonight")} {ico("i-arrow")}</a>
        <button class="btn btn-line ink" type="button" data-save="{w["id"]}" aria-pressed="false">{ico("i-heart")}<span data-save-label>{t("save_recipe")}</span></button>
      </div>
    </div>
  </section>

  {src("tips.html")}

  <section aria-labelledby="journal-title">
    <div class="sec-head">
      <div><p class="eyebrow">{t("the_journal")}</p><h2 id="journal-title">{t("journal_h2")}</h2></div>
      <a class="link-more" href="{R}journal.html">{t("all_stories")} {ico("i-arrow")}</a>
    </div>
    <div class="posts">{posts}</div>
  </section>

  <section class="about-teaser" aria-labelledby="about-title">
    <div class="arch-wrap rv">
      <div class="arch"><img src="{img("chapati")}" alt="{e(t("roti_alt"))}" loading="lazy"></div>
      <div class="arch-badge" aria-hidden="true">{t("fatma")}</div>
    </div>
    <div>
      <div class="ornament" aria-hidden="true"><i></i></div>
      <p class="eyebrow" id="about-title" style="margin-top:14px">{t("meet_fatma")}</p>
      <blockquote>{t("quote_family")}</blockquote>
      <p class="copy">{t("notebook_p")}</p>
      <a class="btn btn-line ink" href="{R}story.html">{t("read_story")} {ico("i-arrow")}</a>
    </div>
  </section>
</div>'''
    page("index.html", SITE if L.id == "en" else f"{SITE} · {t('home_title')}", t("home_desc"), main, "home", suffix=False)


# ---------------------------------------------------------------- recipes
def build_recipes():
    R = L.root
    chips = f'<button class="chip" type="button" data-chip="all" data-go="all" aria-pressed="true">{t("all")}</button>' + "".join(
        f'<button class="chip" type="button" data-chip="{c["id"]}" data-go="{c["id"]}" aria-pressed="false">{e(c["name"])}</button>' for c in L.cats)
    cards = "".join(card(r) for r in L.recipes)
    qf = "".join(
        f'<li><button type="button" data-qf="cat:{c["id"]}" data-go="{c["id"]}" aria-pressed="false">{ico(c["icon"], "i")}<span>{e(c["name"])}</span><span class="n">{count_cat(c["id"])}</span>{ico("i-chev", "c")}</button></li>' for c in L.cats)
    qf += f'<li><button type="button" data-qf="veg" data-go="veg" aria-pressed="false">{ico("i-leaf", "i")}<span>{t("vegetarian")}</span><span class="n">{sum(1 for r in L.recipes if r.get("veg"))}</span>{ico("i-chev", "c")}</button></li>'
    qf += f'<li><button type="button" data-qf="quick" data-go="quick" aria-pressed="false">{ico("i-clock", "i")}<span>{t("quick_45")}</span><span class="n">{sum(1 for r in L.recipes if quick(r))}</span>{ico("i-chev", "c")}</button></li>'
    qf += f'<li><button type="button" data-qf="saved" data-go="saved" aria-pressed="false">{ico("i-heart", "i")}<span>{t("saved_recipes")}</span><span class="n" data-saved-n>0</span>{ico("i-chev", "c")}</button></li>'
    cols = "".join(
        f'<button class="col" type="button" data-col="{c["id"]}" data-go="col-{c["id"]}" aria-pressed="false"><img src="{img(c["img"])}" alt="" loading="lazy"><span><b>{e(c["name"])}</b><small>{tn("n_recipes", sum(1 for r in L.recipes if in_col(r, c["id"])))}</small></span>{ico("i-chev")}</button>'
        for c in L.cols)
    tags = "".join(f'<button type="button" data-go="search-{e(q.lower().replace(" ", "-"))}">{e(q)}</button>' for q in L.ui["popular"])
    sp = L.recipes[0]
    main = page_head([(t("recipes"), None)], t("all_recipes_h1"),
                     t("recipes_sub", n=len(L.recipes)), "chicken_biryani") + f'''
<div class="wrap page page-main">
  <section class="main" id="results" aria-label="{e(t("recipes"))}" style="scroll-margin-top:96px">
    <div>
      <div class="recipes-top">
        <div class="chips" role="group" aria-label="{e(t("filter_by_cat"))}">{chips}</div>
        <label class="search" for="q"><span class="sr">{t("search_recipes")}</span>{ico("i-search")}<input id="q" type="search" placeholder="{e(t("search_ph_short"))}" autocomplete="off"></label>
      </div>
      <div id="catBanner"></div>
      <p class="count" id="count" aria-live="polite">{tn("n_recipes", len(L.recipes))}</p>
      <div class="grid" id="grid">{cards}</div>
      <p class="empty" id="empty" hidden></p>
    </div>
  </section>
  <aside class="side" aria-label="{e(t("recipe_shortcuts"))}">
    <a class="special" id="special" href="{R}recipes/{sp["id"]}.html">
      <img id="spImg" src="{img(sp["id"])}" alt="{e(sp["name"])}">
      {steam(3)}
      <span class="lbl">{t("todays_special")}</span>
      <span class="sb"><span><h4 id="spName">{e(sp["name"])}</h4><p id="spSub">{e(sp["time"])} · {e(sp["region"])}</p></span><span class="arrow-dot">{ico("i-arrow")}</span></span>
    </a>
    <div class="box"><h3>{t("quick_filters")}</h3><ul class="qf">{qf}</ul></div>
    <div class="box"><h3>{t("collections")}</h3><div class="cols">{cols}</div></div>
    <div class="box"><h3>{t("popular_searches")}</h3><div class="tags">{tags}</div></div>
    <div class="side-news">
      <p class="eyebrow">{t("the_sunday_letter")}</p>
      <h3 style="margin-top:8px">{t("side_news_h")}</h3>
      <p>{t("side_news_p")}</p>
      <form class="inline-form" id="miniForm" novalidate>
        <label class="sr" for="miniEmail">{t("email")}</label>
        <input id="miniEmail" type="email" placeholder="{e(t("your_email"))}" autocomplete="email">
        <button type="submit" aria-label="{e(t("subscribe"))}">{ico("i-arrow")}</button>
      </form>
      <p class="mini-err" id="miniErr" aria-live="polite"></p>
    </div>
  </aside>
</div>'''
    page("recipes.html", t("all_recipes_title"), t("recipes_desc", n=len(L.recipes)), main, "recipes", "chicken_biryani")


# ---------------------------------------------------------------- recipe pages
def serves_parts(r):
    """Base number and unit for the servings stepper, or None for jars."""
    en = EN_BY_ID[r["id"]]["serves"]
    if "jar" in en or not re.match(r"^\d", en):
        return None
    n = int(re.match(r"^(\d+)", en).group(1))
    unit = re.sub(r"^\d+(?:\s*[–-]\s*\d+)?\s*", "", r["serves"]) or t("servings_unit")
    return n, unit


def related(r, n=3):
    out = [x for x in L.recipes if x["cat"] == r["cat"] and x["id"] != r["id"]]
    if len(out) < n:
        out += [x for x in L.recipes if x["id"] != r["id"] and x not in out and set(x.get("cols", [])) & set(r.get("cols", []))]
    if len(out) < n:
        out += [x for x in L.recipes if x["id"] != r["id"] and x not in out]
    return out[:n]


def spice_links(r):
    text = " ".join(EN_BY_ID[r["id"]]["ing"]).lower()
    found = [s for s in L.spices if any(w in text for w in SPICE_WORDS[s["slug"]])]
    if not found:
        return ""
    links = "".join(f'<a href="{L.root}spices/{s["slug"]}.html"><img src="{img(s["img"])}" alt="" loading="lazy">{e(s["name"])}</a>' for s in found)
    return f'<div class="spice-links"><p class="eyebrow">{t("spices_in_recipe")}</p><div>{links}</div></div>'


def build_recipe(r):
    R = L.root
    c = L.cat[r["cat"]]
    sp = serves_parts(r)
    serv = (f'<span class="serv" id="serv" data-base="{sp[0]}" data-unit="{e(sp[1])}" data-to="{e(t("range_to"))}"><button type="button" id="servMinus" aria-label="{e(t("fewer_servings"))}">−</button><output id="servOut" aria-live="polite">{sp[0]} {e(sp[1])}</output><button type="button" id="servPlus" aria-label="{e(t("more_servings"))}">+</button></span>'
            if sp else f'<span class="serv"><output>{e(r["serves"])}</output></span>')
    ings = "".join(f'<li><label><input type="checkbox"><span data-ing>{e(i)}</span></label></li>' for i in r["ing"])
    steps = "".join(f'<li><button type="button" aria-pressed="false">{e(s)}</button></li>' for s in r["steps"])
    rel = "".join(card(x, rv=True) for x in related(r))
    ld = {
        "@context": "https://schema.org", "@type": "Recipe", "name": r["name"], "description": r["intro"],
        "image": f"{SITE_URL.rstrip('/')}/images/{r['id']}.jpg", "author": {"@type": "Person", "name": "Fatma"},
        "inLanguage": L.id, "recipeCategory": c["name"], "recipeCuisine": t("cuisine"), "recipeYield": r["serves"],
        "totalTime": f"PT{r['mins']}M",
        "recipeIngredient": r["ing"], "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r["steps"]],
    }
    main = f'''<div class="wrap rd">
  <nav class="crumbs ink" aria-label="{e(t("breadcrumb"))}"><a href="{R}">{t("home")}</a><span aria-hidden="true" class="sep">/</span><a href="{R}recipes.html">{t("recipes")}</a><span aria-hidden="true" class="sep">/</span><a href="{R}recipes.html#{c["id"]}">{e(c["name"])}</a><span aria-hidden="true" class="sep">/</span><span>{e(r["name"])}</span></nav>
  <div class="rd-top" style="margin-top:26px">
    <div class="rd-media"><img src="{img(r["id"])}" alt="{e(r["name"])}">{steam(5)}<span class="tag">{e(c["name"])}</span></div>
    <div class="rd-body">
      <p class="eyebrow">{e(c["name"])} · {e(r["region"])}</p>
      <h1>{e(r["name"])}</h1>
      <p class="intro">{e(r["intro"])}</p>
      <div class="mstats"><div><b>{e(r["time"])}</b><small>{t("time")}</small></div><div><b>{e(r["serves"])}</b><small>{t("serves")}</small></div><div><b>{e(r["level"])}</b><small>{t("level")}</small></div></div>
      <div class="rd-actions">
        <button class="btn btn-line ink" type="button" data-save="{r["id"]}" aria-pressed="false">{ico("i-heart")}<span data-save-label>{t("save_recipe")}</span></button>
        <a class="btn btn-green" href="#method">{t("start_cooking")} {ico("i-arrow")}</a>
        <button class="btn btn-line ink" type="button" id="printBtn">{ico("i-steps")}{t("print")}</button>
      </div>
    </div>
  </div>
  <div class="rd-grid">
    <aside class="rd-panel rd-ing" aria-labelledby="ing-title">
      <h2 id="ing-title">{t("ingredients")} {serv}</h2>
      <ul class="checklist">{ings}</ul>
      <p class="hint-line">{t("tick_hint")}</p>
    </aside>
    <section class="rd-panel" id="method" aria-labelledby="method-title" style="scroll-margin-top:96px">
      <h2 id="method-title">{t("method")}</h2>
      <ol class="method">{steps}</ol>
      <p class="hint-line">{t("tap_hint")}</p>
      <div class="tipbox"><b>{t("fatmas_tip")}</b>{e(r["tip"])}</div>
      {spice_links(r)}
    </section>
  </div>
</div>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">{t("keep_cooking")}</p><h2 id="rel-title">{t("also_like_h2")}</h2></div>
  <a class="link-more" href="{R}recipes.html#{c["id"]}">{e(t("more_x", name=c["name"].lower()))} {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
</section>'''
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    page(f"recipes/{r['id']}.html", r["name"], r["intro"], main, "recipes", r["id"], head)


# ---------------------------------------------------------------- story
def build_story():
    R = L.root
    story = src("story.html").replace('<section class="story" id="story"', '<section class="story" id="story-main"')
    gallery = "".join(f'<a href="{R}recipes/{i}.html"><img src="{img(i)}" alt="{e(L.by_id[i]["name"])}" loading="lazy"><span>{e(L.by_id[i]["name"])}</span></a>' for i in STORY_GALLERY)
    main = page_head([(t("fatmas_story"), None)], t("story_h1"), t("story_sub"), "tips_spices") + story + f'''
<section class="wrap" style="padding-block:24px 40px" aria-labelledby="promise-title">
  <div class="sec-head"><div><p class="eyebrow">{t("what_expect")}</p><h2 id="promise-title">{t("promise_h2")}</h2></div></div>
  <div class="promise">
    <div class="rv">{ico("i-pot")}<h3>{t("promise1_h")}</h3><p>{t("promise1_p")}</p></div>
    <div class="rv">{ico("i-steps")}<h3>{t("promise2_h")}</h3><p>{t("promise2_p")}</p></div>
    <div class="rv">{ico("i-map")}<h3>{t("promise3_h")}</h3><p>{t("promise3_p")}</p></div>
  </div>
</section>
<section class="wrap story-page" style="padding-top:40px" aria-labelledby="gal-title">
  <div class="sec-head"><div><p class="eyebrow">{t("from_kitchen")}</p><h2 id="gal-title">{t("favourites_h2")}</h2></div><a class="link-more" href="{R}recipes.html">{t("all_recipes")} {ico("i-arrow")}</a></div>
  <div class="gallery">{gallery}</div>
  <div class="center-cta" style="gap:12px;flex-wrap:wrap"><a class="btn btn-green" href="{R}recipes.html">{t("explore_recipes")} {ico("i-arrow")}</a><a class="btn btn-line ink" href="{R}ask.html">{t("ask_question")}</a></div>
</section>'''
    page("story.html", t("fatmas_story"), t("story_desc"), main, "story", "tips_spices")


# ---------------------------------------------------------------- ask
def build_ask():
    main = page_head([(t("ask_fatma"), None)], t("ask_h1"), t("ask_sub"), "chicken_qorma") + src("contact.html")
    page("ask.html", t("ask_fatma"), t("ask_desc"), main, "ask", "chicken_qorma")


# ---------------------------------------------------------------- journal
def build_journal():
    R = L.root
    posts = "".join(post_card(p) for p in L.journal)
    spices = "".join(spice_card(s) for s in L.spices[:6])
    main = page_head([(t("journal"), None)], t("journal_h1"), t("journal_sub"), "sheer_khurma") + f'''
<section class="wrap" style="padding-block:72px 40px" aria-label="{e(t("articles"))}">
  <div class="posts">{posts}</div>
</section>
<section class="wrap" style="padding-block:40px 96px" aria-labelledby="sg-title">
  <div class="sec-head"><div><p class="eyebrow">{t("spice_guide")}</p><h2 id="sg-title">{t("know_masala_h2")}</h2></div><a class="link-more" href="{R}spices.html">{t("all_n_spices", n=len(L.spices))} {ico("i-arrow")}</a></div>
  <div class="posts">{spices}</div>
</section>'''
    page("journal.html", t("journal"), t("journal_desc"), main, "journal", "sheer_khurma")
    for p in L.journal:
        body = ""
        for blk in p["body"]:
            if blk[0] == "h":
                body += f"<h2>{e(blk[1])}</h2>"
            elif blk[0] == "p":
                body += f"<p>{e(blk[1])}</p>"
            elif blk[0] == "callout":
                body += f'<div class="callout"><b>{e(blk[1])}</b>{e(blk[2])}</div>'
        rel = "".join(card(L.by_id[i], rv=True) for i in p["related"][:3])
        main = page_head([(t("journal"), f"{R}journal.html"), (p["title"], None)], e(p["title"]), p["summary"], p["img"], p["tag"] + " · " + p["read"]) + f'''
<article class="wrap article">
  <p class="lead">{e(p["lead"])}</p>
  <figure><img src="{img(p["img"])}" alt="" loading="lazy"></figure>
  {body}
</article>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">{t("cook_from_story")}</p><h2 id="rel-title">{t("try_next_h2")}</h2></div><a class="link-more" href="{R}journal.html">{t("all_stories")} {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
</section>'''
        page(f"journal/{p['slug']}.html", p["title"], p["summary"], main, "journal", p["img"])


# ---------------------------------------------------------------- spice guide
def spice_card(s):
    return f'''<article class="post rv">
  <a class="stretch" href="{L.root}spices/{s["slug"]}.html">
    <div class="media"><span class="post-tag">{e(s["local"])}</span><img src="{img(s["img"])}" alt="{e(s["name"])} ({e(s["local"])})" loading="lazy"></div>
    <h3 style="margin-top:14px">{e(s["name"])} <span class="gold-word">({e(s["local"].lower())})</span></h3>
  </a>
  <p>{e(s["lead"])}</p>
  <span class="read">{t("read_guide")} {ico("i-arrow")}</span>
</article>'''


def build_spices():
    R = L.root
    cards = "".join(spice_card(s) for s in L.spices)
    main = page_head([(t("spice_guide"), None)], t("spices_h1"), t("spices_sub"), "tips_spices") + f'''
<section class="wrap" style="padding-block:64px 96px" aria-label="{e(t("spices"))}">
  <div class="posts">{cards}</div>
  <p class="disclaimer">{t("spices_disclaimer")}</p>
</section>'''
    page("spices.html", t("spices_title"), t("spices_desc"), main, "journal", "tips_spices")
    for s in L.spices:
        body = "".join(f"<h2>{e(h)}</h2><p>{e(x)}</p>" for h, x in s["sections"])
        faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in s["faq"])
        labels = s.get("sources_label") or [x for x, _ in s["sources"]]
        src_list = "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{e(lbl)}</a></li>' for lbl, (_, u) in zip(labels, s["sources"]))
        rel = "".join(card(L.by_id[i], rv=True) for i in s["recipes"] if i in L.by_id)
        others = "".join(f'<a href="{R}spices/{o["slug"]}.html"><img src="{img(o["img"])}" alt="" loading="lazy">{e(o["name"])}</a>' for o in L.spices if o["slug"] != s["slug"])
        used = t("list_sep").join(L.by_id[i]["name"] for i in s["recipes"] if i in L.by_id)
        ld = [
            {"@context": "https://schema.org", "@type": "Article", "headline": s["title"], "description": s["meta"],
             "image": f"{SITE_URL.rstrip('/')}/images/{s['img']}.jpg", "author": {"@type": "Person", "name": "Fatma"},
             "publisher": {"@type": "Organization", "name": SITE}, "inLanguage": L.id, "about": f"{s['name']} ({s['local']}, {s['latin']})"},
            {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": L.id,
             "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in s["faq"]]},
        ]
        head = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
        main = page_head([(t("spice_guide"), f"{R}spices.html"), (s["name"], None)],
                         f'{e(s["name"])} <em>({e(s["local"].lower())})</em>', s["lead"], s["img"], t("spice_guide") + " · " + s["latin"]) + f'''
<article class="wrap article">
  <div class="glance">
    <div><small>{t("urdu_name")}</small><b>{e(s["urdu"] if L.id != "ur" else s["name"])}</b></div>
    <div><small>{t("local_name")}</small><b>{e(s["local"])}</b></div>
    <div><small>{t("botanical_name")}</small><b><i lang="la">{e(s["latin"])}</i></b></div>
    <div><small>{t("try_it_in")}</small><b>{e(used)}</b></div>
  </div>
  <figure><img src="{img(s["img"])}" alt="{e(s["name"])} ({e(s["local"])})" loading="lazy"></figure>
  {body}
  <h2>{t("faq_h2")}</h2>
  <div class="faq">{faq}</div>
  <div class="sources"><h3>{t("sources")}</h3><ul>{src_list}</ul></div>
  <p class="disclaimer">{t("spice_disclaimer")}</p>
</article>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">{e(t("cook_with_x", name=s["name"]))}</p><h2 id="rel-title">{t("use_it_h2")}</h2></div><a class="link-more" href="{R}spices.html">{t("all_spices")} {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
  <div class="spice-links" style="margin-top:44px"><p class="eyebrow">{t("more_spice_guide")}</p><div>{others}</div></div>
</section>'''
        page(f"spices/{s['slug']}.html", s["title"], s["meta"], main, "journal", s["img"], head, suffix=False)


def build_404():
    R = L.root
    main = f'''<section class="page-head">
  <div class="ph-img"><img src="{img("hero_biryani")}" alt=""></div>
  <div class="wrap">
    <p class="eyebrow" style="margin-top:18px">{t("nf_eyebrow")}</p>
    <h1>{t("nf_h1")}</h1>
    <p class="ph-sub">{t("nf_sub")}</p>
    <form class="hero-search" role="search" data-search style="margin-top:28px">
      {ico("i-search", "s")}
      <label class="sr" for="nfQ">{t("search_recipes")}</label>
      <input id="nfQ" type="search" placeholder="{e(t("search_ph"))}" autocomplete="off">
      <button type="submit" aria-label="{e(t("search"))}">{ico("i-arrow")}</button>
    </form>
    <div class="f-actions" style="margin-top:24px"><a class="btn btn-gold" href="{R}">{t("go_home")}</a><a class="btn btn-line" href="{R}recipes.html">{t("browse_recipes")}</a></div>
  </div>
</section>'''
    page("404.html", t("nf_eyebrow"), t("nf_desc"), main, noindex=True)
    L.pages.remove("404.html")


def build_sitemap(all_pages):
    if not SITE_URL:
        return
    base = SITE_URL.rstrip("/")
    urls = ""
    for lang, pages in all_pages.items():
        for p in pages:
            loc = f"{base}/{LANGS[lang]['prefix']}{'' if p == 'index.html' else p}"
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{k}" href="{base}/{LANGS[k]["prefix"]}{"" if p == "index.html" else p}"/>'
                for k in ORDER)
            urls += f"<url><loc>{loc}</loc>{alts}</url>\n"
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + "</urlset>\n")
    open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")


# ---------------------------------------------------------------- data.js
def build_data():
    keep = ["id", "name", "cat", "region", "time", "mins", "level", "serves", "veg", "cols", "intro"]
    payload = {"lang": L.id, "ui": L.ui["js"], "categories": L.cats, "collections": L.cols,
               "recipes": [{k: r[k] for k in keep if k in r} for r in L.recipes]}
    name = "data.js" if L.id == "en" else f"data.{L.id}.js"
    open(os.path.join(HERE, "assets", name), "w", encoding="utf-8").write(
        "/* Generated by build.py. Do not edit by hand. */\nwindow.TP = " + json.dumps(payload, ensure_ascii=False) + ";\n")


def build_lang(lang):
    use(lang)
    L.pages = []
    build_data()
    build_home()
    build_recipes()
    for r in L.recipes:
        build_recipe(r)
    build_story()
    build_ask()
    build_journal()
    build_spices()
    build_404()
    return L.pages


if __name__ == "__main__":
    missing = [r["id"] for r in EN_DATA["recipes"] if not os.path.exists(os.path.join(HERE, "images", r["id"] + ".jpg"))]
    if missing:
        raise SystemExit("Missing photos in images/: " + ", ".join(missing))
    pages = {lang: build_lang(lang) for lang in ORDER}
    build_sitemap(pages)
    n = len(EN_DATA["recipes"])
    print(f"Built {len(ORDER)} languages, each with home, recipes, story, ask, journal, {n} recipe pages, "
          f"{len(EN_JOURNAL)} articles and {len(EN_SPICES)} spice guides.")
    if MISSING:
        uniq = sorted(set(MISSING))
        print(f"{len(uniq)} missing translations (English used instead):")
        for m in uniq[:60]:
            print("  " + m)
        if "--strict" in sys.argv:
            raise SystemExit(1)
