# DevTools Suite — File Diff + PDF Editor

> Fully **client-side** browser utility: compare file diffs with syntax highlighting **and** convert, annotate & download PDFs — no server, no upload, no data ever leaves your browser.

---

## Live Demo

Deploy to GitHub Pages (see [DEPLOY.md](DEPLOY.md)):
```
https://YOUR-USERNAME.github.io/devtools-suite/diffview.html
```

---

## Features

### File Diff Module
- Side-by-side and unified diff views
- Syntax highlighting for 60+ languages (JS, Python, Go, Rust, SQL, YAML …)
- Char-level inline diff — highlights exact characters that changed within a line
- Line numbers, change navigation (Alt+Up / Alt+Down)
- Similarity score with animated progress bar
- Ignore-whitespace toggle
- Copy diff to clipboard (git-unified format)
- CRLF/LF/CR normalisation — Windows vs Unix files compare cleanly
- Dark / light theme persisted in localStorage

### PDF Tools Module
- Convert to PDF client-side: .docx .xlsx .pptx .txt .html .jpg .png .gif .webp
- In-browser editor: text annotations, highlights, freehand draw, eraser
- Insert images + signature pad (touch + mouse)
- Page reorder, rotate, delete
- Undo stack (Ctrl+Z)
- Export bakes all edits into a real downloadable PDF

### Keyboard Shortcuts (PDF)
`T` text · `H` highlight · `D` draw · `E` eraser · `I` image · `S` signature · `Esc` select · `Ctrl+Z` undo · Arrow keys page navigation

---

## Usage

Open `diffview.html` in any modern browser — no install, no build step required.

```bash
# Serve locally
npx serve .
# then open http://localhost:3000/diffview.html
```

---

## File Structure

```
devtools-suite/
├── diffview.html   # entire app — single self-contained file (~107 KB)
├── README.md
├── DEPLOY.md       # deployment guide (GitHub Pages, Netlify, Vercel …)
└── .gitignore
```

---

## Privacy

Zero data transmission. All processing happens entirely in your browser using:
PDF.js · pdf-lib · jsPDF · mammoth.js · SheetJS · JSZip · html2canvas · highlight.js

---

## Browser Support

Chrome 90+ · Firefox 88+ · Safari 14+ · Edge 90+

---

## License

MIT — free to use, modify and deploy.
