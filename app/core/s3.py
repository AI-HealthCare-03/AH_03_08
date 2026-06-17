import boto3
from botocore.exceptions import ClientError

from app.core import config

_PRESIGNED_URL_EXPIRES = 3600  # 1시간


def _s3_client():
    return boto3.client(
        "s3",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY,
        aws_secret_access_key=config.AWS_SECRET_KEY,
    )


def upload_to_s3(file_content: bytes, file_name: str) -> str:
    """S3에 파일 업로드 후 raw URL 반환"""
    s3 = _s3_client()
    key = f"uploads/{file_name}"
    try:
        s3.put_object(Bucket=config.S3_BUCKET_NAME, Key=key, Body=file_content)
        return f"https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        raise RuntimeError(f"S3 업로드 실패: {e}") from e


def get_presigned_url(s3_url: str, expires_in: int = _PRESIGNED_URL_EXPIRES) -> str:
    """raw S3 URL → presigned URL (프라이빗 버킷 이미지 조회용)"""
    if not s3_url or not s3_url.startswith("http"):
        return s3_url
    key = s3_url.split(".amazonaws.com/")[-1]
    s3 = _s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": config.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
