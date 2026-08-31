import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = resolve(import.meta.dirname, '..')
const repoRoot = resolve(root, '..')

describe('deployment contract', () => {
  it('uses one relocatable Vite artifact for both hosts', () => {
    const viteConfig = readFileSync(resolve(root, 'vite.config.ts'), 'utf8')
    const wrangler = readFileSync(resolve(root, 'wrangler.jsonc'), 'utf8')
    const workflow = readFileSync(resolve(repoRoot, '.github/workflows/showcase-pages.yml'), 'utf8')
    expect(viteConfig).toContain("base: './'")
    expect(wrangler).toContain('"directory": "./dist"')
    expect(workflow).toContain('path: site/dist')
  })
})
