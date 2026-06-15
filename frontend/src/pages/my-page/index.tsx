import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuthStore } from '@/app/providers/auth-store'
import {
  useCurrentUser,
  useUpdateProfile,
  useAllergies,
  useAddAllergy,
  useDeleteAllergy,
  useConditions,
  useAddCondition,
  useDeleteCondition,
} from '@/entities/user/api'
import type { AllergyItem, ConditionItem } from '@/entities/user/model'

const SEVERITY_CONFIG = {
  mild:     { label: '경미',   dot: 'bg-emerald-400' },
  moderate: { label: '중등도', dot: 'bg-amber-400' },
  severe:   { label: '심각',   dot: 'bg-red-500' },
}

function getSeverity(s: string) {
  return SEVERITY_CONFIG[s as keyof typeof SEVERITY_CONFIG] ?? { label: s, dot: 'bg-gray-300' }
}

// ── 프로필 편집 폼 ────────────────────────────────────────────
function ProfileEditForm({ initialName, initialGender, initialBirthDate, onClose }: {
  initialName?: string
  initialGender?: string | null
  initialBirthDate?: string | null
  onClose: () => void
}) {
  const [name, setName] = useState(initialName ?? '')
  const [gender, setGender] = useState(initialGender ?? '')
  const [birthDate, setBirthDate] = useState(initialBirthDate ?? '')
  const { mutate: update, isPending } = useUpdateProfile()

  function handleSave() {
    const body: { name?: string; gender?: string; birth_date?: string } = {}
    if (name.trim()) body.name = name.trim()
    if (gender) body.gender = gender
    if (birthDate) body.birth_date = birthDate
    update(body, { onSuccess: onClose })
  }

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-6 flex flex-col items-center gap-5">
      <div className="h-16 w-16 rounded-full flex items-center justify-center text-2xl font-bold text-white select-none"
        style={{ background: 'linear-gradient(135deg, #1D9E75 0%, #0F6E56 100%)' }}>
        {name?.[0]?.toUpperCase() ?? '?'}
      </div>

      <div className="w-full flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-400">이름</label>
        <input
          type="text" value={name} onChange={(e) => setName(e.target.value)}
          placeholder="이름을 입력하세요" autoFocus
          className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10"
        />
      </div>

      <div className="w-full flex flex-col gap-2">
        <label className="text-xs font-medium text-gray-400">성별</label>
        <div className="flex gap-2">
          {(['MALE', 'FEMALE'] as const).map((g) => (
            <button key={g} type="button" onClick={() => setGender(g)}
              className={`px-5 py-2 rounded-full text-sm font-medium border transition-colors ${
                gender === g
                  ? 'border-[#1D9E75] bg-[#1D9E75] text-white'
                  : 'border-gray-200 text-gray-500 bg-white hover:bg-gray-50'
              }`}>
              {g === 'MALE' ? '남성' : '여성'}
            </button>
          ))}
        </div>
      </div>

      <div className="w-full flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-400">생년월일</label>
        <input
          type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)}
          className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10"
        />
      </div>

      <div className="flex gap-2 w-full pt-1">
        <button onClick={onClose}
          className="flex-1 py-2.5 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
          취소
        </button>
        <button onClick={handleSave} disabled={isPending || !name.trim()}
          className="flex-1 py-2.5 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
          style={{ background: '#1D9E75' }}>
          {isPending ? '저장 중...' : '저장'}
        </button>
      </div>
    </div>
  )
}

// ── 건강 지표 편집 폼 ──────────────────────────────────────────
function HealthEditForm({ initialHeight, initialWeight, onClose }: {
  initialHeight?: number | null
  initialWeight?: number | null
  onClose: () => void
}) {
  const [height, setHeight] = useState(initialHeight?.toString() ?? '')
  const [weight, setWeight] = useState(initialWeight?.toString() ?? '')
  const { mutate: update, isPending } = useUpdateProfile()

  function handleSave() {
    const body: { height_cm?: number; weight_kg?: number } = {}
    const h = parseFloat(height)
    const w = parseFloat(weight)
    if (!isNaN(h)) body.height_cm = h
    if (!isNaN(w)) body.weight_kg = w
    update(body, { onSuccess: onClose })
  }

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5 flex flex-col gap-4">
      <p className="text-sm font-semibold text-gray-700">신체 정보 편집</p>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500">신장 (cm)</label>
          <input type="number" step="any" value={height} onChange={(e) => setHeight(e.target.value)}
            placeholder="예: 170" className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500">체중 (kg)</label>
          <input type="number" step="any" value={weight} onChange={(e) => setWeight(e.target.value)}
            placeholder="예: 65" className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10" />
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">취소</button>
        <button onClick={handleSave} disabled={isPending}
          className="px-4 py-2 rounded-xl text-sm text-white font-medium disabled:opacity-50 transition-colors"
          style={{ background: '#1D9E75' }}>
          {isPending ? '저장 중...' : '저장'}
        </button>
      </div>
    </div>
  )
}

