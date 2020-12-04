from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from freezegun import freeze_time
import pytest

from pcapi.model_creators.generic_creators import create_booking
from pcapi.model_creators.generic_creators import create_deposit
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_stock
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.models import ApiErrors
from pcapi.models import RightsType
from pcapi.models import ThingType
from pcapi.models import user_sql_entity
from pcapi.repository import repository


@pytest.mark.usefixtures("db_session")
def test_cannot_create_admin_that_can_book(app):
    # Given
    user = create_user(is_beneficiary=True, is_admin=True)

    # When
    with pytest.raises(ApiErrors):
        repository.save(user)


class HasRightsTest:
    @pytest.mark.usefixtures("db_session")
    def test_user_has_no_editor_right_on_offerer_if_he_is_not_attached(self, app):
        # given
        offerer = create_offerer()
        user = create_user(is_admin=False)
        repository.save(offerer, user)

        # when
        has_rights = user.hasRights(RightsType.editor, offerer.id)

        # then
        assert has_rights is False

    @pytest.mark.usefixtures("db_session")
    def test_user_has_editor_right_on_offerer_if_he_is_attached(self, app):
        # given
        offerer = create_offerer()
        user = create_user(is_admin=False)
        user_offerer = create_user_offerer(user, offerer)
        repository.save(user_offerer)

        # when
        has_rights = user.hasRights(RightsType.editor, offerer.id)

        # then
        assert has_rights is True

    @pytest.mark.usefixtures("db_session")
    def test_user_has_no_editor_right_on_offerer_if_he_is_attached_but_not_validated_yet(self, app):
        # given
        offerer = create_offerer()
        user = create_user(email="bobby@test.com", is_admin=False)
        user_offerer = create_user_offerer(user, offerer, validation_token="AZEFRGTHRQFQ")
        repository.save(user_offerer)

        # when
        has_rights = user.hasRights(RightsType.editor, offerer.id)

        # then
        assert has_rights is False

    @pytest.mark.usefixtures("db_session")
    def test_user_has_editor_right_on_offerer_if_he_is_not_attached_but_is_admin(self, app):
        # given
        offerer = create_offerer()
        user = create_user(is_beneficiary=False, is_admin=True)
        repository.save(offerer, user)

        # when
        has_rights = user.hasRights(RightsType.editor, offerer.id)

        # then
        assert has_rights is True


