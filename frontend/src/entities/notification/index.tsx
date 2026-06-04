import { useNotifications, useToggleNotification, useDeleteNotification } from '@/entities/notification/api'

export function NotificationPage() {
  const { data: notifications, isLoading } = useNotifications()
  const { mutate: toggle } = useToggleNotification()
  const { mutate: remove } = useDeleteNotification()

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-lg font-bold text-gray-900">알림 설정</h1>
        <p className="mt-0.5 text-sm text-gray-500">복약 알림을 관리하세요</p>
      </div>

      {isLoading && (
        <div className="py-10 text-center text-sm text-gray-400">불러오는 중...</div>
      )}

      {!isLoading && notifications?.length === 0 && (
        <div className="rounded-2xl border border-dashed border-gray-200 py-12 text-center">
          <p className="text-sm font-medium text-gray-500">등록된 알림이 없습니다</p>
          <p className="mt-1 text-xs text-gray-400">의료기록 업로드 후 가이드를 생성하면 알림이 자동 등록됩니다</p>
        </div>
      )}

      {!isLoading && notifications && notifications.length > 0 && (
        <ul className="space-y-3">
          {notifications.map((n) => (
            <li
              key={n.id}
              className={`rounded-2xl border bg-white p-4 shadow-sm transition-opacity ${!n.is_active ? 'opacity-50' : ''}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{n.title}</p>
                  <p className="mt-0.5 text-xs text-gray-400">
                    {n.scheduled_time.slice(0, 5)} · {n.type === 'push' ? '앱 푸시' : '이메일'}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/* 활성화 토글 */}
                  <button
                    onClick={() => toggle({ id: n.id, is_active: !n.is_active })}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors
                      ${n.is_active ? 'bg-teal-500' : 'bg-gray-200'}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform
                      ${n.is_active ? 'translate-x-4' : 'translate-x-1'}`}
                    />
                  </button>
                  {/* 삭제 */}
                  <button
                    onClick={() => remove(n.id)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}