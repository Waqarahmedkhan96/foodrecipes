#!/usr/bin/env python3
"""Build the Tasty Pakistan by Fatma website.

All recipes live in data/recipes.json and journal articles in data/journal.json.
Run `python3 build.py` after editing either file. It writes:

  index.html, recipes.html, story.html, ask.html, journal.html
  recipes/<recipe-id>.html   one page per recipe
  journal/<slug>.html        one page per article
  assets/data.js             recipe data for filtering on the recipes page
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "Tasty Pakistan by Fatma"

data = json.load(open(os.path.join(HERE, "data/recipes.json"), encoding="utf-8"))
journal = json.load(open(os.path.join(HERE, "data/journal.json"), encoding="utf-8"))["posts"]
SPICES = json.load(open(os.path.join(HERE, "data/spices.json"), encoding="utf-8"))["spices"]
SP = {s["slug"]: s for s in SPICES}

# Set this to the live address (for example "https://www.tastypakistan.com") to also
# write sitemap.xml, robots.txt and canonical links. Leave empty until the domain is known.
SITE_URL = ""
PAGES = []

# Words in a recipe's ingredients that link to a spice guide.
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
CATS, COLS, RECIPES = data["categories"], data["collections"], data["recipes"]
BY_ID = {r["id"]: r for r in RECIPES}
CAT = {c["id"]: c for c in CATS}
COL = {c["id"]: c for c in COLS}

# Home page choices: change these ids to feature different dishes.
FEATURED = [{"id": "chicken_biryani", "img": "hero_biryani"}, {"id": "beef_nihari"}, {"id": "chicken_karahi"}, {"id": "zarda"}]
PICKS = ["chicken_karahi", "kabli_pulao", "beef_haleem", "golgappay", "chicken_qorma", "gulab_jamun"]
WEEK = "beef_nihari"
POPULAR = ["Biryani", "Karahi", "Nihari", "Haleem", "Chaat", "Pakora", "Pulao", "Qorma", "Zarda", "Kheer"]

e = lambda s: html.escape(str(s), quote=True)
src = lambda name: open(os.path.join(HERE, "src", name), encoding="utf-8").read()
SPRITE = src("sprite.svg")


def ico(i, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} aria-hidden="true"><use href="#{i}"/></svg>'


def steam(n):
    return '<div class="steam" aria-hidden="true">' + "<i></i>" * n + "</div>"


def quick(r):
    return r["mins"] <= 45


def in_col(r, cid):
    return quick(r) if cid == "quick" else cid in r.get("cols", [])


def count_cat(cid):
    return sum(1 for r in RECIPES if r["cat"] == cid)


def slug_text(r):
    return " ".join([r["name"], r["region"], CAT[r["cat"]]["name"], " ".join(r["ing"])]).lower()


# ---------------------------------------------------------------- layout
def header(root, active):
    def link(href, label, key):
        on = ' class="on" aria-current="page"' if key == active else ""
        return f'<a href="{root}{href}"{on}>{label}</a>'
    dd = "".join(
        f'<a href="{root}recipes.html#{c["id"]}"><img src="{root}images/{c["img"]}.jpg" alt="" loading="lazy"><span><b>{e(c["name"])}</b><small>{count_cat(c["id"])} recipes</small></span></a>'
        for c in CATS)
    return f'''<header class="site" id="hdr">
  <div class="wrap bar">
    <a class="brand" href="{root}index.html" aria-label="{SITE}, home">
      <svg aria-hidden="true"><use href="#logo"/></svg>
      <span><b>Tasty Pakistan</b><small>by Fatma</small></span>
    </a>
    <nav class="links" id="nav" aria-label="Main">
      {link("index.html", "Home", "home")}
      {link("recipes.html", "Recipes", "recipes")}
      <div class="dd">
        <button class="dd-btn" type="button" aria-expanded="false" aria-controls="ddPanel">Categories {ico("i-chev")}</button>
        <div class="dd-panel" id="ddPanel">{dd}<a class="dd-all" href="{root}recipes.html">View all recipes</a></div>
      </div>
      {link("journal.html", "Journal", "journal")}
      {link("story.html", "Fatma's story", "story")}
      {link("ask.html", "Ask Fatma", "ask")}
    </nav>
    <div class="bar-actions">
      <a class="ico-btn" href="{root}recipes.html#find" aria-label="Search recipes">{ico("i-search")}</a>
      <a class="ico-btn" href="{root}recipes.html#saved" aria-label="Saved recipes">{ico("i-heart")}<span class="badge-count" hidden>0</span></a>
      <a class="btn btn-gold" href="#subscribe">Subscribe</a>
      <button class="ico-btn menu-btn" id="menuBtn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="nav">{ico("i-menu")}</button>
    </div>
  </div>
</header>'''


def footer(root):
    cats = "".join(f'<li><a href="{root}recipes.html#{c["id"]}">{e(c["name"])}</a></li>' for c in CATS)
    cols = "".join(f'<li><a href="{root}recipes.html#col-{c["id"]}">{e(c["name"])}</a></li>' for c in COLS)
    return f'''<footer>
  <div class="wrap">
    <div class="foot-top">
      <a class="brand" href="{root}index.html" aria-label="{SITE}, home"><svg aria-hidden="true"><use href="#logo"/></svg><span><b>Tasty Pakistan</b><small>by Fatma</small></span></a>
      <p>Recipes, stories and weekly inspiration from the Pakistani home kitchen.</p>
      <a class="btn btn-gold" href="#subscribe">Get the Sunday letter {ico("i-arrow")}</a>
    </div>
    <div class="foot">
      <div><h4>Recipes</h4><ul>{cats}</ul></div>
      <div><h4>Collections</h4><ul>{cols}<li><a href="{root}recipes.html#veg">Vegetarian</a></li></ul></div>
      <div><h4>Read</h4><ul><li><a href="{root}journal.html">Journal</a></li><li><a href="{root}spices.html">Spice guide</a></li><li><a href="{root}story.html">Fatma's story</a></li><li><a href="#subscribe">Sunday letter</a></li></ul></div>
      <div><h4>Talk</h4><ul><li><a href="{root}ask.html">Ask Fatma</a></li><li><a href="{root}ask.html#request">Recipe requests</a></li><li><a href="{root}ask.html#collab">Collaborations</a></li></ul></div>
    </div>
    <div class="copyline"><span>© 2026 {SITE}</span><span>Made with ghee and patience</span></div>
  </div>
</footer>'''


def page(path, title, desc, main, active="", image="hero_biryani", head_extra="", suffix=True, root_override=None):
    root = root_override if root_override is not None else "../" * path.count("/")
    full_title = title if (title == SITE or not suffix) else f"{title} · {SITE}"
    PAGES.append(path)
    if SITE_URL:
        head_extra = f'<link rel="canonical" href="{SITE_URL.rstrip("/")}/{"" if path == "index.html" else path}">\n' + head_extra
    body = (SPRITE + "\n" + header(root, active) + f'\n<main id="top">\n{main}\n</main>\n'
            + src("sub.html") + "\n" + footer(root))
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0F2F23">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{(SITE_URL.rstrip("/") + "/") if SITE_URL else root}images/{image}.jpg">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500&family=Great+Vibes&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
{head_extra}</head>
<body data-root="{root}">
{body}
<script src="{root}assets/data.js"></script>
<script src="{root}assets/site.js"></script>
</body>
</html>
'''
    doc = doc.replace("{{root}}", root)
    out = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)


# ---------------------------------------------------------------- pieces
def card(r, root, rv=False):
    c = CAT[r["cat"]]
    veg = f'<span>{ico("i-leaf")}Veg</span>' if r.get("veg") else ""
    return f'''<article class="card{' rv' if rv else ''}" data-id="{r["id"]}" data-cat="{r["cat"]}" data-veg="{1 if r.get("veg") else 0}" data-mins="{r["mins"]}" data-cols="{" ".join(r.get("cols", []))}" data-text="{e(slug_text(r))}">
  <div class="media"><img src="{root}images/{r["id"]}.jpg" alt="" loading="lazy">{steam(3)}<span class="tag">{e(c["name"])}</span>
    <button class="heart" type="button" data-save="{r["id"]}" aria-pressed="false" aria-label="Save {e(r["name"])}">{ico("i-heart")}</button></div>
  <div class="card-body">
    <span class="region">{e(r["region"])}</span>
    <h3><a class="card-link" href="{root}recipes/{r["id"]}.html">{e(r["name"])}</a></h3>
    <span class="facts"><span>{ico("i-clock")}{e(r["time"])}</span><span>{ico("i-chef")}{e(r["level"])}</span>{veg}</span>
  </div>
</article>'''


def page_head(root, crumbs, title_html, sub, img, eyebrow=""):
    cr = f'<a href="{root}index.html">Home</a>'
    for label, href in crumbs:
        cr += '<span aria-hidden="true">/</span>' + (f'<a href="{href}">{e(label)}</a>' if href else f'<span>{e(label)}</span>')
    eb = f'<p class="eyebrow" style="margin-top:18px">{e(eyebrow)}</p>' if eyebrow else ""
    return f'''<section class="page-head">
  <div class="ph-img"><img src="{root}images/{img}.jpg" alt=""></div>
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">{cr}</nav>
    {eb}
    <h1>{title_html}</h1>
    <p class="ph-sub">{e(sub)}</p>
  </div>
</section>'''


def post_card(p, root):
    return f'''<article class="post rv">
  <a class="stretch" href="{root}journal/{p["slug"]}.html">
    <div class="media"><span class="post-tag">{e(p["tag"])}</span><img src="{root}images/{p["img"]}.jpg" alt="" loading="lazy">{steam(3)}</div>
    <h3 style="margin-top:14px">{e(p["title"])}</h3>
  </a>
  <p>{e(p["summary"])}</p>
  <span class="read">{e(p["read"])} {ico("i-arrow")}</span>
</article>'''


# ---------------------------------------------------------------- home
def build_home():
    root = ""
    rail = "".join(
        f'<a class="cat" href="recipes.html#{c["id"]}" aria-label="{e(c["name"])}, {count_cat(c["id"])} recipes"><img src="images/{c["img"]}.jpg" alt="" loading="lazy"><span class="cat-body"><span><b>{e(c["name"])}</b><small>{count_cat(c["id"])} recipes</small></span><span class="arrow-dot">{ico("i-arrow")}</span></span></a>'
        for c in CATS)
    f0 = BY_ID[FEATURED[0]["id"]]
    thumbs = "".join(
        f'<button class="thumb" type="button" aria-label="Feature {e(BY_ID[f["id"]]["name"])}" aria-pressed="{str(i == 0).lower()}"><img src="images/{f.get("img", f["id"])}.jpg" alt="" loading="lazy"></button>'
        for i, f in enumerate(FEATURED))
    picks = "".join(card(BY_ID[i], root, rv=True) for i in PICKS)
    w = BY_ID[WEEK]
    posts = "".join(post_card(p, root) for p in journal[:3])
    main = src("hero.html") + f'''
<div class="wrap home">
  <section id="categories" aria-labelledby="cat-title">
    <div class="sec-head">
      <div><p class="eyebrow">Explore our kitchen</p><h2 id="cat-title">Flavours from <span class="gold-word">every corner</span> of Pakistan</h2></div>
      <a class="link-more" href="recipes.html">All recipes {ico("i-arrow")}</a>
    </div>
    <div class="rail-wrap">
      <button class="rail-btn prev" type="button" id="railPrev" aria-label="Scroll categories left">{ico("i-left")}</button>
      <div class="rail" id="rail">{rail}</div>
      <button class="rail-btn next" type="button" id="railNext" aria-label="Scroll categories right">{ico("i-arrow")}</button>
    </div>
  </section>

  <section class="featured rv" aria-labelledby="f-title" id="featured" data-ids='{json.dumps(FEATURED)}'>
    <div class="f-copy">
      <p class="eyebrow" id="fEyebrow">Featured recipe · {e(f0["region"])}</p>
      <h2 id="f-title">{e(f0["name"])}</h2>
      <p class="blurb" id="fBlurb">{e(f0["intro"])}</p>
      <div class="f-meta" id="fMeta"><span>{ico("i-clock")}{e(f0["time"])}</span><span>{ico("i-chef")}{e(f0["level"])}</span><span>{ico("i-users")}{e(f0["serves"])}</span></div>
      <div class="f-actions">
        <a class="btn btn-gold" id="fOpen" href="recipes/{f0["id"]}.html">View recipe {ico("i-arrow")}</a>
        <a class="btn btn-line ink" id="fCat" href="recipes.html#{f0["cat"]}">More {e(CAT[f0["cat"]]["name"].lower())}</a>
      </div>
    </div>
    <div class="f-media">
      <img id="fImg" src="images/{FEATURED[0].get("img", f0["id"])}.jpg" alt="{e(f0["name"])}">
      {steam(4)}
      <div class="seal" aria-hidden="true"><span>Fatma's<br>pick</span></div>
    </div>
    <div class="thumbs" role="group" aria-label="Choose a featured recipe">{thumbs}</div>
  </section>

  <section aria-labelledby="picks-title">
    <div class="sec-head">
      <div><p class="eyebrow">Fatma's picks</p><h2 id="picks-title">Loved at <span class="gold-word">every table</span></h2></div>
      <a class="link-more" href="recipes.html">See all {len(RECIPES)} recipes {ico("i-arrow")}</a>
    </div>
    <div class="picks">{picks}</div>
    <div class="center-cta"><a class="btn btn-green" href="recipes.html">Browse all recipes {ico("i-arrow")}</a></div>
  </section>

  <section class="week rv" aria-labelledby="week-title">
    <a class="plate" href="recipes/{w["id"]}.html" aria-label="Open {e(w["name"])}"><img src="images/{w["id"]}.jpg" alt="{e(w["name"])}" loading="lazy">{steam(4)}</a>
    <div>
      <p class="eyebrow">Recipe of the week</p>
      <h2 id="week-title">{e(w["name"])}</h2>
      <p class="copy">{e(w["intro"])}</p>
      <div class="mstats"><div><b>{e(w["time"])}</b><small>Time</small></div><div><b>{e(w["serves"])}</b><small>Serves</small></div><div><b>{e(w["level"])}</b><small>Level</small></div></div>
      <div class="week-actions">
        <a class="btn btn-green" href="recipes/{w["id"]}.html">Cook it tonight {ico("i-arrow")}</a>
        <button class="btn btn-line ink" type="button" data-save="{w["id"]}" aria-pressed="false">{ico("i-heart")}<span data-save-label>Save recipe</span></button>
      </div>
    </div>
  </section>

  {src("tips.html")}

  <section aria-labelledby="journal-title">
    <div class="sec-head">
      <div><p class="eyebrow">The journal</p><h2 id="journal-title">Stories from the <span class="gold-word">dastarkhwan</span></h2></div>
      <a class="link-more" href="journal.html">All stories {ico("i-arrow")}</a>
    </div>
    <div class="posts">{posts}</div>
  </section>

  <section class="about-teaser" aria-labelledby="about-title">
    <div class="arch-wrap rv">
      <div class="arch"><img src="images/chapati.jpg" alt="Fresh roti puffing on an iron tawa" loading="lazy"></div>
      <div class="arch-badge" aria-hidden="true">Fatma</div>
    </div>
    <div>
      <div class="ornament" aria-hidden="true"><i></i></div>
      <p class="eyebrow" id="about-title" style="margin-top:14px">Meet Fatma</p>
      <blockquote>“Every recipe here was first cooked for <em>family</em>, long before it was written for you.”</blockquote>
      <p class="copy">Tasty Pakistan began as a notebook of my mother's recipes, the measurements written as “a handful” and “until it smells right”. I cooked each one until I could write it down properly.</p>
      <a class="btn btn-line ink" href="story.html">Read Fatma's story {ico("i-arrow")}</a>
    </div>
  </section>
</div>'''
    page("index.html", SITE, "Heirloom Pakistani recipes, stories and weekly meal ideas from Fatma's kitchen.", main, "home")


# ---------------------------------------------------------------- recipes
def build_recipes():
    root = ""
    chips = '<button class="chip" type="button" data-chip="all" data-go="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" type="button" data-chip="{c["id"]}" data-go="{c["id"]}" aria-pressed="false">{e(c["name"])}</button>' for c in CATS)
    cards = "".join(card(r, root) for r in RECIPES)
    qf = "".join(
        f'<li><button type="button" data-qf="cat:{c["id"]}" data-go="{c["id"]}" aria-pressed="false">{ico(c["icon"], "i")}<span>{e(c["name"])}</span><span class="n">{count_cat(c["id"])}</span>{ico("i-chev", "c")}</button></li>' for c in CATS)
    qf += f'<li><button type="button" data-qf="veg" data-go="veg" aria-pressed="false">{ico("i-leaf", "i")}<span>Vegetarian</span><span class="n">{sum(1 for r in RECIPES if r.get("veg"))}</span>{ico("i-chev", "c")}</button></li>'
    qf += f'<li><button type="button" data-qf="quick" data-go="quick" aria-pressed="false">{ico("i-clock", "i")}<span>45 minutes or less</span><span class="n">{sum(1 for r in RECIPES if quick(r))}</span>{ico("i-chev", "c")}</button></li>'
    qf += f'<li><button type="button" data-qf="saved" data-go="saved" aria-pressed="false">{ico("i-heart", "i")}<span>Saved recipes</span><span class="n" data-saved-n>0</span>{ico("i-chev", "c")}</button></li>'
    cols = "".join(
        f'<button class="col" type="button" data-col="{c["id"]}" data-go="col-{c["id"]}" aria-pressed="false"><img src="images/{c["img"]}.jpg" alt="" loading="lazy"><span><b>{e(c["name"])}</b><small>{sum(1 for r in RECIPES if in_col(r, c["id"]))} recipes</small></span>{ico("i-chev")}</button>'
        for c in COLS)
    tags = "".join(f'<button type="button" data-go="search-{t.lower()}">{t}</button>' for t in POPULAR)
    sp = RECIPES[0]
    main = page_head(root, [("Recipes", None)], "All <em>recipes</em>",
                     f"{len(RECIPES)} home-tested Pakistani recipes. Filter by category or collection, or search for a dish.", "chicken_biryani") + f'''
<div class="wrap page page-main">
  <section class="main" id="results" aria-label="Recipes" style="scroll-margin-top:96px">
    <div>
      <div class="recipes-top">
        <div class="chips" role="group" aria-label="Filter by category">{chips}</div>
        <label class="search" for="q"><span class="sr">Search recipes</span>{ico("i-search")}<input id="q" type="search" placeholder="Search recipes…" autocomplete="off"></label>
      </div>
      <div id="catBanner"></div>
      <p class="count" id="count" aria-live="polite">{len(RECIPES)} recipes</p>
      <div class="grid" id="grid">{cards}</div>
      <p class="empty" id="empty" hidden></p>
    </div>
  </section>
  <aside class="side" aria-label="Recipe shortcuts">
    <a class="special" id="special" href="recipes/{sp["id"]}.html">
      <img id="spImg" src="images/{sp["id"]}.jpg" alt="{e(sp["name"])}">
      {steam(3)}
      <span class="lbl">Today's special</span>
      <span class="sb"><span><h4 id="spName">{e(sp["name"])}</h4><p id="spSub">{e(sp["time"])} · {e(sp["region"])}</p></span><span class="arrow-dot">{ico("i-arrow")}</span></span>
    </a>
    <div class="box"><h3>Quick filters</h3><ul class="qf">{qf}</ul></div>
    <div class="box"><h3>Collections</h3><div class="cols">{cols}</div></div>
    <div class="box"><h3>Popular searches</h3><div class="tags">{tags}</div></div>
    <div class="side-news">
      <p class="eyebrow">The Sunday letter</p>
      <h3 style="margin-top:8px">Get new recipes in your inbox</h3>
      <p>One letter a week: five dinners, one showstopper and the shopping list.</p>
      <form class="inline-form" id="miniForm" novalidate>
        <label class="sr" for="miniEmail">Email</label>
        <input id="miniEmail" type="email" placeholder="Your email address" autocomplete="email">
        <button type="submit" aria-label="Subscribe">{ico("i-arrow")}</button>
      </form>
      <p class="mini-err" id="miniErr" aria-live="polite"></p>
    </div>
  </aside>
</div>'''
    page("recipes.html", "All recipes", f"Browse {len(RECIPES)} Pakistani recipes by category: biryani, karahi, daal, breads, street food and desserts.", main, "recipes", "chicken_biryani")


# ---------------------------------------------------------------- recipe pages
def serves_parts(s):
    m = re.match(r"^(\d+)(?:\s*[–-]\s*\d+)?\s*(.*)$", s)
    if not m or "jar" in s:
        return None
    return int(m.group(1)), (m.group(2) or "servings")


def related(r, n=3):
    out = [x for x in RECIPES if x["cat"] == r["cat"] and x["id"] != r["id"]]
    if len(out) < n:
        out += [x for x in RECIPES if x["id"] != r["id"] and x not in out and set(x.get("cols", [])) & set(r.get("cols", []))]
    if len(out) < n:
        out += [x for x in RECIPES if x["id"] != r["id"] and x not in out]
    return out[:n]


def spice_links(r):
    text = " ".join(r["ing"]).lower()
    found = [s for s in SPICES if any(w in text for w in SPICE_WORDS[s["slug"]])]
    if not found:
        return ""
    links = "".join(f'<a href="../spices/{s["slug"]}.html"><img src="../images/{s["img"]}.jpg" alt="" loading="lazy">{e(s["urdu"])}</a>' for s in found)
    return f'<div class="spice-links"><p class="eyebrow">Spices in this recipe</p><div>{links}</div></div>'


def build_recipe(r):
    root = "../"
    c = CAT[r["cat"]]
    sp = serves_parts(r["serves"])
    serv = (f'<span class="serv" id="serv" data-base="{sp[0]}" data-unit="{e(sp[1])}"><button type="button" id="servMinus" aria-label="Fewer servings">−</button><output id="servOut" aria-live="polite">{sp[0]} {e(sp[1])}</output><button type="button" id="servPlus" aria-label="More servings">+</button></span>'
            if sp else f'<span class="serv"><output>{e(r["serves"])}</output></span>')
    ings = "".join(f'<li><label><input type="checkbox"><span data-ing>{e(i)}</span></label></li>' for i in r["ing"])
    steps = "".join(f'<li><button type="button" aria-pressed="false">{e(s)}</button></li>' for s in r["steps"])
    rel = "".join(card(x, root, rv=True) for x in related(r))
    ld = {
        "@context": "https://schema.org", "@type": "Recipe", "name": r["name"], "description": r["intro"],
        "image": f"images/{r['id']}.jpg", "author": {"@type": "Person", "name": "Fatma"},
        "recipeCategory": c["name"], "recipeCuisine": "Pakistani", "recipeYield": r["serves"],
        "recipeIngredient": r["ing"], "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r["steps"]],
    }
    main = f'''<div class="wrap rd">
  <nav class="crumbs ink" aria-label="Breadcrumb"><a href="../index.html">Home</a><span aria-hidden="true">/</span><a href="../recipes.html">Recipes</a><span aria-hidden="true">/</span><a href="../recipes.html#{c["id"]}">{e(c["name"])}</a><span aria-hidden="true">/</span><span>{e(r["name"])}</span></nav>
  <div class="rd-top" style="margin-top:26px">
    <div class="rd-media"><img src="../images/{r["id"]}.jpg" alt="{e(r["name"])}">{steam(5)}<span class="tag">{e(c["name"])}</span></div>
    <div class="rd-body">
      <p class="eyebrow">{e(c["name"])} · {e(r["region"])}</p>
      <h1>{e(r["name"])}</h1>
      <p class="intro">{e(r["intro"])}</p>
      <div class="mstats"><div><b>{e(r["time"])}</b><small>Time</small></div><div><b>{e(r["serves"])}</b><small>Serves</small></div><div><b>{e(r["level"])}</b><small>Level</small></div></div>
      <div class="rd-actions">
        <button class="btn btn-line ink" type="button" data-save="{r["id"]}" aria-pressed="false">{ico("i-heart")}<span data-save-label>Save recipe</span></button>
        <a class="btn btn-green" href="#method">Start cooking {ico("i-arrow")}</a>
        <button class="btn btn-line ink" type="button" id="printBtn">{ico("i-steps")}Print</button>
      </div>
    </div>
  </div>
  <div class="rd-grid">
    <aside class="rd-panel rd-ing" aria-labelledby="ing-title">
      <h2 id="ing-title">Ingredients {serv}</h2>
      <ul class="checklist">{ings}</ul>
      <p class="hint-line">Tick ingredients off as you gather them.</p>
    </aside>
    <section class="rd-panel" id="method" aria-labelledby="method-title" style="scroll-margin-top:96px">
      <h2 id="method-title">Method</h2>
      <ol class="method">{steps}</ol>
      <p class="hint-line">Tap a step to mark it done.</p>
      <div class="tipbox"><b>Fatma's tip</b>{e(r["tip"])}</div>
      {spice_links(r)}
    </section>
  </div>
</div>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">Keep cooking</p><h2 id="rel-title">You might <span class="gold-word">also like</span></h2></div>
  <a class="link-more" href="../recipes.html#{c["id"]}">More {e(c["name"].lower())} {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
</section>'''
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    page(f"recipes/{r['id']}.html", r["name"], r["intro"], main, "recipes", r["id"], head)


# ---------------------------------------------------------------- story
def build_story():
    root = ""
    story = src("story.html").replace('<section class="story" id="story"', '<section class="story" id="story-main"')
    gal_ids = ["kabli_pulao", "golgappay", "beef_nihari", "gulab_jamun", "balochi_kaak", "chicken_qorma"]
    gallery = "".join(f'<a href="recipes/{i}.html"><img src="images/{i}.jpg" alt="{e(BY_ID[i]["name"])}" loading="lazy"><span>{e(BY_ID[i]["name"])}</span></a>' for i in gal_ids)
    main = page_head(root, [("Fatma's story", None)], "Fatma's <em>story</em>",
                     "From a notebook of handwritten family recipes to a kitchen that cooks for all of Pakistan.", "tips_spices") + story + f'''
<section class="wrap" style="padding-block:24px 40px" aria-labelledby="promise-title">
  <div class="sec-head"><div><p class="eyebrow">What you can expect</p><h2 id="promise-title">Fatma's <span class="gold-word">kitchen promise</span></h2></div></div>
  <div class="promise">
    <div class="rv">{ico("i-pot")}<h3>Cooked at home</h3><p>Every recipe is cooked in a family kitchen with ordinary pots and an ordinary stove, so it works in yours.</p></div>
    <div class="rv">{ico("i-steps")}<h3>Written properly</h3><p>Real measurements and timings, with the small details that grandmothers never wrote down.</p></div>
    <div class="rv">{ico("i-map")}<h3>From every region</h3><p>Karachi street food, Lahori karahi, Peshawari pulao and Balochi breads, all on one table.</p></div>
  </div>
</section>
<section class="wrap story-page" style="padding-top:40px" aria-labelledby="gal-title">
  <div class="sec-head"><div><p class="eyebrow">From Fatma's kitchen</p><h2 id="gal-title">A few <span class="gold-word">family favourites</span></h2></div><a class="link-more" href="recipes.html">All recipes {ico("i-arrow")}</a></div>
  <div class="gallery">{gallery}</div>
  <div class="center-cta" style="gap:12px;flex-wrap:wrap"><a class="btn btn-green" href="recipes.html">Explore the recipes {ico("i-arrow")}</a><a class="btn btn-line ink" href="ask.html">Ask Fatma a question</a></div>
</section>'''
    page("story.html", "Fatma's story", "How Tasty Pakistan began: a notebook of family recipes, cooked and written down properly.", main, "story", "tips_spices")


# ---------------------------------------------------------------- ask
def build_ask():
    root = ""
    contact = src("contact.html").replace('<h2 id="contact-title">Ask Fatma</h2>', '<h2 id="contact-title">Send a note</h2>')
    extra_faq = '''<details><summary>Can I use a pressure cooker?</summary><p>Yes, for nihari, haleem, lobia and most meat curries. Each recipe gives the pressure-cooker time where it helps.</p></details>
        <details><summary>How spicy are the recipes?</summary><p>Home-style medium. Halve the red chilli for children, or add extra green chillies at the end if you like heat.</p></details>
      </div>'''
    contact = contact.replace("</details>\n      </div>", "</details>\n        " + extra_faq, 1)
    main = page_head(root, [("Ask Fatma", None)], "Ask <em>Fatma</em>",
                     "Questions, recipe requests and collaborations. Fatma reads every message.", "chicken_qorma") + contact
    page("ask.html", "Ask Fatma", "Send Fatma a question about a recipe, a recipe request or a collaboration enquiry.", main, "ask", "chicken_qorma")


# ---------------------------------------------------------------- journal
def build_journal():
    root = ""
    posts = "".join(post_card(p, root) for p in journal)
    spices = "".join(spice_card(s, root) for s in SPICES[:6])
    main = page_head(root, [("Journal", None)], "The <em>journal</em>",
                     "Techniques, celebrations and kitchen secrets from the Pakistani dastarkhwan.", "sheer_khurma") + f'''
<section class="wrap" style="padding-block:72px 40px" aria-label="Articles">
  <div class="posts">{posts}</div>
</section>
<section class="wrap" style="padding-block:40px 96px" aria-labelledby="sg-title">
  <div class="sec-head"><div><p class="eyebrow">Spice guide</p><h2 id="sg-title">Know your <span class="gold-word">masala</span></h2></div><a class="link-more" href="spices.html">All {len(SPICES)} spices {ico("i-arrow")}</a></div>
  <div class="posts">{spices}</div>
</section>'''
    page("journal.html", "Journal", "Techniques, celebrations and kitchen secrets from Fatma's kitchen.", main, "journal", "sheer_khurma")
    for p in journal:
        root = "../"
        body = ""
        for blk in p["body"]:
            if blk[0] == "h":
                body += f"<h2>{e(blk[1])}</h2>"
            elif blk[0] == "p":
                body += f"<p>{e(blk[1])}</p>"
            elif blk[0] == "callout":
                body += f'<div class="callout"><b>{e(blk[1])}</b>{e(blk[2])}</div>'
        rel = "".join(card(BY_ID[i], root, rv=True) for i in p["related"][:3])
        main = page_head(root, [("Journal", "../journal.html"), (p["title"], None)], e(p["title"]), p["summary"], p["img"], p["tag"] + " · " + p["read"]) + f'''
<article class="wrap article">
  <p class="lead">{e(p["lead"])}</p>
  <figure><img src="../images/{p["img"]}.jpg" alt="" loading="lazy"></figure>
  {body}
</article>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">Cook from this story</p><h2 id="rel-title">Recipes to <span class="gold-word">try next</span></h2></div><a class="link-more" href="../journal.html">All stories {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
</section>'''
        page(f"journal/{p['slug']}.html", p["title"], p["summary"], main, "journal", p["img"])


# ---------------------------------------------------------------- spice guide
def spice_card(s, root):
    return f'''<article class="post rv">
  <a class="stretch" href="{root}spices/{s["slug"]}.html">
    <div class="media"><span class="post-tag">{e(s["english"])}</span><img src="{root}images/{s["img"]}.jpg" alt="{e(s["urdu"])} ({e(s["english"])})" loading="lazy"></div>
    <h3 style="margin-top:14px">{e(s["urdu"])} <span class="gold-word">({e(s["english"].lower())})</span></h3>
  </a>
  <p>{e(s["lead"])}</p>
  <span class="read">Read the guide {ico("i-arrow")}</span>
</article>'''


def build_spices():
    root = ""
    cards = "".join(spice_card(s, root) for s in SPICES)
    main = page_head(root, [("Spice guide", None)], "The spice <em>guide</em>",
                     "What each masala is, where it comes from, why Pakistani cooks use it, and what science says about its health benefits.", "tips_spices") + f'''
<section class="wrap" style="padding-block:64px 96px" aria-label="Spices">
  <div class="posts">{cards}</div>
  <p class="disclaimer">These guides are for cooking and general interest, not medical advice. Health findings are summarised from the sources listed in each guide. Speak to your doctor before using spices as supplements or remedies.</p>
</section>'''
    page("spices.html", "Spice guide: Pakistani masala explained", "A guide to the spices of Pakistani cooking: haldi, zeera, dhaniya, lal mirch, kali mirch, elaichi, dalchini, laung, adrak and lehsan. History, uses and health benefits.", main, "journal", "tips_spices")
    for s in SPICES:
        root = "../"
        body = "".join(f"<h2>{e(h)}</h2><p>{e(t)}</p>" for h, t in s["sections"])
        faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in s["faq"])
        src_list = "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{e(t)}</a></li>' for t, u in s["sources"])
        rel = "".join(card(BY_ID[i], root, rv=True) for i in s["recipes"] if i in BY_ID)
        others = "".join(f'<a href="{o["slug"]}.html"><img src="../images/{o["img"]}.jpg" alt="" loading="lazy">{e(o["urdu"])}</a>' for o in SPICES if o["slug"] != s["slug"])
        used = ", ".join(BY_ID[i]["name"] for i in s["recipes"] if i in BY_ID)
        ld = [
            {"@context": "https://schema.org", "@type": "Article", "headline": s["title"], "description": s["meta"],
             "image": f"images/{s['img']}.jpg", "author": {"@type": "Person", "name": "Fatma"},
             "publisher": {"@type": "Organization", "name": SITE}, "inLanguage": "en", "about": f"{s['urdu']} ({s['english']}, {s['latin']})"},
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in s["faq"]]},
        ]
        head = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
        main = page_head(root, [("Spice guide", "../spices.html"), (s["urdu"], None)],
                         f'{e(s["urdu"])} <em>({e(s["english"].lower())})</em>', s["lead"], s["img"], "Spice guide · " + s["latin"]) + f'''
<article class="wrap article">
  <div class="glance">
    <div><small>Urdu name</small><b>{e(s["urdu"])}</b></div>
    <div><small>English</small><b>{e(s["english"])}</b></div>
    <div><small>Botanical name</small><b><i>{e(s["latin"])}</i></b></div>
    <div><small>Try it in</small><b>{e(used)}</b></div>
  </div>
  <figure><img src="../images/{s["img"]}.jpg" alt="{e(s["urdu"])} ({e(s["english"])})" loading="lazy"></figure>
  {body}
  <h2>Frequently asked questions</h2>
  <div class="faq">{faq}</div>
  <div class="sources"><h3>Sources</h3><ul>{src_list}</ul></div>
  <p class="disclaimer">This guide is for cooking and general interest and is not medical advice. Speak to your doctor before using any spice as a supplement or remedy, especially if you are pregnant or take medicines.</p>
</article>
<section class="wrap rel" aria-labelledby="rel-title">
  <div class="sec-head"><div><p class="eyebrow">Cook with {e(s["urdu"].lower())}</p><h2 id="rel-title">Recipes that <span class="gold-word">use it</span></h2></div><a class="link-more" href="../spices.html">All spices {ico("i-arrow")}</a></div>
  <div class="picks">{rel}</div>
  <div class="spice-links" style="margin-top:44px"><p class="eyebrow">More from the spice guide</p><div>{others}</div></div>
</section>'''
        page(f"spices/{s['slug']}.html", s["title"], s["meta"], main, "journal", s["img"], head, suffix=False)


def build_404():
    # Absolute paths so the page works at any missing URL depth on the server.
    main = f'''<section class="page-head">
  <div class="ph-img"><img src="/images/hero_biryani.jpg" alt=""></div>
  <div class="wrap">
    <p class="eyebrow" style="margin-top:18px">Page not found</p>
    <h1>This dish isn't <em>on the menu</em></h1>
    <p class="ph-sub">The page you're looking for has moved or never existed. Try the recipes, or search for a dish.</p>
    <form class="hero-search" role="search" data-search style="margin-top:28px">
      {ico("i-search", "s")}
      <label class="sr" for="nfQ">Search recipes</label>
      <input id="nfQ" type="search" placeholder="Search biryani, nihari, kheer…" autocomplete="off">
      <button type="submit" aria-label="Search">{ico("i-arrow")}</button>
    </form>
    <div class="f-actions" style="margin-top:24px"><a class="btn btn-gold" href="/index.html">Go to home</a><a class="btn btn-line" href="/recipes.html">Browse recipes</a></div>
  </div>
</section>'''
    page("404.html", "Page not found", "This page could not be found.", main, head_extra='<meta name="robots" content="noindex">\n', root_override="/")
    PAGES.remove("404.html")


def build_sitemap():
    if not SITE_URL:
        return
    base = SITE_URL.rstrip("/")
    urls = "".join(f"<url><loc>{base}/{'' if p == 'index.html' else p}</loc></url>" for p in PAGES)
    open(os.path.join(HERE, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")


# ---------------------------------------------------------------- data.js
def build_data():
    keep = ["id", "name", "cat", "region", "time", "mins", "level", "serves", "veg", "cols", "intro"]
    payload = {"categories": CATS, "collections": COLS, "recipes": [{k: r[k] for k in keep if k in r} for r in RECIPES]}
    open(os.path.join(HERE, "assets/data.js"), "w", encoding="utf-8").write(
        "/* Generated by build.py from data/recipes.json. Do not edit by hand. */\nwindow.TP = " + json.dumps(payload, ensure_ascii=False) + ";\n")


if __name__ == "__main__":
    missing = [r["id"] for r in RECIPES if not os.path.exists(os.path.join(HERE, "images", r["id"] + ".jpg"))]
    if missing:
        raise SystemExit("Missing photos in images/: " + ", ".join(missing))
    build_data()
    build_home()
    build_recipes()
    for r in RECIPES:
        build_recipe(r)
    build_story()
    build_ask()
    build_journal()
    build_spices()
    build_404()
    build_sitemap()
    print(f"Built home, recipes, story, ask, journal, {len(RECIPES)} recipe pages, {len(journal)} articles and {len(SPICES)} spice guides.")
