from datetime import date
from datetime import datetime
from datetime import time
import uuid

from dateutil.relativedelta import relativedelta
import factory
from factory.declarations import LazyAttribute

import pcapi.core.bookings.conf as bookings_conf
from pcapi.core.testing import BaseFactory
import pcapi.core.users.models
from pcapi.models import BeneficiaryImport
from pcapi.models import BeneficiaryImportStatus
from pcapi.models import user_session
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.models.deposit import DepositType
from pcapi.utils import crypto

from . import constants
from . import models


DEFAULT_PASSWORD = "user@AZERTY123"

GIVEN_DEPOSIT_BY_AGE = {
    15: DepositType.GRANT_15,
    16: DepositType.GRANT_16,
    17: DepositType.GRANT_17,
    18: DepositType.GRANT_18,
}


class UserFactory(BaseFactory):
    class Meta:
        model = pcapi.core.users.models.User

    email = factory.Sequence("jean.neige{}@example.com".format)
    address = factory.Sequence("{} place des noces rouges".format)
    city = "La Rochelle"
    dateOfBirth = datetime.combine(date(1980, 1, 1), time(0, 0))
    departementCode = "75"
    firstName = "Jean"
    lastName = "Neige"
    publicName = "Jean Neige"
    isEmailValidated = True
    isBeneficiary = False
    isAdmin = False
    roles = []
    hasSeenProTutorials = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._create(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._build(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance


class AdminFactory(BaseFactory):
    class Meta:
        model = pcapi.core.users.models.User

    email = factory.Sequence("un.admin{}@example.com".format)
    address = factory.Sequence("{} rue des détectives".format)
    city = "Bordeaux"
    departementCode = "33"
    firstName = "Frank"
    lastName = "Columbo"
    publicName = "Frank Columbo"
    isEmailValidated = True
    isAdmin = True
    isBeneficiary = False
    roles = [pcapi.core.users.models.UserRole.ADMIN]
    hasSeenProTutorials = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._create(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._build(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance


class BeneficiaryGrant18Factory(BaseFactory):
    class Meta:
        model = pcapi.core.users.models.User

    email = factory.Sequence("jeanne.doux{}@example.com".format)
    address = factory.Sequence("{} rue des machines".format)
    city = "Paris"
    dateOfBirth = datetime.combine(date.today(), time(0, 0)) - relativedelta(years=18, months=1)
    departementCode = "75"
    firstName = "Jeanne"
    lastName = "Doux"
    isEmailValidated = True
    isAdmin = False
    isBeneficiary = True
    roles = [pcapi.core.users.models.UserRole.BENEFICIARY]
    hasSeenProTutorials = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        if "publicName" not in kwargs and kwargs["firstName"] and kwargs["lastName"]:
            kwargs["publicName"] = "%s %s" % (kwargs["firstName"], kwargs["lastName"])
        instance = super()._create(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        if "publicName" not in kwargs and kwargs["firstName"] and kwargs["lastName"]:
            kwargs["publicName"] = "%s %s" % (kwargs["firstName"], kwargs["lastName"])
        instance = super()._build(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance

    @factory.post_generation
    def deposit(obj, create, extracted, **kwargs):  # pylint: disable=no-self-argument
        if not create:
            return None

        if "dateCreated" not in kwargs:
            kwargs["dateCreated"] = obj.dateCreated

        return DepositGrantFactory(user=obj, **kwargs)


class UnderageBeneficiaryFactory(BeneficiaryGrant18Factory):
    class Params:
        subscription_age = 15

    roles = [pcapi.core.users.models.UserRole.UNDERAGE_BENEFICIARY]
    dateOfBirth = LazyAttribute(
        lambda o: datetime.combine(date.today(), time(0, 0)) - relativedelta(years=o.subscription_age, months=5)
    )
    dateCreated = LazyAttribute(lambda o: o.dateOfBirth + relativedelta(years=o.subscription_age, hours=12))

    @factory.post_generation
    def deposit(obj, create, extracted, **kwargs):  # pylint: disable=no-self-argument
        if not create:
            return None

        if "dateCreated" not in kwargs:
            kwargs["dateCreated"] = obj.dateCreated

        return DepositGrantFactory(
            user=obj,
            **kwargs,
            type=GIVEN_DEPOSIT_BY_AGE.get(relativedelta(obj.dateCreated, obj.dateOfBirth).years, DepositType.GRANT_15),
        )


class ProFactory(BaseFactory):
    class Meta:
        model = pcapi.core.users.models.User

    email = factory.Sequence("ma.librairie{}@example.com".format)
    address = factory.Sequence("{} rue des cinémas".format)
    city = "Toulouse"
    departementCode = "31"
    firstName = "René"
    lastName = "Coty"
    publicName = "René Coty"
    isEmailValidated = True
    isAdmin = False
    isBeneficiary = False
    roles = [pcapi.core.users.models.UserRole.PRO]
    hasSeenProTutorials = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._create(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        password = kwargs.get("password", DEFAULT_PASSWORD)
        kwargs["password"] = crypto.hash_password(password)
        instance = super()._build(model_class, *args, **kwargs)
        instance.clearTextPassword = DEFAULT_PASSWORD
        return instance


class TokenFactory(BaseFactory):
    class Meta:
        model = models.Token

    value = factory.Sequence("XYZ{0}".format)


class ResetPasswordToken(TokenFactory):
    type = models.TokenType.RESET_PASSWORD
    expirationDate = factory.LazyFunction(lambda: datetime.now() + constants.RESET_PASSWORD_TOKEN_LIFE_TIME)


class EmailValidationToken(TokenFactory):
    type = models.TokenType.EMAIL_VALIDATION
    expirationDate = factory.LazyFunction(lambda: datetime.now() + constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME)


class IdCheckToken(TokenFactory):
    type = models.TokenType.ID_CHECK
    creationDate = factory.LazyFunction(datetime.now)
    expirationDate = factory.LazyFunction(lambda: datetime.now() + constants.ID_CHECK_TOKEN_LIFE_TIME)


class UserSessionFactory(BaseFactory):
    class Meta:
        model = user_session.UserSession

    uuid = factory.LazyFunction(uuid.uuid4)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        try:
            user = kwargs.pop("user")
        except KeyError:
            raise ValueError('UserSessionFactory requires a "user" argument.')
        kwargs["userId"] = user.id
        return super()._create(model_class, *args, **kwargs)


class FavoriteFactory(BaseFactory):
    class Meta:
        model = models.Favorite

    offer = factory.SubFactory("pcapi.core.offers.factories.OfferFactory")
    user = factory.SubFactory(UserFactory)


class BeneficiaryImportFactory(BaseFactory):
    class Meta:
        model = BeneficiaryImport

    applicationId = factory.Sequence(lambda n: n)
    beneficiary = factory.SubFactory("pcapi.core.users.factories.UserFactory")
    source = BeneficiaryImportSources.jouve.value


class BeneficiaryImportStatusFactory(BaseFactory):
    class Meta:
        model = BeneficiaryImportStatus

    status = ImportStatus.CREATED.value
    date = factory.Faker("date_time_between", start_date="-30d", end_date="-1d")
    detail = factory.Faker("sentence", nb_words=3)
    beneficiaryImport = factory.SubFactory(BeneficiaryImportFactory)
    author = factory.SubFactory("pcapi.core.users.factories.UserFactory")


# DepositFactory in core module to avoid import loops
class DepositGrantFactory(BaseFactory):
    class Meta:
        model = models.Deposit

    user = factory.SubFactory(BeneficiaryGrant18Factory)
    source = "public"
    type = DepositType.GRANT_18

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if "amount" in kwargs:
            raise ValueError("You cannot directly set deposit amount: set version instead")
        version = kwargs.get("version", bookings_conf.get_current_deposit_version_for_type(kwargs["type"]))
        deposit_configuration = bookings_conf.get_limit_configuration_for_type_and_version(kwargs["type"], version)
        amount = deposit_configuration.TOTAL_CAP
        kwargs["version"] = version
        kwargs["amount"] = amount
        if "expirationDate" not in kwargs:
            beneficiary = kwargs.get("user")
            kwargs["expirationDate"] = deposit_configuration.compute_expiration_date(beneficiary.dateOfBirth)
        return super()._create(model_class, *args, **kwargs)
