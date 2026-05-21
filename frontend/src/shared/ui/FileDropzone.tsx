import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'

interface FileDropzoneProps {
  accept?: string
  maxSizeMB?: number
  hint?: string
  onFileSelect: (file: File) => void
}

export function FileDropzone({
  accept = '.pdf,.jpg,.jpeg,.png',
  maxSizeMB = 20,
  hint,
  onFileSelect,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function validate(file: File) {
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`파일 크기는 최대 ${maxSizeMB}MB입니다.`)
      return false
    }
    setError(null)
    return true
  }

  function handleFile(file: File) {
    if (validate(file)) onFileSelect(file)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer
        ${isDragging ? 'border-primary bg-primary/5' : 'border-gray-200 bg-gray-50'}`}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
        }}
      />

      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm">
        <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
      </div>

      <p className="text-sm text-gray-500 text-center">
        파일을 드래그하거나 클릭하여 업로드
      </p>
      {hint && <p className="text-xs text-gray-400 text-center">{hint}</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="mt-1"
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
      >
        파일 선택
      </Button>
    </div>
  )
}
