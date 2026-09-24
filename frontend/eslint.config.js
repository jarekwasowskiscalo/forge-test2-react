import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/**
 * ESLint for the SPA.
 *
 * `tsc --noEmit` already runs in `npm run build` and catches every type error,
 * so this config deliberately does **not** repeat type checking. What it adds
 * is the class of defect a type checker cannot see:
 *
 * - `react-hooks` -- a missing dependency or a conditional hook is a stale
 *   render or a crash, and both type-check perfectly. This is the reason the
 *   linter is here at all.
 * - floating promises, unsafe `any` flow, unused values -- the ones that
 *   silently accumulate in a codebase 50 people copy from.
 *
 * There is no Prettier. The repo is already consistently formatted, and
 * introducing a formatter now would rewrite every file in one commit and bury
 * the review history of code that is otherwise heavily annotated. Formatting
 * is enforced by review here; adding a second, differently-opinionated
 * formatter is a decision for a quiet week, not a side effect of an audit.
 */
export default tseslint.config(
  {
    ignores: [
      'dist',
      'node_modules',
      // Generated. Its producer is reviewed; its output is not edited.
      'src/api/schema.d.ts',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        // `projectService` picks the nearest tsconfig per file. The two config
        // files below are outside `tsconfig.json`'s `include`, so they are
        // named explicitly rather than left to fail.
        projectService: {
          allowDefaultProject: ['vitest.config.ts'],
        },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Vite's fast refresh only works when a module exports components alone.
      // `allowConstantExport` covers the `const X = ...` a few files export
      // beside their component.
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // The codebase uses `void promise` deliberately at fire-and-forget call
      // sites (query invalidation, `void refetch()`); that is the escape hatch,
      // not a reason to switch the rule off.
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  {
    // Config files run in Node, not in the browser.
    files: ['*.config.{js,ts}'],
    languageOptions: { globals: globals.node },
  },
  {
    // Plain JS build tooling: no TypeScript project covers it, so the
    // type-aware rules have no types to reason about and every `process.argv`
    // reads as `any`. Syntax and the untyped rules still apply.
    files: ['**/*.{js,mjs,cjs}'],
    ...tseslint.configs.disableTypeChecked,
    languageOptions: {
      ...tseslint.configs.disableTypeChecked.languageOptions,
      globals: globals.node,
    },
  },
)
