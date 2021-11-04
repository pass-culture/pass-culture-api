from datetime import datetime
from typing import List
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import func

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.models import User


AGE18_ELIGIBLE_BIRTH_DATE = datetime.utcnow() - relativedelta(years=ELIGIBILITY_AGE_18)


def get_users_who_will_turn_eighteen_in_one_month() -> Optional[List[User]]:
    _18_YEARS_IN_1_MONTHS = (
        datetime.utcnow() - relativedelta(years=ELIGIBILITY_AGE_18) + relativedelta(days=30)
    ).date()
    return User.query.filter(func.date(User.dateOfBirth) == _18_YEARS_IN_1_MONTHS).all()


def get_users_beneficiary_three_months_before_credit_expiration() -> Optional[List[User]]:
    # not tested yet
    IN_3_MONTHS = (datetime.utcnow() + relativedelta(days=90)).date()
    return User.query.filter(func.date(User.deposit_expiration_date) == IN_3_MONTHS).all()


def get_inactive_user_since_thirty_days() -> Optional[List[User]]:
    # not tested yet
    _30_DAYS_AGO = (datetime.utcnow() - relativedelta(days=30)).date()
    return User.query.filter(func.date(User.lastConnectionDate) >= _30_DAYS_AGO).all()


def get_users_having_one_year_since_subscription_by_month() -> Optional[List[User]]:
    # not tested yet
    # example : get all users subscribed in january from one year ago
    _12_MONTHS_AGO = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=365)
    _11_MONTHS_AGO = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=335)
    return (
        User.query.filter(func.date(User.deposit_activation_date) >= _12_MONTHS_AGO)
        .filter(func.date(User.deposit_activation_date) <= _11_MONTHS_AGO)
        .all()
    )
