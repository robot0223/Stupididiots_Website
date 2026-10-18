/* A local Markdown helper: export here, commit through GitHub. No server writes. */
(() => {
  'use strict';
  const form = document.querySelector('#post-form');
  if (!form) return;
  const storageKey = 'stupididiots-journal-draft-v1';
  const limits = { title: 100, author: 80, date: 10, category: 30, project: 30, summary: 240, body: 20000 };
  const projectNames = { 'drop-tap': 'Drop Tap', 'jansen-linkage': 'Jansen Linkage', 'heart-model': 'Working Heart Model' };
  const categories = ['Project update', 'Experiment', 'Note'];
  const fields = Object.fromEntries(Object.keys(limits).map((key) => [key, form.elements.namedItem(key)]));
  const get = (selector) => document.querySelector(selector);
  const draftStatus = get('#draft-status');
  const exportStatus = get('#export-status');
  function localToday() {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }
  const today = localToday();
  fields.date.value = today;
  let storageAvailable = true;
  let saveTimer;
  let draftVersion = 0;

  function readValues() {
    return Object.fromEntries(Object.keys(limits).map((key) => [key, fields[key].value.slice(0, limits[key])]));
  }

  function safeLink(value) {
    if (!/^https?:\/\//i.test(value) || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) && url.hostname ? url.href : null;
    } catch { return null; }
  }

  function localPath(value) {
    return Boolean(value && /^[A-Za-z0-9._/-]+$/.test(value) && !value.startsWith('/') && value.split('/').every((part) => part && part !== '.' && part !== '..'));
  }

  function validPublishingLink(value) {
    if (/[\u0000-\u0020\u007f\\]/.test(value)) return false;
    if (/^https?:/i.test(value)) return Boolean(safeLink(value));
    if (/^mailto:/i.test(value)) {
      const address = value.slice(7).split(/[?#]/)[0];
      return Boolean(address && address.includes('@') && !address.startsWith('//'));
    }
    if (/^[A-Za-z][A-Za-z0-9+.-]*:/.test(value) || value.startsWith('//') || value.includes('?')) return false;
    const pieces = value.split('#');
    if (pieces.length > 2 || (pieces.length === 2 && !/^[A-Za-z0-9._:-]+$/.test(pieces[1]))) return false;
    return (pieces[0] === '' && pieces.length === 2) || localPath(pieces[0]);
  }

  function contentError(body) {
    let inCodeBlock = false;
    const textLines = [];
    for (const line of body.replace(/\r\n?/g, '\n').split('\n')) {
      if (inCodeBlock) {
        if (line.trim() === '```') inCodeBlock = false;
        continue;
      }
      if (line.startsWith('```')) {
        const language = line.slice(3).trim();
        if (language && !/^[A-Za-z0-9_+-]{1,32}$/.test(language)) return 'Use a short language name after a code fence, such as javascript.';
        inCodeBlock = true;
      } else { textLines.push(line); }
    }
    if (inCodeBlock) return 'Close your code block with a line containing three backticks (```).';
    const inlinePattern = /`([^`\n]+)`|!\[([^\]\n]*)\]\(([^)\s]+)\)|\[([^\]\n]+)\]\(([^)\s]+)\)/g;
    for (const match of textLines.join('\n').matchAll(inlinePattern)) {
      if (match[1] !== undefined) continue;
      if (match[3] !== undefined) {
        const path = match[3];
        if (!match[2].trim() || !localPath(path) || !path.startsWith('assets/posts/') || !/\.(png|jpe?g|gif|webp|avif)$/i.test(path)) {
          return 'Images need descriptive alt text and a PNG, JPEG, GIF, WebP, or AVIF file under assets/posts/. See the image instructions below.';
        }
      } else if (!validPublishingLink(match[5])) {
        return 'One of your Markdown links is invalid. Use a complete https:// or http:// address, a mailto: address, or a site path without ../ or a query string.';
      }
    }
    return '';
  }

  function appendInline(parent, source, depth = 0) {
    if (depth > 4) { parent.append(document.createTextNode(source)); return; }
    const pattern = /(\*\*([^*\n]+)\*\*|\*([^*\n]+)\*|`([^`\n]+)`|\[([^\]\n]+)\]\(([^)\s]+)\))/g;
    let end = 0;
    for (const match of source.matchAll(pattern)) {
      parent.append(document.createTextNode(source.slice(end, match.index)));
      if (match[2]) {
        const strong = document.createElement('strong'); appendInline(strong, match[2], depth + 1); parent.append(strong);
      } else if (match[3]) {
        const em = document.createElement('em'); appendInline(em, match[3], depth + 1); parent.append(em);
      } else if (match[4]) {
        const code = document.createElement('code'); code.textContent = match[4]; parent.append(code);
      } else {
        const href = safeLink(match[6]);
        if (href) {
          const link = document.createElement('a'); link.href = href; link.target = '_blank'; link.rel = 'noopener noreferrer'; appendInline(link, match[5], depth + 1); parent.append(link);
        } else { parent.append(document.createTextNode(match[0])); }
      }
      end = match.index + match[0].length;
    }
    parent.append(document.createTextNode(source.slice(end)));
  }

  function renderMarkdown(source, target) {
    target.replaceChildren();
    const lines = source.replace(/\r\n?/g, '\n').split('\n');
    const isBlockStart = (line) => /^(#{1,6}\s|\s*```|\s*>\s?|\s*[-*+]\s|\s*\d+\.\s)/.test(line);
    let index = 0;
    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) { index += 1; continue; }
      if (/^\s*```/.test(line)) {
        const codeLines = []; index += 1;
        while (index < lines.length && !/^\s*```/.test(lines[index])) codeLines.push(lines[index++]);
        if (index < lines.length) index += 1;
        const pre = document.createElement('pre'); const code = document.createElement('code'); code.textContent = codeLines.join('\n'); pre.append(code); target.append(pre); continue;
      }
      const heading = line.match(/^(#{1,6})\s+(.+)$/);
      if (heading) { const node = document.createElement(`h${Math.max(2, heading[1].length)}`); appendInline(node, heading[2]); target.append(node); index += 1; continue; }
      if (/^\s*>\s?/.test(line)) {
        const quoteLines = [];
        while (index < lines.length && /^\s*>\s?/.test(lines[index])) quoteLines.push(lines[index++].replace(/^\s*>\s?/, ''));
        const node = document.createElement('blockquote'); appendInline(node, quoteLines.join(' ')); target.append(node); continue;
      }
      const listMatch = line.match(/^\s*([-*+]|\d+\.)\s+(.+)$/);
      if (listMatch) {
        const ordered = /^\d/.test(listMatch[1]);
        const list = document.createElement(ordered ? 'ol' : 'ul');
        if (ordered) list.start = Number.parseInt(listMatch[1], 10);
        const listPattern = ordered ? /^\s*\d+\.\s+(.+)$/ : /^\s*[-*+]\s+(.+)$/;
        while (index < lines.length) {
          const item = lines[index].match(listPattern); if (!item) break;
          const li = document.createElement('li'); appendInline(li, item[1]); list.append(li); index += 1;
        }
        target.append(list); continue;
      }
      const paragraph = [line]; index += 1;
      while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) paragraph.push(lines[index++]);
      const node = document.createElement('p'); appendInline(node, paragraph.join(' ')); target.append(node);
    }
  }

  function filename(values) {
    let slug = values.title.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 64).replace(/-$/g, '') || 'new-post';
    if (!/[a-z]/.test(slug)) slug = `post-${slug}`;
    return `posts/${/^\d{4}-\d{2}-\d{2}$/.test(values.date) ? values.date : today}-${slug}.md`;
  }

  function markdown(values) {
    const metadata = ['title', 'author', 'date', 'category', 'project', 'summary'].map((key) => `${key}: ${JSON.stringify(values[key].replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, ' ').trim())}`).join('\n');
    return `---\n${metadata}\n---\n\n${values.body.trim()}\n`;
  }

  function updatePreview() {
    const values = readValues();
    get('#preview-title').textContent = values.title.trim() || 'Your next small discovery.';
    get('#preview-author').textContent = values.author.trim() || 'Your name';
    get('#preview-avatar').textContent = values.author.trim() ? Array.from(values.author.trim())[0].toUpperCase() : '✳';
    get('#preview-category').textContent = values.category;
    const project = get('#preview-project'); project.textContent = projectNames[values.project] || ''; project.hidden = !project.textContent;
    const previewDate = get('#preview-date');
    const parsedDate = values.date ? new Date(`${values.date}T12:00:00`) : null;
    previewDate.textContent = parsedDate && !Number.isNaN(parsedDate.getTime()) ? parsedDate.toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Choose a date';
    previewDate.dateTime = values.date;
    const summary = get('#preview-summary'); summary.textContent = values.summary.trim() || 'The short version of your story will appear here.'; summary.classList.toggle('is-placeholder', !values.summary.trim());
    const body = get('#preview-body');
    if (values.body.trim()) renderMarkdown(values.body, body);
    else { const placeholder = document.createElement('p'); placeholder.className = 'is-placeholder'; placeholder.textContent = 'This is your space for the details. Start writing on the left, and watch your post take shape.'; body.replaceChildren(placeholder); }
    get('#summary-count').textContent = `${values.summary.length} / 240`;
    const wordCount = values.body.trim() ? values.body.trim().split(/\s+/).length : 0;
    get('#body-count').textContent = `${wordCount.toLocaleString()} ${wordCount === 1 ? 'word' : 'words'}`;
    const path = filename(values);
    get('#post-filename').textContent = path;
    get('#github-create').href = `https://github.com/robot0223/Stupididiots_Website/new/main?filename=${encodeURIComponent(path)}`;
    if (!get('#copy-fallback').hidden) get('#markdown-output').value = markdown(values);
  }

  function saveDraft() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(readValues()));
      draftStatus.textContent = 'Saved on this device';
      storageAvailable = true;
    } catch {
      storageAvailable = false;
      draftStatus.textContent = 'Draft saving unavailable — copy or download';
    }
  }

  function validate() {
    for (const key of ['title', 'author', 'summary', 'body']) fields[key].setCustomValidity(fields[key].value.trim() ? '' : 'Please fill in this field.');
    const rawDate = fields.date.value;
    const parsed = new Date(`${rawDate}T12:00:00`);
    const validDate = /^\d{4}-\d{2}-\d{2}$/.test(rawDate) && !Number.isNaN(parsed.getTime()) && parsed.getFullYear() > 0 && parsed.getFullYear() === Number(rawDate.slice(0, 4)) && parsed.getMonth() + 1 === Number(rawDate.slice(5, 7)) && parsed.getDate() === Number(rawDate.slice(8, 10));
    fields.date.setCustomValidity(validDate ? '' : 'Choose a valid date.');
    const error = contentError(fields.body.value);
    if (error) fields.body.setCustomValidity(error);
    return form.reportValidity();
  }

  try {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const draft = JSON.parse(stored);
      if (draft && typeof draft === 'object' && !Array.isArray(draft)) {
        for (const key of Object.keys(limits)) {
          if (typeof draft[key] === 'string') fields[key].value = draft[key].slice(0, limits[key]);
        }
        if (!categories.includes(fields.category.value)) fields.category.value = 'Project update';
        if (!(fields.project.value in projectNames)) fields.project.value = '';
        if (!fields.date.value) fields.date.value = today;
        draftStatus.textContent = 'Draft restored from this device';
      }
    }
  } catch {
    storageAvailable = false;
    draftStatus.textContent = 'Draft saving unavailable — copy or download';
  }

  form.addEventListener('submit', (event) => event.preventDefault());
  form.addEventListener('input', (event) => {
    draftVersion += 1;
    if (typeof event.target.setCustomValidity === 'function') event.target.setCustomValidity('');
    updatePreview(); exportStatus.textContent = '';
    clearTimeout(saveTimer);
    if (storageAvailable) draftStatus.textContent = 'Saving on this device…';
    saveTimer = setTimeout(saveDraft, 400);
  });
  form.addEventListener('change', updatePreview);
  window.addEventListener('pagehide', () => { clearTimeout(saveTimer); saveDraft(); });

  const newDraft = get('#new-draft');
  newDraft.hidden = false;
  newDraft.addEventListener('click', () => {
    const hasContent = ['title', 'summary', 'body'].some((key) => fields[key].value.trim());
    if (hasContent && !window.confirm('Start a new draft? This will clear the current draft on this device. Copy or download it first if you want to keep it.')) return;
    clearTimeout(saveTimer);
    draftVersion += 1;
    for (const key of Object.keys(limits)) {
      if (key !== 'author') fields[key].value = '';
      fields[key].setCustomValidity('');
    }
    fields.date.value = localToday();
    fields.category.value = 'Project update';
    get('#copy-fallback').hidden = true;
    get('#markdown-output').value = '';
    exportStatus.textContent = '';
    try {
      localStorage.removeItem(storageKey);
      storageAvailable = true;
      draftStatus.textContent = 'New draft ready';
    } catch {
      storageAvailable = false;
      draftStatus.textContent = 'New draft ready; saved draft could not be cleared';
    }
    updatePreview();
    fields.title.focus();
  });

  get('#copy-markdown').addEventListener('click', async () => {
    if (!validate()) return;
    const text = markdown(readValues());
    const copiedVersion = draftVersion;
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('Clipboard not available');
      await navigator.clipboard.writeText(text);
      if (copiedVersion !== draftVersion) return;
      get('#copy-fallback').hidden = true;
      exportStatus.textContent = 'Markdown copied. Open GitHub, paste it into the new file, and commit.';
    } catch {
      if (copiedVersion !== draftVersion) return;
      const output = get('#markdown-output'); output.value = text; get('#copy-fallback').hidden = false; output.focus(); output.select();
      exportStatus.textContent = 'Copy the selected Markdown below, then paste it into the new file on GitHub.';
    }
  });
  get('#download-markdown').addEventListener('click', () => {
    if (!validate()) return;
    const values = readValues();
    const url = URL.createObjectURL(new Blob([markdown(values)], { type: 'text/markdown;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename(values).split('/').pop(); anchor.hidden = true; document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    exportStatus.textContent = 'Download prepared. Add the .md file to the repository’s posts folder and commit it.';
  });
  get('#github-create').addEventListener('click', (event) => {
    if (!validate()) event.preventDefault();
    else exportStatus.textContent = 'Paste your copied Markdown into the GitHub editor, then commit the new file.';
  });
  updatePreview();
})();
