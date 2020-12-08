from wtforms import Form

from pcapi.admin.custom_views.partner_user_view import PartnerUserView
from pcapi.models import UserSQLEntity


class PartnerUserViewTest:
    def test_should_generate_a_random_password_on_creation(self, app, db_session):
        # given
        user = UserSQLEntity()
        user.password = None
        view = PartnerUserView(model=UserSQLEntity, session=db_session)

        # when
        view.on_model_change(Form(), model=user, is_created=True)

        # then
        assert user.password is not None

    def test_should_preserve_password_on_edition(self, app, db_session):
        # given
        user = UserSQLEntity()
        user.password = "OriginalPassword"
        view = PartnerUserView(model=UserSQLEntity, session=db_session)

        # when
        view.on_model_change(Form(), model=user, is_created=False)

        # then
        assert user.password == "OriginalPassword"

    def test_a_partner_should_never_be_a_beneficiary(self, app, db_session):
        # given
        user = UserSQLEntity()
        view = PartnerUserView(model=UserSQLEntity, session=db_session)

        # when
        view.on_model_change(Form(), model=user, is_created=False)

        # then
        assert user.isBeneficiary == False

    def test_a_partner_should_never_be_an_admin(self, app, db_session):
        # given
        user = UserSQLEntity()
        view = PartnerUserView(model=UserSQLEntity, session=db_session)

        # when
        view.on_model_change(Form(), model=user, is_created=False)

        # then
        assert user.isAdmin == False

    def test_should_create_the_public_name(self, app, db_session):
        # given
        user = UserSQLEntity()
        user.firstName = "Ken"
        user.lastName = "Thompson"
        user.publicName = None
        view = PartnerUserView(model=UserSQLEntity, session=db_session)

        # when
        view.on_model_change(Form(), model=user, is_created=False)

        # then
        assert user.publicName == "Ken Thompson"
