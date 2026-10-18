# Post to the member journal

Members publish through this repository's existing GitHub access. The website does not create accounts, accept uploads, store credentials, or send posts to a server.

## The easiest route

1. Open [`_template.md`](_template.md) in this folder and copy its contents.
2. Open this repository on GitHub. In `posts/`, select **Add file → Create new file**.
3. Name it `YYYY-MM-DD-a-short-title.md`, for example `2026-10-19-testing-a-new-idea.md`. Use lowercase letters, numbers, and hyphens, with at least one letter in the title part. The filename date and the `date` field must match.
4. Paste the template, fill in your name, title, date, summary, and any related project, then replace the body with your Markdown post. Use your own name and actual work. Set `draft: false` when you want the entry to appear, or omit `draft`.
5. Commit to `main` if your repository permissions allow it, or create a branch and pull request for review. **Build journal** validates pull requests with read-only repository permissions. Merging to `main` runs the publishing job in GitHub Actions.
6. Check that the action succeeds. It commits the generated journal, homepage cards, and relevant project updates to the same branch. The site's existing hosting process can then serve those files.

You can also copy `_template.md` locally, rename the copy, and edit it in a text editor before committing or uploading it to GitHub. The template and this README are never published as posts. No example member posts are included in the site.

The publishing action must be allowed to write repository contents. Branch protection or an organization policy may require the local-build route below instead. If a member pushes another commit while the action is running, its normal push can fail safely; run **Build journal → Run workflow** again after reviewing the branch. The action never force-pushes. It does not configure or change hosting. In particular, commits made with GitHub's workflow token do not trigger a separate GitHub Pages branch build; an existing deployment workflow must build/deploy the updated site, or a member can include the generated pages in their own commit.

## Metadata

Every post starts with one `---` block. Values may be plain single-line text or double-quoted JSON strings. Use double quotes and `\"` for quotes inside a value; single-quoted YAML, multiline YAML, arrays, and objects are not supported. Unknown fields and duplicate fields are errors, so typos do not silently disappear.

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | Yes | The post's title. |
| `author` | Yes | The name credited on the post. |
| `date` | Yes | A real date in `YYYY-MM-DD`, matching the filename. |
| `summary` | Yes | A short description used in the journal and cards. |
| `category` | No | `Project update`, `Experiment`, or `Note`. Defaults to `Note`. |
| `project` | No | Blank, `drop-tap`, `jansen-linkage`, or `heart-model`. The display names `Drop Tap`, `Jansen Linkage`, and `Working Heart Model` also work. |
| `cover` | No | A site-relative raster image path such as `assets/posts/my-prototype.png`. |
| `draft` | No | Unquoted `true` hides the post; `false` publishes it. Defaults to `false`. |

Drafts are still validated, but they have no generated page or feed entry. A future date does not schedule publication: use `draft: true` until the post is ready. Files in a public GitHub repository, including draft Markdown, are publicly readable there.

To add a new project, update the project directory and add its slug/display name to `PROJECTS` in `scripts/build_posts.py`; a matching `projects/slug.html` can then receive its updates.

## Writing format

Supported Markdown is deliberately small:

- Paragraphs separated by a blank line. Adjacent text lines become one paragraph.
- `## Section heading` and `### Smaller heading`; headings through six `#` characters work. A single `#` is rendered as a section heading below the page title.
- `**Bold**`, `*italic*`, and backtick-delimited inline code.
- `[A link](https://example.com)`, `http://` links, and `mailto:` links. Link labels and URLs must each fit on one line; URLs with literal spaces or `)` should be percent-encoded in external links.
- Site links written from the repository root: `[Drop Tap](projects/drop-tap.html)`. Do not prepend `../` or `/`. Simple existing page anchors such as `#top` work.
- One-level `- Bullet`, `* Bullet`, `+ Bullet`, or `1. Numbered` lists. Numbered lists preserve their first number. Separate different lists with a blank line. Nested lists and indented continuation blocks are not supported.
- Blockquotes beginning with `> `.
- Code blocks surrounded by triple-backtick lines. Add an optional language name after the opening fence, such as `python`.
- `![Describe what the image shows](assets/posts/my-prototype.png)` for local images. Upload the image to that folder before building; PNG, JPEG, GIF, WebP, and AVIF files are supported. Use alt text that conveys what matters in the image. Cover images repeat the linked post title context and are treated as decorative; describe meaningful details in the post body.

Raw HTML is displayed as text. Scripts, iframes, SVG uploads, external image embeds, unsafe URL schemes, path traversal, and symlinked files are not accepted by the publishing format. Tables, HTML embeds, reference-style links, and advanced Markdown extensions are not part of this format. When sharing code that contains Markdown punctuation, use a code block.

## Preview locally

From the repository root, with Python 3.10 or newer:

```sh
python3 scripts/build_posts.py --check
python3 scripts/build_posts.py
python3 -m http.server 8000
```

Open `http://localhost:8000/journal/`. No packages, passwords, or API keys are needed. `--check` validates without writing files. To run the publisher's regression tests:

```sh
python3 scripts/test_posts.py
```

Commit the Markdown, any images, and the generated changes together if you build locally. To edit a post, edit its Markdown and build again. To remove a published post, delete its Markdown or set `draft: true`, then build again.

## Generated files

`journal/index.html`, `journal/YYYY-MM-DD-title.html`, and `journal/feed.json` are generated. The feed is a plain JSON list for future integrations, with no generated timestamp. The build also refreshes marked journal sections in the homepage and existing project pages. Newer dates appear first, with reverse filename order as a stable tie-breaker.

Keep `journal/.generated-posts.json` committed. It records the generated files that the builder owns, so deleting a post removes only its old generated page. Files outside that manifest are preserved. The builder refuses to replace an existing journal output that is not recorded in its manifest. Edit the templates in `scripts/templates/` for shared journal layout changes, then rebuild.

The GitHub action watches source Markdown, post images, the builder, tests, and templates. Pull requests into `main` run tests and validation against GitHub's merge ref without writing to the repository. Pushes to `main` and manual branch runs build and commit the results. Generated output is excluded from its triggers, so its own commit does not cause a publishing loop.
