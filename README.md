# Stupid Idiots

A small, independent collective: different people, individual projects, and a shared space for our work.

## Run

Open `index.html`, or run `python3 -m http.server 8000` from this directory and open http://localhost:8000. No build step or dependencies are required.

## Files

- `index.html` — hero, About, three featured project slots, three member profiles, footer, and inline SVG ribbon.
- `css/styles.css` — layout, responsive rules, placeholder artwork, hover effects, and ribbon styling.
- `js/main.js` — scroll-linked text entrances, with reduced-motion support. The ribbon follows the page without a continuous animation loop.

## Replace the editable slots

The bracketed text is intentionally unfinished; these are not claims about actual people or projects.

### Featured projects

Search for `data-project-slot="1"`, `"2"`, or `"3"` in `index.html`. Replace the title, category, summary, creator credit, status, and expanded project information. Replace the `.hub-project-visual` contents with a real image and meaningful alt text. Add a real project/repository link when available; placeholder link text is not clickable.

The first project is the larger lead feature. Projects two and three sit underneath it.

### Members

Search for `data-member-slot="1"`, `"2"`, or `"3"`. Replace the name, interests, short bio, portrait/avatar, and profile link. Duplicate or remove a whole `article` to change the number of members. No names or biographies have been invented.

Remove the small draft notes and “EDITABLE SLOT” badges when real content is ready.

## Editing and hosting

The hero typography and current purple ribbon are preserved. The page uses standard HTML, CSS, and JavaScript. The existing hero background photo loads from its Unsplash URL; other artwork is CSS or SVG. Native project accordions and all content work without JavaScript.

Webflow and this repository were updated together for this reconstruction. Future edits are not automatically synchronized. GitHub scroll effects are lightweight JavaScript equivalents of the native Webflow interactions.

## Animation and typography update

The serif accents use the regular sans-serif font. Scroll-linked text entrances are retained, and the full-page ribbon is no longer translated continuously. The matching changes are saved in Webflow but have not been published there. Future GitHub pushes require an explicit request.

The JavaScript pauses each text entrance when it reaches its target. Fully revealed text stays at opacity 1 with no transform and receives no animation-frame updates while scrolling beyond its reveal range. Scrolling back into the range resumes the effect. This additional optimization applies to these standalone files; Webflow's native interactions remain unchanged.
