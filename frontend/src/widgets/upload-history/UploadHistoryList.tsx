import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Pencil, Trash2, MoreVertical, Sparkles } from 'lucide-react'
import { StatusBadge } from '@/shared/ui/StatusBadge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import { useMedicalRecords, useDeleteRecord, useUpdateRecord, useGenerateGuide } from '@/entities/medical-record/api'
import { useInvalidateGuides } from '@/entities/guide/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import type { MedicalRecord } from '@/entities/medical-record/model'
import { toast } from 'sonner'

const TYPE_ICON: Record<string, string> = {
  prescription: 'file-text',
  medicine_bag: 'package',
  pill_photo: 'camera',
}

const TYPE_BADGE: Record<string, { bg: string; color: string }> = {
  prescription: { bg: '#EFF6FF', color: '#1D4ED8' },
  medicine_bag: { bg: '#FFF7ED', color: '#C2410C' },
  pill_photo:   { bg: '#F0FDF4', color: '#15803D' },
}

export function UploadHistoryList() {
  const { data: records, isLoading } = useMedicalRecords()
  const navigate = useNavigate()
  const { mutate: deleteRecord, isPending: isDeleting } = useDeleteRecord()
  const { mutate: updateRecord, isPending: isUpdating } = useUpdateRecord()
  const { mutate: generateGuide, isPending: isGenerating } = useGenerateGuide()
  const invalidateGuides = useInvalidateGuides()
  const [generatingId, setGeneratingId] = useState<string | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<MedicalRecord | null>(null)
  const [editTarget, setEditTarget] = useState<MedicalRecord | null>(null)
  const [editForm, setEditForm] = useState({ hospital: '', pharmacy: '', disease_code: '', issued_at: '' })
  const [menuOpen, setMenuOpen] = useState<string | null>(null)

  function handleGenerateGuide(record: MedicalRecord) {
    setGeneratingId(record.id)
    generateGuide(String(record.id), {
      onSuccess: (data) => {
        invalidateGuides()
        toast.success('가이드 생성 요청 완료!')
        navigate(`/guide?id=${data.guide_id}`)
      },
      onError: () => toast.error('가이드 생성에 실패했습니다.'),
      onSettled: () => setGeneratingId(null),
    })
  }

  function openEdit(record: MedicalRecord) {
    setEditTarget(record)
    setEditForm({
      hospital: record.parsed_data?.hospital ?? '',
      pharmacy: record.parsed_data?.pharmacy ?? '',
      disease_code: record.parsed_data?.disease_code ?? '',
      issued_at: record.parsed_data?.issued_at ?? '',
    })
  }

  function handleUpdate() {
    if (!editTarget) return
    updateRecord({
      id: String(editTarget.id),
      parsed_data: {
        ...editTarget.parsed_data,
        medications: editTarget.parsed_data?.medications ?? [],
        hospital: editForm.hospital || undefined,
        pharmacy: editForm.pharmacy || undefined,
        disease_code: editForm.disease_code || undefined,
        issued_at: editForm.issued_at || undefined,
      },
    }, { onSuccess: () => setEditTarget(null) })
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 rounded-xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!records?.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-400">
        <p className="text-sm">업로드된 기록이 없습니다.</p>
      </div>
    )
  }

  return (
    <>
      <ul className="space-y-3">
        {records.slice(0, 5).map((record) => {
          const meta = RECORD_TYPE_META[record.record_type]
          const canNavigate = record.status === 'completed' && !!record.guide_id
          const canGenerate = record.status === 'completed' && !record.guide_id
          const isThisGenerating = generatingId === record.id
          const isMenuOpen = menuOpen === record.id

          return (
            <li
              key={record.id}
              onClick={() => { setMenuOpen(null); canNavigate && navigate(`/guide?id=${record.guide_id}`) }}
              className={`relative flex items-start gap-3 rounded-xl bg-white p-4 shadow-sm transition-colors ${canNavigate ? 'cursor-pointer hover:bg-gray-50' : ''}`}
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 mt-0.5">
                <RecordIcon name={TYPE_ICON[record.record_type]} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className="shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                    style={TYPE_BADGE[record.record_type]}
                  >
                    {meta.label}
                  </span>
                  {(() => {
                    const name = record.record_type === 'medicine_bag'
                      ? record.parsed_data?.pharmacy
                      : record.parsed_data?.hospital
                    const diseaseName = record.parsed_data?.disease_name
                    return name
                      ? <span className="truncate text-sm font-medium text-gray-800">
                          {name}{diseaseName ? ` (${diseaseName})` : ''}
                        </span>
                      : null
                  })()}
                </div>

                <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                  {(() => {
                    const d = record.parsed_data?.issued_at ? new Date(record.parsed_data.issued_at) : null
                    const valid = d && !isNaN(d.getTime())
                    return valid
                      ? <span className="text-xs text-gray-400">처방일 {d!.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })}</span>
                      : null
                  })()}
                  {record.parsed_data?.disease_code && (
                    <span className="rounded px-1.5 py-0.5 text-xs font-medium"
                      style={{ background: '#D1FAE5', color: '#065F46' }}>
                      {record.parsed_data.disease_code}
                    </span>
                  )}
                  {(record.parsed_data?.medications?.length ?? 0) > 0 && (
                    <span className="text-xs text-gray-400">
                      약 {record.parsed_data!.medications!.length}종
                    </span>
                  )}
                  {!record.parsed_data?.issued_at && !record.parsed_data?.hospital && !record.parsed_data?.pharmacy && (
                    <span className="text-xs text-gray-400">{new Date(record.created_at).toLocaleDateString('ko-KR')}</span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 shrink-0">
                <StatusBadge status={record.status} />

                {canGenerate && (
                  <button
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-white"
                    style={{ background: '#1D9E75' }}
                    onClick={e => { e.stopPropagation(); handleGenerateGuide(record) }}
                    disabled={isThisGenerating || isGenerating}
                  >
                    <Sparkles className="h-3 w-3" />
                    {isThisGenerating ? '생성 중...' : '가이드 생성'}
                  </button>
                )}

                {/* 더보기 메뉴 */}
                <div className="relative" onClick={e => e.stopPropagation()}>
                  <button
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    onClick={() => setMenuOpen(isMenuOpen ? null : record.id)}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>

                  {isMenuOpen && (
                    <div className="absolute right-0 top-7 z-10 w-28 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
                      <button
                        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                        onClick={() => { setMenuOpen(null); openEdit(record) }}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        수정
                      </button>
                      <button
                        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
                        onClick={() => { setMenuOpen(null); setDeleteTarget(record) }}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        삭제
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      {/* 삭제 확인 다이얼로그 */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="기록을 삭제하시겠어요?"
        description="삭제된 기록과 연결된 가이드도 함께 삭제됩니다. 이 작업은 되돌릴 수 없습니다."
        confirmLabel={isDeleting ? '삭제 중...' : '삭제'}
        variant="danger"
        onConfirm={() => deleteRecord(String(deleteTarget!.id), { onSuccess: () => setDeleteTarget(null) })}
      />

      {/* 수정 다이얼로그 */}
      <Dialog open={!!editTarget} onOpenChange={(open) => !open && setEditTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>기록 수정</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {editTarget?.record_type !== 'medicine_bag' ? (
              <label className="block">
                <span className="text-xs text-gray-500">병원명</span>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                  value={editForm.hospital}
                  onChange={e => setEditForm(f => ({ ...f, hospital: e.target.value }))}
                />
              </label>
            ) : (
              <label className="block">
                <span className="text-xs text-gray-500">약국명</span>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                  value={editForm.pharmacy}
                  onChange={e => setEditForm(f => ({ ...f, pharmacy: e.target.value }))}
                />
              </label>
            )}
            <label className="block">
              <span className="text-xs text-gray-500">질병 분류 기호</span>
              <input
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                placeholder="예: N30.0"
                value={editForm.disease_code}
                onChange={e => setEditForm(f => ({ ...f, disease_code: e.target.value }))}
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">처방일</span>
              <input
                type="date"
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                value={editForm.issued_at ? editForm.issued_at.slice(0, 10) : ''}
                onChange={e => setEditForm(f => ({ ...f, issued_at: e.target.value }))}
              />
            </label>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditTarget(null)}>취소</Button>
            <Button disabled={isUpdating} onClick={handleUpdate}>
              {isUpdating ? '저장 중...' : '저장'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function RecordIcon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    'file-text': (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 12h6M9 16h6M7 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2M9 4h6v2H9V4z" />
    ),
    package: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    ),
    camera: (
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m8.5 8.5 7 7" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
          d="M 15.5 5 A 3 3 0 0 1 19 8.5" />
      </>
    ),
  }
  return (
    <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      {paths[name]}
    </svg>
  )
}
