# Stupid Idiots

A static website and member journal for our independent collective. One voice. Different minds.

## Run locally

```sh
python3 scripts/build_posts.py
python3 -m http.server 8000
```

Visit `http://localhost:8000`. Python 3.10+ is enough; there are no packages to install. The output is ordinary HTML, CSS, and JavaScript and can be served by any static host. The checked-in generated pages are also ready to view without running the build.

## Publish a member post

1. Open the site's **Write a post** page (`journal/write.html`). Fill in your name, title, short summary, and story; optionally choose a related project.
2. **Copy Markdown**, then **Open GitHub**. Paste the complete Markdown into the new file and commit it, or propose a pull request if the branch requires review. The editor also offers a `.md` download.
3. When the Markdown reaches `main`, the **Build journal** GitHub Actions workflow validates it and commits the generated journal pages, homepage updates, and related-project updates. Your existing static hosting must publish the resulting files.

There are no website accounts or server submission endpoints. Publishing uses members' existing GitHub repository access. Draft text stays in the current browser when local storage is available; the editor does not transmit it. The GitHub link contains only the proposed filename. A public copy of the writing page doesn't grant permission to change the repository.

Members comfortable editing files can copy `posts/_template.md` instead. See [the posting guide](posts/README.md) for Markdown, images, drafts, editing, and removal.

## Repository setup

Commit and push this change to make the included workflow available. GitHub Actions must be enabled and the workflow must be allowed to write repository contents. Branch rules may require generated changes to go through a pull request instead; in that case run `python3 scripts/build_posts.py` locally and include the generated files in that pull request. The workflow does not deploy or change the site's hosting configuration. GitHub Pages branch builds are not triggered by workflow-token commits; for that hosting setup, include generated pages in the member's commit or use a deployment workflow that builds before deploying.

The workflow uses the repository's built-in token. It needs no application secrets, database, or additional service. Validation also runs for pull requests with read-only permissions. No account or hosting setup is bundled with the site.

## Site structure

- `index.html` — introduction, project cards, and latest posts.
- `projects/index.html` and `projects/*.html` — project directory and individual overviews.
- `about.html` — collective, vision, and collaboration context.
- `journal/index.html` and generated dated pages — member posts.
- `journal/write.html` — local draft editor and Markdown export.
- `posts/*.md` — editable post sources; `_template.md` and `README.md` aren't published.
- `scripts/build_posts.py` and `scripts/templates/` — static journal builder and page templates.

Edit project and About content in the HTML pages. Keep project names/statuses consistent across their homepage card, directory entry, and detail page. The builder owns the marked journal sections in the homepage and project pages. Edit journal layouts in `scripts/templates/`, then rebuild. It only removes dated output files recorded in `journal/.generated-posts.json`; never edit generated posts directly.

Styling is in `css/`, with original navy, ice, and lavender colors. `js/site.js` controls the mobile menu; `js/motion.js` adds optional animation. Browsing works without JavaScript; the writing helper requires it. No external fonts, analytics, or runtime dependencies are loaded.

Artwork is conceptual rather than product screenshots or engineering schematics. Creator credits and external project links remain unpublished until real information is available. No member posts have been invented.

## Check changes

```sh
python3 scripts/test_posts.py
python3 scripts/build_posts.py --check
python3 scripts/build_posts.py
```

The build validates all posts before writing outputs. Markdown supports headings, emphasis, lists, quotes, code, links, and local raster images. Raw HTML is displayed as text. Unsupported metadata or unsafe links produce a filename and an actionable error.
