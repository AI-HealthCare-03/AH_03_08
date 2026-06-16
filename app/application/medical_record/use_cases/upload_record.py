import base64
import uuid

import boto3
from botocore.exceptions import ClientError
from celery import Celery

from app.application.medical_record.dto.record_dto import UploadRecordCommand
from app.core import config
from app.domain.medical_record.entity import MedicalRecord
from app.domain.medical_record.repository import AbstractRecordRepository
from app.domain.medical_record.value_objects import RecordType

_celery = Celery(broker=config.CELERY_BROKER_URL, backend=config.CELERY_RESULT_BACKEND)


def _upload_to_s3(file_content: bytes, file_name: str) -> str:
    """S3에 파일 업로드 후 URL 반환"""
    s3 = boto3.client(
        "s3",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY,
        aws_secret_access_key=config.AWS_SECRET_KEY,
    )
    bucket = config.S3_BUCKET_NAME
    key = f"uploads/{file_name}"
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_content,
        )
        return f"https://{bucket}.s3.{config.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        raise RuntimeError(f"S3 업로드 실패: {e}") from e


class UploadRecordUseCase:
    def __init__(self, repo: AbstractRecordRepository) -> None:
        self.repo = repo

    async def execute(self, command: UploadRecordCommand) -> MedicalRecord:
        file_name = f"{uuid.uuid4()}_{command.original_filename}"

        # S3 업로드
        file_url = _upload_to_s3(command.file_content, file_name)

        record = MedicalRecord(
            user_id=command.user_id,
            record_type=command.record_type,
            file_url=file_url,
        )
        saved = await self.repo.save(record)

        if command.record_type == RecordType.PILL:
            self._dispatch_image_analyze(saved.id, command.file_content, command.user_id)
        else:
            # OCR은 S3 URL을 넘김
            self._dispatch_ocr(saved.id, file_url)
        return saved

    def _dispatch_ocr(self, record_id: uuid.UUID, file_url: str) -> None:
        _celery.send_task(
            "ai_worker.tasks.ocr_task.process_ocr",
            args=[str(record_id), file_url],
            queue="image",
        )

    def _dispatch_image_analyze(self, record_id: uuid.UUID, image_bytes: bytes, user_id: int) -> None:
        _celery.send_task(
            "ai_worker.tasks.image_task.classify_pill",
            kwargs={
                "record_id": str(record_id),
                "user_id": str(user_id),
                "image_bytes": base64.b64encode(image_bytes).decode("utf-8"),
            },
            queue="image",
        )
