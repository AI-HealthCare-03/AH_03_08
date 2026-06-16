from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` MODIFY COLUMN `gender` VARCHAR(10) NULL;
        ALTER TABLE `users` MODIFY COLUMN `birth_date` DATE NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE `users` SET `gender` = 'MALE' WHERE `gender` IS NULL;
        UPDATE `users` SET `birth_date` = '2000-01-01' WHERE `birth_date` IS NULL;
        ALTER TABLE `users` MODIFY COLUMN `gender` VARCHAR(10) NOT NULL;
        ALTER TABLE `users` MODIFY COLUMN `birth_date` DATE NOT NULL;"""
