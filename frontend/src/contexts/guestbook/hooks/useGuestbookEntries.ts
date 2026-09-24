import { useEffect } from 'react'
import {
  keepPreviousData,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import type { UseInfiniteQueryResult, UseMutationResult } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import type { components } from '@/api/schema'
import { firstPageRequest, nextPageRequest } from '@/contexts/guestbook/lib/entryPaging'
import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

export type GuestbookEntryCreate = components['schemas']['GuestbookEntryCreate']
export type GuestbookEntryUpdate = components['schemas']['GuestbookEntryUpdate']
export type GuestbookEntryPage = components['schemas']['GuestbookEntryPage']

/**
 * Which end of the book to read from. The two words are the contract's, not
 * this module's -- taken from the generated schema so a third order added to
 * the API cannot be missed here.
 */
export type GuestbookEntrySort = components['schemas']['GuestbookEntrySort']

/**
 * What a read of the book asks for -- **the question, and nothing about how
 * much of the answer is on screen**.
 *
 * `limit` used to be a third member and that was the defect: a page size is not
 * part of a question's identity, so asking for a bigger piece looked to the
 * cache like somebody had asked something else. Worse, once the size hit the
 * contract's ceiling it stopped changing, the key stopped moving with it, and
 * pressing "Load more" refetched nothing at all.
 */
export interface GuestbookEntryQuery {
  /** Narrow to entries containing this. Empty means the whole book. */
  search: string
  sort: GuestbookEntrySort
}

/** How much of the answer the address says is on screen. Never part of the key. */
export interface GuestbookEntryPaging {
  /** How many entries the address asks to see. */
  shown: number
  /** How many one press of "Load more" adds. */
  step: number
}

/**
 * The query keys for this resource, in one object.
 *
 * Every mutation below invalidates `all`, so a key written by hand at a call
 * site is a cache that silently stops refreshing. Components never call
 * `client.GET` directly (spec/design/conventions.md § Frontend) -- that rule is
 * what makes this the only place the key shape exists.
 *
 * **`list` takes the question**, so two different searches are two different
 * cache entries rather than one entry that flips between two answers. Without
 * that, going back to a phrase already typed would show the previous phrase's
 * results until the refetch landed.
 */
export const guestbookEntryKeys = {
  all: ['guestbook-entries'] as const,
  list: (query: GuestbookEntryQuery) => ['guestbook-entries', 'list', query] as const,
}

/**
 * One piece of the book, **together with the question it answers**.
 *
 * The second half is the whole point. `keepPreviousData` hands back the
 * previous key's pages while the new ones travel, so a screen reading the
 * phrase from the address and the counts from here would put a new phrase in
 * front of old numbers -- and say "2 matches for “Zzz”" over two entries that
 * match nothing of the sort. The question rides with its own answer.
 *
 * `asked` is the current render's `query`, which is the key the fetch runs
 * under, so the attribution is right by construction rather than by care.
 */
interface AnsweredPage extends GuestbookEntryPage {
  asked: GuestbookEntryQuery
}

/** Everything the screen needs about the list, flattened out of the pieces. */
export interface GuestbookEntryList {
  /** Every entry loaded so far, in the server's order (`BR-04`). */
  entries: GuestbookEntry[]
  /** How many match the question these entries answer. */
  total: number
  /** How many the book holds (`BR-05`). */
  totalAll: number
  /** The question `entries`, `total` and `totalAll` are the answer to. */
  answering: GuestbookEntryQuery
}

/**
 * The book, read a piece at a time, up to as much as the address asks for.
 *
 * `keepPreviousData` is what makes the search box usable: without it every
 * settled phrase replaces the list with the loading state, so the screen
 * flickers empty between searches and the reader loses their place. With it the
 * previous answer stays on screen -- and the caller is told so through
 * `isPlaceholderData`, which is how the screen labels it rather than passing it
 * off as the answer to the newer question.
 *
 * **The address is the source of truth for how much is loaded.** `shown` says
 * how many entries belong on screen; the effect below asks for pieces until
 * that many are there or the book runs out. A press of "Load more" therefore
 * writes the address and nothing else -- one direction of flow, and a reload of
 * the same address restores the same range.
 */
export function useGuestbookEntries(
  query: GuestbookEntryQuery,
  { shown, step }: GuestbookEntryPaging,
): UseInfiniteQueryResult<GuestbookEntryList> {
  const result = useInfiniteQuery({
    queryKey: guestbookEntryKeys.list(query),
    queryFn: async ({ pageParam }): Promise<AnsweredPage> => {
      const page = await unwrap(
        client.GET('/api/guestbook-entries', {
          params: {
            query: {
              // Absent rather than empty: `q=` and no `q` at all mean the same
              // thing to the server, and sending the empty one would put a
              // pointless parameter in every request the screen makes.
              q: query.search === '' ? undefined : query.search,
              sort: query.sort,
              limit: pageParam.limit,
              // Absent at its default for the same reason, and present the
              // moment there is a second piece -- which is the parameter the
              // screen was not using while the endpoint had it all along.
              offset: pageParam.offset === 0 ? undefined : pageParam.offset,
            },
          },
        }),
      )
      return { ...page, asked: query }
    },
    initialPageParam: firstPageRequest(shown),
    getNextPageParam: (lastPage, allPages) =>
      nextPageRequest({
        loaded: allPages.reduce((count, page) => count + page.items.length, 0),
        shown,
        total: lastPage.total,
        step,
      }),
    placeholderData: keepPreviousData,
    select: (data) => {
      const last = data.pages.at(-1)
      return {
        entries: data.pages.flatMap((page) => page.items),
        total: last?.total ?? 0,
        totalAll: last?.total_all ?? 0,
        // The first piece's question, because every piece of one key answers
        // the same one and the first is the one that is always there.
        answering: data.pages[0]?.asked ?? query,
      }
    },
  })

  const loaded = result.data?.entries.length ?? 0
  const { isPlaceholderData, isFetching, hasNextPage, fetchNextPage } = result

  /**
   * Fill the screen up to what the address asks for.
   *
   * One piece per pass, re-entered when that piece lands, and refused while the
   * data on screen belongs to another question -- fetching a second piece of an
   * answer whose first piece has not arrived would put the pieces out of order.
   * It terminates on the book rather than on `shown`: `hasNextPage` goes false
   * at `total`, so an address asking for more entries than exist stops at the
   * last one.
   */
  useEffect(() => {
    if (isPlaceholderData || isFetching || !hasNextPage) return
    if (loaded >= shown) return
    void fetchNextPage()
  }, [isPlaceholderData, isFetching, hasNextPage, fetchNextPage, loaded, shown])

  return result
}

/** Add an entry, then refetch the list. */
export function useCreateGuestbookEntry(): UseMutationResult<
  components['schemas']['GuestbookEntryRead'],
  Error,
  GuestbookEntryCreate
> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: GuestbookEntryCreate) =>
      unwrap(client.POST('/api/guestbook-entries', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: guestbookEntryKeys.all }),
  })
}

