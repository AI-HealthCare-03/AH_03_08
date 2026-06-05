// import { useState } from 'react'

// import { ThumbsDown, ThumbsUp } from 'lucide-react'

// import { Button } from '@/components/ui/button'

// import {

//   useFeedbackForGuide,

//   useSubmitFeedback,

//   type GuideFeedbackRating,

// } from '@/entities/guide/api'

// import { toast } from '@/shared/lib/toast'

// import { NEGATIVE_FEEDBACK_CATEGORIES, POSITIVE_FEEDBACK_CATEGORIES } from './constants'



// interface GuideFeedbackProps {

//   guideId: string

// }



// function FeedbackChipGrid({

//   labels,

//   selected,

//   onToggle,

// }: {

//   labels: readonly string[]

//   selected: string[]

//   onToggle: (label: string) => void

// }) {

//   return (

//     <div className="flex flex-wrap gap-2 justify-start">

//       {labels.map((label) => {

//         const on = selected.includes(label)

//         return (

//           <button

//             key={label}

//             type="button"

//             onClick={() => onToggle(label)}

//             className={`rounded-xl px-3 py-2 text-sm text-gray-900 border bg-white transition-colors ${

//               on

//                 ? 'border-brand-primary bg-brand-lightest ring-1 ring-brand-primary/20'

//                 : 'border-gray-300 hover:border-gray-400'

//             }`}

//           >

//             {label}

//           </button>

//         )

//       })}

//     </div>

//   )

// }



// export function GuideFeedback({ guideId }: GuideFeedbackProps) {

//   const { feedback: existing } = useFeedbackForGuide(guideId)

//   const { mutate: submit, isPending } = useSubmitFeedback()



//   const [submittedRating, setSubmittedRating] = useState<GuideFeedbackRating | null>(null)

//   const [formKind, setFormKind] = useState<'positive' | 'negative' | null>(null)

//   const [categories, setCategories] = useState<string[]>([])

//   const [comment, setComment] = useState('')



//   const done = submittedRating !== null || existing != null

//   const selectedRating = submittedRating ?? existing?.rating ?? null



//   function toggleCategory(label: string) {

//     setCategories((prev) =>

//       prev.includes(label) ? prev.filter((c) => c !== label) : [...prev, label],

//     )

//   }



//   function resetForm() {

//     setFormKind(null)

//     setCategories([])

//     setComment('')

//   }



//   function submitWithRating(rating: GuideFeedbackRating) {

//     submit(

//       {

//         guide_id: guideId,

//         rating,

//         tag_ids: categories,

//         comment: comment.trim() || null,

//       },

//       {

//         onSuccess: () => {

//           setSubmittedRating(rating)

//           setFormKind(null)

//           toast.success(

//             rating === 1 ? '도움이 되었다니 다행이에요!' : '피드백이 등록되었습니다.',

//           )

//         },

//         onError: () => toast.error('피드백 전송에 실패했습니다.'),

//       },

//     )

//   }



//   return (

//     <section className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">

//       <h3 className="text-center text-sm font-semibold text-gray-800 mb-4">

//         이 가이드가 도움이 되었나요?

//       </h3>



//       {!done && formKind === null && (

//         <div className="flex gap-3">

//           <button

//             type="button"

//             disabled={isPending}

//             onClick={() => {

//               setCategories([])

//               setComment('')

//               setFormKind('positive')

//             }}

//             className="flex-1 flex flex-col items-center gap-2 rounded-2xl border-2 border-amber-200 bg-amber-50 py-4 px-3 transition-colors hover:bg-amber-100 disabled:opacity-50"

//           >

//             <ThumbsUp className="h-8 w-8 text-amber-500" strokeWidth={1.5} />

//             <span className="text-sm font-medium text-amber-900">도움이 됐어요</span>

//           </button>

//           <button

//             type="button"

//             disabled={isPending}

//             onClick={() => {

//               setCategories([])

//               setComment('')

//               setFormKind('negative')

//             }}

