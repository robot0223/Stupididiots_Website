#!/usr/bin/env python3
"""Regression tests for publishing, run entirely in temporary directories."""

import json
import tempfile
import unittest
from pathlib import Path

from build_posts import BuildError, build, markdown, read_post, safe_link


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="journal-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "posts").mkdir()
        (self.root / "scripts/templates").mkdir(parents=True)
        (self.root / "projects").mkdir()
        (self.root / "assets/posts").mkdir(parents=True)
        (self.root / "scripts/templates/journal-index.html").write_text(
            '<main data-count="{{POST_COUNT}}">{{POSTS}}</main>', encoding="utf-8")
        (self.root / "scripts/templates/journal-post.html").write_text(
            '<title>{{TITLE}}</title><h1>{{TITLE}}</h1><p>{{AUTHOR}} {{DATE}} {{CATEGORY}} '
            '{{PROJECT}} {{SUMMARY}} {{POST_SLUG}}</p>{{COVER}}<article>{{CONTENT}}</article>', encoding="utf-8")
        (self.root / "index.html").write_text(
            'home<!-- journal:latest:start -->old<!-- journal:latest:end -->end', encoding="utf-8")
        (self.root / "projects/drop-tap.html").write_text(
            '<!-- journal:project:drop-tap:start -->old<!-- journal:project:drop-tap:end -->', encoding="utf-8")

    def post(self, slug="2026-10-19-first-experiment", body="## What happened\n\nA useful observation.", **fields):
        metadata = {"title": "First experiment", "author": "Test Member", "date": slug[:10],
                    "category": "Experiment", "summary": "A short account of a test."}
        metadata.update(fields)
        lines = []
        for key, value in metadata.items():
            if value is None:
                continue
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        path = self.root / "posts" / (slug + ".md")
        path.write_text("---\n" + "\n".join(lines) + "\n---\n\n" + body + "\n", encoding="utf-8")
        return path

    def generated(self, slug="2026-10-19-first-experiment"):
        return (self.root / "journal" / (slug + ".html")).read_text(encoding="utf-8")

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_empty_journal_and_ignored_author_templates(self):
        (self.root / "posts/_template.md").write_text("not a valid post")
        (self.root / "posts/README.md").write_text("documentation")
        self.assertEqual(build(self.root), 0)
        self.assertIn("No posts published yet", self.generated("index"))
        self.assertEqual(json.loads((self.root / "journal/feed.json").read_text()), [])
        self.assertIn('href="journal/write.html"', (self.root / "index.html").read_text())

    def test_json_metadata_and_unicode(self):
        self.post(title='A "quoted" title: 안녕하세요', author="테스트")
        build(self.root)
        page = self.generated()
        self.assertIn('A &quot;quoted&quot; title: 안녕하세요', page)
        self.assertIn("테스트", page)

    def test_plain_metadata_and_default_category(self):
        path = self.post(category=None)
        text = path.read_text().replace('title: "First experiment"', 'title: First experiment')
        path.write_text(text)
        post = read_post(path, self.root)
        self.assertEqual(post.title, "First experiment")
        self.assertEqual(post.category, "Note")

    def test_markdown_supported_blocks(self):
        body = ('## Heading\n\nA **bold** and *italic* paragraph with `inline <code>`.\n'
                'Same paragraph.\n\n- First\n- Second\n\n1. One\n2. Two\n\n'
                '> A quotation.\n\n```python\nprint("<script>")\n```\n\n'
                '[External](https://example.com) [Project](projects/drop-tap.html)')
        rendered = markdown(body, self.root)
        for fragment in ('<h2>Heading</h2>', '<strong>bold</strong>', '<em>italic</em>',
                         '<code>inline &lt;code&gt;</code>', '<ul><li>First</li>',
                         '<ol><li>One</li>', '<blockquote><p>A quotation.</p></blockquote>',
                         '<code class="language-python">', 'href="../projects/drop-tap.html"'):
            self.assertIn(fragment, rendered)

    def test_html_and_metadata_are_escaped(self):
        self.post(title='<img src=x onerror="alert(1)">',
                  body='<script>alert(1)</script>\n\n<iframe src="javascript:alert(1)"></iframe>')
        build(self.root)
        page = self.generated()
        self.assertNotIn("<script>", page)
        self.assertNotIn("<iframe", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)

    def test_unsafe_links_rejected(self):
        for url in ("javascript:alert(1)", "JaVaScRiPt:evil", "data:text/html,bad", "//evil.example",
                    "../secret.txt", "%2e%2e/secret", "/etc/passwd", "assets/../secret", "file:///tmp/a"):
            with self.subTest(url=url), self.assertRaises(BuildError):
                markdown(f"[link]({url})", self.root)

    def test_safe_web_email_and_anchor_links(self):
        for url in ("https://example.com/path?q=x&y=z", "http://example.com", "mailto:team@example.com", "#top"):
            with self.subTest(url=url):
                self.assertEqual(safe_link(url), url)

    def test_raster_images_and_cover(self):
        (self.root / "assets/posts/test.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"test-image")
        self.post(body='![A prototype](assets/posts/test.png)', cover="assets/posts/test.png")
        build(self.root)
        self.assertIn('src="../assets/posts/test.png" alt="A prototype"', self.generated())
        self.assertIn('class="post-cover"', self.generated())
        self.assertIn('src="assets/posts/test.png"', (self.root / "index.html").read_text())

    def test_image_restrictions(self):
        (self.root / "assets/posts/bad.png").write_text('<svg onload="alert(1)"></svg>')
        cases = ["![Text](https://example.com/a.png)", "![Text](assets/posts/nope.png)",
                 "![Text](assets/posts/bad.png)", "![](assets/posts/bad.png)",
                 "![Text](assets/posts/../bad.png)", "![Text](assets/posts/x.svg)"]
        for body in cases:
            with self.subTest(body=body), self.assertRaises(BuildError):
                markdown(body, self.root)

    def test_symlink_images_are_rejected(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.root / "assets/posts/link.png").symlink_to(outside)
        with self.assertRaises(BuildError):
            markdown("![Text](assets/posts/link.png)", self.root)

    def test_missing_and_unknown_metadata(self):
        for fields in ({"title": None}, {"author": ""}, {"summary": ""}, {"unknown": "oops"},
                       {"category": "News"}, {"project": "nonexistent"}):
            with self.subTest(fields=fields):
                self.post(**fields)
                with self.assertRaises(BuildError):
                    build(self.root)

    def test_duplicate_metadata_rejected(self):
        path = self.post()
        path.write_text(path.read_text().replace("---\n", '---\ntitle: duplicate\n', 1))
        with self.assertRaisesRegex(BuildError, "Duplicate"):
            build(self.root)

    def test_date_and_filename_validation(self):
        for slug, date in (("2026-02-30-impossible", "2026-02-30"),
                           ("2026-10-19-test", "2026-10-18"), ("2026-10-19-123", "2026-10-19"),
                           ("bad-name", "2026-10-19"), ("2026-10-19-test", "20261019")):
            with self.subTest(slug=slug, date=date):
                path = self.post(slug, date=date)
                with self.assertRaises(BuildError):
                    build(self.root)
                path.unlink()

    def test_drafts_never_appear_and_remove_previously_published_output(self):
        self.post()
        build(self.root)
        self.post(draft=True)
        self.assertEqual(build(self.root), 0)
        self.assertFalse((self.root / "journal/2026-10-19-first-experiment.html").exists())
        self.assertNotIn("First experiment", (self.root / "index.html").read_text())

    def test_draft_errors_are_still_reported(self):
        self.post(draft=True, body="[unsafe](javascript:evil)")
        with self.assertRaises(BuildError):
            build(self.root)

    def test_sorting_and_latest_limit(self):
        for slug in ("2026-10-17-older", "2026-10-19-alpha", "2026-10-19-zeta", "2026-10-18-middle"):
            self.post(slug, title=slug)
        build(self.root)
        feed = json.loads((self.root / "journal/feed.json").read_text())
        self.assertEqual([item["slug"] for item in feed], ["2026-10-19-zeta", "2026-10-19-alpha",
                                                         "2026-10-18-middle", "2026-10-17-older"])
        self.assertNotIn("2026-10-17-older", (self.root / "index.html").read_text())

    def test_project_display_name_routes_only_matching_posts(self):
        self.post(project="Drop Tap")
        self.post("2026-10-18-unrelated", title="Unrelated")
        build(self.root)
        project = (self.root / "projects/drop-tap.html").read_text()
        self.assertIn('href="../journal/2026-10-19-first-experiment.html"', project)
        self.assertNotIn("Unrelated", project)
        self.assertIn("Drop Tap", self.generated())

    def test_deterministic_rebuild_and_noop_mtime(self):
        self.post()
        build(self.root)
        before = self.snapshot()
        mtime = (self.root / "journal/index.html").stat().st_mtime_ns
        build(self.root)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(mtime, (self.root / "journal/index.html").stat().st_mtime_ns)

    def test_public_output_permissions_and_noop_permission_repair(self):
        self.post()
        build(self.root)
        paths = [*sorted((self.root / "journal").iterdir()), self.root / "index.html",
                 self.root / "projects/drop-tap.html"]
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        for path in paths:
            self.assertEqual(path.stat().st_mode & 0o777, 0o644, str(path))
            path.chmod(0o600)
        build(self.root)
        for path in paths:
            self.assertEqual(path.stat().st_mode & 0o777, 0o644, str(path))
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before[path])

    def test_check_does_not_write(self):
        self.post()
        before = self.snapshot()
        self.assertEqual(build(self.root, check=True), 1)
        self.assertEqual(before, self.snapshot())

    def test_deletion_preserves_unowned_files(self):
        path = self.post()
        build(self.root)
        (self.root / "journal/write.html").write_text("authored writer page")
        path.unlink()
        build(self.root)
        self.assertFalse((self.root / "journal/2026-10-19-first-experiment.html").exists())
        self.assertEqual((self.root / "journal/write.html").read_text(), "authored writer page")

    def test_existing_unowned_output_is_not_overwritten(self):
        (self.root / "journal").mkdir()
        (self.root / "journal/index.html").write_text("authored page")
        with self.assertRaisesRegex(BuildError, "untracked"):
            build(self.root)
        self.assertEqual((self.root / "journal/index.html").read_text(), "authored page")

    def test_manifest_cannot_delete_arbitrary_files(self):
        build(self.root)
        for data in (["../index.html"], ["write.html"], {"path": "index.html"}, ["index.html", "index.html"]):
            with self.subTest(data=data):
                (self.root / "journal/.generated-posts.json").write_text(json.dumps(data))
                before = self.snapshot()
                with self.assertRaises(BuildError):
                    build(self.root)
                self.assertEqual(before, self.snapshot())

    def test_output_symlinks_are_rejected(self):
        build(self.root)
        path = self.root / "journal/index.html"
        path.unlink()
        path.symlink_to(self.root / "index.html")
        before = (self.root / "index.html").read_text()
        with self.assertRaises(BuildError):
            build(self.root)
        self.assertEqual(before, (self.root / "index.html").read_text())

    def test_all_validation_precedes_mutation(self):
        self.post()
        build(self.root)
        self.post(title="Changed title")
        self.post("2026-10-18-invalid", body="```\nunclosed")
        before = self.snapshot()
        with self.assertRaises(BuildError):
            build(self.root)
        self.assertEqual(before, self.snapshot())

    def test_unknown_template_token_and_broken_markers_are_errors(self):
        template = self.root / "scripts/templates/journal-index.html"
        template.write_text("{{POSTS}}{{UNKNOWN}}")
        with self.assertRaisesRegex(BuildError, "Unknown template"):
            build(self.root)
        template.write_text("{{POSTS}}")
        (self.root / "index.html").write_text("<!-- journal:latest:start -->")
        with self.assertRaisesRegex(BuildError, "markers"):
            build(self.root)

    def test_authored_template_like_text_is_not_interpreted(self):
        self.post(title="Literal {{CONTENT}}", body="Keep {{TITLE}} literal.")
        build(self.root)
        self.assertIn("Literal {{CONTENT}}", self.generated())
        self.assertIn("Keep {{TITLE}} literal.", self.generated())

    def test_excessively_nested_blockquotes_fail_with_authoring_error(self):
        with self.assertRaisesRegex(BuildError, "nested too deeply"):
            markdown(">" * 20 + " deeply nested text", self.root)

    def test_list_marker_variants_and_ordered_start(self):
        for marker in ("-", "*", "+"):
            with self.subTest(marker=marker):
                self.assertEqual(markdown(f"{marker} One\n{marker} Two", self.root),
                                 "<ul><li>One</li><li>Two</li></ul>")
        self.assertEqual(markdown("7. Seven\n8. Eight", self.root),
                         '<ol start="7"><li>Seven</li><li>Eight</li></ol>')


if __name__ == "__main__":
    unittest.main()
