# Share something with the collective

Use the site's **Write a post** page to prepare an update, experiment, or note. Copy the Markdown, use **Open GitHub**, paste it into the proposed new file, and commit it or open a pull request. Only the repository permissions you already have are used.

The filename belongs under `posts/`, for example `posts/2026-10-19-a-small-discovery.md`. A related-project selection makes the post appear on that project's page as well as the journal. The homepage shows the latest three entries.

For direct editing, start with `posts/_template.md`. The [posting guide](posts/README.md) explains metadata, images, drafts, and Markdown. Edit or remove the source `.md` file to update or remove a published post, then let the workflow rebuild it.

Before merging a pull request, check that **Build journal** passes. If repository rules prevent the workflow from committing generated pages, run the builder locally and include its output in the pull request. Publishing on the live website depends on the repository's configured static host.