//             className="flex-1 flex flex-col items-center gap-2 rounded-2xl border-2 border-red-100 bg-red-50 py-4 px-3 transition-colors hover:bg-red-100 disabled:opacity-50"

//           >

//             <ThumbsDown className="h-8 w-8 text-red-400" strokeWidth={1.5} />

//             <span className="text-sm font-medium text-red-800">아쉬워요</span>

//           </button>

//         </div>

//       )}



//       {!done && formKind === 'positive' && (

//         <div className="space-y-4">

//           <p className="text-sm text-gray-900">어떤 점이 도움이 되었나요? (복수 선택)</p>

//           <FeedbackChipGrid

//             labels={POSITIVE_FEEDBACK_CATEGORIES}

//             selected={categories}

//             onToggle={toggleCategory}

//           />

//           <div>

//             <label htmlFor="guide-feedback-comment-positive" className="text-sm text-gray-900">

//               추가 의견 (선택)

//             </label>

//             <textarea

//               id="guide-feedback-comment-positive"

//               value={comment}

//               onChange={(e) => setComment(e.target.value.slice(0, 300))}

//               placeholder="자유롭게 작성해주세요."

//               rows={3}

//               maxLength={300}

//               className="mt-2 w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-brand-primary/30"

//             />

//             <p className="mt-1 text-right text-xs text-gray-400">{comment.length} / 300</p>

//           </div>

//           <div className="flex gap-2">

//             <Button type="button" variant="outline" className="flex-1" onClick={resetForm}>

//               취소

//             </Button>

//             <Button

//               type="button"

//               className="flex-1 text-white bg-brand-primary hover:bg-brand-dark"

//               disabled={isPending}

//               onClick={() => submitWithRating(1)}

//             >

//               제출하기

//             </Button>

//           </div>

//         </div>

//       )}



//       {!done && formKind === 'negative' && (

//         <div className="space-y-4">

//           <p className="text-sm text-gray-900">어떤 점이 그랬나요? (복수 선택)</p>

//           <FeedbackChipGrid

//             labels={NEGATIVE_FEEDBACK_CATEGORIES}

//             selected={categories}

//             onToggle={toggleCategory}

//           />

//           <div>

//             <label htmlFor="guide-feedback-comment-negative" className="text-sm text-gray-900">

//               추가 의견 (선택)

//             </label>

//             <textarea

//               id="guide-feedback-comment-negative"

//               value={comment}

//               onChange={(e) => setComment(e.target.value.slice(0, 300))}

//               placeholder="자유롭게 작성해주세요."

//               rows={3}

//               maxLength={300}

//               className="mt-2 w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-brand-primary/30"

//             />

//             <p className="mt-1 text-right text-xs text-gray-400">{comment.length} / 300</p>

//           </div>

//           <div className="flex gap-2">

//             <Button type="button" variant="outline" className="flex-1" onClick={resetForm}>

//               취소

//             </Button>

//             <Button

//               type="button"

//               className="flex-1 text-white bg-brand-primary hover:bg-brand-dark"

//               disabled={isPending}

//               onClick={() => submitWithRating(0)}

//             >

//               제출하기

//             </Button>

//           </div>

//         </div>

//       )}



//       {done && (

//         <p className="text-center text-sm text-gray-500 py-2">

//           {selectedRating === 1 ? '👍 피드백 감사합니다!' : '👎 소중한 의견 감사합니다.'}

//         </p>

//       )}

//     </section>

//   )

// }

import { useState } from 'react'
import { Check, ThumbsDown, ThumbsUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  useFeedbackForGuide,
  useSubmitFeedback,
  type GuideFeedbackRating,
} from '@/entities/guide/api'
import { toast } from '@/shared/lib/toast'
import { NEGATIVE_FEEDBACK_CATEGORIES, POSITIVE_FEEDBACK_CATEGORIES } from './constants'

interface GuideFeedbackProps {
  guideId: string
}

