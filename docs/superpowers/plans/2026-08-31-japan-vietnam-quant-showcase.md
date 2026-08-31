# Japan vs Vietnam Quant Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained interactive client-facing site under `site/` that explains Japan vs Vietnam equity-quant strategy fit, preserves the Vietnam research boundary, and can deploy from one build artifact to GitHub Pages and Cloudflare Workers Static Assets.

**Architecture:** The site is a static Vite + React + TypeScript application. All public comparison claims live in typed static data with explicit `fact`, `judgment`, or `implementation` evidence categories; view components consume those records without reading private repositories or research runtime data. Deployment uses a relative Vite asset base so the same `dist/` artifact works at a GitHub Pages repository subpath and at a Cloudflare Worker root URL.

**Tech Stack:** Node.js 22, Vite, React, TypeScript, Vitest, Testing Library, Apache ECharts, Cloudflare Wrangler.

**Spec:** `docs/superpowers/specs/2026-08-31-japan-vietnam-quant-showcase-design.md`

## Global Constraints

- Keep `site/` independently movable to a future `quant-market-showcase` repository.
- Do not import, clone, fetch, or expose private `guan-japanese-nira` code or outputs from the public site build.
- Treat all 1–5 ratings as `RESEARCH JUDGMENT`, never as performance forecasts.
- Do not present the Vietnam repository as having validated alpha while its research gate remains incomplete.
- Use official/public market sources for facts; expose source title, URL, and as-of date in the evidence UI.
- Build must work with a relative Vite base (`./`) so one `dist/` deploys to GitHub Pages and Cloudflare Workers Static Assets.
- GitHub Pages deployment runs only from `main`; PRs run build/test but do not deploy.
- Cloudflare configuration is checked into `site/wrangler.jsonc`; actual Cloudflare deployment requires a connected/authorized account and is not coupled to PR CI.
- No backend, database, authentication, realtime market data, online backtest, or private strategy metrics in this phase.

---

### Task 1: Site scaffold, typed data, and behavioral tests

**Files:**
- Create: `site/package.json`
- Create: `site/package-lock.json`
- Create: `site/index.html`
- Create: `site/tsconfig.json`
- Create: `site/tsconfig.node.json`
- Create: `site/vite.config.ts`
- Create: `site/src/data/types.ts`
- Create: `site/src/data/marketComparison.ts`
- Create: `site/src/data/evidence.ts`
- Create: `site/src/data/marketComparison.test.ts`
- Create: `site/src/test/setup.ts`

**Interfaces:**
- Produces `StrategyFit`, `Evidence`, `MarketProfile`, `CapitalProfile`, and typed data arrays consumed by all later components.
- Produces `strategyFits`, `marketProfiles`, `capitalProfiles`, and `evidence` exports.

- [ ] **Step 1: Write failing data-contract tests** asserting all strategy scores are 1–5, every strategy references existing evidence IDs, each evidence row has a valid category, and Japan private implementation evidence contains no private URLs or strategy performance.
- [ ] **Step 2: Run `npm test -- --run src/data/marketComparison.test.ts` and verify RED** because the data modules do not yet exist.
- [ ] **Step 3: Implement the minimal typed data model and comparison dataset** with the ten approved strategy rows, radar dimensions, capital profiles, and evidence records.
- [ ] **Step 4: Run the data-contract test and verify GREEN.**
- [ ] **Step 5: Run `npm run typecheck`.**

### Task 2: Core client narrative and interactive strategy fit

**Files:**
- Create: `site/src/main.tsx`
- Create: `site/src/App.tsx`
- Create: `site/src/components/HeroComparison.tsx`
- Create: `site/src/components/StrategyHeatmap.tsx`
- Create: `site/src/components/EvidenceDrawer.tsx`
- Create: `site/src/components/StrategyHeatmap.test.tsx`
- Create: `site/src/styles/app.css`

**Interfaces:**
- `StrategyHeatmap` consumes `StrategyFit[]` and `Evidence[]` and exposes category filter buttons plus accessible score cells.
- `EvidenceDrawer` consumes a selected `StrategyFit | null` and associated evidence records.

- [ ] **Step 1: Write failing component tests** for category filtering, accessible score labels, and opening evidence detail from a strategy row.
- [ ] **Step 2: Run the focused tests and verify RED.**
- [ ] **Step 3: Implement Hero, heatmap, evidence drawer, and top-level layout.**
- [ ] **Step 4: Run focused tests and verify GREEN.**
- [ ] **Step 5: Run `npm run typecheck` and `npm run build`.**

