import { useState } from 'react'
import { useMonthlyCalendar, useUpdateEventStatus } from '@/entities/calendar/api'
import type { CalendarEvent } from '@/entities/calendar/model'

const DAYS = ['일', '월', '화', '수', '목', '금', '토']

const STATUS_STYLE: Record<string, string> = {
  TAKEN: 'bg-teal-500',
  MISSED: 'bg-red-400',
  PENDING: 'bg-gray-300',
}

const STATUS_LABEL: Record<string, string> = {
  TAKEN: '복용 완료',
  MISSED: '미복용',
  PENDING: '예정',
}

export function CalendarPage() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const { data, isLoading } = useMonthlyCalendar(year, month)
  const { mutate: updateStatus } = useUpdateEventStatus()

  // 날짜별 이벤트 맵
  const eventMap = new Map<string, CalendarEvent[]>()
  data?.items.forEach((e) => {
    const list = eventMap.get(e.event_date) ?? []
    list.push(e)
    eventMap.set(e.event_date, list)
  })

  // 달력 그리드 생성
  const firstDay = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()
  const cells: (number | null)[] = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]

  function prevMonth() {
    if (month === 1) { setYear(y => y - 1); setMonth(12) }
    else setMonth(m => m - 1)
    setSelectedDate(null)
  }

  function nextMonth() {
    if (month === 12) { setYear(y => y + 1); setMonth(1) }
    else setMonth(m => m + 1)
    setSelectedDate(null)
  }

  function dateStr(day: number) {
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  }

  const selectedEvents = selectedDate ? (eventMap.get(selectedDate) ?? []) : []

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-lg font-bold text-gray-900">복약 캘린더</h1>
        <p className="mt-0.5 text-sm text-gray-500">날짜를 선택해 복약 현황을 확인하세요</p>
      </div>

      {/* 월 네비게이션 */}
      <div className="flex items-center justify-between">
        <button onClick={prevMonth} className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50">‹</button>
        <span className="text-base font-semibold text-gray-800">{year}년 {month}월</span>
        <button onClick={nextMonth} className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50">›</button>
      </div>

      {/* 달력 */}
      <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        {/* 요일 헤더 */}
        <div className="grid grid-cols-7 mb-2">
          {DAYS.map((d, i) => (
            <div key={d} className={`text-center text-xs font-medium py-1 ${i === 0 ? 'text-red-400' : i === 6 ? 'text-blue-400' : 'text-gray-400'}`}>{d}</div>
          ))}
        </div>

        {/* 날짜 셀 */}
        {isLoading ? (
          <div className="py-10 text-center text-sm text-gray-400">불러오는 중...</div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, idx) => {
              if (!day) return <div key={idx} />
              const ds = dateStr(day)
              const events = eventMap.get(ds) ?? []
              const isToday = ds === today.toISOString().slice(0, 10)
              const isSelected = ds === selectedDate
              return (
                <button
                  key={ds}
                  onClick={() => setSelectedDate(ds === selectedDate ? null : ds)}
                  className={`flex flex-col items-center rounded-xl py-1.5 transition-colors
                    ${isSelected ? 'bg-teal-50 ring-1 ring-teal-400' : 'hover:bg-gray-50'}
                  `}
                >
                  <span className={`text-sm w-7 h-7 flex items-center justify-center rounded-full
                    ${isToday ? 'bg-teal-600 text-white font-bold' : 'text-gray-700'}
                  `}>{day}</span>
                  {events.length > 0 && (
                    <div className="flex gap-0.5 mt-0.5 flex-wrap justify-center">
                      {events.slice(0, 3).map((e) => (
                        <span key={e.id} className={`w-1.5 h-1.5 rounded-full ${STATUS_STYLE[e.status]}`} />
                      ))}
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* 선택한 날짜 이벤트 */}
      {selectedDate && (
        <section className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm space-y-3">
          <h2 className="text-sm font-semibold text-gray-700">{selectedDate} 복약 일정</h2>
          {selectedEvents.length === 0 ? (
            <p className="text-xs text-gray-400">이 날의 복약 일정이 없습니다.</p>
          ) : (
            <ul className="space-y-2">
              {selectedEvents.map((e) => (
                <li key={e.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{e.scheduled_time.slice(0, 5)}</p>
                    {e.note && <p className="text-xs text-gray-400">{e.note}</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full text-white ${STATUS_STYLE[e.status]}`}>
                      {STATUS_LABEL[e.status]}
                    </span>
                    {e.status === 'PENDING' && (
                      <button
                        onClick={() => updateStatus({ id: e.id, status: 'TAKEN' })}
                        className="text-xs text-teal-600 font-medium hover:underline"
                      >
                        완료
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {/* 범례 */}
      <div className="flex gap-4 text-xs text-gray-500">
        {Object.entries(STATUS_LABEL).map(([k, v]) => (
          <div key={k} className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${STATUS_STYLE[k]}`} />
            {v}
          </div>
        ))}
      </div>
    </div>
  )
}