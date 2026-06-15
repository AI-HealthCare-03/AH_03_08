import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )
        self.sender = settings.SES_SENDER_EMAIL

    async def send_verification_email(self, to_email: str, token: str):
        verify_url = f"{settings.ALLOWED_ORIGINS}/auth/verify-email?token={token}"
        try:
            self.client.send_email(
                Source=self.sender,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "[MediLog] 이메일 인증", "Charset": "UTF-8"},
                    "Body": {
                        "Html": {
                            "Data": f"""
                            <h2>MediLog 이메일 인증</h2>
                            <p>아래 링크를 클릭하여 이메일 인증을 완료하세요.</p>
                            <a href="{verify_url}">이메일 인증하기</a>
                            <p>링크는 24시간 동안 유효합니다.</p>
                            """,
                            "Charset": "UTF-8",
                        }
                    },
                },
            )
        except ClientError as e:
            raise RuntimeError(f"이메일 발송 실패: {e.response['Error']['Message']}") from e

    def send_notification_email(self, to_email: str, title: str, scheduled_time: str):
        try:
            self.client.send_email(
                Source=self.sender,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "[MediLog] 복약 알림 등록", "Charset": "UTF-8"},
                    "Body": {
                        "Html": {
                            "Data": f"""
                            <h2>복약 알림이 등록되었습니다.</h2>
                            <p><b>{title}</b></p>
                            <p>복용 시간: {scheduled_time}</p>
                            <p>MediLog 앱에서 복약 현황을 확인하세요.</p>
                            """,
                            "Charset": "UTF-8",
                        }
                    },
                },
            )
        except ClientError as e:
            raise RuntimeError(f"알림 이메일 발송 실패: {e.response['Error']['Message']}") from e