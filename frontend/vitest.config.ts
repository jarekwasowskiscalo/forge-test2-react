/**
 * Test configuration, deliberately separate from `vite.config.ts`.
 *
 * Vitest reads this file in preference to the Vite one, which keeps the two
 * concerns apart -- but the reason it *has* to be separate is narrower: Vite 8
 * bundles with rolldown while vitest's config types still describe rollup's
 * plugin context, so a single file typed for both makes `tsc` reject every
 * plugin in the array. This file is excluded from `tsc --noEmit` (see
 * tsconfig.json) for that reason and no other; everything under `src/`,
 * including the tests, is still fully type-checked.
 *
 * Two projects, split by extension. `.test.ts` is the pure half -- the
 * contract, the error normaliser, the decimal arithmetic -- and runs on plain
 * node: no jsdom to boot, no setup file, and a DOM assertion in a pure-rules
 * test fails loudly instead of quietly working. `.test.tsx` is the component
 * half: jsdom plus `src/test-setup.ts`, which registers the jest-dom matchers.
 * The extension is already the honest declaration of which half a test is in,
 * so the config reads it rather than inventing a second marker.
 *
 * Coverage is measured and never gated, the same argument the backend makes in
 * spec/design/testing.md: a threshold invites lines written to please a
 * counter, while a number that *falls* is a suite that stopped reaching
 * somewhere. The report lands under .sdd/ (gitignored) because it is a
 * per-machine measurement, not an artefact.
 */
import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  resolve: {
    // The same `@/` alias the application uses, so a test imports a module by
    // the path the module's own neighbours use.
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    globals: true,
    // The reporters live HERE and not on the callers' command lines, and that move
    // is the fix rather than a tidy-up. `includeConsoleOutput` defaults to TRUE --
    // a green run of this suite wrote two `<system-out>` elements -- and this junit
    // is uploaded as a CI artefact, so captured console output was leaving the
    // machine that needed it (Article XI). The option can only be attached where the
    // reporter is NAMED, and `--reporter=junit` on the command line overrides this
    // array wholesale: passing the flag and setting the option here silently kept
    // the default. Measured both ways before it was written down.
    //
    // The CI workflow asserted the opposite of all this in a comment beside its own
    // invocation -- "the junit reporter does not capture console output" -- which is
    // why the upload was considered safe.
    reporters: ['default', ['junit', { includeConsoleOutput: false }]],
    // Named here for the same reason: without it a plain `npm run test` prints the
    // whole junit document to stdout. The path is the one `gate.py` reads
    // (`_FRONTEND_REPORT`) and is gitignored, so every caller gets one report shape
    // in one place and none of them has to remember a flag.
    outputFile: { junit: '../.sdd/reports/frontend.junit.xml' },
    coverage: {
      provider: 'v8',
      include: ['src/**'],
      // The generated type map is not ours to cover; fixtures and the setup
      // file are test plumbing, and counting them flatters the number.
      exclude: ['src/api/schema.d.ts', 'src/**/*.test.*', 'src/test-setup.ts'],
      reporter: ['text', 'json-summary'],
      reportsDirectory: '../.sdd/reports/frontend-coverage',
    },
    projects: [
      {
        extends: true,
        test: {
          name: 'node',
          environment: 'node',
          include: ['src/**/*.test.ts'],
        },
      },
      {
        extends: true,
        test: {
          name: 'dom',
          environment: 'jsdom',
          include: ['src/**/*.test.tsx'],
          setupFiles: ['src/test-setup.ts'],
        },
      },
    ],
  },
})
