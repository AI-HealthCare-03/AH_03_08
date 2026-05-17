from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.application.medical_record.dto.record_dto import UpdateRecordCommand, UploadRecordCommand
from app.application.medical_record.use_cases.get_record import GetRecordUseCase
from app.application.medical_record.use_cases.list_records import ListRecordsUseCase
from app.application.medical_record.use_cases.update_record import UpdateRecordUseCase
from app.application.medical_record.use_cases.upload_record import UploadRecordUseCase
from app.dependencies.security import get_request_user
from app.domain.medical_record.repository import AbstractRecordRepository
from app.domain.medical_record.value_objects import RecordType
from app.infrastructure.medical_record.repository import TortoiseRecordRepository
from app.models.users import User
from app.presentation.api.v1.records.schemas import (
    RecordListResponseSchema,
    RecordResponseSchema,
    UpdateRecordRequestSchema,
)

records_router = APIRouter(prefix="/records", tags=["records"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def get_record_repository() -> AbstractRecordRepository:
    return TortoiseRecordRepository()


def get_upload_use_case(
    repo: Annotated[AbstractRecordRepository, Depends(get_record_repository)],
) -> UploadRecordUseCase:
    return UploadRecordUseCase(repo)


def get_get_record_use_case(
    repo: Annotated[AbstractRecordRepository, Depends(get_record_repository)],
) -> GetRecordUseCase:
    return GetRecordUseCase(repo)


def get_list_records_use_case(
    repo: Annotated[AbstractRecordRepository, Depends(get_record_repository)],
) -> ListRecordsUseCase:
    return ListRecordsUseCase(repo)


def get_update_use_case(
    repo: Annotated[AbstractRecordRepository, Depends(get_record_repository)],
) -> UpdateRecordUseCase:
    return UpdateRecordUseCase(repo)


@records_router.post("/upload", response_model=RecordResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def upload_record(
    record_type: Annotated[RecordType, Form()],
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[UploadRecordUseCase, Depends(get_upload_use_case)],
) -> RecordResponseSchema:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JPG, PNG, PDF 파일만 업로드 가능합니다.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="파일 크기는 10MB를 초과할 수 없습니다.")

    command = UploadRecordCommand(
        user_id=user.id,
        record_type=record_type,
        file_content=content,
        original_filename=file.filename or "unknown",
    )
    record = await use_case.execute(command)
    return RecordResponseSchema.model_validate(record)


@records_router.get("", response_model=RecordListResponseSchema, status_code=status.HTTP_200_OK)
async def list_records(
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[ListRecordsUseCase, Depends(get_list_records_use_case)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RecordListResponseSchema:
    records, total = await use_case.execute(user_id=user.id, page=page, limit=limit)
    return RecordListResponseSchema(
        total=total,
        page=page,
        items=[RecordResponseSchema.model_validate(r) for r in records],
    )


@records_router.get("/{record_id}", response_model=RecordResponseSchema, status_code=status.HTTP_200_OK)
async def get_record(
    record_id: UUID,
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[GetRecordUseCase, Depends(get_get_record_use_case)],
) -> RecordResponseSchema:
    record = await use_case.execute(record_id=record_id, user_id=user.id)
    return RecordResponseSchema.model_validate(record)


@records_router.put("/{record_id}", response_model=RecordResponseSchema, status_code=status.HTTP_200_OK)
async def update_record(
    record_id: UUID,
    body: UpdateRecordRequestSchema,
    user: Annotated[User, Depends(get_request_user)],
    use_case: Annotated[UpdateRecordUseCase, Depends(get_update_use_case)],
) -> RecordResponseSchema:
    command = UpdateRecordCommand(
        record_id=record_id,
        user_id=user.id,
        parsed_data=body.parsed_data,
    )
    record = await use_case.execute(command)
    return RecordResponseSchema.model_validate(record)
