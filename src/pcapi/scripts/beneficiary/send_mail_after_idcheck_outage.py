from datetime import datetime
import logging
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import not_
from sqlalchemy.orm import Query

from pcapi.core import mails
from pcapi.core.bookings import conf
from pcapi.core.users import constants
from pcapi.core.users.api import create_id_check_token
from pcapi.core.users.models import Token
from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription_validator import ELIGIBLE_DEPARTMENTS
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription_validator import EXCLUDED_DEPARTMENTS
from pcapi.models import UserOfferer
from pcapi.models.feature import FeatureToggle
from pcapi.repository import feature_queries
from pcapi.utils.urls import generate_firebase_dynamic_link


logger = logging.getLogger(__name__)


def get_newly_eligible_user_email_data(user: User, token: Token, is_native_app_link=True) -> dict:
    expiration_timestamp = int(token.expirationDate.timestamp())
    if is_native_app_link:
        email_link = generate_firebase_dynamic_link(
            path="id-check",
            params={"licenceToken": token.value, "expirationTimestamp": expiration_timestamp, "email": user.email},
        )
    else:
        email_link = f"https://id-check-front.passculture.app/?licence_token={token.value}"
    limit_configuration = conf.LIMIT_CONFIGURATIONS[conf.get_current_deposit_version()]
    deposit_amount = limit_configuration.TOTAL_CAP
    return {
        "Mj-TemplateID": 2902675,
        "Mj-TemplateLanguage": True,
        "Mj-trackclick": 1,
        "Vars": {
            "nativeAppLink": email_link,
            "depositAmount": int(deposit_amount),
        },
    }


def send_newly_eligible_user_email(user: User, is_native_app_link=True) -> bool:
    token = create_id_check_token(user)
    if not token:
        logger.warning("Could not create token for user %s to notify its elibility", user.id)
        return False
    data = get_newly_eligible_user_email_data(user, token, is_native_app_link=is_native_app_link)
    return mails.send(recipients=[user.email], data=data)


# Basically, this is _is_postal_code_eligible refactored for queries
def _filter_by_eligible_postal_code(query: Query) -> Query:
    if not feature_queries.is_active(FeatureToggle.WHOLE_FRANCE_OPENING):
        eligible_departments_arg = "(%s)%%" % ("|".join(ELIGIBLE_DEPARTMENTS))
        return query.filter(User.postalCode.op("SIMILAR TO")(eligible_departments_arg))
    # New behaviour: all departments are eligible, except a few.
    excluded_departments_arg = "(%s)%%" % ("|".join(EXCLUDED_DEPARTMENTS))
    return query.filter(not_(User.postalCode.op("SIMILAR TO")(excluded_departments_arg)))


def _get_eligible_users_created_between(
    start_date: datetime, end_date: datetime, max_number: Optional[int] = None
) -> list[User]:
    today = datetime.combine(datetime.today(), datetime.min.time())
    query = User.query.outerjoin(UserOfferer).filter(
        User.dateCreated.between(start_date, end_date),
        User.isBeneficiary == False,  # not already beneficiary
        User.isAdmin == False,  # not an admin
        UserOfferer.userId.is_(None),  # not a pro
        User.dateOfBirth > today - relativedelta(years=(constants.ELIGIBILITY_AGE + 1)),  # less than 19yo
        User.dateOfBirth <= today - relativedelta(years=constants.ELIGIBILITY_AGE),  # more than or 18yo
    )
    query = _filter_by_eligible_postal_code(query)
    if max_number:
        query = query.limit(max_number)
    return query.order_by(User.dateCreated).all()


def send_mail_to_potential_beneficiaries(
    start_date: datetime, end_date: datetime, max_number: Optional[int] = None, is_native_app_link=True
) -> None:
    # BEWARE: start_date and end_date are expected to be in UTC
    logger.info(
        (
            "Sending IDCheck mails to %s new users created between %s and %s "
            "to notify them they can start the idcheck process - if they eligible"
        ),
        (max_number or ""),
        start_date,
        end_date,
    )
    user = None
    try:
        for i, user in enumerate(_get_eligible_users_created_between(start_date, end_date, max_number)):
            if user.is_eligible:
                if not send_newly_eligible_user_email(user, is_native_app_link=is_native_app_link):
                    print(f"Could not send mail to user {user.id}")
            if i % 100:
                print(f"Processed {i} users")
    finally:
        if user:
            print("Last user creation datetime: %s" % user.dateCreated)
        else:
            print("No user found within the timeframe")
