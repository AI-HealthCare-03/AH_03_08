from uuid import UUID

from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository
from app.domain.medical_record.value_objects import RecordStatus, RecordType
from app.models.medical_records import MedicalRecord as MedicalRecordORM


class TortoiseRecordRepository(AbstractRecordRepository):
    def _to_domain(self, orm: MedicalRecordORM, guide_id: UUID | None = None) -> MedicalRecord:
        return MedicalRecord(
            id=orm.id,
            user_id=orm.user_id,
            record_type=RecordType(orm.record_type),
            status=RecordStatus(orm.status.upper()),
            ocr_raw_text=orm.ocr_raw_text,
            parsed_data=orm.parsed_data,
            file_url=orm.file_url,
            created_at=orm.created_at,
            guide_id=guide_id,
        )

    async def save(self, record: MedicalRecord) -> MedicalRecord:
        orm = await MedicalRecordORM.create(
            id=record.id,
            user_id=record.user_id,
            record_type=int(record.record_type),
            status=str(record.status),
            ocr_raw_text=record.ocr_raw_text,
            parsed_data=record.parsed_data,
            file_url=record.file_url,
        )
        return self._to_domain(orm)

    async def find_by_id(self, record_id: UUID) -> MedicalRecord | None:
        orm = await MedicalRecordORM.get_or_none(id=record_id)
        return self._to_domain(orm) if orm else None

    async def find_by_user_id_paginated(self, user_id: int, page: int, limit: int) -> tuple[list[MedicalRecord], int]:
        from app.models.guide import Guide as GuideORM

        qs = MedicalRecordORM.filter(user_id=user_id, record_type__in=[0, 1, 2]).order_by("-created_at")
        total = await qs.count()
        orm_records = await qs.offset((page - 1) * limit).limit(limit)

        record_ids = [r.id for r in orm_records]
        guide_rows = await GuideORM.filter(record_id__in=record_ids).values("id", "record_id")
        guide_map: dict[str, UUID] = {}
        for g in guide_rows:
            try:
                guide_map[str(g["record_id"])] = g["id"]
            except Exception:
                pass
        return [self._to_domain(r, guide_id=guide_map.get(str(r.id))) for r in orm_records], total

    async def update_parsed_data(self, record_id: UUID, parsed_data: dict) -> MedicalRecord:
        orm = await MedicalRecordORM.get(id=record_id)
        orm.parsed_data = parsed_data
        await orm.save(update_fields=["parsed_data"])
        return self._to_domain(orm)

    async def delete_by_id(self, record_id: UUID) -> None:
        await MedicalRecordORM.filter(id=record_id).delete()

    async def delete_old_records(self, user_id: int, keep: int) -> None:
        records = await MedicalRecordORM.filter(user_id=user_id).order_by("-created_at").values_list("id", flat=True)
        if len(records) > keep:
            old_ids = records[keep:]
            await MedicalRecordORM.filter(id__in=old_ids).delete()
