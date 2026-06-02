import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import { type Guide, guideSchema, type GuideStatus } from './model'

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message: string
}

export type GuideFeedbackRating = 0 | 1

export interface GuideFeedback {
  id: string
  guide_id: string
  rating: GuideFeedbackRating
  tag_ids: string[]
  comment: string | null
  status: string
  created_at: string | null
}

export interface SubmitFeedbackPayload {
  guide_id: string
  rating: GuideFeedbackRating
  tag_ids?: string[]
  comment?: string | null
}

const KEYS = {
  all: ['guides'] as const,
  list: () => [...KEYS.all, 'list'] as const,
  detail: (id: string) => [...KEYS.all, 'detail', id] as const,
  status: (id: string) => [...KEYS.all, 'status', id] as const,
  feedbacks: () => [...KEYS.all, 'feedbacks'] as const,
}

function parseJsonField<T>(value: unknown, fallback: T): T {
  if (value == null) return fallback
  if (typeof value === 'string') {
    try {
      return JSON.parse(value) as T
    } catch {
      return fallback
    }
  }
  return value as T
}

function normalizeGuide(raw: Record<string, unknown>): Guide {
  return guideSchema.parse({
    ...raw,
    allergy_warnings: parseJsonField(raw.allergy_warnings, []),
    condition_interactions: parseJsonField(raw.condition_interactions, []),
  })
}

async function fetchGuides(): Promise<Guide[]> {
  const { data } = await apiClient.get<ApiEnvelope<{ total: number; items: Record<string, unknown>[] }>>(
    '/guides',
  )
  const items = data.data.items ?? []
  return items.map((raw, index) => {
    try {
      return normalizeGuide(raw)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      throw new Error(`가이드 데이터 형식 오류 (항목 ${index + 1}): ${msg}`)
    }
  })
}

async function fetchGuide(id: string): Promise<Guide> {
  const { data } = await apiClient.get<ApiEnvelope<Record<string, unknown>>>(`/guides/${id}`)
  return normalizeGuide(data.data)
}

async function fetchGuideStatus(id: string): Promise<{ guide_id: string; status: GuideStatus }> {
  const { data } = await apiClient.get<ApiEnvelope<{ guide_id: string; status: GuideStatus }>>(
    `/guides/${id}/status`,
  )
  return data.data
}

export function useGuides() {
  return useQuery({
    queryKey: KEYS.list(),
    queryFn: fetchGuides,
  })
}

export function useGuide(id: string | null) {
  return useQuery({
    queryKey: KEYS.detail(id!),
    queryFn: () => fetchGuide(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'processing') return 2000
      return false
    },
  })
}

export function useGuideStatus(id: string | null, enabled = true) {
  return useQuery({
    queryKey: KEYS.status(id!),
    queryFn: () => fetchGuideStatus(id!),
    enabled: !!id && enabled,
    refetchInterval: (query) => {
      if (query.state.data?.status === 'processing') return 2000
      return false
    },
  })
}

export function useInvalidateGuides() {
  const qc = useQueryClient()
  return () => qc.invalidateQueries({ queryKey: KEYS.all })
}

async function fetchMyFeedbacks(): Promise<GuideFeedback[]> {
  const { data } = await apiClient.get<ApiEnvelope<{ total: number; items: GuideFeedback[] }>>(
    '/guides/feedbacks/list',
  )
  return data.data.items
}

async function submitFeedback(payload: SubmitFeedbackPayload): Promise<{ feedback_id: string }> {
  const { data } = await apiClient.post<ApiEnvelope<{ feedback_id: string }>>('/guides/feedbacks', {
    guide_id: payload.guide_id,
    rating: payload.rating,
    comment: payload.comment ?? null,
    tag_ids: payload.tag_ids ?? [],
  })
  return data.data
}

export function useMyFeedbacks() {
  return useQuery({
    queryKey: KEYS.feedbacks(),
    queryFn: fetchMyFeedbacks,
  })
}

export function useFeedbackForGuide(guideId: string | null) {
  const query = useMyFeedbacks()
  const feedback = query.data?.find((f) => f.guide_id === guideId)
  return { ...query, feedback }
}

export function useSubmitFeedback() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.feedbacks() }),
  })
}

export type AssetType = 'tts' | 'card_news'

export interface CreateAssetResponse {
  asset_id: string
  status: string
}

async function createAsset(guideId: string, assetType: AssetType): Promise<CreateAssetResponse> {
  const { data } = await apiClient.post<ApiEnvelope<CreateAssetResponse>>(
    `/guides/${guideId}/assets`,
    { asset_type: assetType },
  )
  return data.data
}

export function useCreateAsset(guideId: string) {
  return useMutation({
    mutationFn: (assetType: AssetType) => createAsset(guideId, assetType),
  })
}