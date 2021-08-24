import pytest

from pcapi.core.testing import override_settings
from pcapi.core.users import factories as user_factories
from pcapi.core.users.exceptions import InvalidUserRoleException
from pcapi.core.users.models import User


@pytest.mark.usefixtures("db_session")
class UserTest:
    class UserRoleTest:
        def test_has_admin_role(self):
            user = user_factories.AdminFactory()

            assert user.has_admin_role
            assert User.query.filter(User.has_admin_role.is_(False)).all() == []
            assert User.query.filter(User.has_admin_role.is_(True)).all() == [user]

        def test_has_beneficiary_role(self):
            user = user_factories.BeneficiaryFactory()

            assert user.has_beneficiary_role
            assert User.query.filter(User.has_beneficiary_role.is_(False)).all() == []
            assert User.query.filter(User.has_beneficiary_role.is_(True)).all() == [user]

        def test_has_admin_role_with_legacy_property(self):
            user = user_factories.UserFactory(isAdmin=True, roles=[])

            assert user.has_admin_role
            assert User.query.filter(User.has_admin_role.is_(False)).all() == []
            assert User.query.filter(User.has_admin_role.is_(True)).all() == [user]

        def test_has_beneficiary_role_with_legacy_property(self):
            user = user_factories.UserFactory(isBeneficiary=True, roles=[])

            assert user.has_beneficiary_role
            assert User.query.filter(User.has_beneficiary_role.is_(False)).all() == []
            assert User.query.filter(User.has_beneficiary_role.is_(True)).all() == [user]

        def test_has_pro_role(self):
            user = user_factories.ProFactory()

            assert user.has_pro_role
            assert User.query.filter(User.has_pro_role.is_(False)).all() == []
            assert User.query.filter(User.has_pro_role.is_(True)).all() == [user]

        def test_add_role_on_new_user(self):
            user = User()

            user.add_pro_role()

            assert user.has_pro_role

        def test_add_admin_role(self):
            user = user_factories.UserFactory.build()

            user.add_admin_role()

            assert user.has_admin_role
            assert user.isAdmin

        def test_add_admin_role_only_once(self):
            user = user_factories.UserFactory.build()
            user.add_admin_role()

            user.add_admin_role()

            assert user.has_admin_role
            assert len(user.roles) == 1

        def test_add_beneficiary_role(self):
            user = user_factories.UserFactory.build()

            user.add_beneficiary_role()

            assert user.has_beneficiary_role
            assert user.isBeneficiary

        def test_add_beneficiary_role_only_once(self):
            user = user_factories.UserFactory.build()
            user.add_beneficiary_role()

            user.add_beneficiary_role()

            assert user.has_beneficiary_role
            assert len(user.roles) == 1

        def test_add_pro_role(self):
            user = user_factories.UserFactory.build()

            user.add_pro_role()

            assert user.has_pro_role

        def test_add_pro_role_only_once(self):
            user = user_factories.UserFactory.build()
            user.add_pro_role()

            user.add_pro_role()

            assert user.has_pro_role
            assert len(user.roles) == 1

        def test_cannot_add_beneficiary_role_to_an_admin(self):
            user = user_factories.AdminFactory()

            with pytest.raises(InvalidUserRoleException):
                user.add_beneficiary_role()

                assert not user.has_beneficiary_role
                assert user.has_admin_role

        def test_cannot_add_admin_role_to_a_beneficiary(self):
            user = user_factories.BeneficiaryFactory.build()

            with pytest.raises(InvalidUserRoleException):
                user.add_admin_role()

                assert user.has_beneficiary_role
                assert not user.has_admin_role

        def test_cannot_add_beneficiary_role_to_an_admin_with_legacy_property(self):
            user = user_factories.UserFactory.build(isAdmin=True, roles=[])

            with pytest.raises(InvalidUserRoleException):
                user.add_beneficiary_role()

                assert not user.has_beneficiary_role
                assert not user.isBeneficiary
                assert user.has_admin_role
                assert user.isAdmin

        def test_cannot_add_admin_role_to_a_beneficiary_with_legacy_property(self):
            user = user_factories.UserFactory.build(isBeneficiary=True, roles=[])

            with pytest.raises(InvalidUserRoleException):
                user.add_admin_role()

                assert user.has_beneficiary_role
                assert user.isBeneficiary
                assert not user.has_admin_role
                assert not user.isAdmin

        def test_remove_admin_role(self):
            user = user_factories.AdminFactory.build()

            user.remove_admin_role()

            assert not user.has_admin_role
            assert not user.isAdmin

        def test_remove_admin_role_when_user_is_not_admin(self):
            user = user_factories.BeneficiaryFactory.build()

            user.remove_admin_role()

            assert user.has_beneficiary_role
            assert not user.has_admin_role
            assert not user.isAdmin

        def test_remove_beneficiary_role(self):
            user = user_factories.BeneficiaryFactory.build()

            user.remove_beneficiary_role()

            assert not user.has_beneficiary_role
            assert not user.isBeneficiary

        def test_remove_beneficiary_role_when_user_is_not_beneficiary(self):
            user = user_factories.ProFactory.build()

            user.remove_beneficiary_role()

            assert user.has_pro_role
            assert not user.has_beneficiary_role
            assert not user.isBeneficiary

        def test_remove_pro_role(self):
            user = user_factories.ProFactory.build()

            user.remove_pro_role()

            assert not user.has_pro_role

        def test_remove_pro_role_when_user_is_not_pro(self):
            user = user_factories.BeneficiaryFactory.build()

            user.remove_pro_role()

            assert user.has_beneficiary_role
            assert not user.has_pro_role


@pytest.mark.usefixtures("db_session")
class SuperAdminTest:
    @override_settings(SUPER_ADMIN_EMAIL_ADDRESSES="super@admin.user", IS_PROD=True)
    def test_super_user_prod(self):
        user = user_factories.UserFactory(email="super@admin.user")
        assert user.is_super_admin()

    @override_settings(SUPER_ADMIN_EMAIL_ADDRESSES="", IS_PROD=True)
    def test_super_user_prod_not_configured(self):
        user = user_factories.UserFactory(email="simple-admin@admin.user")
        assert user.is_super_admin() is False

    @override_settings()
    def test_super_user_not_prod_not_admin(self):
        user = user_factories.UserFactory(email="simple-user@example.com")
        assert user.is_super_admin() is False

    @override_settings()
    def test_super_user_not_prod_is_admin_is_super_admin(self):
        user = user_factories.AdminFactory()
        assert user.is_super_admin()
