from enum import Enum
import typing

from flask import Flask
from flask_admin.base import Admin
from markupsafe import Markup
from sqlalchemy.orm.session import Session

from pcapi import models
from pcapi.admin.custom_views import fraud_view
from pcapi.admin.custom_views import offer_view
from pcapi.admin.custom_views.admin_user_view import AdminUserView
from pcapi.admin.custom_views.allocine_pivot_view import AllocinePivotView
from pcapi.admin.custom_views.api_key_view import ApiKeyView
from pcapi.admin.custom_views.beneficiary_import_view import BeneficiaryImportView
from pcapi.admin.custom_views.beneficiary_user_view import BeneficiaryUserView
from pcapi.admin.custom_views.booking_view import BookingView
from pcapi.admin.custom_views.criteria_view import CriteriaView
from pcapi.admin.custom_views.feature_view import FeatureView
from pcapi.admin.custom_views.many_offers_operations_view import ManyOffersOperationsView
from pcapi.admin.custom_views.offer_category_view import OfferCategoryView
from pcapi.admin.custom_views.offer_category_view import OfferSubcategoryView
from pcapi.admin.custom_views.offerer_view import OffererView
from pcapi.admin.custom_views.partner_user_view import PartnerUserView
from pcapi.admin.custom_views.pro_user_view import ProUserView
from pcapi.admin.custom_views.suspend_fraudulent_users import SuspendFraudulentUsersView
from pcapi.admin.custom_views.user_offerer_view import UserOffererView
from pcapi.admin.custom_views.venue_provider_view import VenueProviderView
from pcapi.admin.custom_views.venue_view import VenueView
from pcapi.core.offerers.models import ApiKey
from pcapi.core.offerers.models import Offerer
from pcapi.core.offers.models import OfferValidationConfig
from pcapi.core.providers.models import VenueProvider
from pcapi.core.users.models import User


class Category(Enum):
    def __str__(self) -> str:
        return str(self.value)

    OFFRES_STRUCTURES_LIEUX = "Offre, Lieux & Structure"
    USERS = "Utilisateurs"
    CUSTOM_OPERATIONS = "Autres fonctionnalités"
    FRAUD = "Anti Fraude"


def install_admin_views(admin: Admin, session: Session) -> None:
    admin.add_view(
        offer_view.OfferView(models.Offer, session, name="Offres", category=Category.OFFRES_STRUCTURES_LIEUX)
    )
    admin.add_view(
        fraud_view.FraudView(
            User, session, name="Bénéficiaires", endpoint="/beneficiary_fraud", category=Category.FRAUD
        )
    )
    admin.add_view(
        offer_view.OfferForVenueSubview(
            models.Offer,
            session,
            name="Offres pour un lieu",
            endpoint="offer_for_venue",
        )
    )
    admin.add_view(
        CriteriaView(models.Criterion, session, name="Tags des offres", category=Category.OFFRES_STRUCTURES_LIEUX)
    )
    admin.add_view(OffererView(Offerer, session, name="Structures", category=Category.OFFRES_STRUCTURES_LIEUX))
    admin.add_view(VenueView(models.Venue, session, name="Lieux", category=Category.OFFRES_STRUCTURES_LIEUX))
    admin.add_view(
        UserOffererView(
            models.UserOfferer, session, name="Lien Utilisateurs/Structures", category=Category.OFFRES_STRUCTURES_LIEUX
        )
    )
    admin.add_view(
        ProUserView(
            User,
            session,
            name="Comptes Pros",
            category=Category.USERS,
            endpoint="/pro_users",
        )
    )
    admin.add_view(
        VenueProviderView(
            VenueProvider,
            session,
            name="Imports automatiques",
            endpoint="venue_providers",
            category=Category.CUSTOM_OPERATIONS,
        )
    )
    admin.add_view(
        AdminUserView(
            User,
            session,
            name="Comptes admin",
            category=Category.USERS,
            endpoint="/admin_users",
        )
    )
    admin.add_view(
        BeneficiaryUserView(
            User,
            session,
            name="Comptes Jeunes",
            category=Category.USERS,
            endpoint="/beneficiary_users",
        )
    )
    admin.add_view(
        PartnerUserView(User, session, name="Comptes Grand Public", category=Category.USERS, endpoint="/partner_users")
    )
    admin.add_view(FeatureView(models.Feature, session, name="Feature Flipping", category=None))
    admin.add_view(
        BeneficiaryImportView(models.BeneficiaryImport, session, name="Imports DMS", category=Category.USERS)
    )
    admin.add_view(ApiKeyView(ApiKey, session, name="Clés API", category=Category.USERS))
    admin.add_view(
        AllocinePivotView(
            models.AllocinePivot, session, name="Pivot Allocine", category=Category.OFFRES_STRUCTURES_LIEUX
        )
    )
    admin.add_view(
        ManyOffersOperationsView(
            name="Opérations sur plusieurs offres",
            endpoint="/many_offers_operations",
            category=Category.CUSTOM_OPERATIONS,
        )
    )
    admin.add_view(
        BookingView(
            name="Réservations",
            endpoint="/bookings",
            category=Category.CUSTOM_OPERATIONS,
        )
    )
    admin.add_view(
        offer_view.ValidationView(
            models.Offer,
            session,
            name="Validation",
            endpoint="/validation",
            category=Category.CUSTOM_OPERATIONS,
        )
    )

    admin.add_view(
        offer_view.ImportConfigValidationOfferView(
            OfferValidationConfig,
            session,
            name="Configuration des règles de fraude",
            endpoint="/fraud_rules_configuration",
            category=Category.CUSTOM_OPERATIONS,
        )
    )

    admin.add_view(
        SuspendFraudulentUsersView(
            name="Suspension d'utilisateurs via noms de domaine",
            endpoint="/suspend_fraud_users",
            category=Category.CUSTOM_OPERATIONS,
        )
    )

    admin.add_view(
        OfferCategoryView(
            models.OfferCategory,
            session,
            name="Catégories d'offres",
            endpoint="/offer_categoriess",
            category=Category.CUSTOM_OPERATIONS,
        )
    )

    admin.add_view(
        OfferSubcategoryView(
            models.OfferSubcategory,
            session,
            name="Sous-catégories d'offres",
            endpoint="/offer_subcategories",
            category=Category.CUSTOM_OPERATIONS,
        )
    )


def yesno(value: typing.Any) -> str:
    css_class = "success" if value else "danger"
    text_value = "Oui" if value else "Non"
    return Markup(f"""<span class="badge badge-{css_class}">{text_value}</span>""")


def install_admin_template_filters(app: Flask) -> None:
    app.jinja_env.filters["yesno"] = yesno
