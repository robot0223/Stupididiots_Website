#!/usr/bin/env python3
"""Build the static member journal using Python's standard library only."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"title", "author", "date", "category", "project", "summary", "cover", "draft"}
CATEGORIES = {"Project update": "project-update", "Experiment": "experiment", "Note": "note"}
PROJECTS = {
    "drop-tap": "Drop Tap",
    "jansen-linkage": "Jansen Linkage",
    "heart-model": "Working Heart Model",
}
SLUG = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MANIFEST = ".generated-posts.json"
INLINE = re.compile(
    r"`([^`\n]+)`|!\[([^\]\n]*)\]\(([^)\s]+)\)|"
    r"\[([^\]\n]+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*|"
    r"(?<!\*)\*([^*\n]+)\*(?!\*)"
)


class BuildError(ValueError):
    """An actionable authoring or output validation error."""


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    author: str
    date: str
    category: str
    project: str
    summary: str
    cover: str
    content: str
    draft: bool


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def local_path(value: str) -> str:
    if (not value or value.startswith("/") or "\\" in value or "%" in value
            or not re.fullmatch(r"[A-Za-z0-9._/-]+", value)
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise BuildError(f"Unsafe local path: {value!r}; use a path from the site root without '..'.")
    return value


def image_path(value: str, root: Path) -> str:
    value = local_path(value)
    if not value.startswith("assets/posts/"):
        raise BuildError("Images must be saved under assets/posts/.")
    path = root / value
    try:
        path.resolve().relative_to((root / "assets/posts").resolve())
    except ValueError as exc:
        raise BuildError(f"Image path leaves assets/posts/: {value}") from exc
    # Do not follow repository symlinks, even when their current target is local.
    if any(part.is_symlink() for part in [path, *path.parents] if part != root.parent):
        raise BuildError(f"Image paths cannot contain symlinks: {value}")
    if not path.is_file():
        raise BuildError(f"Image does not exist: {value}")
    with path.open("rb") as image_file:
        signature = image_file.read(32)
    suffix = path.suffix.lower()
    valid = (
        suffix == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n")
        or suffix in {".jpg", ".jpeg"} and signature.startswith(b"\xff\xd8\xff")
        or suffix == ".gif" and signature[:6] in {b"GIF87a", b"GIF89a"}
        or suffix == ".webp" and signature[:4] == b"RIFF" and signature[8:12] == b"WEBP"
        or suffix == ".avif" and signature[4:8] == b"ftyp"
        and (b"avif" in signature[8:32] or b"avis" in signature[8:32])
    )
    if not valid:
        raise BuildError(f"Image must be a matching PNG, JPEG, GIF, WebP, or AVIF file: {value}")
    return value


def safe_link(value: str) -> str:
    if any(ord(char) < 33 or ord(char) == 127 for char in value) or "\\" in value:
        raise BuildError(f"Unsafe link: {value!r}")
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise BuildError(f"Invalid link: {value!r}") from exc
    if parsed.scheme.lower() in {"http", "https"}:
        if not parsed.netloc or not parsed.hostname:
            raise BuildError(f"Web links need a hostname: {value!r}")
        return value
    if parsed.scheme.lower() == "mailto":
        if not parsed.path or "@" not in parsed.path or parsed.netloc:
            raise BuildError(f"Invalid email link: {value!r}")
        return value
    if parsed.scheme or parsed.netloc or value.startswith("//"):
        raise BuildError(f"Unsupported link scheme: {value!r}; use http, https, or mailto.")
    if parsed.query:
        raise BuildError("Local links do not support query strings.")
    if parsed.fragment and not re.fullmatch(r"[A-Za-z0-9._:-]+", parsed.fragment):
        raise BuildError(f"Unsafe local link fragment: {value!r}")
    if value.startswith("#") and parsed.fragment:
        return value
    path = local_path(parsed.path)
    return "../" + path + ("#" + parsed.fragment if parsed.fragment else "")


def inline(text: str, root: Path, depth: int = 0, linked: bool = False) -> str:
    if depth > 12:
        raise BuildError("Inline formatting is nested too deeply.")
    result: list[str] = []
    offset = 0
    for match in INLINE.finditer(text):
        result.append(escape(text[offset:match.start()]))
        code, alt, image, label, link, bold, italic = match.groups()
        if code is not None:
            result.append(f"<code>{escape(code)}</code>")
        elif image is not None:
            if not alt.strip():
                raise BuildError("Every image needs meaningful alt text inside ![...].")
            src = image_path(image, root)
            result.append(f'<img src="../{escape(src)}" alt="{escape(alt)}" loading="lazy" decoding="async">')
        elif link is not None:
            href = safe_link(link)
            if linked:
                raise BuildError("Links cannot be nested inside other links.")
            result.append(f'<a href="{escape(href)}">{inline(label, root, depth + 1, True)}</a>')
        else:
            tag, content = ("strong", bold) if bold is not None else ("em", italic)
            result.append(f"<{tag}>{inline(content, root, depth + 1, linked)}</{tag}>")
        offset = match.end()
    result.append(escape(text[offset:]))
    return "".join(result)


def markdown(body: str, root: Path, depth: int = 0) -> str:
    """Render a deliberately small Markdown subset; raw HTML is always text."""
    if depth > 12:
        raise BuildError("Blockquotes are nested too deeply.")
    lines = body.splitlines()
    result: list[str] = []
    index = 0
    starter = re.compile(r"^(?:#{1,6}\s|```|>\s?|[-*+]\s+|\d+\.\s+)")
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip()
            if language and not re.fullmatch(r"[A-Za-z0-9_+-]{1,32}", language):
                raise BuildError("Code fence language must be a short name, such as python or javascript.")
            code: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                code.append(lines[index])
                index += 1
            if index == len(lines):
                raise BuildError("Code block is missing its closing ``` fence.")
            css = f' class="language-{escape(language)}"' if language else ""
            result.append(f"<pre><code{css}>{escape(chr(10).join(code))}</code></pre>")
            index += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = max(len(heading[1]), 2)
            result.append(f"<h{level}>{inline(heading[2], root)}</h{level}>")
            index += 1
            continue
        if line.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].startswith(">"):
                quote.append(re.sub(r"^> ?", "", lines[index]))
                index += 1
            result.append(f"<blockquote>{markdown(chr(10).join(quote), root, depth + 1)}</blockquote>")
            continue
        unordered = re.match(r"^[-*+]\s+(.+)$", line)
        ordered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if unordered or ordered:
            tag = "ul" if unordered else "ol"
            pattern = r"^[-*+]\s+(.+)$" if unordered else r"^\d+\.\s+(.+)$"
            start = f' start="{int(ordered[1])}"' if ordered and int(ordered[1]) != 1 else ""
            items = []
            while index < len(lines):
                item = re.match(pattern, lines[index])
                if not item:
                    break
                items.append(f"<li>{inline(item[1], root)}</li>")
                index += 1
            result.append(f"<{tag}{start}>{''.join(items)}</{tag}>")
            continue
        paragraph = [line.strip()]
        index += 1
        while index < len(lines) and lines[index].strip() and not starter.match(lines[index]):
            paragraph.append(lines[index].strip())
            index += 1
        result.append(f"<p>{inline(' '.join(paragraph), root)}</p>")
    return "\n".join(result)


def read_post(path: Path, root: Path) -> Post:
    try:
        if path.is_symlink():
            raise BuildError("Post files cannot be symlinks.")
        text = path.read_text(encoding="utf-8")
        if not SLUG.fullmatch(path.stem) or not re.search(r"[a-z]", path.stem[11:]):
            raise BuildError("Filename must be YYYY-MM-DD-a-meaningful-title.md (lowercase letters, numbers, hyphens).")
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            raise BuildError("Start the file with a --- metadata block.")
        try:
            end = lines.index("---", 1)
        except ValueError as exc:
            raise BuildError("Metadata block is missing its closing --- line.") from exc
        metadata: dict[str, str | bool] = {}
        for line in lines[1:end]:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            field = re.fullmatch(r"([a-z]+):[ \t]*(.*)", line)
            if not field:
                raise BuildError(f"Use one metadata field per line: {line!r}")
            key, value = field.groups()
            value = value.strip()
            if key not in FIELDS:
                raise BuildError(f"Unknown metadata field: {key}")
            if key in metadata:
                raise BuildError(f"Duplicate metadata field: {key}")
            if key == "draft":
                if value not in {"true", "false"}:
                    raise BuildError("draft must be true or false (without quotes).")
                metadata[key] = value == "true"
                continue
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError as exc:
                    raise BuildError(f"Invalid JSON-quoted value for {key}.") from exc
                if not isinstance(value, str):
                    raise BuildError(f"{key} must be a string.")
            if any(ord(char) < 32 for char in value):
                raise BuildError(f"{key} must fit on one line without control characters.")
            metadata[key] = value.strip()
        for key in ("title", "author", "date", "summary"):
            if not metadata.get(key):
                raise BuildError(f"Required metadata is missing: {key}")
        date = str(metadata["date"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise BuildError("date must use YYYY-MM-DD.")
        try:
            dt.date.fromisoformat(date)
        except ValueError as exc:
            raise BuildError("date is not a real calendar date.") from exc
        if path.stem[:10] != date:
            raise BuildError("The filename date must match the metadata date.")
        category = str(metadata.get("category", "Note"))
        if category not in CATEGORIES:
            raise BuildError("category must be Project update, Experiment, or Note.")
        project = str(metadata.get("project", ""))
        project = next((slug for slug, name in PROJECTS.items() if name.casefold() == project.casefold()), project)
        if project and project not in PROJECTS:
            raise BuildError("project must be blank or one of: " + ", ".join(PROJECTS))
        cover = str(metadata.get("cover", ""))
        if cover:
            image_path(cover, root)
        body = "\n".join(lines[end + 1:]).strip()
        if not body:
            raise BuildError("Write some post content below the metadata block.")
        return Post(path.stem, str(metadata["title"]), str(metadata["author"]), date,
                    category, project, str(metadata["summary"]), cover,
                    markdown(body, root), bool(metadata.get("draft", False)))
    except (BuildError, UnicodeError) as exc:
        raise BuildError(f"{path.name}: {exc}") from exc


def cards(posts: list[Post], prefix: str = "", heading: str = "h2", asset_prefix: str = "../") -> str:
    output = []
    for post in posts:
        cover = (f'<img class="journal-cover" src="{asset_prefix}{escape(post.cover)}" '
                 f'alt="" loading="lazy" decoding="async">') if post.cover else ""
        output.append(
            f'<article class="journal-card" data-category="{CATEGORIES[post.category]}">'
            f'<a class="journal-card-link" href="{prefix}{post.slug}.html">{cover}'
            f'<div class="journal-meta"><span class="journal-category">{escape(post.category)}</span>'
            f'<time class="journal-date" datetime="{post.date}">{post.date}</time></div>'
            f'<{heading} class="journal-title">{escape(post.title)}</{heading}>'
            f'<p class="journal-summary">{escape(post.summary)}</p>'
            f'<span class="journal-byline">By {escape(post.author)} <span aria-hidden="true">↗</span></span>'
            '</a></article>'
        )
    return "\n".join(output)


def empty_state(prefix: str = "", project: bool = False) -> str:
    heading = "The next chapter is yours." if not project else "What happens next?"
    text = ("No posts published yet. A rough sketch, a useful discovery, or a project update — it all belongs here."
            if not project else "No updates for this project yet. Members can share the next experiment or milestone.")
    return (f'<div class="journal-empty"><span class="journal-empty-mark" aria-hidden="true">✳</span>'
            f'<h2>{heading}</h2><p>{text}</p>'
            f'<a class="inline-link" href="{prefix}write.html">Write a post <span aria-hidden="true">↗</span></a></div>')


def template(source: str, values: dict[str, str]) -> str:
    # One pass: a literal {{TOKEN}} written by a member is never reinterpreted as template markup.
    unknown = set(re.findall(r"\{\{([A-Z_]+)\}\}", source)) - values.keys()
    if unknown:
        raise BuildError("Unknown template placeholders: " + ", ".join(sorted(unknown)))
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], source)


def owned_name(name: str) -> bool:
    return name in {"index.html", "feed.json"} or (name.endswith(".html") and bool(SLUG.fullmatch(name[:-5])))


def read_manifest(directory: Path) -> set[str]:
    path = directory / MANIFEST
    if path.is_symlink():
        raise BuildError("The generated-file manifest cannot be a symlink.")
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise BuildError(f"Invalid {MANIFEST}; refusing cleanup.") from exc
    if (not isinstance(data, list) or any(not isinstance(name, str) or not owned_name(name) for name in data)
            or len(data) != len(set(data))):
        raise BuildError(f"Unsafe {MANIFEST}; expected a list of generated journal filenames.")
    return set(data)


def replace_marker(source: str, key: str, replacement: str) -> str:
    start, end = f"<!-- journal:{key}:start -->", f"<!-- journal:{key}:end -->"
    if start not in source and end not in source:
        return source
    if source.count(start) != 1 or source.count(end) != 1 or source.index(start) > source.index(end):
        raise BuildError(f"Expected exactly one ordered pair of journal:{key} markers.")
    before, remainder = source.split(start, 1)
    _, after = remainder.split(end, 1)
    return before + start + "\n" + replacement + "\n" + end + after


def atomic_write(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        # Static HTML and JSON are public assets, including files left at 0600
        # by an older build. Repair permissions without rewriting unchanged data.
        path.chmod(0o644)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                                         prefix=".post-build-", delete=False) as output:
            output.write(content)
            temporary = Path(output.name)
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build(root: Path = ROOT, check: bool = False) -> int:
    root = root.resolve()
    posts_dir, journal_dir = root / "posts", root / "journal"
    if posts_dir.is_symlink() or journal_dir.is_symlink():
        raise BuildError("posts/ and journal/ must be real directories, not symlinks.")
    if not posts_dir.is_dir():
        raise BuildError("posts/ directory does not exist.")
    posts = [read_post(path, root) for path in sorted(posts_dir.glob("*.md"))
             if path.name not in {"README.md", "_template.md"}]
    posts = sorted((post for post in posts if not post.draft), key=lambda post: (post.date, post.slug), reverse=True)
    templates = root / "scripts/templates"
    try:
        index_template = (templates / "journal-index.html").read_text(encoding="utf-8")
        post_template = (templates / "journal-post.html").read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise BuildError("Both scripts/templates/journal-index.html and journal-post.html are required.") from exc
    if "{{POSTS}}" not in index_template or "{{CONTENT}}" not in post_template:
        raise BuildError("Journal templates must contain {{POSTS}} and {{CONTENT}}, respectively.")
    generated: dict[str, str] = {
        "index.html": template(index_template, {"POSTS": cards(posts) or empty_state(), "POST_COUNT": str(len(posts))}),
    }
    for post in posts:
        cover = (f'<figure class="post-cover"><img src="../{escape(post.cover)}" alt="" '
                 'decoding="async"></figure>') if post.cover else ""
        values = {"TITLE": escape(post.title), "AUTHOR": escape(post.author), "DATE": post.date,
                  "CATEGORY": escape(post.category), "PROJECT": escape(PROJECTS.get(post.project, "Independent note")),
                  "SUMMARY": escape(post.summary), "CONTENT": post.content, "COVER": cover,
                  "POST_SLUG": post.slug}
        generated[post.slug + ".html"] = template(post_template, values)
    feed = [{"slug": post.slug, "url": post.slug + ".html", "title": post.title,
             "author": post.author, "date": post.date, "category": post.category,
             "project": post.project, "summary": post.summary,
             "cover": "../" + post.cover if post.cover else ""} for post in posts]
    generated["feed.json"] = json.dumps(feed, ensure_ascii=False, indent=2) + "\n"
    owned = read_manifest(journal_dir)
    for name in owned | generated.keys():
        path = journal_dir / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise BuildError(f"Generated output must be a regular file: journal/{name}")
        if path.exists() and name in generated and name not in owned:
            raise BuildError(f"Refusing to overwrite untracked journal/{name}; move it aside before the first build.")
    page_updates: dict[Path, str] = {}
    homepage = root / "index.html"
    if homepage.is_symlink():
        raise BuildError("Pages containing journal markers cannot be symlinks.")
    if homepage.exists():
        page_updates[homepage] = replace_marker(homepage.read_text(encoding="utf-8"), "latest",
                                               cards(posts[:3], "journal/", "h3", "") or empty_state("journal/"))
    for slug in PROJECTS:
        page = root / "projects" / (slug + ".html")
        if page.is_symlink() or page.parent.is_symlink():
            raise BuildError("Pages containing journal markers cannot be symlinks.")
        if page.exists():
            selected = [post for post in posts if post.project == slug]
            page_updates[page] = replace_marker(page.read_text(encoding="utf-8"), "project:" + slug,
                                               cards(selected, "../journal/", "h3") or empty_state("../journal/", True))
    if not check:
        journal_dir.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            atomic_write(journal_dir / name, content)
        for path, content in page_updates.items():
            atomic_write(path, content)
        for name in owned - generated.keys():
            (journal_dir / name).unlink(missing_ok=True)
        atomic_write(journal_dir / MANIFEST, json.dumps(sorted(generated), indent=2) + "\n")
    return len(posts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate all inputs without writing files.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Site directory (defaults to this repository).")
    args = parser.parse_args()
    try:
        count = build(args.root, args.check)
    except (BuildError, OSError) as exc:
        print(f"Post build failed: {exc}", file=sys.stderr)
        return 1
    print(f"{'Validated' if args.check else 'Built'} {count} published post{'s' if count != 1 else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