// ── 태그 입력 폼 ──────────────────────────────────────────────
function TagAddForm({ placeholder, onAdd, onCancel, isPending }: {
  placeholder: string
  onAdd: (name: string, severity: string) => void
  onCancel: () => void
  isPending: boolean
}) {
  const [name, setName] = useState('')
  const [severity, setSeverity] = useState('mild')

  return (
    <div className="flex items-center gap-2 mt-1">
      <select value={severity} onChange={(e) => setSeverity(e.target.value)}
        className="rounded-xl border border-gray-200 px-2 py-1.5 text-xs text-gray-600 focus:outline-none focus:border-[#1D9E75] shrink-0">
        <option value="mild">경미</option>
        <option value="moderate">중등도</option>
        <option value="severe">심각</option>
      </select>
      <input
        type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder={placeholder}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing && name.trim()) onAdd(name.trim(), severity) }}
        autoFocus
        className="flex-1 min-w-0 rounded-xl border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10"
      />
      <button onClick={() => { if (name.trim()) onAdd(name.trim(), severity) }}
        disabled={!name.trim() || isPending}
        className="shrink-0 px-3 py-1.5 rounded-xl text-xs text-white font-medium disabled:opacity-40"
        style={{ background: '#1D9E75' }}>추가</button>
      <button onClick={onCancel} className="shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
        <XIcon />
      </button>
    </div>
  )
}

// ── 태그 섹션 (알러지 / 기저질환 공용) ──────────────────────
function TagSection({
  title, icon, items, isLoading, showForm, setShowForm,
  onAdd, onDelete, isPending, placeholder, emptyText, deleteTarget, setDeleteTarget, deleteLabel,
}: {
  title: string; icon: React.ReactNode; items: (AllergyItem | ConditionItem)[]
  isLoading: boolean; showForm: boolean; setShowForm: (v: boolean) => void
  onAdd: (name: string, severity: string) => void; onDelete: (id: string) => void
  isPending: boolean; placeholder: string; emptyText: string
  deleteTarget: string | null; setDeleteTarget: (v: string | null) => void; deleteLabel: string
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-gray-400">{icon}</span>
          <p className="text-sm font-semibold text-gray-700">{title}</p>
        </div>
        {!showForm && (
          <button onClick={() => setShowForm(true)}
            className="text-xs font-medium px-3 py-1 rounded-lg border border-dashed border-gray-300 text-gray-400 hover:border-[#1D9E75] hover:text-[#1D9E75] transition-colors">
            + 추가
          </button>
        )}
      </div>
      {isLoading ? (
        <div className="flex gap-2">
          <Skeleton className="h-7 w-20 rounded-full" />
          <Skeleton className="h-7 w-24 rounded-full" />
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {items.length === 0 && !showForm && (
            <p className="text-xs text-gray-400 py-1">{emptyText}</p>
          )}
          {items.map((item) => {
            const name = 'allergen_name' in item ? item.allergen_name : item.condition_name
            const { label, dot } = getSeverity(item.severity)
            return (
              <span key={item.id}
                className="inline-flex items-center gap-2 pl-2.5 pr-2 py-1 rounded-full text-xs font-medium border border-gray-200 bg-white text-gray-700">
                <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                <span>{name}</span>
                <span className="text-gray-400 text-[10px]">{label}</span>
                <button onClick={() => setDeleteTarget(item.id)}
                  className="opacity-40 hover:opacity-80 transition-opacity">
                  <XSmallIcon />
                </button>
              </span>
            )
          })}
        </div>
      )}
      {showForm && (
        <TagAddForm placeholder={placeholder} isPending={isPending}
          onAdd={(name, severity) => onAdd(name, severity)}
          onCancel={() => setShowForm(false)} />
      )}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title={deleteLabel}
        confirmLabel="삭제" variant="danger"
        onConfirm={() => { if (deleteTarget) onDelete(deleteTarget) }}
      />
    </div>
  )
}

