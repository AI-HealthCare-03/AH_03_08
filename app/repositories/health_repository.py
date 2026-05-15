from app.models.medical_records import MedicalRecord
from app.models.guides import Guide
from app.models.medications import Medication
from app.models.underlying_diseases import UnderlyingDisease
from app.models.allergies import Allergy


class HealthRepository:
    def __init__(self):
        self._record = MedicalRecord
        self._guide = Guide
        self._medication = Medication
        self._disease = UnderlyingDisease
        self._allergy = Allergy

    # ── MedicalRecord ────────────────────────────────────────
    async def create_record(self, user_id, ocr_raw_text=None, parsed_data=None, record_type=0):
        return await self._record.create(
            user_id=user_id,
            ocr_raw_text=ocr_raw_text,
            parsed_data=parsed_data,
            record_type=record_type,
        )

    async def get_record(self, record_id, user_id):
        return await self._record.get_or_none(id=record_id, user_id=user_id)

    async def get_records_by_user(self, user_id, limit=20, offset=0):
        return await self._record.filter(user_id=user_id).order_by("-created_at").offset(offset).limit(limit)

    # ── Guide (AI 분석 결과) ──────────────────────────────────
    async def create_guide(self, user_id, medical_record_id):
        return await self._guide.create(
            user_id=user_id,
            medical_record_id=medical_record_id,
        )

    async def get_guide(self, guide_id, user_id):
        return await self._guide.get_or_none(id=guide_id, user_id=user_id)

    async def update_guide(self, guide_id, medication_guide=None, lifestyle_guide=None, llm_model=None):
        await self._guide.filter(id=guide_id).update(
            medication_guide=medication_guide,
            lifestyle_guide=lifestyle_guide,
            llm_model=llm_model,
        )

    # ── Medication ────────────────────────────────────────────
    async def create_medication(self, medical_record_id, drug_name, dosage=None, frequency=None, instructions=None, warnings=None):
        return await self._medication.create(
            medical_record_id=medical_record_id,
            drug_name=drug_name,
            dosage=dosage,
            frequency=frequency,
            instructions=instructions,
            warnings=warnings,
        )

    async def get_medications_by_record(self, medical_record_id):
        return await self._medication.filter(medical_record_id=medical_record_id)

    # ── UnderlyingDisease ─────────────────────────────────────
    async def create_disease(self, user_id, name, severity=None):
        return await self._disease.create(user_id=user_id, underlying_disease_name=name, severity=severity)

    async def get_diseases_by_user(self, user_id):
        return await self._disease.filter(user_id=user_id)

    async def delete_disease(self, disease_id, user_id):
        return await self._disease.filter(id=disease_id, user_id=user_id).delete()

    # ── Allergy ───────────────────────────────────────────────
    async def create_allergy(self, user_id, name, severity=None):
        return await self._allergy.create(user_id=user_id, allergy_name=name, severity=severity)

    async def get_allergies_by_user(self, user_id):
        return await self._allergy.filter(user_id=user_id)

    async def delete_allergy(self, allergy_id, user_id):
        return await self._allergy.filter(id=allergy_id, user_id=user_id).delete()