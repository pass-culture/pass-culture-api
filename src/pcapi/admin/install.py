from flask_admin.base import Admin
from sqlalchemy.orm.session import Session

from pcapi.admin.custom_views.allocine_pivot_view import AllocinePivotView
from pcapi.admin.custom_views.beneficiary_import_view import BeneficiaryImportView
from pcapi.admin.custom_views.beneficiary_user_view import BeneficiaryUserView
from pcapi.admin.custom_views.criteria_view import CriteriaView
from pcapi.admin.custom_views.feature_view import FeatureView
from pcapi.admin.custom_views.offer_view import OfferView
from pcapi.admin.custom_views.offerer_view import OffererView
from pcapi.admin.custom_views.pro_user_view import ProUserView
from pcapi.admin.custom_views.user_offerer_view import UserOffererView
from pcapi.admin.custom_views.venue_view import VenueView
from pcapi.models import AllocinePivot
from pcapi.models import BeneficiaryImport
from pcapi.models import Criterion
from pcapi.models import Feature
from pcapi.models import Offer
from pcapi.models import Offerer
from pcapi.models import UserOfferer
from pcapi.models import UserSQLEntity
from pcapi.models import VenueSQLEntity


def install_admin_views(admin: Admin, session: Session) -> None:
    admin.add_view(OfferView(Offer, session, name="Offres", category="Pro"))
    admin.add_view(CriteriaView(Criterion, session, name="Tags des offres", category="Pro"))
    admin.add_view(OffererView(Offerer, session, name="Structures", category="Pro"))
    admin.add_view(VenueView(VenueSQLEntity, session, name="Lieux", category="Pro"))
    admin.add_view(UserOffererView(UserOfferer, session, name="Lien Utilisateurs/Structures", category="Pro"))
    admin.add_view(
        ProUserView(
            UserSQLEntity,
            session,
            name="Comptes Pros",
            category="Utilisateurs",
            endpoint="/pro_users",
        )
    )
    admin.add_view(
        BeneficiaryUserView(
            UserSQLEntity, session, name="Comptes Jeunes", category="Utilisateurs", endpoint="/beneficiary_users"
        )
    )
    admin.add_view(FeatureView(Feature, session, name="Fonctionnalités", category=None))
    admin.add_view(BeneficiaryImportView(BeneficiaryImport, session, name="Imports DMS", category="Utilisateurs"))
    admin.add_view(AllocinePivotView(AllocinePivot, session, name="Pivot Allocine", category="Pro"))
