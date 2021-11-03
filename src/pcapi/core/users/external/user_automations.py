from datetime import datetime

from dateutil.relativedelta import relativedelta

from pcapi.core.users.constants import ELIGIBILITY_AGE_18
from pcapi.models import User


AGE18_ELIGIBLE_BIRTH_DATE = datetime.utcnow() - relativedelta(years=ELIGIBILITY_AGE_18)
_18_YEARS_AGO = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(
    years=ELIGIBILITY_AGE_18
)
_19_YEARS_AGO = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(years=19)


def get_users_who_turned_eighteen_today():
    return User.query.filter(User.dateOfBirth.between(_19_YEARS_AGO, _18_YEARS_AGO)).all()
