# Deploying OFFSIDE to Vercel

The web app is a static Next.js site that reads frozen incident fixtures — no server, no
database, no runtime model. Vercel serves it from its edge CDN at zero cost.

## One-time setup

1. **Import the repo** at [vercel.com/new](https://vercel.com/new) → select
   `vighriday/offside-june-2026`.
2. **Set the Root Directory to `web`.** This is the only non-default setting and it is
   essential — the Next.js app lives in `web/`, not the repo root. Vercel will then find
   `web/package.json` and `web/vercel.json`.
3. Leave the rest as detected:
   - Framework Preset: **Next.js** (auto-detected; also pinned in `vercel.json`)
   - Build Command: `npm run build` (resolves to `next build --webpack`)
   - Install Command: `npm install`
   - Output Directory: `.next` (Next.js default)
4. **Deploy.** No environment variables are needed — the app reads only committed
   fixtures.

## Why `--webpack`

The build runs with `next build --webpack` (pinned in `package.json`). IBM Carbon's SCSS
needs `sassOptions.includePaths`, which the Turbopack builder does not yet honour. Webpack
respects it, so the build is reliable on every platform. Vercel builds on Linux, where
this is stable.

## What deploys

`web/fixtures/<incident>.json` is bundled at build time and read by the server component.
Until the Colab bake runs, the app shows `hand-of-god-1986.sample.json` (a schema-valid
placeholder, flagged in the UI). Once the real fixture lands in `web/fixtures/`, the next
deploy serves it automatically — no code change.

## After the bake

The bake writes `web/fixtures/hand-of-god-1986.json` and commits it. Pushing that commit
triggers a Vercel redeploy that serves the real, audited bundle in place of the sample.
