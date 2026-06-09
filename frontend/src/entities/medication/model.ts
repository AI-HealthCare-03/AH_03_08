export interface MedicationItem {
  id: string
  drug_name: string
  dosage: string | null
  frequency: string | null
  instructions: string | null
  created_at: string
  record_type?: number | null
  source_name?: string | null
}
