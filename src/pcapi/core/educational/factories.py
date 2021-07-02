import datetime

import factory

from pcapi.core.testing import BaseFactory

from . import models


class EducationalInstitutionFactory(BaseFactory):
    class Meta:
        model = models.EducationalInstitution

    institutionId = factory.Sequence("{}470009E".format)


class EducationalYearFactory(BaseFactory):
    class Meta:
        model = models.EducationalYear

    adageId = factory.Sequence(lambda number: str(6 + number))
    beginningDate = factory.Sequence(
        lambda number: datetime.datetime(2020, 9, 1) + datetime.timedelta(days=365 * number)
    )
    expirationDate = factory.Sequence(
        lambda number: datetime.datetime(2021, 8, 31) + datetime.timedelta(days=365 * number)
    )


class EducationalDepositFactory(BaseFactory):
    class Meta:
        model = models.EducationalDeposit

    educationalInstitution = factory.SubFactory(EducationalInstitutionFactory)
    educationalYear = factory.SubFactory(EducationalYearFactory)


class EducationalBookingFactory(BaseFactory):
    class Meta:
        model = models.EducationalBooking

    educationalInstitution = factory.SubFactory(EducationalInstitutionFactory)
    educationalYear = factory.SubFactory(EducationalYearFactory)
