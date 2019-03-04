from models.pc_object import PcObject
from sandboxes.scripts.utils.helpers import get_password_from_email
from tests.test_utils import create_user
from utils.logger import logger

departement_codeS = ["93", "97"]
WEBAPP_TAGS = [
    "has-signed-up",
    "has-booked-activation",
    "has-confirmed-activation",
    "has-booked-some",
    "has-no-more-money"
]


def create_industrial_webapp_users():
    logger.info('create_industrial_webapp_users')

    users_by_name = {}

    validation_prefix, validation_suffix = 'AZERTY', 123
    validation_suffix += 1

    # loop on department and tags
    for departement_code in departement_codeS:

        for tag in WEBAPP_TAGS:
            short_tag = "".join([chunk[0].upper() for chunk in tag.split('-')])

            if tag == "has-signed-up":
                reset_password_token = '{}{}'.format(validation_prefix, validation_suffix)
                validation_suffix += 1
            else:
                reset_password_token = None

            email = "pctest.jeune{}.{}@btmx.fr".format(departement_code, tag)
            users_by_name['jeune{} {}'.format(departement_code, tag)] = create_user(
                public_name="PC Test Jeune {} {}".format(departement_code, short_tag), first_name="PC Test Jeune",
                last_name="{} {}".format(departement_code, short_tag), postal_code="{}100".format(departement_code),
                departement_code=str(departement_code), email=email, reset_password_token=reset_password_token)

    PcObject.check_and_save(*users_by_name.values())

    logger.info('created {} users'.format(len(users_by_name)))

    return users_by_name
