from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import TEXT
from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy.event import listens_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import OfferValidationStatus
from pcapi.domain.postal_code.postal_code import OVERSEAS_DEPARTEMENT_CODE_START
from pcapi.domain.postal_code.postal_code import PostalCode
from pcapi.domain.ts_vector import create_ts_vector_and_table_args
from pcapi.models.bank_information import BankInformationStatus
from pcapi.models.db import Model
from pcapi.models.db import db
from pcapi.models.deactivable_mixin import DeactivableMixin
from pcapi.models.has_address_mixin import HasAddressMixin
from pcapi.models.has_thumb_mixin import HasThumbMixin
from pcapi.models.needs_validation_mixin import NeedsValidationMixin
from pcapi.models.pc_object import PcObject
from pcapi.models.providable_mixin import ProvidableMixin
from pcapi.models.user_offerer import UserOfferer
from pcapi.models.versioned_mixin import VersionedMixin
from pcapi.utils.date import CUSTOM_TIMEZONES
from pcapi.utils.date import METROPOLE_TIMEZONE
from pcapi.utils.date import get_department_timezone
from pcapi.utils.date import get_postal_code_timezone


CONSTRAINT_CHECK_IS_VIRTUAL_XOR_HAS_ADDRESS = """
(
    "isVirtual" IS TRUE
    AND (address IS NULL AND "postalCode" IS NULL AND city IS NULL AND "departementCode" IS NULL)
)
OR
(
    "isVirtual" IS FALSE
    AND siret is NOT NULL
    AND ("postalCode" IS NOT NULL AND city IS NOT NULL AND "departementCode" IS NOT NULL)
)
OR
(
    "isVirtual" IS FALSE
    AND (siret is NULL and comment is NOT NULL)
    AND (address IS NOT NULL AND "postalCode" IS NOT NULL AND city IS NOT NULL AND "departementCode" IS NOT NULL)
)

"""

CONSTRAINT_CHECK_HAS_SIRET_XOR_HAS_COMMENT_XOR_IS_VIRTUAL = """
    (siret IS NULL AND comment IS NULL AND "isVirtual" IS TRUE)
    OR (siret IS NULL AND comment IS NOT NULL AND "isVirtual" IS FALSE)
    OR (siret IS NOT NULL AND "isVirtual" IS FALSE)
"""


class Venue(PcObject, Model, HasThumbMixin, HasAddressMixin, ProvidableMixin, VersionedMixin, NeedsValidationMixin):
    __tablename__ = "venue"

    id = Column(BigInteger, primary_key=True)

    name = Column(String(140), nullable=False)

    siret = Column(String(14), nullable=True, unique=True)

    departementCode = Column(String(3), nullable=True)

    latitude = Column(Numeric(8, 5), nullable=True)

    longitude = Column(Numeric(8, 5), nullable=True)

    venueProviders = relationship("VenueProvider", back_populates="venue")

    managingOffererId = Column(BigInteger, ForeignKey("offerer.id"), nullable=False, index=True)

    managingOfferer = relationship("Offerer", foreign_keys=[managingOffererId], backref="managedVenues")

    bookingEmail = Column(String(120), nullable=True)

    postalCode = Column(String(6), nullable=True)

    city = Column(String(50), nullable=True)

    publicName = Column(String(255), nullable=True)

    isVirtual = Column(
        Boolean,
        CheckConstraint(CONSTRAINT_CHECK_IS_VIRTUAL_XOR_HAS_ADDRESS, name="check_is_virtual_xor_has_address"),
        nullable=False,
        default=False,
        server_default=expression.false(),
    )

    isPermanent = Column(
        Boolean,
        nullable=True,
        default=True,
    )

    comment = Column(
        TEXT,
        CheckConstraint(
            CONSTRAINT_CHECK_HAS_SIRET_XOR_HAS_COMMENT_XOR_IS_VIRTUAL, name="check_has_siret_xor_comment_xor_isVirtual"
        ),
        nullable=True,
    )

    venueTypeId = Column(Integer, ForeignKey("venue_type.id"), nullable=True)

    venueType = relationship("VenueType", foreign_keys=[venueTypeId])

    venueLabelId = Column(Integer, ForeignKey("venue_label.id"), nullable=True)

    dateCreated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def store_departement_code(self) -> None:
        self.departementCode = PostalCode(self.postalCode).get_departement_code()

    @property
    def bic(self) -> Optional[str]:
        return self.bankInformation.bic if self.bankInformation else None

    @property
    def iban(self) -> Optional[str]:
        return self.bankInformation.iban if self.bankInformation else None

    @property
    def demarchesSimplifieesApplicationId(self) -> Optional[int]:
        if not self.bankInformation:
            return None

        can_show_application_id = (
            self.bankInformation.status == BankInformationStatus.DRAFT
            or self.bankInformation.status == BankInformationStatus.ACCEPTED
        )
        if not can_show_application_id:
            return None

        return self.bankInformation.applicationId

    @property
    def nOffers(self) -> int:
        return (
            Offer.query.filter(and_(Offer.venueId == self.id, Offer.validation != OfferValidationStatus.DRAFT))
            .with_entities(Offer.id)
            .count()
        )

    @hybrid_property
    def timezone(self) -> str:
        if self.departementCode is None:
            return get_postal_code_timezone(self.managingOfferer.postalCode)
        return get_department_timezone(self.departementCode)

    @timezone.expression
    def timezone(cls):  # pylint: disable=no-self-argument
        offerer_alias = aliased(Offerer)
        return case(
            [
                (
                    cls.departementCode.is_(None),
                    case(
                        CUSTOM_TIMEZONES,
                        value=db.session.query(offerer_alias.departementCode)
                        .filter(cls.managingOffererId == offerer_alias.id)
                        .as_scalar(),
                        else_=METROPOLE_TIMEZONE,
                    ),
                )
            ],
            else_=case(CUSTOM_TIMEZONES, value=cls.departementCode, else_=METROPOLE_TIMEZONE),
        )


