# Share something with the collective

Start with [`posts/_template.md`](posts/_template.md) to share an update, experiment, or note. Copy its contents into a new Markdown file in `posts/` on GitHub or locally, fill in the metadata and story, then commit it or open a pull request. Only the repository permissions you already have are used.

Use a filename such as `posts/2026-10-19-a-small-discovery.md`, with the same date in the post's metadata. Setting the `project` field makes the post appear on that project's page as well as the journal. The homepage shows the latest three entries.

The [posting guide](posts/README.md) explains GitHub steps, metadata, images, drafts, and Markdown. Edit or remove the source `.md` file to update or remove a published post, then let the workflow rebuild it.

Before merging a pull request, check that **Build journal** passes. If repository rules prevent the workflow from committing generated pages, run the builder locally and include its output in the pull request. Publishing on the live website depends on the repository's configured static host.