### Task 3: Market-structure visuals, alpha-to-PnL explanation, and strategy architecture

**Files:**
- Create: `site/src/components/MarketRadar.tsx`
- Create: `site/src/components/AlphaToPnL.tsx`
- Create: `site/src/components/ArchitectureCompare.tsx`
- Create: `site/src/components/MarketVisuals.test.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles/app.css`

**Interfaces:**
- `MarketRadar` consumes `MarketProfile[]` and renders ECharts radar plus a textual fallback/legend.
- `AlphaToPnL` renders qualitative implementation-haircut stages without invented bps.
- `ArchitectureCompare` renders the approved Japan and Vietnam research pipelines as semantic ordered flows.

- [ ] **Step 1: Write failing tests** asserting radar dimension text exists, the PnL section does not contain invented `bps`/percent performance claims, and both architecture pipelines expose all required stages.
- [ ] **Step 2: Run focused tests and verify RED.**
- [ ] **Step 3: Implement the three visual sections with responsive layouts and accessible textual equivalents.**
- [ ] **Step 4: Run focused tests and verify GREEN.**
- [ ] **Step 5: Run `npm run build`.**

### Task 4: Capital profile explorer, project maturity, methodology, and source UX

**Files:**
- Create: `site/src/components/CapitalProfile.tsx`
- Create: `site/src/components/MaturityCompare.tsx`
- Create: `site/src/components/Methodology.tsx`
- Create: `site/src/components/ClientExplainers.test.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles/app.css`

**Interfaces:**
- `CapitalProfile` consumes `CapitalProfile[]` and switches among `small`, `medium`, and `institutional` views.
- `MaturityCompare` displays engineering maturity only and explicitly disclaims performance interpretation.
- `Methodology` lists fact/judgment/implementation definitions and evidence sources with as-of dates.

- [ ] **Step 1: Write failing tests** for capital-profile switching, Vietnam research-gate wording, Japan private-strategy boundary wording, and source links.
- [ ] **Step 2: Run focused tests and verify RED.**
- [ ] **Step 3: Implement the explorer, maturity comparison, and methodology/evidence footer.**
- [ ] **Step 4: Run focused tests and verify GREEN.**
- [ ] **Step 5: Run the full `npm test -- --run`, `npm run typecheck`, and `npm run build`.**

### Task 5: Static deployment and repository integration

**Files:**
- Create: `site/wrangler.jsonc`
- Create: `.github/workflows/showcase-pages.yml`
- Modify: `.gitignore`
- Modify: `README.md`
- Create: `site/README.md`

**Interfaces:**
- Vite emits `site/dist/` with relative asset paths.
- GitHub Actions builds `site/`, uploads `site/dist`, and deploys only on pushes to `main`; pull requests run validation only.
- Wrangler serves `./dist` as static assets with no Worker script.

- [ ] **Step 1: Add a failing build/deployment contract test or shell assertion** that checks `vite.config.ts` uses `base: './'`, GitHub Pages workflow uploads `site/dist`, and Wrangler points to `./dist`.
- [ ] **Step 2: Verify RED before deployment files exist.**
- [ ] **Step 3: Add deployment configuration and documentation.** Use `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, `actions/deploy-pages@v4`, Node 22, and a current `wrangler.jsonc` static-assets configuration.
- [ ] **Step 4: Verify GREEN and run `npm ci && npm test -- --run && npm run typecheck && npm run build`.**
- [ ] **Step 5: Verify the built `dist/index.html` references relative assets and contains no private GitHub repository URL.**

### Task 6: Final repository verification and PR

**Files:**
- Review all files changed since `main`.

**Interfaces:**
- Produces a reviewable PR from `codex/japan-vietnam-showcase` into `main`.

- [ ] **Step 1: Run Python baseline tests** from repository root to ensure the site addition did not regress the research package.
- [ ] **Step 2: Run frontend full validation** with `npm ci`, tests, typecheck, and production build.
- [ ] **Step 3: Run whitespace/diff checks** and inspect the generated source map/build output for accidental private data references; do not commit `site/dist` or `site/node_modules`.
- [ ] **Step 4: Review the branch diff against the approved spec** for scope, research claims, and information boundaries.
- [ ] **Step 5: Create a PR** summarizing scope, tests, deployment behavior, evidence/research boundaries, and the remaining Cloudflare authorization step.
