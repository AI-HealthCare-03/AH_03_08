from ai_worker.celery_app import celery_app


@celery_app.task(name="ai_worker.tasks.tts_tasks.generate_tts_task")
def generate_tts_task(asset_id: int, guide_id: int, text: str):
    # TODO: TTS 생성 구현
    pass
