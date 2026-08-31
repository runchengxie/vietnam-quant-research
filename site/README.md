# 日本与越南量化策略适配度看板

这是 `vietnam-quant-research` 的客户展示层，用交互式页面解释日本与越南股票量化策略在市场结构、组合形式、模型、执行摩擦和资金容量上的差异。

## 内容边界

- `site/` 只使用人工整理、可公开发布的静态研究摘要。
- 不读取仓库外数据目录，不依赖商业数据，也不依赖任何私有 Git 仓库。
- 日本部分只描述可以公开披露的工程能力，不发布模型参数、持仓、收益、候选名单或专有因子实现。
- 越南部分继续遵守主仓库的研究门槛。在数据质量和时点语义得到批准前，页面不会宣称已经发现并验证了 alpha。

## 本地开发

```bash
cd site
npm install
npm test -- --run
npm run typecheck
npm run build
npm run dev
```

Vite 使用 `base: './'`，因此 `dist/` 内的资源采用相对路径。同一份构建产物可以部署到 GitHub Pages 的仓库子路径，也可以部署到 Cloudflare Workers Static Assets 的根路径。

## GitHub Pages

`.github/workflows/showcase-pages.yml` 会在拉取请求中执行测试、类型检查和构建。合并到 `main` 后，工作流才会执行 Pages 部署。仓库需要将 GitHub Pages 的发布来源设置为 GitHub Actions。

当前 workflow 使用 GitHub 官方推荐的 `actions/configure-pages@v5`、`actions/upload-pages-artifact@v4` 和 `actions/deploy-pages@v4`。

## Cloudflare Workers Static Assets

`wrangler.jsonc` 将 `./dist` 配置为静态资源目录。当前项目不包含 Worker 脚本，实际发布需要先完成 Cloudflare 账户授权。

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

每条新结论都应明确归入以下类别：

- `FACT`：可以通过来源核验的市场事实。
- `RESEARCH JUDGMENT`：用于比较策略适配度的研究判断。
- `IMPLEMENTATION STATUS`：两个研究项目当前的工程状态。

修改评分时，需要同时更新理由、证据和 `asOf` 日期，避免页面长期展示失去时效的判断。
