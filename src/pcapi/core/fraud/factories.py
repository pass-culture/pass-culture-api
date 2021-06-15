import random

import factory

from pcapi.core import testing
import pcapi.core.users.factories as users_factories

from . import models


JOUVE_CTRL_VALUES = ["OK", "KO"]


class JouveContentFactory(factory.Factory):
    class Meta:
        model = models.JouveContent

    activity = random.choice(["Etudiant"])
    address = "25 rue du moulin vert"
    birthDate = factory.Faker("date", pattern="%d/%m/%Y")
    birthLocationCtrl = random.choice(JOUVE_CTRL_VALUES)
    bodyBirthDateCtrl = random.choice(JOUVE_CTRL_VALUES)
    bodyBirthDateLevel = factory.Faker("pyint", max_value=100)
    bodyFirstNameCtrl = random.choice(JOUVE_CTRL_VALUES)
    bodyFirstNameLevel = factory.Faker("pyint", max_value=100)
    bodyNameLevel = factory.Faker("pyint", max_value=100)
    bodyNameCtrl = random.choice(JOUVE_CTRL_VALUES)
    bodyPieceNumber = factory.Faker("pyint")
    bodyPieceNumberCtrl = random.choice(JOUVE_CTRL_VALUES)
    bodyPieceNumberLevel = factory.Faker("pyint", max_value=100)
    city = "Paris"
    creatorCtrl = random.choice(JOUVE_CTRL_VALUES)
    id = factory.Faker("pyint")
    email = factory.Sequence("jeanne.doux{}@example.com".format)
    firstName = factory.Sequence("Jeanne{}".format)
    gender = random.choice(["Male", "Female"])
    initialNumberCtrl = factory.Faker("pyint")
    initialSizeCtrl = random.choice(JOUVE_CTRL_VALUES)
    lastName = factory.Sequence("doux{}".format)
    phoneNumber = factory.Sequence("+3361212121{}".format)
    postalCode = "75008"
    posteCodeCtrl = "75"
    serviceCodeCtrl = factory.Faker("pystr")


USERPROFILING_RATING = ["neutral", "low", "good"]
USERPROFILING_RESULTS = ["sucess", "failure"]


class UserProfilingFraudDataFactory(factory.Factory):
    class Meta:
        model = models.UserProfilingFraudData

    account_email_result = random.choice(USERPROFILING_RESULTS)
    account_email_score = factory.Faker("pyint")
    account_telephone_result = random.choice(USERPROFILING_RESULTS)
    account_telephone_score = factory.Faker("pyint")
    bb_bot_rating = random.choice(USERPROFILING_RATING)
    bb_bot_score = factory.Faker("pyfloat", min_value=-100.0, max_value=100.0)
    bb_fraud_rating = random.choice(USERPROFILING_RATING)
    bb_fraud_score = factory.Faker("pyfloat", min_value=-100.0, max_value=100.0)
    digital_id_result = random.choice(USERPROFILING_RESULTS)
    digital_id_trust_score = factory.Faker("pyfloat", min_value=-100.0, max_value=100.0)
    digital_id_trust_score_rating = random.choice(USERPROFILING_RATING)
    digital_id_confidence = factory.Faker("pyint")
    digital_id_confidence_rating = random.choice(USERPROFILING_RATING)
    policy_score = factory.Faker("pyint")
    reason_code = factory.List((factory.Sequence("Reason code #{0}".format) for x in range(2)))
    request_id = factory.Faker("pystr")
    risk_rating = random.choice(USERPROFILING_RATING)
    tmx_risk_rating = random.choice(USERPROFILING_RATING)
    tmx_summary_reason_code = factory.List(factory.Sequence("Reason code #{0}".format) for x in range(1))
    summary_risk_score = factory.Faker("pyint")


FRAUD_CHECK_TYPE_MODEL_ASSOCIATION = {
    models.FraudCheckType.JOUVE: JouveContentFactory,
    models.FraudCheckType.USER_PROFILING: UserProfilingFraudDataFactory,
}


class BeneficiaryFraudCheckFactory(testing.BaseFactory):
    class Meta:
        model = models.BeneficiaryFraudCheck

    user = factory.SubFactory(users_factories.UserFactory)
    type = factory.LazyAttribute(lambda o: random.choice(list(models.FraudCheckType)))
    thirdPartyId = factory.Sequence("ThirdPartyIdentifier-{0}".format)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""

        factory_class = FRAUD_CHECK_TYPE_MODEL_ASSOCIATION.get(kwargs["type"])
        content = {}
        if factory_class:
            content = factory_class().dict()

        kwargs["resultContent"] = content

        return super()._create(model_class, *args, **kwargs)


class BeneficiaryFraudResultFactory(testing.BaseFactory):
    class Meta:
        model = models.BeneficiaryFraudResult

    user = factory.SubFactory(users_factories.UserFactory)
    status = factory.LazyAttribute(lambda o: random.choice(list(models.FraudStatus)).value)
    reason = factory.Sequence("Fraud Result excuse #{0}".format)
