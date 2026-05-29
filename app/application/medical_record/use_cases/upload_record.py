import uuid
from pathlib import Path

from celery import Celery

from app.application.medical_record.dto.record_dto import UploadRecordCommand
from app.core import config
from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository
from app.domain.medical_record.value_objects import RecordType

_celery = Celery(broker=config.CELERY_BROKER_URL, backend=config.CELERY_RESULT_BACKEND)


class UploadRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, command: UploadRecordCommand) -> MedicalRecord:
        file_name = f"{uuid.uuid4()}_{command.original_filename}"
        file_path = Path(config.UPLOAD_DIR) / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(command.file_content)

        record = MedicalRecord(
            user_id=command.user_id,
            record_type=command.record_type,
        )
        saved = await self.repo.save(record)

        # REQ-IMG: pill_photo(2) 타입은 낱알약 분류 task로 분기
        if command.record_type == RecordType.PILL:
            self._dispatch_image_analyze(saved.id, command.file_content)
        else:
            self._dispatch_ocr(saved.id, str(file_path))

        return saved

    def _dispatch_ocr(self, record_id: uuid.UUID, file_path: str) -> None:
        _celery.send_task(
            "ai_worker.tasks.ocr_task.process_ocr",
            args=[str(record_id), file_path],
            queue="image",
        )

    # REQ-IMG: 낱알약 이미지 분류 task 등록 (태준)
    def _dispatch_image_analyze(self, record_id: uuid.UUID, image_bytes: bytes) -> None:
        _celery.send_task(
            "ai_worker.tasks.image_task.classify_pill",
            kwargs={
                "record_id": str(record_id),
                "user_id": "",
                "image_bytes": image_bytes,
            },
            queue="image",
        )
