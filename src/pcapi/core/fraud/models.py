from dataclasses import dataclass
import enum
from typing import Optional

import pydantic
from pydantic.class_validators import validator
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.orm

from pcapi.models.db import Model
from pcapi.models.pc_object import PcObject


class FraudCheckType(enum.Enum):
    JOUVE = "jouve"
    USER_PROFILING = "user_profiling"
    DMS = "dms"


class FraudStatus(enum.Enum):
    OK = "OK"
    KO = "KO"
    SUSPICIOUS = "SUSPICIOUS"


def _parse_level(level: Optional[str]) -> Optional[None]:
    if not level:
        return None
    try:
        return int(level)
    except ValueError:
        return None


class JouveContent(pydantic.BaseModel):
    # TODO: analyze jouve results to see where we can remove "optional"
    activity: Optional[str]
    address: Optional[str]
    birthDate: Optional[str]
    birthLocationCtrl: Optional[str]
    bodyBirthDateCtrl: Optional[str]
    bodyBirthDateLevel: Optional[int]
    bodyFirstNameCtrl: Optional[str]
    bodyFirstNameLevel: Optional[int]
    bodyNameLevel: Optional[int]
    bodyNameCtrl: Optional[str]
    bodyPieceNumber: Optional[str]
    bodyPieceNumberCtrl: Optional[str]
    bodyPieceNumberLevel: Optional[int]
    city: Optional[str]
    creatorCtrl: Optional[str]
    id: int
    email: Optional[str]
    firstName: Optional[str]
    gender: Optional[str]
    initialNumberCtrl: Optional[str]
    initialSizeCtrl: Optional[str]
    lastName: Optional[str]
    phoneNumber: Optional[str]
    postalCode: Optional[str]
    posteCodeCtrl: Optional[str]
    serviceCodeCtrl: Optional[str]

    _parse_body_birth_date_level = validator("bodyBirthDateLevel", pre=True, allow_reuse=True)(_parse_level)
    _parse_body_first_name_level = validator("bodyFirstNameLevel", pre=True, allow_reuse=True)(_parse_level)
    _parse_body_name_level = validator("bodyNameLevel", pre=True, allow_reuse=True)(_parse_level)
    _parse_body_piece_number_level = validator("bodyPieceNumberLevel", pre=True, allow_reuse=True)(_parse_level)


class BeneficiaryFraudCheck(PcObject, Model):
    __tablename__ = "beneficiary_fraud_check"

    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)

    dateCreated = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now())

    userId = sqlalchemy.Column(sqlalchemy.BigInteger, sqlalchemy.ForeignKey("user.id"), index=True, nullable=False)

    user = sqlalchemy.orm.relationship("User", foreign_keys=[userId], backref="beneficiaryFraudChecks")

    type = sqlalchemy.Column(sqlalchemy.Enum(FraudCheckType, create_constraint=False), nullable=False)

    thirdPartyId = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False)

    resultContent = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB)


class BeneficiaryFraudResult(PcObject, Model):
    __tablename__ = "beneficiary_fraud_result"

    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)

    userId = sqlalchemy.Column(sqlalchemy.BigInteger, sqlalchemy.ForeignKey("user.id"), index=True, nullable=False)

    user = sqlalchemy.orm.relationship(
        "User", foreign_keys=[userId], backref=sqlalchemy.orm.backref("beneficiaryFraudResult", uselist=False)
    )

    status = sqlalchemy.Column(sqlalchemy.Enum(FraudStatus, create_constraint=False))

    reason = sqlalchemy.Column(sqlalchemy.Text)

    dateCreated = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now())

    dateUpdated = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True, onupdate=sqlalchemy.func.now())


@dataclass
class FraudItem:
    status: FraudStatus
    detail: Optional[str]