class WalletBalanceTest:
    @pytest.mark.usefixtures("db_session")
    def test_wallet_balance_is_0_with_no_deposits_and_no_bookings(self, app):
        # given
        user = create_user()
        repository.save(user)

        # when
        balance = user.wallet_balance

        # then
        assert balance == Decimal(0)

    @pytest.mark.usefixtures("db_session")
    def test_wallet_balance_is_the_sum_of_deposits_if_no_bookings(self, app):
        # given
        user = create_user()
        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        repository.save(deposit1, deposit2)

        # when
        balance = user.wallet_balance

        # then
        assert balance == Decimal(150)

    @pytest.mark.usefixtures("db_session")
    def test_wallet_balance_is_the_sum_of_deposits_minus_the_sum_of_bookings(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        stock1 = create_stock(offer=offer, price=20)
        stock2 = create_stock(offer=offer, price=30)
        booking1 = create_booking(user=user, quantity=1, stock=stock1, venue=venue)
        booking2 = create_booking(user=user, quantity=2, stock=stock2, venue=venue)

        repository.save(deposit1, deposit2, booking1, booking2)

        # when
        balance = user.wallet_balance

        # then
        assert balance == Decimal(70)

    @pytest.mark.usefixtures("db_session")
    def test_wallet_balance_does_not_count_cancelled_bookings(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        stock1 = create_stock(offer=offer, price=20)
        stock2 = create_stock(offer=offer, price=30)
        booking1 = create_booking(user=user, is_cancelled=False, quantity=1, stock=stock1, venue=venue)
        booking2 = create_booking(user=user, is_cancelled=True, quantity=2, stock=stock2, venue=venue)

        repository.save(deposit1, deposit2, booking1, booking2)

        # when
        balance = user.wallet_balance

        # then
        assert balance == Decimal(130)


class RealWalletBalanceTest:
    @pytest.mark.usefixtures("db_session")
    def test_real_wallet_balance_is_0_with_no_deposits_and_no_bookings(self, app):
        # given
        user = create_user()
        repository.save(user)

        # when
        balance = user.real_wallet_balance

        # then
        assert balance == Decimal(0)

    @pytest.mark.usefixtures("db_session")
    def test_real_wallet_balance_is_the_sum_of_deposits_if_no_bookings(self, app):
        # given
        user = create_user()
        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        repository.save(deposit1, deposit2)

        # when
        balance = user.real_wallet_balance

        # then
        assert balance == Decimal(150)

    @pytest.mark.usefixtures("db_session")
    def test_real_wallet_balance_is_the_sum_of_deposits_minus_the_sum_of_used_bookings(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        stock1 = create_stock(offer=offer, price=20)
        stock2 = create_stock(offer=offer, price=30)
        stock3 = create_stock(offer=offer, price=40)
        booking1 = create_booking(user=user, is_used=True, quantity=1, stock=stock1, venue=venue)
        booking2 = create_booking(user=user, is_used=True, quantity=2, stock=stock2, venue=venue)
        booking3 = create_booking(user=user, is_used=False, quantity=1, stock=stock3, venue=venue)

        repository.save(deposit1, deposit2, booking1, booking2, booking3)

        # when
        balance = user.real_wallet_balance

        # then
        assert balance == Decimal(70)

    @pytest.mark.usefixtures("db_session")
    def test_real_wallet_balance_does_not_count_cancelled_bookings(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        deposit1 = create_deposit(user, amount=100)
        deposit2 = create_deposit(user, amount=50)
        stock1 = create_stock(offer=offer, price=20)
        stock2 = create_stock(offer=offer, price=30)
        stock3 = create_stock(offer=offer, price=40)
        booking1 = create_booking(user=user, is_cancelled=True, is_used=True, quantity=1, stock=stock1, venue=venue)
        booking2 = create_booking(user=user, is_cancelled=False, is_used=True, quantity=2, stock=stock2, venue=venue)
        booking3 = create_booking(user=user, is_cancelled=False, is_used=True, quantity=1, stock=stock3, venue=venue)

        repository.save(deposit1, deposit2, booking1, booking2, booking3)

        # when
        balance = user.real_wallet_balance

        # then
        assert balance == Decimal(50)


class HasPhysicalVenuesTest:
    @pytest.mark.usefixtures("db_session")
    def test_webapp_user_has_no_venue(self, app):
        # given
        user = create_user()

        # when
        repository.save(user)

        # then
        assert user.hasPhysicalVenues is False

    @pytest.mark.usefixtures("db_session")
    def test_pro_user_has_one_digital_venue_by_default(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        offerer_venue = create_venue(offerer, is_virtual=True, siret=None)

        # when
        repository.save(offerer_venue, user_offerer)

        # then
        assert user.hasPhysicalVenues is False

    @pytest.mark.usefixtures("db_session")
    def test_pro_user_has_one_digital_venue_and_a_physical_venue(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)
        offerer_virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        offerer_physical_venue = create_venue(offerer)
        repository.save(offerer_virtual_venue, offerer_physical_venue, user_offerer)

        # then
        assert user.hasPhysicalVenues is True


class nOffersTest:
    @pytest.mark.usefixtures("db_session")
    def test_webapp_user_has_no_offerers(self, app):
        # given
        user = create_user()

        repository.save(user)

        # then
        assert user.hasOffers is False

    @pytest.mark.usefixtures("db_session")
    def test_pro_user_with_offers_from_many_offerers(self, app):
        # given
        user = create_user()
        offerer = create_offerer()
        offerer2 = create_offerer(siren="123456788")
        user_offerer = create_user_offerer(user, offerer)
        user_offerer2 = create_user_offerer(user, offerer2)
        offerer_virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        offerer2_physical_venue = create_venue(offerer2, siret="12345678856734")
        offerer2_virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        offer = create_offer_with_thing_product(
            offerer_virtual_venue, thing_type=ThingType.JEUX_VIDEO_ABO, url="http://fake.url"
        )
        offer2 = create_offer_with_thing_product(offerer2_physical_venue)

        repository.save(offer, offer2, user_offerer, user_offerer2)

        # then
        assert user.hasOffers is True


class needsToSeeTutorialsTest:
    @pytest.mark.usefixtures("db_session")
    def test_beneficiary_has_to_see_tutorials_when_not_already_seen(self, app):
        # given
        user = create_user(is_beneficiary=True, has_seen_tutorials=False)
        # when
        repository.save(user)
        # then
        assert user.needsToSeeTutorials is True

    @pytest.mark.usefixtures("db_session")
    def test_beneficiary_has_not_to_see_tutorials_when_already_seen(self, app):
        # given
        user = create_user(is_beneficiary=True, has_seen_tutorials=True)
        # when
        repository.save(user)
        # then
        assert user.needsToSeeTutorials is False

    @pytest.mark.usefixtures("db_session")
    def test_pro_user_has_not_to_see_tutorials_when_already_seen(self, app):
        # given
        user = create_user(is_beneficiary=False)
        # when
        repository.save(user)
        # then
        assert user.needsToSeeTutorials is False


class DevEnvironmentPasswordHasherTest:
    def test_hash_password_uses_md5(self):
        hashed = user_sql_entity.hash_password("secret")
        assert hashed == b"5ebe2294ecd0e0f08eab7690d2a6ee69"

    def test_check_password(self):
        hashed = user_sql_entity.hash_password("secret")
        assert not user_sql_entity.check_password("wrong", hashed)
        assert user_sql_entity.check_password("secret", hashed)


@patch("pcapi.settings.IS_DEV", False)
class ProdEnvironmentPasswordHasherTest:
    def test_hash_password_uses_bcrypt(self):
        hashed = user_sql_entity.hash_password("secret")
        assert hashed != "secret"
        assert hashed.startswith(b"$2b$")  # bcrypt prefix

    def test_check_password(self):
        hashed = user_sql_entity.hash_password("secret")
        assert not user_sql_entity.check_password("wrong", hashed)
        assert user_sql_entity.check_password("secret", hashed)


class CalculateAgeTest:
    @freeze_time("2018-06-01")
    def test_calculate_age(self):
        assert create_user(date_of_birth=None).calculate_age() is None
        assert create_user(date_of_birth=datetime(2000, 6, 1)).calculate_age() == 18  # happy birthday
        assert create_user(date_of_birth=datetime(1999, 7, 1)).calculate_age() == 18
        assert create_user(date_of_birth=datetime(2000, 7, 1)).calculate_age() == 17
        assert create_user(date_of_birth=datetime(1999, 5, 1)).calculate_age() == 19
