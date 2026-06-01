from ai_worker.card_news.base import CardNewsGenerator
from ai_worker.core.config import Config


def get_card_news_generator(config: Config) -> CardNewsGenerator:
    return CardNewsGenerator(
        bucket_name=config.S3_BUCKET_NAME,
        aws_access_key=config.AWS_ACCESS_KEY,
        aws_secret_key=config.AWS_SECRET_KEY,
        aws_region=config.AWS_REGION,
    )