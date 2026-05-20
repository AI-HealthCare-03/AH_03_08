import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'
import { queryClient } from '@/shared/lib/queryClient'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster position="top-center" richColors closeButton />
    </QueryClientProvider>
  )
}
