import { Badge, Text } from '../../../design-system'
import { useTodoStatsQuery } from '../hooks/useTodoStatsQuery'

export function TodoStatsSummary() {
  const { data, isError } = useTodoStatsQuery()
  if (isError) return null
  if (!data)
    return (
      <Text muted size="small" role="status">
        Loading statistics…
      </Text>
    )
  if (data.total === 0) return null
  return (
    <section aria-label="Task statistics" className="row compact">
      <Badge variant="info">{data.active} active</Badge>
      <Badge variant="success">{data.completed} completed</Badge>
      {data.overdue > 0 && (
        <Badge variant="warning">{data.overdue} overdue</Badge>
      )}
      <Text as="span" muted size="small">
        {Math.round((data.completed / data.total) * 100)}% done
      </Text>
    </section>
  )
}
