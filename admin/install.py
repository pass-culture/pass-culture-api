from admin.custom_views import OffererAdminView, UserAdminView, FeatureAdminView, VenueAdminView, BeneficiaryImportView
from models import Offerer, User, Feature, Venue, BeneficiaryImport


def install_admin_views(admin, session):
    admin.add_view(OffererAdminView(Offerer, session, name='Structures', category='Pro'))
    admin.add_view(VenueAdminView(Venue, session, name='Lieux', category='Pro'))
    admin.add_view(UserAdminView(User, session, name='Comptes', category='Utilisateurs'))
    admin.add_view(BeneficiaryImportView(BeneficiaryImport, session, name='Imports DMS', category='Utilisateurs'))
    admin.add_view(FeatureAdminView(Feature, session, name='Fonctionnalités', category=None))
