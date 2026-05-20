import { Skeleton } from '@/components/ui/skeleton'

interface SkeletonListProps {
  count?: number
  className?: string
}

export function SkeletonList({ count = 3, className = 'h-16' }: SkeletonListProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className={`w-full rounded-xl ${className}`} />
      ))}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm space-y-3">
      <Skeleton className="h-4 w-2/3 rounded" />
      <Skeleton className="h-3 w-full rounded" />
      <Skeleton className="h-3 w-4/5 rounded" />
    </div>
  )
}
