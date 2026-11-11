import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { agentTasksApi } from '@/api/agentTasks'

export function useTasks() {
  return useQuery({
    queryKey: ['agent-tasks'],
    queryFn: agentTasksApi.list,
  })
}

export function useTaskMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })

  const createMutation = useMutation({ mutationFn: agentTasksApi.create, onSuccess: invalidate })
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof agentTasksApi.update>[1] }) =>
      agentTasksApi.update(id, payload),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({ mutationFn: agentTasksApi.remove, onSuccess: invalidate })

  return { createMutation, updateMutation, deleteMutation }
}
