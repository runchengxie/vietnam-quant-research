# Japan vs Vietnam Quant Market Fit Showcase

这是 `vietnam-quant-research` 的客户展示层，用交互式页面解释日本与越南股票量化策略在市场结构、组合形式、模型、执行摩擦和资金容量上的差异。

## 边界

- `site/` 只使用人工整理、可公开发布的静态研究摘要。
- 不读取仓库外数据目录，不依赖商业数据，也不依赖任何私有 Git 仓库。
- 日本侧只描述可公开披露的工程能力，不发布模型参数、持仓、收益、候选名单或专有因子实现。
- 越南侧继续遵守主仓库 research gate，在数据质量与 point-in-time 语义未批准前不宣称已验证 alpha。

## 本地开发

```bash
cd site
npm install
npm test -- --run
npm run typecheck
npm run build
npm run dev
```

Vite 使用 `base: './'`，因此 `dist/` 内资源采用相对路径。同一份构建产物可以部署到 GitHub Pages 的 repository subpath，也可以部署到 Cloudflare Workers Static Assets 根路径。

## GitHub Pages

`.github/workflows/showcase-pages.yml` 在 pull request 上执行测试、类型检查和构建；合并到 `main` 后才执行 Pages 部署。仓库需要把 GitHub Pages 的 publishing source 设置为 **GitHub Actions**。

当前 workflow 使用 GitHub 官方推荐的 `actions/configure-pages@v5`、`actions/upload-pages-artifact@v4` 和 `actions/deploy-pages@v4`。

## Cloudflare Workers Static Assets

`wrangler.jsonc` 将 `./dist` 配置为静态资源目录，不包含 Worker script。Cloudflare 当前建议新静态项目使用 Workers Static Assets；实际发布需要授权 Cloudflare 账户。

```bash
cd site
npm install
npm run deploy:cloudflare
```

部署命令会先构建，再执行 `wrangler deploy`。不要把 Cloudflare token 提交到仓库。

## 内容更新

核心比较数据：

- `src/data/marketComparison.ts`
- `src/data/evidence.ts`

所有新结论都应明确归入：

- `FACT`
- `RESEARCH JUDGMENT`
- `IMPLEMENTATION STATUS`

评分变化需要同时更新 rationale、evidence 和 `asOf` 日期，避免一张多年不更新的雷达图逐渐变成金融民俗。
