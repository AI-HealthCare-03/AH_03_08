import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { RecordTypeSelector } from './RecordTypeSelector'
import { ParsedDataForm } from './ParsedDataForm'
import { FileDropzone } from '@/shared/ui/FileDropzone'
import { Button } from '@/components/ui/button'
import { useInvalidateGuides } from '@/entities/guide/api'
import {
  useUploadRecord,
  useRecord,
  useUpdateRecord,
  useGenerateGuide,
} from '@/entities/medical-record/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import type { ParsedData } from '@/entities/medical-record/model'
import type { RecordType } from '@/shared/types'

export function RecordUploadForm() {
  const navigate = useNavigate()
  const [selectedType, setSelectedType] = useState<RecordType | null>(null)
  const [previewFile, setPreviewFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [recordId, setRecordId] = useState<string | null>(null)
  const [editedData, setEditedData] = useState<ParsedData | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { mutate: upload, isPending: isUploading } = useUploadRecord()
  const { data: record } = useRecord(recordId)
  const { mutate: updateRecord, isPending: isUpdating } = useUpdateRecord()
  const { mutate: generateGuide, isPending: isGenerating } = useGenerateGuide()
  const invalidateGuides = useInvalidateGuides()

  useEffect(() => {
    if (!previewFile?.type.startsWith('image/')) return
    const url = URL.createObjectURL(previewFile)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [previewFile])

  useEffect(() => {
    if (record?.status === 'completed' && record.parsed_data) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEditedData((prev) => prev ?? (record.parsed_data as ParsedData))
    }
  }, [record?.status, record?.parsed_data])

  function resetRecord() {
    setRecordId(null)
    setEditedData(null)
  }

  function handleTypeChange(type: RecordType) {
    setSelectedType(type)
    resetRecord()
    setPreviewFile(null)
    setPreviewUrl(null)
  }

  function doUpload(file: File, type: RecordType) {
    upload(
      { file, record_type: type },
      {
        onSuccess: (data) => setRecordId(data.id),
        onError: () => toast.error('업로드에 실패했습니다. 다시 시도해 주세요.'),
      },
    )
  }

  function checkResolution(file: File): Promise<boolean> {
    if (!file.type.startsWith('image/')) return Promise.resolve(true)
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        URL.revokeObjectURL(img.src)
        if (img.width < 600 || img.height < 600) {
          toast.warning(
            `이미지 해상도가 낮습니다 (${img.width}×${img.height}px). 더 선명한 사진을 사용하면 인식률이 높아집니다.`,
            { duration: 5000 },
          )
        }
        resolve(true)
      }
      img.onerror = () => { URL.revokeObjectURL(img.src); resolve(true) }
      img.src = URL.createObjectURL(file)
    })
  }

  async function handleFileSelect(file: File) {
    if (!selectedType) { toast.error('먼저 기록 종류를 선택해주세요.'); return }
    setPreviewFile(file)
    if (!file.type.startsWith('image/')) setPreviewUrl(null)
    resetRecord()
    await checkResolution(file)
    doUpload(file, selectedType)
  }

  async function handleChangeFile(file: File) {
    if (!selectedType) return
    setPreviewFile(file)
    if (!file.type.startsWith('image/')) setPreviewUrl(null)
    resetRecord()
    await checkResolution(file)
    doUpload(file, selectedType)
  }

  function handleGenerateGuide() {
    if (!recordId || !editedData) return
    updateRecord(
      { id: recordId, parsed_data: editedData },
      {
        onSuccess: () => {
          generateGuide(recordId, {
            onSuccess: (data) => {
              invalidateGuides()
              toast.success('가이드 생성 요청 완료! 가이드 탭에서 확인하세요.')
              navigate(`/guide?id=${data.guide_id}`)
            },
            onError: () => toast.error('가이드 생성에 실패했습니다.'),
          })
        },
        onError: () => toast.error('데이터 저장에 실패했습니다.'),
      },
    )
  }

  const isProcessing = record?.status === 'pending' || record?.status === 'processing'
  const isCompleted = record?.status === 'completed'
  const isFailed = record?.status === 'failed'
  const hint = selectedType
    ? `${RECORD_TYPE_META[selectedType].label} · PDF, JPG, PNG · 최대 10MB`
    : undefined

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">1. 기록 종류 선택</h2>
        <RecordTypeSelector selected={selectedType} onChange={handleTypeChange} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">2. 파일 업로드</h2>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleChangeFile(file)
            e.target.value = ''
          }}
        />

        {!previewFile ? (
          <FileDropzone hint={hint} onFileSelect={handleFileSelect} />
        ) : previewUrl ? (
          <div className="group relative overflow-hidden rounded-xl border border-gray-100 cursor-pointer">
            <img src={previewUrl} alt="미리보기" className="h-48 w-full object-contain bg-[#F5F5F4]" />
            <div className="absolute bottom-0 left-0 right-0 bg-black/40 px-3 py-1.5">
              <p className="truncate text-xs text-white">{previewFile.name}</p>
            </div>
            {!isProcessing && !isUploading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow hover:bg-gray-50"
                >
                  파일 변경
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="group relative flex items-center gap-3 rounded-xl border border-gray-100 bg-[#F5F5F4] px-4 py-3 cursor-pointer">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50">
              <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M9 12h6M9 16h6M7 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2M9 4h6v2H9V4z" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-gray-700">{previewFile.name}</p>
              <p className="text-xs text-gray-400">{(previewFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            {!isProcessing && !isUploading && (
              <div className="absolute inset-0 rounded-xl flex items-center justify-end px-4 bg-black/5 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-lg bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow hover:bg-gray-50"
                >
                  파일 변경
                </button>
              </div>
            )}
          </div>
        )}

        {(isUploading || isProcessing) && (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-primary/5 px-4 py-3">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent shrink-0" />
            <p className="text-sm text-primary">
              {isUploading ? '파일 업로드 중...' : 'OCR 분석 중... 잠시만 기다려 주세요.'}
            </p>
          </div>
        )}

        {isFailed && (
          <div className="mt-3 rounded-xl bg-red-50 px-4 py-3">
            <p className="text-sm text-red-600">OCR 처리에 실패했습니다. 파일을 다시 업로드해주세요.</p>
          </div>
        )}
      </section>

      {isCompleted && editedData && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">3. 내용 확인 및 수정</h2>
            <span className="text-xs text-gray-400">틀린 내용이 있으면 수정해주세요</span>
          </div>
          <ParsedDataForm data={editedData} onChange={setEditedData} />
          <Button
            className="mt-4 w-full"
            disabled={isUpdating || isGenerating}
            onClick={handleGenerateGuide}
          >
            {isUpdating || isGenerating ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                처리 중...
              </span>
            ) : (
              '가이드 생성'
            )}
          </Button>
        </section>
      )}
    </div>
  )
}
