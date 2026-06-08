import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/shared/ui/PageHeader'
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
  mild:     { label: '경미',   className: 'bg-yellow-50 text-yellow-700' },
  moderate: { label: '중등도', className: 'bg-orange-50 text-orange-700' },
  severe:   { label: '심각',   className: 'bg-red-50 text-red-700' },
}

function SeverityBadge({ severity }: { severity: string }) {
  const cfg = SEVERITY_CONFIG[severity as keyof typeof SEVERITY_CONFIG] ?? { label: severity, className: 'bg-gray-100 text-gray-600' }
  return <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${cfg.className}`}>{cfg.label}</span>
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-50">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{title}</p>
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value ?? '—'}</span>
    </div>
  )
}

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
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-500 w-12 shrink-0">신장</label>
        <input
          type="number"
          value={height}
          onChange={(e) => setHeight(e.target.value)}
          placeholder="cm"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:border-[#1D9E75]"
        />
      </div>
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-500 w-12 shrink-0">체중</label>
        <input
          type="number"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          placeholder="kg"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:border-[#1D9E75]"
        />
      </div>
      <div className="flex gap-2 justify-end mt-1">
        <button onClick={onClose} className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50">
          취소
        </button>
        <button
          onClick={handleSave}
          disabled={isPending}
          className="text-xs px-3 py-1.5 rounded-lg text-white disabled:opacity-60"
          style={{ background: '#1D9E75' }}
        >
          저장
        </button>
      </div>
    </div>
  )
}

function AddItemForm({ placeholder, onAdd, onCancel, isPending }: {
  placeholder: string
  onAdd: (name: string, severity: string) => void
  onCancel: () => void
  isPending: boolean
}) {
  const [name, setName] = useState('')
  const [severity, setSeverity] = useState('mild')

  return (
    <div className="flex flex-col gap-2 pt-2 border-t border-gray-100 mt-2">
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder={placeholder}
        className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:border-[#1D9E75]"
        autoFocus
      />
      <select
        value={severity}
        onChange={(e) => setSeverity(e.target.value)}
        className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:border-[#1D9E75]"
      >
        <option value="mild">경미</option>
        <option value="moderate">중등도</option>
        <option value="severe">심각</option>
      </select>
      <div className="flex gap-2 justify-end">
        <button onClick={onCancel} className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50">
          취소
        </button>
        <button
          onClick={() => { if (name.trim()) onAdd(name.trim(), severity) }}
          disabled={!name.trim() || isPending}
          className="text-xs px-3 py-1.5 rounded-lg text-white disabled:opacity-60"
          style={{ background: '#1D9E75' }}
        >
          추가
        </button>
      </div>
    </div>
  )
}

function AllergyList() {
  const { data: allergies, isLoading } = useAllergies()
  const { mutate: addAllergy, isPending: isAdding } = useAddAllergy()
  const { mutate: deleteAllergy } = useDeleteAllergy()
  const [showForm, setShowForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<AllergyItem | null>(null)

  return (
    <SectionCard title="알러지 정보">
      {isLoading ? (
        <Skeleton className="h-8 w-full rounded" />
      ) : (
        <div className="flex flex-col gap-2">
          {!allergies?.length && !showForm && (
            <p className="text-sm text-gray-400 text-center py-2">등록된 알러지가 없습니다.</p>
          )}
          {allergies?.map((item) => (
            <div key={item.id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-800">{item.allergen_name}</span>
                <SeverityBadge severity={item.severity} />
              </div>
              <button
                onClick={() => setDeleteTarget(item)}
                className="p-1 rounded text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
          {showForm ? (
            <AddItemForm
              placeholder="알러지 물질 입력 (예: 페니실린)"
              isPending={isAdding}
              onAdd={(name, severity) => addAllergy({ allergen_name: name, severity }, { onSuccess: () => setShowForm(false) })}
              onCancel={() => setShowForm(false)}
            />
          ) : (
            <button
              onClick={() => setShowForm(true)}
              className="mt-1 text-xs text-[#1D9E75] hover:underline text-left"
            >
              + 추가하기
            </button>
          )}
        </div>
      )}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title={`'${deleteTarget?.allergen_name}' 알러지를 삭제하시겠습니까?`}
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => { if (deleteTarget) deleteAllergy(deleteTarget.id) }}
      />
    </SectionCard>
  )
}

function ConditionList() {
  const { data: conditions, isLoading } = useConditions()
  const { mutate: addCondition, isPending: isAdding } = useAddCondition()
  const { mutate: deleteCondition } = useDeleteCondition()
  const [showForm, setShowForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ConditionItem | null>(null)

  return (
    <SectionCard title="기저질환">
      {isLoading ? (
        <Skeleton className="h-8 w-full rounded" />
      ) : (
        <div className="flex flex-col gap-2">
          {!conditions?.length && !showForm && (
            <p className="text-sm text-gray-400 text-center py-2">등록된 기저질환이 없습니다.</p>
          )}
          {conditions?.map((item) => (
            <div key={item.id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-800">{item.condition_name}</span>
                <SeverityBadge severity={item.severity} />
              </div>
              <button
                onClick={() => setDeleteTarget(item)}
                className="p-1 rounded text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
          {showForm ? (
            <AddItemForm
              placeholder="질환명 입력 (예: 고혈압)"
              isPending={isAdding}
              onAdd={(name, severity) => addCondition({ condition_name: name, severity }, { onSuccess: () => setShowForm(false) })}
              onCancel={() => setShowForm(false)}
            />
          ) : (
            <button
              onClick={() => setShowForm(true)}
              className="mt-1 text-xs text-[#1D9E75] hover:underline text-left"
            >
              + 추가하기
            </button>
          )}
        </div>
      )}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title={`'${deleteTarget?.condition_name}'을 삭제하시겠습니까?`}
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => { if (deleteTarget) deleteCondition(deleteTarget.id) }}
      />
    </SectionCard>
  )
}

export function MyPage() {
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const { data: user, isLoading } = useCurrentUser()
  const [editingHealth, setEditingHealth] = useState(false)
  const [logoutOpen, setLogoutOpen] = useState(false)

  const genderLabel = user?.gender === 'MALE' ? '남성' : user?.gender === 'FEMALE' ? '여성' : null

  function handleLogout() {
    logout()
    navigate('/auth/login', { replace: true })
  }

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader title="마이페이지" />

      <div className="flex flex-col gap-4">
        {/* 프로필 */}
        <SectionCard title="프로필">
          {isLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-4 w-32 rounded" />
              <Skeleton className="h-4 w-48 rounded" />
            </div>
          ) : (
            <div className="flex flex-col divide-y divide-gray-50">
              <InfoRow label="이름" value={user?.name} />
              <InfoRow label="이메일" value={user?.email} />
              <InfoRow label="성별" value={genderLabel} />
              <InfoRow label="생년월일" value={user?.birth_date ?? null} />
            </div>
          )}
        </SectionCard>

        {/* 건강 정보 */}
        <SectionCard title="건강 정보">
          {isLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-4 w-24 rounded" />
              <Skeleton className="h-4 w-24 rounded" />
            </div>
          ) : editingHealth ? (
            <HealthEditForm
              initialHeight={user?.height_cm}
              initialWeight={user?.weight_kg}
              onClose={() => setEditingHealth(false)}
            />
          ) : (
            <div className="flex flex-col divide-y divide-gray-50">
              <InfoRow label="신장" value={user?.height_cm ? `${user.height_cm} cm` : null} />
              <InfoRow label="체중" value={user?.weight_kg ? `${user.weight_kg} kg` : null} />
              <div className="pt-2">
                <button
                  onClick={() => setEditingHealth(true)}
                  className="text-xs text-[#1D9E75] hover:underline"
                >
                  편집
                </button>
              </div>
            </div>
          )}
        </SectionCard>

        {/* 알러지 */}
        <AllergyList />

        {/* 기저질환 */}
        <ConditionList />

        {/* 로그아웃 */}
        <button
          onClick={() => setLogoutOpen(true)}
          className="w-full rounded-2xl border border-gray-100 bg-white shadow-sm py-3.5 text-sm font-medium text-red-500 hover:bg-red-50 transition-colors"
        >
          로그아웃
        </button>
      </div>

      <ConfirmDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="로그아웃 하시겠습니까?"
        confirmLabel="로그아웃"
        variant="danger"
        onConfirm={handleLogout}
      />
    </div>
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
