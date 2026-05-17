from enum import IntEnum, StrEnum


class RecordType(IntEnum):
    PRESCRIPTION = 0 # 진료처방전
    DRUG_BAG = 1 # 조제약봉투
    PILL = 2 # 알약


class RecordStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
