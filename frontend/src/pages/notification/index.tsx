import { useState } from 'react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { EmptyState } from '@/shared/ui/EmptyState'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useNotifications, useUpdateNotification, useDeleteNotification } from '@/entities/notification/api'
import type { NotificationItem } from '@/entities/notification/model'

function formatTime(time: string): string {
  const [hourStr, minuteStr] = time.split(':')
  const hour = parseInt(hourStr, 10)
  const ampm = hour < 12 ? '오전' : '오후'
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
  return `${ampm} ${String(displayHour).padStart(2, '0')}:${minuteStr}`
}

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: () => void; disabled?: boolean }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:cursor-not-allowed ${
        checked ? 'bg-[#1D9E75]' : 'bg-gray-200'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition duration-200 ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  )
}

function NotificationCard({ item }: { item: NotificationItem }) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: update, isPending: isToggling } = useUpdateNotification()
  const { mutate: remove, isPending: isDeleting } = useDeleteNotification()

  return (
    <div
      className={`rounded-2xl bg-white border border-gray-100 shadow-sm p-4 flex items-center gap-4 transition-opacity ${
        item.is_active ? '' : 'opacity-55'
      }`}
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{item.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">{formatTime(item.scheduled_time)}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
            {item.type === 'push' ? '푸시' : '이메일'}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <Toggle
          checked={item.is_active}
          disabled={isToggling}
          onChange={() => update({ id: item.id, is_active: !item.is_active })}
        />
        <button
          onClick={() => setDeleteOpen(true)}
          disabled={isDeleting}
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-50 transition-colors disabled:opacity-40"
          aria-label="알림 삭제"
        >
          <TrashIcon />
        </button>
      </div>
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="알림을 삭제하시겠습니까?"
        description="삭제된 알림은 복구할 수 없습니다."
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => remove(item.id)}
      />
    </div>
  )
}

function NotificationSkeleton() {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4 flex items-center gap-4">
      <div className="flex-1 flex flex-col gap-2">
        <Skeleton className="h-4 w-40 rounded" />
        <Skeleton className="h-3 w-24 rounded" />
      </div>
      <Skeleton className="h-6 w-11 rounded-full" />
      <Skeleton className="h-7 w-7 rounded-lg" />
    </div>
  )
}

export function NotificationPage() {
  const { data: notifications, isLoading, isError, error } = useNotifications()

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="알림 설정"
        description="복약 시간에 맞춰 알림을 받아보세요."
      />

      <div className="flex flex-col gap-3">
        {isLoading ? (
          <>
            <NotificationSkeleton />
            <NotificationSkeleton />
            <NotificationSkeleton />
          </>
        ) : isError ? (
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm">
            <EmptyState
              icon={<BellIcon />}
              title="알림을 불러오지 못했습니다"
              description={error instanceof Error ? error.message : '잠시 후 다시 시도해주세요.'}
            />
          </div>
        ) : !notifications?.length ? (
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm">
            <EmptyState
              icon={<BellIcon />}
              title="등록된 알림이 없습니다"
              description="의약품 등록 후 알림을 추가할 수 있습니다."
            />
          </div>
        ) : (
          notifications.map((item) => <NotificationCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  )
}

function BellIcon() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  )
}