/**
 * Change an entry, then refetch the list.
 *
 * The list is refetched rather than patched in place because the server owns
 * `updated_at`, the ordering and both counts: writing the server's answer back
 * into the cached page by hand would work until the day an edit moves the entry
 * out of the current search.
 *
 * **Invalidation is also what keeps the pieces honest.** Refetching an infinite
 * query replays every piece from the first, recomputing each offset over the
 * order as it now stands -- so an entry added or removed while several pieces
 * are on screen shifts the boundaries rather than duplicating an entry across
 * them or dropping one between them.
 */
export function useUpdateGuestbookEntry(): UseMutationResult<
  components['schemas']['GuestbookEntryRead'],
  Error,
  { id: string; body: GuestbookEntryUpdate }
> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: GuestbookEntryUpdate }) =>
      unwrap(
        client.PATCH('/api/guestbook-entries/{entry_id}', {
          params: { path: { entry_id: id } },
          body,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: guestbookEntryKeys.all }),
  })
}

/** Remove an entry permanently, then refetch the list. */
export function useDeleteGuestbookEntry(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await unwrap(
        client.DELETE('/api/guestbook-entries/{entry_id}', {
          params: { path: { entry_id: id } },
        }),
      )
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: guestbookEntryKeys.all }),
  })
}
