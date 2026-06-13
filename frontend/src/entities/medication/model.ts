export interface MedicationItem {
  id: string
  drug_name: string
  dosage: string | null
  frequency: string | null
  instructions: string | null
  drug_class: string | null
  created_at: string
  record_type?: number | null
  source_name?: string | null
  diagnosis?: string | null
  start_date?: string | null
  end_date?: string | null
}

export interface DrugSearchItem {
  drug_name: string
  drug_class: string | null
  dosage: string | null
}
