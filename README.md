# shop

A Herald extension that searches clothing stores for items in your sizes and
hands back links, prices and a contact sheet of the product photos.

Stores: H&M US, Uniqlo US and Old Navy US, each read through the JSON endpoint
its own website calls. Kohl's refuses scripts, so it is read through a real
Chrome window on a Mac you can reach over ssh, and stays off until you name
one. Nothing is added to a cart or bought.

## Install

```bash
herald ext install https://github.com/benmross/herald-shop
herald config set shop.sizes.tops L
herald config set shop.sizes.pants 32/30
herald ext enable shop
ln -s ~/.herald/extensions/shop/bin/herald-shop ~/.local/bin/herald-shop
```

Optional, for Kohl's: `herald config set shop.kohls.ssh_host <alias>`, where
`<alias>` is an ssh host for a Mac with Google Chrome installed. Kohl's also
needs Playwright in Herald's venv (`~/herald/venv/bin/pip install playwright`).
The contact sheet needs Pillow.

## Settings

| key | what |
|---|---|
| `shop.sizes` | one entry per kind of garment, e.g. `{"tops": "L", "pants": "32/30"}`. `herald-shop --for tops` uses one. |
| `shop.notes` | free text on fit, read by the skill (for example "sizes up to L in hoodies") |
| `shop.kohls.ssh_host` | an ssh host alias for a Mac running Chrome; Kohl's is off without it |

Your sizes live in your own config.json and never in this directory, so
`herald ext update shop` can always fast-forward it.

## Use

Ask Herald for clothes and the `shop` skill does the rest, or run it directly:

```bash
herald-shop "baggy jeans" --for pants -n 5
herald-shop "oversized hoodie" "heavyweight hoodie" --for tops --sheet /tmp/hoodies
```

Only H&M's listing has per-size stock, so sizes are enforced there. Uniqlo is
matched on the sizes a style comes in and Old Navy and Kohl's are not checked;
results from those are marked so.