function AllergySection() {
  const { data: allergies = [], isLoading } = useAllergies()
  const { mutate: add, isPending } = useAddAllergy()
  const { mutate: remove } = useDeleteAllergy()
  const [showForm, setShowForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const target = allergies.find(a => a.id === deleteTarget)

  return (
    <TagSection
      title="알러지" icon={<AlertIcon />} items={allergies} isLoading={isLoading}
      showForm={showForm} setShowForm={setShowForm}
      onAdd={(name, severity) => add({ allergen_name: name, severity }, { onSuccess: () => setShowForm(false) })}
      onDelete={(id) => remove(id)} isPending={isPending}
      placeholder="알러지 물질 입력 (예: 페니실린)" emptyText="등록된 알러지가 없습니다."
      deleteTarget={deleteTarget} setDeleteTarget={setDeleteTarget}
      deleteLabel={`'${target?.allergen_name}' 알러지를 삭제하시겠습니까?`}
    />
  )
}

function ConditionSection() {
  const { data: conditions = [], isLoading } = useConditions()
  const { mutate: add, isPending } = useAddCondition()
  const { mutate: remove } = useDeleteCondition()
  const [showForm, setShowForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const target = conditions.find(c => c.id === deleteTarget)

  return (
    <TagSection
      title="기저질환" icon={<HeartIcon />} items={conditions} isLoading={isLoading}
      showForm={showForm} setShowForm={setShowForm}
      onAdd={(name, severity) => add({ condition_name: name, severity }, { onSuccess: () => setShowForm(false) })}
      onDelete={(id) => remove(id)} isPending={isPending}
      placeholder="질환명 입력 (예: 고혈압)" emptyText="등록된 기저질환이 없습니다."
      deleteTarget={deleteTarget} setDeleteTarget={setDeleteTarget}
      deleteLabel={`'${target?.condition_name}'을 삭제하시겠습니까?`}
    />
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────
export function MyPage() {
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const { data: user, isLoading } = useCurrentUser()
  const [editingProfile, setEditingProfile] = useState(false)
  const [editingHealth, setEditingHealth] = useState(false)
  const [logoutOpen, setLogoutOpen] = useState(false)

  const genderLabel = user?.gender === 'MALE' ? '남성' : user?.gender === 'FEMALE' ? '여성' : null

  function handleLogout() {
    logout()
    navigate('/auth/login', { replace: true })
  }

  return (
    <div className="flex flex-col min-h-full gap-5 pb-6 max-w-3xl mx-auto w-full">

      {/* ── 프로필 헤더 ── */}
      {editingProfile ? (
        <ProfileEditForm
          initialName={user?.name}
          initialGender={user?.gender}
          initialBirthDate={user?.birth_date}
          onClose={() => setEditingProfile(false)}
        />
      ) : (
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-6 flex items-center gap-4">
          {isLoading ? (
            <>
              <Skeleton className="h-14 w-14 rounded-full shrink-0" />
              <div className="flex flex-col gap-2 flex-1">
                <Skeleton className="h-5 w-28 rounded" />
                <Skeleton className="h-4 w-44 rounded" />
              </div>
            </>
          ) : (
            <>
              <div className="h-14 w-14 shrink-0 rounded-full flex items-center justify-center text-xl font-bold text-white select-none"
                style={{ background: 'linear-gradient(135deg, #1D9E75 0%, #0F6E56 100%)' }}>
                {user?.name?.[0] ?? '?'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base font-bold text-gray-800 truncate">{user?.name ?? '—'}</p>
                <p className="text-sm text-gray-400 truncate mt-0.5">{user?.email}</p>
                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                  {genderLabel && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium">{genderLabel}</span>
                  )}
                  {user?.birth_date && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium">{user.birth_date}</span>
                  )}
                </div>
              </div>
              <button onClick={() => setEditingProfile(true)}
                className="shrink-0 text-xs font-medium px-3 py-1 rounded-lg text-[#1D9E75] border border-[#1D9E75]/30 hover:bg-[#1D9E75]/5 transition-colors">
                편집
              </button>
            </>
          )}
        </div>
      )}

      {/* ── 신체 정보 ── */}
      {editingHealth ? (
        <HealthEditForm
          initialHeight={user?.height_cm}
          initialWeight={user?.weight_kg}
          onClose={() => setEditingHealth(false)}
        />
      ) : (
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-gray-400"><RulerIcon /></span>
              <p className="text-sm font-semibold text-gray-700">신체 정보</p>
            </div>
            <button onClick={() => setEditingHealth(true)}
              className="text-xs font-medium px-3 py-1 rounded-lg text-[#1D9E75] border border-[#1D9E75]/30 hover:bg-[#1D9E75]/5 transition-colors">
              편집
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '신장', value: user?.height_cm, unit: 'cm' },
              { label: '체중', value: user?.weight_kg, unit: 'kg' },
            ].map(({ label, value, unit }) => (
              <div key={label} className="rounded-xl bg-gray-50 px-4 py-3">
                <p className="text-xs text-gray-400 mb-1">{label}</p>
                {isLoading ? (
                  <Skeleton className="h-7 w-16 rounded" />
                ) : value ? (
                  <p className="text-xl font-bold text-gray-800">
                    {value}<span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>
                  </p>
                ) : (
                  <p className="text-xl font-bold text-gray-300">—</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 의료 정보 (알러지 + 기저질환) ── */}
      <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5 flex flex-col gap-5">
        <AllergySection />
        <div className="border-t border-gray-50" />
        <ConditionSection />
      </div>

      {/* ── 로그아웃 ── */}
      <button
        onClick={() => setLogoutOpen(true)}
        className="w-full rounded-2xl py-3.5 text-sm font-semibold text-red-500 bg-red-50 hover:bg-red-100 transition-colors"
      >
        로그아웃
      </button>

      <ConfirmDialog
        open={logoutOpen} onOpenChange={setLogoutOpen}
        title="로그아웃 하시겠습니까?" confirmLabel="로그아웃" variant="danger"
        onConfirm={handleLogout}
      />

    </div>
  )
}

function XIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function XSmallIcon() {
  return (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function RulerIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
    </svg>
  )
}
function AlertIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  )
}
function HeartIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
    </svg>
  )
}
