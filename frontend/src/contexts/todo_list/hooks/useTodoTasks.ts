import { useMutation, useMutationState, useQuery, useQueryClient } from '@tanstack/react-query'
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

import type { TodoTask } from '../lib/todoTask'

export type TodoTaskList = components['schemas']['TodoTaskList']
export type TodoTaskCreate = components['schemas']['TodoTaskCreate']
type TodoTaskUpdate = components['schemas']['TodoTaskUpdate']

/**
 * A tick: the task, and the state the person chose for it -- the one field of
 * `TodoTaskUpdate` a tick sends, required here because a tick always carries it.
 */
export interface TodoTaskMarking {
  id: TodoTask['id']
  done: NonNullable<TodoTaskUpdate['done']>
}

/** A correction: the task, and its new text as the shared rule leaves it -- `text` alone. */
export interface TodoTaskCorrection {
  id: TodoTask['id']
  text: NonNullable<TodoTaskUpdate['text']>
}

/**
 * The one place the screen's copy of the to-do list is read and written.
 *
 * Two promises live here and nowhere else (`spec/design/architecture.md` § The
 * to-do list -- where each rule lives; `spec/design/ui/todo-list.md` § Data):
 *
 * 1. **The cache is written only from the application's answer.** No mutation
 *    below has an `onMutate`, and none writes an answer into the cached list by
 *    hand -- so no row, tick or text is ever on screen before the service has
 *    stored it, and nothing is left there after a failure (`R-10`). An optimistic
 *    tick rolled back on failure is still a tick the person saw made, on the one
 *    list whose whole point is saying what is done.
 * 2. **A change that went through is followed by a fresh read of the whole list**,
 *    which is also when other people's changes arrive (`R-1`). The answer to a
 *    write is one task; the list around it may have moved meanwhile, and only a
 *    read can say how.
 *
 * The fresh read is awaited inside each mutation's own `onSuccess`, so a write is
 * still pending until the list it changed has been read again. That is what lets
 * the screen say "Task added." and show the task in the same moment, and what
 * lets a deleted row leave the list at the moment its question closes, rather than
 * a beat later with the row briefly back as if nothing had happened.
 *
 * Components never call the client themselves (`spec/design/conventions.md`
 * § Frontend); this module is the only place the key shape exists.
 */
export const todoTaskKeys = {
  all: ['todo-tasks'] as const,
  list: () => ['todo-tasks', 'list'] as const,
  /** Every tick in flight carries this key, so the screen can tell which boxes are locked. */
  marking: () => ['todo-tasks', 'marking'] as const,
}

/**
 * The whole list, as the service orders it.
 *
 * No parameters and no pages: the list is read whole and shown in the order it
 * arrives, never sorted again (`BR-11`, `spec/design/api.md` § The to-do list's
 * endpoints).
 */
export function useTodoTasks(): UseQueryResult<TodoTaskList> {
  return useQuery({
    queryKey: todoTaskKeys.list(),
    queryFn: () => unwrap(client.GET('/api/todo-tasks')),
    // Never the 30-second copy `main.tsx` allows by default: whenever the list is
    // opened -- by its address, a reload or the header link "To-do list" -- it
    // shows the tasks exactly as stored at that moment (`CR-2609-823a/R-3`
    // clause 5; `spec/design/ui/system-states.md` § Interactions, `Q-25`). The
    // guestbook keeps the default.
    staleTime: 0,
  })
}

/** Add a task -- the text as the shared rule leaves it -- then read the list again. */
export function useAddTodoTask(): UseMutationResult<TodoTask, Error, TodoTaskCreate> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TodoTaskCreate) => unwrap(client.POST('/api/todo-tasks', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: todoTaskKeys.all }),
  })
}

/**
 * Mark a task done or not done, then read the list again.
 *
 * **It sends `done` alone, carrying the state chosen** -- never "the opposite of
 * what is stored", and never the text written back: two people ticking the same
 * task done both end with it done, and a tick and a correction sent at the same
 * moment are both kept (`BR-09`, `BR-10`, `spec/design/api.md` § `TodoTaskUpdate`).
 *
 * Every tick carries `todoTaskKeys.marking()`, because several can travel at once
 * -- one per row -- and a mutation observer only remembers the last one it sent.
 * `useTodoTasksBeingMarked` reads them all.
 */
export function useMarkTodoTask(): UseMutationResult<TodoTask, Error, TodoTaskMarking> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: todoTaskKeys.marking(),
    mutationFn: ({ id, done }: TodoTaskMarking) =>
      unwrap(
        client.PATCH('/api/todo-tasks/{todo_task_id}', {
          params: { path: { todo_task_id: id } },
          body: { done },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: todoTaskKeys.all }),
  })
}

/**
 * The tasks whose tick is travelling right now -- each one's box is locked on the
 * state that is stored until its own answer comes (`spec/design/ui/todo-list.md`
 * § A task's row, `loading`).
 */
export function useTodoTasksBeingMarked(): string[] {
  return useMutationState({
    filters: { mutationKey: todoTaskKeys.marking(), status: 'pending' },
    select: (mutation) => (mutation.state.variables as TodoTaskMarking).id,
  })
}

/**
 * Correct a task's text, then read the list again.
 *
 * **It sends `text` alone**, so the done mark somebody else may be changing at the
 * same moment is never written back (`BR-10`).
 */
export function useCorrectTodoTask(): UseMutationResult<TodoTask, Error, TodoTaskCorrection> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, text }: TodoTaskCorrection) =>
      unwrap(
        client.PATCH('/api/todo-tasks/{todo_task_id}', {
          params: { path: { todo_task_id: id } },
          body: { text },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: todoTaskKeys.all }),
  })
}

/**
 * Delete a task for good, then read the list again. The answer is a `204` with
 * no body, and it is the success, not a body (`BR-13`).
 */
export function useDeleteTodoTask(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await unwrap(
        client.DELETE('/api/todo-tasks/{todo_task_id}', {
          params: { path: { todo_task_id: id } },
        }),
      )
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: todoTaskKeys.all }),
  })
}