@listens_for(Venue, "before_insert")
def before_insert(mapper, connect, self):
    _fill_departement_code_from_postal_code(self)


@listens_for(Venue, "before_update")
def before_update(mapper, connect, self):
    _fill_departement_code_from_postal_code(self)


def _fill_departement_code_from_postal_code(self):
    if not self.isVirtual:
        if not self.postalCode:
            raise IntegrityError(None, None, None)
        self.store_departement_code()


ts_indexes = [
    ("idx_venue_fts_name", Venue.name),
    (
        "idx_venue_fts_publicName",
        Venue.publicName,
    ),
    ("idx_venue_fts_address", Venue.address),
    ("idx_venue_fts_siret", Venue.siret),
    ("idx_venue_fts_city", Venue.city),
]

(Venue.__ts_vectors__, Venue.__table_args__) = create_ts_vector_and_table_args(ts_indexes)


class Offerer(
    PcObject,
    Model,
    HasThumbMixin,
    HasAddressMixin,
    ProvidableMixin,
    NeedsValidationMixin,
    DeactivableMixin,
    VersionedMixin,
):
    id = Column(BigInteger, primary_key=True)

    dateCreated = Column(DateTime, nullable=False, default=datetime.utcnow)

    name = Column(String(140), nullable=False)

    users = relationship("User", secondary="user_offerer")

    siren = Column(
        String(9), nullable=True, unique=True
    )  # FIXME: should not be nullable, is until we have all SIRENs filled in the DB

    def grant_access(self, user):
        if not user:
            return None
        user_offerer = UserOfferer()
        user_offerer.offerer = self
        user_offerer.user = user
        return user_offerer

    @property
    def bic(self):
        return self.bankInformation.bic if self.bankInformation else None

    @property
    def iban(self):
        return self.bankInformation.iban if self.bankInformation else None

    @property
    def demarchesSimplifieesApplicationId(self):
        if not self.bankInformation:
            return None

        can_show_application_id = (
            self.bankInformation.status == BankInformationStatus.DRAFT
            or self.bankInformation.status == BankInformationStatus.ACCEPTED
        )
        if not can_show_application_id:
            return None

        return self.bankInformation.applicationId

    @property
    def nOffers(self):
        n_offers = 0
        for venue in self.managedVenues:
            n_offers += venue.nOffers
        return n_offers

    def append_user_has_access_attribute(self, user_id: int, is_admin: bool) -> None:
        if is_admin:
            self.userHasAccess = True
            return

        authorizations = [user_offer.isValidated for user_offer in self.UserOfferers if user_offer.userId == user_id]

        if authorizations:
            user_has_access_as_editor = authorizations[0]
        else:
            user_has_access_as_editor = False

        self.userHasAccess = user_has_access_as_editor

    @hybrid_property
    def departementCode(self):
        return PostalCode(self.postalCode).get_departement_code()

    @departementCode.expression
    def departementCode(cls):  # pylint: disable=no-self-argument
        return case(
            [
                (
                    cast(func.substring(cls.postalCode, 1, 2), Integer) >= OVERSEAS_DEPARTEMENT_CODE_START,
                    func.substring(cls.postalCode, 1, 3),
                )
            ],
            else_=func.substring(cls.postalCode, 1, 2),
        )


offerer_ts_indexes = [
    ("idx_offerer_fts_name", Offerer.name),
    ("idx_offerer_fts_address", Offerer.address),
    ("idx_offerer_fts_siret", Offerer.siren),
]

(Offerer.__ts_vectors__, Offerer.__table_args__) = create_ts_vector_and_table_args(offerer_ts_indexes)
