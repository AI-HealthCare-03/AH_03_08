export type RecordType = 'prescription' | 'medicine_bag' | 'pill_photo'

export type RecordStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  status_code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}
