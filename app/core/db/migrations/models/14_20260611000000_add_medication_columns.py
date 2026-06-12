from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `medications`
            ADD COLUMN `drug_class` VARCHAR(200),
            ADD COLUMN `memo` LONGTEXT;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `medications`
            DROP COLUMN `drug_class`,
            DROP COLUMN `memo`;
    """
