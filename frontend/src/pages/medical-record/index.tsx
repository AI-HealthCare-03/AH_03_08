import { RecordUploadForm } from '@/features/record-upload/RecordUploadForm'
import { UploadHistoryList } from '@/widgets/upload-history/UploadHistoryList'

export function MedicalRecordPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-lg font-bold text-gray-900">의료기록</h1>
        <p className="mt-0.5 text-sm text-gray-500">업로드하면 AI가 분석해드려요</p>
      </div>

      <RecordUploadForm />

      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">업로드 기록</h2>
        <UploadHistoryList />
      </section>
    </div>
  )
}
