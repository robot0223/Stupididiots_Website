# Stupid Idiots

A small, independent collective: different people, individual projects, and a shared space for our work.

## Run

Open `index.html`, or run `python3 -m http.server 8000` from this directory and open http://localhost:8000. No build step or dependencies are required.

## Files

- `index.html` — hero, About, three featured project slots, three member profiles, and footer.
- `css/styles.css` — layout, responsive rules, placeholder artwork, and hover effects.
- `js/main.js` — scroll-linked text entrances, with reduced-motion support.

## Replace the editable slots

The bracketed text is intentionally unfinished; these are not claims about actual people or projects.

### Featured projects

Search for `data-project-slot="1"`, `"2"`, or `"3"` in `index.html`. Replace the title, category, summary, creator credit, status, and expanded project information. Replace the `.hub-project-visual` contents with a real image and meaningful alt text. Add a real project/repository link when available; placeholder link text is not clickable.

The first project is the larger lead feature. Projects two and three sit underneath it.

### Members

Search for `data-member-slot="1"`, `"2"`, or `"3"`. Replace the name, interests, short bio, portrait/avatar, and profile link. Duplicate or remove a whole `article` to change the number of members. No names or biographies have been invented.

Remove the small draft notes and “EDITABLE SLOT” badges when real content is ready.

## Editing and hosting

The hero typography is preserved. The decorative ribbon and hero ellipse have been removed. The page uses standard HTML, CSS, and JavaScript. The existing hero background photo loads from its Unsplash URL; other artwork is CSS or SVG. Native project accordions and all content work without JavaScript.

Webflow and this repository were updated together for this reconstruction. Future edits are not automatically synchronized. GitHub scroll effects are lightweight JavaScript equivalents of the native Webflow interactions.

## Animation and typography

Highlighted text uses the same sans-serif font as the surrounding text. Scroll-linked entrances stop updating when they settle and resume when the reveal target changes. Reduced-motion preferences are respected.

The ribbon, guiding light, particles, and decorative hero ellipse have been removed. Webflow uses the same text-entrance JavaScript in its Home embed; the previous native text interactions are removed to avoid running both implementations.

Webflow changes are saved but not published. Future GitHub pushes require an explicit request.
