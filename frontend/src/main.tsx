import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'

import { ApiError } from '@/api/problem'
import { ToastProvider } from '@/components/ui/Toast'
import { router } from '@/router'

import './index.css'

/**
 * All server state goes through TanStack Query -- nothing here hand-rolls a
 * fetch-in-useEffect.
 *
 * `retry` is a function rather than a number because retrying a 4xx is
 * pointless: a 404 entry id will still be missing, and a 422 will still fail
 * validation. Only 5xx and transport failures (status 0) are worth a second
 * attempt. **Mutations never retry at all**: a POST that timed out may have
 * been carried out anyway, and a blind second attempt is how one entry becomes
 * two.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry(failureCount, error) {
        if (failureCount >= 2) return false
        if (error instanceof ApiError) return error.status === 0 || error.status >= 500
        return true
      },
      // Refetching on every window focus is noise for a list this small and
      // this slow-moving; each mutation invalidates the key it affected, which
      // is the refresh that actually corresponds to something happening.
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
    mutations: { retry: false },
  },
})

const container = document.getElementById('root')
if (!container) throw new Error('#root is missing from index.html')

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </QueryClientProvider>
  </StrictMode>,
)
