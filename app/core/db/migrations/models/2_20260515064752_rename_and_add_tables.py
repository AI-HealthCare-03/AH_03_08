from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> None:
    await db.execute_script("""
        CREATE TABLE IF NOT EXISTS `medications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `drug_name` VARCHAR(200) NOT NULL,
    `dosage` VARCHAR(100),
    `frequency` VARCHAR(100),
    `instructions` LONGTEXT,
    `warnings` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `medical_record_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_medicati_medical__494c8c82` FOREIGN KEY (`medical_record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `underlying_diseases` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `underlying_disease_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_underlyi_users_0044808f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `allergies` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `allergy_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_allergie_users_cc13c577` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;""")


async def downgrade(db: BaseDBAsyncClient) -> None:
    await db.execute_script("""
        DROP TABLE IF EXISTS `medications`;
        DROP TABLE IF EXISTS `underlying_diseases`;
        DROP TABLE IF EXISTS `allergies`;""")


MODELS_STATE = (
    "eJztXFtz2jgU/iuMn9qZbIdASLJ9I4SkbLlkgOx2ehmPsIXx1Bdqy0mZTv77SvJVxjbGWB"
    "li/FJiWT1H+o58Lp9k/xF0U4aa/eHRhpbwsfFHAOs1/vWahbOGYAAdhi1uR9yMwEKj7Q5u"
    "oB1VQ4a/oY3bvv3AlzowgAJlfGk4moYbwMJGFpAQblkCzYa4af1TXKpQk6lmX5EqE2mOof"
    "5yyDWyHNJVhkvgaCgU56qTwx6k3RuUL19eiJKpOboRypVNCQ9DNZRQkgINaAEUlUVHJaLN"
    "mo7oRlUGBrqjI8U3JdMgM1ENZNOBK6TTX3+3Wu32VavZvrzuXFxdda6b17gvHc72rasXOi"
    "VbstQ1Uk0jHMx6g1amEajGSgR3IuGQXK10YIP7wXhOOpgYWdcepOHlJXmmSw/v0EgtPdZi"
    "tsxYiwwQiDSFhoI6UDXGVgHu6cbyu+yyViB8h8H8/8xarLcCVqq9dPBb1KChoBW+vGjmNQ"
    "WWkWGKf7vT3qfu9N1F8z1rj7F3p0VvEcuECK6AvYKyuAa2/WxaMi8sE9RwRvW8dV0urFhg"
    "Kq70Hgss/eWEpi+bM4StkhdmK31htrYWJp6I7Pp5HgiG0gtj2DccneI4wBACQ4I78bzchl"
    "MYdYf9jw3y73fjru9eub9CUZgvU1G+jIO8UC20ksGGF8xR+YWAvsV30xZr3sWJowdEqg4/"
    "kD8y8LvtzvsxfNZYDhSxoRf8lmJcB2+/eF6yWzxP94rn8fWm2iJOv9SnXZ7Ry4H2B5NRUA"
    "jJG9PUIDAOXXQLLCYrbZpMhuS2btu/NDePiiVR48fRTR/DS9HFnVTE5FYsprKuGjsg9VuK"
    "YeorOA1INWAjUTOVnaCmPvTAQaZomM/JMPsFRRRlVmdhZ0kcXakOk/whRGaE14LMrpQkY8"
    "wHo/5s3h09MBYhHpbcadHWTax1K3AFQhr/DeafGuSy8XUydiOjaSPFohrDfvOvMUNKFiSI"
    "iQDxMWTi88Iq5WJJAauQJ4a28RZTmZYNF+cRG9ZZy+UZNmf1zuqs7crDriuoKiskSnoJ2V"
    "aSl2XkFzLhnWaCVCImr72WREhWKjp5vBn2Gw/Tfm8wG0zGLPz0JhvDpv3uMAblszvVnwon"
    "KBn51YbSxI/SSlxb5pNaTk2ahOe2kiqX9+5s1TIIp3Qwc/GtBxdUzZJxxALTS6omRfJHmk"
    "IXShGZCkQryqdTAnUBpJ/PwJJFhn6N5EkrgEQb2jYWZpdZ6BYqF7zB3n2eQg3Q+RV3D96e"
    "ATYnmrnzE/y14ssLY22EfXLwQ1hJJO7JzHJhYEHJtORKgjCCsioBbUpnmAoG8+TEdiWIQg"
    "bRPDtXAfbB1lW4ziqxd3WoL20nUKSHuNJ2Ohfa9sjQnZtUkaLDLpcFzIclnjRePNBNTnrd"
    "Wa97SzMWCzwH5qdD88JdLMcyLZynGZ/hZhdXvecj5O/C5nQjR4qbO7jXRS6/8zlobxQPFz"
    "m7vLeA802JxEVDEXLjH3ULoZYqZ6s6NRnRKiq+D+eQtSapKQTrHP4+uLDKhnHe/zJnqAIf"
    "vnej7pf3TJE1nIzv/e4RuHvDyU2cd1WX0EYbDXJFOUHLKYFsO7oOrDK2/JLA9aSLCINzas"
    "gCTYOWshFxvmjgGZeROSdBnKSmEMz/zCbjQ2F+NPDdb9htobOGptroRwboRF826HF8z1je"
    "kAiIg47HLavUZeKhQ5Ihl1TDJkGfruyEDVDvsVSTi2dyYx4nH9x0RxMZRdWrMNkCkiOeEf"
    "HFmJa3d8j02IlQ/0E/FuJrXx4U2DZElaQAKRfXJdM7lP/rQkuVVkIeAtDrehZhAEHQVAkG"
    "MPH0+m6v0jq/uLq4bl9eBM4kaCnJh7zeofQnaPnPFw8vHxHPm3LpdErmXDqddNKF3IvVU/"
    "hp4gSiJ7qCW4Ox2ghBo3BevjMJD8WfVvlTTtaxz/aSG6hy7zEFcY3daBLDcF6JYPMGi4E9"
    "tpvK4kB57Ju4y+lVt02yN64Pjtr00XB18oo5jAbOS7tTcuTppAeezlbcWaoaFB2rjDfzkl"
    "i4qHjuMJaOYxaQ2xG8JteqSa5FHSiXF9wi8qsWRV81/SKMyQjaNqCF6u78K9o/moBRZkl3"
    "b1QnAzuhl9UjO6ghgXaEqZk3utdNzvLwigenaJapcUvOfNncGYGyCYEMPqAYHSAIhQA8lA"
    "x4o3v++U5Z3Xq5QX2+Kvl8VZ3mVjTNZYMRD8fNaqj3PTmlwH5wz5sCR5IBNgWObq7WKfAR"
    "Lam9UuD6KHxkvec+Cl/2qdaa0M2oFpCKSikXkhjIQDb3pKz0rCwrLavzslPJy+rvJ1TTri"
    "XSykl+r8qscn1Q8/gLlugbWSGTXrWjibEthEPOJrLvGuYp3rbeTgzKN/a4dnUKuDfoqepK"
    "jUOldvj+hPseQ44zJM1CYSMmv9CyxnEj14dL3RjSbl1dBlGDXCTECeFh2p/1poOH+WAyxl"
    "P7btxOH+/Fm+79x8b5d+NhMBziQkbYN5TMRt3hcPvTfPn49of++HYwvq8p94wP8EiWSJ5G"
    "/0VNHh/hiak4pX2hNbBsXOsQX8EJ3ZiG0zqBW5MUJ1DM1lXYsVdhp/qZrMzq6+V/WIFoDQ"
    "=="
)
