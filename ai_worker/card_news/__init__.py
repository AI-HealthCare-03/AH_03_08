from ai_worker.card_news.base import CardNewsGenerator
from ai_worker.core.config import Config


def get_card_news_generator(config: Config) -> CardNewsGenerator:
    return CardNewsGenerator()
