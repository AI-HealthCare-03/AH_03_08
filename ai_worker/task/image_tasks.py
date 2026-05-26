from ai_worker.celery_app import celery_app


@celery_app.task(name="ai_worker.task.image_tasks.generate_card_image_task")
def generate_card_image_task(asset_id: int, guide_id: int):
    # TODO: 카드뉴스 이미지 생성 구현
    pass


@celery_app.task(name="ai_worker.task.image_tasks.generate_daily_tip_card_task")
def generate_daily_tip_card_task(tip_id: str, tip_data: dict, user_id: int):
    # TODO: 데일리 TIP 카드 이미지 생성 구현
    pass
