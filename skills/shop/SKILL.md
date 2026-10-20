---
name: shop
description: Find clothes for the user at H&M, Uniqlo, Old Navy and Kohl's in their sizes and return links. Use when they ask what to wear, for items similar to a photo or outfit, or to look for a specific garment.
---

# Shop

`herald-shop "<query>" [--store hm|uniqlo|oldnavy|kohls] [--for tops|--sizes L,XL] [-n 5] [--sheet x.jpg] [--json]`
searches H&M, Uniqlo and Old Navy (US) through the JSON endpoints their own sites call;
the HTML pages return 403 to scripts. Read-only: nothing is added to a cart or bought,
and a purchase would be red. Men's (and Uniqlo unisex) items only.

Stock: only H&M's listing has per-size stock, so `--sizes` is enforced there. Uniqlo
results are matched on the sizes a style comes in, Old Navy results are not size-checked;
both are marked "stock not checked". Say so when you hand over their links.

Kohl's works only through a real, windowed Chrome on a Mac: headless Chrome, curl and urllib all
get 403. `lib/kohls_browser.py` starts Chrome there over ssh with a debug port and its own profile,
tunnels the port, drives it with Playwright from Herald's venv, and quits that Chrome when the search
ends (left running, it takes over the user's own Chrome window). It is off until
`shop.kohls.ssh_host` names the Mac, and needs that Mac awake and logged in; `herald-shop` says so
when it is not. Kohl's items carry no size data, and the list price shown is before Kohl's Cash and
any rewards discounts.

The user's sizes are in config.json under `shop.sizes`, one entry per kind of garment
(`herald config get shop.sizes`). `--for tops` or `--for pants` uses them; `--sizes` overrides.
Any notes on fit (a kind they size up in, say) are under `shop.notes`. Shoes, belts and rings
use their own size labels, so leave sizes off and tell them what is in stock. If `shop.sizes` is
not set, ask for their sizes and save them with `herald config set shop.sizes.tops M`.

For an outfit photo, run one query per item. Queries that name a style
("baggy jeans", "oversized printed t-shirt") work better than colour words.
The search does not match watches or headphones at H&M; say so rather than guess.
Use the curl-free script: the guard blocks `curl -G` to api.hm.com.

## Looking at the products

Add `--sheet /tmp/x.jpg` and Read the file: it is one numbered grid of the results'
photos, so a session sees them in a single call. Compare it against the photo they
sent before choosing links; names and categories alone matched badly (a "belt"
query returned ones that looked nothing like theirs, and one "washed black" tee was
plain).

Caching: H&M product photos are cached under `ledger/raw/shop/images/` forever, because
image.hm.com URLs end in a hash of the file's content, so a changed picture gets a
new URL and a cached copy cannot be stale. Search results (stock, price, sizes) are
never cached: they change, and nothing in them says when.

Uniqlo and Old Navy image URLs are not content hashes, so those photos are fetched fresh each run.

## How to search a whole outfit or board (what the 18 Oct 2026 board run taught)

1. Read the picture and write the categories first (jeans, outerwear, knits, hoodies, boots, bags, ...).
2. One `herald-shop` run per category, in the background and in parallel, each with 4 to 11 phrasings
   of the same thing, `--pages 2` for the big categories, `--match`/`--exclude` regexes to drop
   off-topic padding, and `--out cat.json`. Do not run them one at a time: Kohl's alone takes about
   6 seconds a page.
3. Read `--from cat.json --list` (names and prices, deduplicated). Kohl's pads results with women's,
   team-merch and third-party marketplace listings, so scan names first and never view all photos.
4. Pick 20 to 40 numbers and run `--from cat.json --pick 3,9,... --sheet x`, then Read the sheet. This
   is the step that catches wrong matches: names lied often (a "washed black" tee was plain, a "men's"
   jean showed a woman model).
5. Only then write links. Say which stores' sizes were not checked.

Marketplace listings from Kohl's (long comma-stuffed titles) are dropped unless `--marketplace`.
Uniqlo is thin on jackets, Old Navy is cheap but its fits run conventional, H&M has the closest
fades and washes, and Kohl's is where Levi's, Timberland-style boots and workwear are cheapest.
