from datetime import datetime
from typing import List
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import extract
from sqlalchemy import func
from sqlalchemy.orm import load_only

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.models import User


AGE18_ELIGIBLE_BIRTH_DATE = datetime.utcnow() - relativedelta(years=ELIGIBILITY_AGE_18)


def get_users_who_will_turn_eighteen_in_one_month() -> Optional[List[User]]:
    _18_YEARS_IN_1_MONTHS = (
        datetime.utcnow() - relativedelta(years=ELIGIBILITY_AGE_18) + relativedelta(days=30)
    ).date()
    return (
        User.query.yield_per(1000)
        .options(load_only(User.email))
        .filter(func.date(User.dateOfBirth) == _18_YEARS_IN_1_MONTHS)
        .all()
    )


def get_users_beneficiary_three_months_before_credit_expiration() -> Optional[List[User]]:
    # not tested yet
    IN_3_MONTHS = (datetime.utcnow() + relativedelta(days=90)).date()
    return (
        User.query.yield_per(1000)
        .options(load_only(User.email))
        .filter(func.date(User.deposit_expiration_date) == IN_3_MONTHS)
        .all()
    )


def get_inactive_user_since_thirty_days() -> Optional[List[User]]:
    _30_DAYS_AGO = (datetime.utcnow() - relativedelta(days=30)).date()
    return (
        User.query.yield_per(1000)
        .options(load_only(User.email))
        .filter(func.date(User.lastConnectionDate) == _30_DAYS_AGO)
        .filter(User.is_beneficiary == True)
        .all()
    )


def get_users_by_month_created_one_year_before() -> Optional[List[User]]:
    # example : get all users created during january from one year ago
    _12_MONTHS_AGO = datetime.utcnow() - relativedelta(months=12)
    return (
        User.query.yield_per(1000)
        .options(load_only(User.email))
        .filter(extract("year", User.dateCreated) == _12_MONTHS_AGO.year)
        .filter(extract("month", User.dateCreated) == _12_MONTHS_AGO.month)
        .all()
    )
