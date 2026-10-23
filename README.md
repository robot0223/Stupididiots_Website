# Stupid Idiots

Official website of our research group.

## Run locally

Open `index.html` in a browser, or run `python3 -m http.server 8000` from this directory and visit http://localhost:8000.

## Edit the site

- `index.html`: page content, navigation, inline SVG ribbon, radio controls, and expandable thoughts.
- `css/styles.css`: layout, typography, responsive styles, translucent artwork, ribbon colors, and CSS animations.
- `js/main.js`: scroll reveal, ribbon drift, and moving typography. Respects reduced-motion preferences.

The page uses standard HTML, CSS, and JavaScript; no build step, jQuery, or Webflow runtime is required. The existing hero background photograph still loads from its Unsplash URL in the stylesheet. All other artwork uses CSS or inline SVG.

The Orbit / Scatter / Align controls and expandable thoughts work without JavaScript. Content remains visible if JavaScript is disabled.

## Design source

Extracted from the saved Webflow Home design on October 23, 2026, preserving its hero and replacing the lower sections with the latest redesign. Webflow scroll interactions are reproduced in vanilla JavaScript. These repository files are the standalone site; edits here do not automatically sync back into Webflow.