function FeedbackChipGrid({
  labels,
  selected,
  onToggle,
}: {
  labels: readonly string[]
  selected: string[]
  onToggle: (label: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {labels.map((label) => {
        const on = selected.includes(label)
        return (
          <button
            key={label}
            type="button"
            onClick={() => onToggle(label)}
            className={`rounded-full px-3 py-1 text-xs font-medium border transition-all ${
              on
                ? 'border-brand-primary bg-brand-lightest text-brand-primary'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

export function GuideFeedback({ guideId }: GuideFeedbackProps) {
  const { feedback: existing } = useFeedbackForGuide(guideId)
  const { mutate: submit, isPending } = useSubmitFeedback()

  const [submittedRating, setSubmittedRating] = useState<GuideFeedbackRating | null>(null)
  const [formKind, setFormKind] = useState<'positive' | 'negative' | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [comment, setComment] = useState('')

  const done = submittedRating !== null || existing != null
  const selectedRating = submittedRating ?? existing?.rating ?? null

  function toggleCategory(label: string) {
    setCategories((prev) =>
      prev.includes(label) ? prev.filter((c) => c !== label) : [...prev, label],
    )
  }

  function resetForm() {
    setFormKind(null)
    setCategories([])
    setComment('')
  }

  function submitWithRating(rating: GuideFeedbackRating) {
    submit(
      {
        guide_id: guideId,
        rating,
        tag_ids: categories,
        comment: comment.trim() || null,
      },
      {
        onSuccess: () => {
          setSubmittedRating(rating)
          setFormKind(null)
          toast.success(rating === 1 ? '도움이 되었다니 다행이에요!' : '피드백이 등록되었습니다.')
        },
        onError: () => toast.error('피드백 전송에 실패했습니다.'),
      },
    )
  }

  const feedbackLabels =
    formKind === 'positive' ? POSITIVE_FEEDBACK_CATEGORIES : NEGATIVE_FEEDBACK_CATEGORIES

  return (
    <section className="rounded-2xl border border-gray-100 bg-white px-5 py-4 shadow-sm">
      {!done && formKind === null && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">이 가이드가 도움이 되었나요?</p>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={isPending}
              onClick={() => { setCategories([]); setComment(''); setFormKind('positive') }}
              className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 transition-all hover:bg-amber-100 hover:border-amber-300 disabled:opacity-50"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
              도움이 됐어요
            </button>
            <button
              type="button"
              disabled={isPending}
              onClick={() => { setCategories([]); setComment(''); setFormKind('negative') }}
              className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-500 transition-all hover:bg-gray-100 hover:border-gray-300 disabled:opacity-50"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
              아쉬워요
            </button>
          </div>
        </div>
      )}

      {!done && formKind !== null && (
        <div className="space-y-3">
          <p className="text-sm text-gray-700">
            {formKind === 'positive' ? '어떤 점이 도움이 되었나요?' : '어떤 점이 그랬나요?'}
            <span className="ml-1 text-xs text-gray-400">복수 선택 가능</span>
          </p>
          <FeedbackChipGrid
            labels={feedbackLabels}
            selected={categories}
            onToggle={toggleCategory}
          />
          <div>
            <textarea
              id="guide-feedback-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value.slice(0, 300))}
              placeholder="추가 의견을 자유롭게 작성해주세요. (선택)"
              rows={2}
              maxLength={300}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 resize-none focus:outline-none focus:bg-white focus:ring-1 focus:ring-brand-primary/40 transition-all"
            />
            <p className="mt-0.5 text-right text-xs text-gray-400">{comment.length} / 300</p>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" size="sm" className="flex-1 text-xs h-8" onClick={resetForm}>
              취소
            </Button>
            <Button
              type="button"
              size="sm"
              className="flex-1 text-xs h-8 text-white bg-brand-primary hover:bg-brand-dark"
              disabled={isPending}
              onClick={() => submitWithRating(formKind === 'positive' ? 1 : 0)}
            >
              제출하기
            </Button>
          </div>
        </div>
      )}

      {done && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">이 가이드가 도움이 되었나요?</p>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
            <Check className="h-3.5 w-3.5 text-green-500" />
            {selectedRating === 1 ? '도움이 됐어요' : '아쉬워요'}
          </span>
        </div>
      )}
    </section>
  )
}