# DiffView — Git Setup & Deployment Guide

## Prerequisites

- [Git](https://git-scm.com/downloads) installed on your machine
- A [GitHub](https://github.com) account (free)

---

## Step 1 — Create a local Git repository

Open a terminal, navigate to the folder that contains `diffview.html`, then run:

```bash
# Move into the project folder
cd path/to/your/diffview-folder

# Initialise a new git repo
git init

# Stage all files
git add diffview.html .gitignore

# First commit
git commit -m "Initial commit: DiffView file comparison tool"
```

---

## Step 2 — Create a GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: **diffview** (or any name you like)
3. Keep it **Public** (required for free GitHub Pages)
4. Leave "Add README" **unchecked** (we already have files)
5. Click **Create repository**

GitHub will show you a page with setup commands. Use the **"push an existing repository"** block:

```bash
git remote add origin https://github.com/YOUR_USERNAME/diffview.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Deployment Options

### Option A — GitHub Pages (free, zero config)

GitHub Pages serves any static HTML directly from your repo — no server needed.

```bash
# In your repo folder, enable GitHub Pages via the gh-pages branch
git checkout -b gh-pages
git push origin gh-pages
```

Then in your GitHub repo:

1. Go to **Settings → Pages**
2. Under **Source**, select branch **`gh-pages`** and folder **`/ (root)`**
3. Click **Save**

Your site will be live at:
```
https://YOUR_USERNAME.github.io/diffview/
```

> **Tip:** Every `git push origin gh-pages` deploys an update automatically.

---

### Option B — Netlify (free, instant HTTPS, drag-and-drop)

1. Go to [app.netlify.com](https://app.netlify.com) and sign in (GitHub login works)
2. Click **"Add new site" → "Import an existing project"**
3. Choose **GitHub** and select your `diffview` repository
4. Build settings:
   - Build command: *(leave blank)*
   - Publish directory: `.` (dot = root)
5. Click **Deploy site**

Your site is live in ~30 seconds at a URL like `https://diffview-abc123.netlify.app`.

**Custom domain:** Netlify → Site settings → Domain management → Add custom domain.

**Auto-deploy:** Every `git push` to `main` triggers a new deploy automatically.

---

### Option C — Vercel (free, global CDN, instant deploys)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from your project folder
cd path/to/diffview-folder
vercel

# Follow the prompts:
#   Set up and deploy? Y
#   Which scope? (your username)
#   Link to existing project? N
#   Project name: diffview
#   In which directory is your code? ./
#   Override settings? N
```

Your site goes live immediately. Subsequent deploys:

```bash
vercel --prod
```

**Or connect to GitHub** at [vercel.com/new](https://vercel.com/new) for auto-deploys on every push.

---

### Option D — Cloudflare Pages (free, unlimited bandwidth)

1. Go to [pages.cloudflare.com](https://pages.cloudflare.com)
2. **Create a project → Connect to Git → GitHub**
3. Select your `diffview` repository
4. Build settings:
   - Framework preset: **None**
   - Build command: *(leave blank)*
   - Build output directory: `/`
5. Click **Save and Deploy**

Live at `https://diffview.pages.dev` (or your custom domain).

---

## Making Updates

All platforms above auto-deploy when you push to GitHub. The workflow is:

```bash
# Edit diffview.html in any text editor, then:
git add diffview.html
git commit -m "describe what you changed"
git push origin main
```

---

## Verifying the live app

Once deployed, visit your URL and confirm:

- [ ] File upload zones accept drag-and-drop
- [ ] Side-by-side and unified views both render
- [ ] Theme toggle (dark/light) works
- [ ] Stats bar shows addition/deletion counts
- [ ] Keyboard shortcut Alt+↓ / Alt+↑ jumps between changes
- [ ] "Copy Diff" button copies to clipboard

---

## Recommended: Pin exact hljs version

The app loads highlight.js from the CDN. To avoid any future CDN changes affecting your app, you can copy `diffview.html`, download the CDN file, and serve it locally alongside your HTML. Or use the version-pinned URL already in the file (`/11.9.0/`).

