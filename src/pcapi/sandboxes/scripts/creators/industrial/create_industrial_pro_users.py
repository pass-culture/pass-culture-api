from datetime import datetime
from datetime import timedelta

from pcapi.model_creators.generic_creators import create_user
from pcapi.repository import repository
from pcapi.utils.logger import logger


PROS_COUNT = 1
departement_codes = ["93", "97"]


def create_industrial_pro_users():
    logger.info("create_industrial_pro_users")

    users_by_name = {}

    for departement_code in departement_codes:

        for pro_count in range(PROS_COUNT):
            email = "pctest.pro{}.{}@btmx.fr".format(departement_code, pro_count)
            users_by_name["pro{} {}".format(departement_code, pro_count)] = create_user(
                reset_password_token_validity_limit=datetime.utcnow() + timedelta(hours=24),
                is_beneficiary=False,
                date_of_birth=None,
                departement_code=str(departement_code),
                email=email,
                first_name="PC Test Pro",
                is_admin=False,
                last_name="{} {}".format(departement_code, pro_count),
                postal_code="{}100".format(departement_code),
                public_name="PC Test Pro {} {}".format(departement_code, pro_count),
            )

    repository.save(*users_by_name.values())

    logger.info("created {} users".format(len(users_by_name)))

    return users_by_name
