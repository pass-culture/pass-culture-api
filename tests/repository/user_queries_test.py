from datetime import datetime, timedelta, MINYEAR

from models import ImportStatus, ThingType
from models import PcObject
from repository.user_queries import get_all_users_wallet_balances, find_by_civility, \
    find_most_recent_beneficiary_creation_date, count_all_activated_users, count_users_having_booked, \
    count_all_activated_users_by_departement, count_users_having_booked_by_departement_code
from tests.conftest import clean_database
from tests.test_utils import create_user, create_offerer, create_venue, create_offer_with_thing_product, create_deposit, \
    create_stock, create_booking, create_beneficiary_import


class GetAllUsersWalletBalancesTest:
    @clean_database
    def test_users_are_sorted_by_user_id(self, app):
        # given
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(price=20, offer=offer)
        stock2 = create_stock(price=30, offer=offer)
        stock3 = create_stock(price=40, offer=offer)
        PcObject.save(stock1, stock2, stock3, user1, user2)

        _create_balances_for_user2(stock3, user2, venue)
        _create_balances_for_user1(stock1, stock2, stock3, user1, venue)

        # when
        balances = get_all_users_wallet_balances()

        # then
        assert len(balances) == 2
        assert balances[0].user_id < balances[1].user_id

    @clean_database
    def test_users_with_no_deposits_are_ignored(self, app):
        # given
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock3 = create_stock(price=40, offer=offer)
        PcObject.save(stock3, user1, user2)

        _create_balances_for_user2(stock3, user2, venue)

        # when
        balances = get_all_users_wallet_balances()

        # then
        assert len(balances) == 1

    @clean_database
    def test_returns_current_balances(self, app):
        # given
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(price=20, offer=offer)
        stock2 = create_stock(price=30, offer=offer)
        stock3 = create_stock(price=40, offer=offer)
        PcObject.save(stock1, stock2, stock3, user1, user2)

        _create_balances_for_user1(stock1, stock2, stock3, user1, venue)
        _create_balances_for_user2(stock3, user2, venue)

        # when
        balances = get_all_users_wallet_balances()

        # then
        assert balances[0].current_balance == 50
        assert balances[1].current_balance == 80

    @clean_database
    def test_returns_real_balances(self, app):
        # given
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(price=20, offer=offer)
        stock2 = create_stock(price=30, offer=offer)
        stock3 = create_stock(price=40, offer=offer)
        PcObject.save(stock1, stock2, stock3, user1, user2)

        _create_balances_for_user1(stock1, stock2, stock3, user1, venue)
        _create_balances_for_user2(stock3, user2, venue)

        # when
        balances = get_all_users_wallet_balances()

        # then
        assert balances[0].real_balance == 90
        assert balances[1].real_balance == 200


class FindByCivilityTest:
    @clean_database
    def test_returns_users_with_matching_criteria_ignoring_case(self, app):
        # given
        user1 = create_user(first_name="john", last_name='DOe', email='john@test.com',
                            date_of_birth=datetime(2000, 5, 1))
        user2 = create_user(first_name="jaNE", last_name='DOe', email='jane@test.com',
                            date_of_birth=datetime(2000, 3, 20))
        PcObject.save(user1, user2)

        # when
        users = find_by_civility('john', 'doe', datetime(2000, 5, 1))

        # then
        assert len(users) == 1
        assert users[0].email == 'john@test.com'

    @clean_database
    def test_returns_users_with_matching_criteria_ignoring_dash(self, app):
        # given
        user2 = create_user(first_name="jaNE", last_name='DOe', email='jane@test.com',
                            date_of_birth=datetime(2000, 3, 20))
        user1 = create_user(first_name="john-bob", last_name='doe', email='john.b@test.com',
                            date_of_birth=datetime(2000, 5, 1))
        PcObject.save(user1, user2)

        # when
        users = find_by_civility('johnbob', 'doe', datetime(2000, 5, 1))

        # then
        assert len(users) == 1
        assert users[0].email == 'john.b@test.com'

    @clean_database
    def test_returns_users_with_matching_criteria_ignoring_spaces(self, app):
        # given
        user2 = create_user(first_name="jaNE", last_name='DOe', email='jane@test.com',
                            date_of_birth=datetime(2000, 3, 20))
        user1 = create_user(first_name="john bob", last_name='doe', email='john.b@test.com',
                            date_of_birth=datetime(2000, 5, 1))
        PcObject.save(user1, user2)

        # when
        users = find_by_civility('johnbob', 'doe', datetime(2000, 5, 1))

        # then
        assert len(users) == 1
        assert users[0].email == 'john.b@test.com'

    @clean_database
    def test_returns_users_with_matching_criteria_ignoring_accents(self, app):
        # given
        user2 = create_user(first_name="jaNE", last_name='DOe', email='jane@test.com',
                            date_of_birth=datetime(2000, 3, 20))
        user1 = create_user(first_name="john bob", last_name='doe', email='john.b@test.com',
                            date_of_birth=datetime(2000, 5, 1))
        PcObject.save(user1, user2)

        # when
        users = find_by_civility('jöhn bób', 'doe', datetime(2000, 5, 1))

        # then
        assert len(users) == 1
        assert users[0].email == 'john.b@test.com'

    @clean_database
    def test_returns_nothing_if_one_criteria_does_not_match(self, app):
        # given
        user = create_user(first_name="Jean", last_name='DOe', date_of_birth=datetime(2000, 5, 1))
        PcObject.save(user)

        # when
        users = find_by_civility('john', 'doe', datetime(2000, 5, 1))

        # then
        assert not users

    @clean_database
    def test_returns_users_with_matching_criteria_first_and_last_names_and_birthdate_and_invalid_email(self, app):
        # given
        user1 = create_user(first_name="john", last_name='DOe', email='john@test.com',
                            date_of_birth=datetime(2000, 5, 1))
        user2 = create_user(first_name="jaNE", last_name='DOe', email='jane@test.com',
                            date_of_birth=datetime(2000, 3, 20))
        PcObject.save(user1, user2)

        # when
        users = find_by_civility('john', 'doe', datetime(2000, 5, 1))

        # then
        assert len(users) == 1
        assert users[0].email == 'john@test.com'


class FindMostRecentBeneficiaryCreationDateTest:
    @clean_database
    def test_returns_created_at_date_of_most_recent_beneficiary_import_with_created_status(
            self, app):
        # given
        now = datetime.utcnow()

        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        three_days_ago = now - timedelta(days=3)

        user1 = create_user(email='user1@test.com', date_created=yesterday)
        user2 = create_user(email='user2@test.com', date_created=two_days_ago)
        user3 = create_user(email='user3@test.com', date_created=three_days_ago)
        beneficiary_import2 = create_beneficiary_import(user2, status=ImportStatus.ERROR, date=two_days_ago,
                                                        demarche_simplifiee_application_id=1)
        beneficiary_import3 = create_beneficiary_import(user3, status=ImportStatus.CREATED, date=three_days_ago,
                                                        demarche_simplifiee_application_id=3)

        PcObject.save(user1, beneficiary_import2, beneficiary_import3)

        # when
        most_recent_creation_date = find_most_recent_beneficiary_creation_date()

        # then
        assert most_recent_creation_date == three_days_ago

    @clean_database
    def test_returns_min_year_if_no_beneficiary_import_exist(self, app):
        # given
        yesterday = datetime.utcnow() - timedelta(days=1)
        user1 = create_user(email='user1@test.com', date_created=yesterday)
        PcObject.save(user1)

        # when
        most_recent_creation_date = find_most_recent_beneficiary_creation_date()

        # then
        assert most_recent_creation_date == datetime(MINYEAR, 1, 1)


class CountAllActivatedUsersTest:
    @clean_database
    def test_returns_1_when_only_one_active_user(self, app):
        # Given
        user_activated = create_user(can_book_free_offers=True)
        user_not_activated = create_user(can_book_free_offers=False, email='email2@test.com')
        PcObject.save(user_activated, user_not_activated)

        # When
        number_of_active_users = count_all_activated_users()

        # Then
        assert number_of_active_users == 1

    @clean_database
    def test_returns_0_when_no_active_user(self, app):
        # Given
        user_activated = create_user(can_book_free_offers=False)
        user_not_activated = create_user(can_book_free_offers=False, email='email2@test.com')
        PcObject.save(user_activated, user_not_activated)

        # When
        number_of_active_users = count_all_activated_users()

        # Then
        assert number_of_active_users == 0


class CountActivatedUsersByDepartementTest:
    @clean_database
    def test_returns_1_when_only_one_active_user_in_departement(self, app):
        # Given
        user_activated = create_user(can_book_free_offers=True, departement_code='74')
        user_not_activated = create_user(can_book_free_offers=False, email='email2@test.com')
        PcObject.save(user_activated, user_not_activated)

        # When
        number_of_active_users = count_all_activated_users_by_departement('74')

        # Then
        assert number_of_active_users == 1

    @clean_database
    def test_returns_0_when_no_active_user_in_departement(self, app):
        # Given
        user_activated = create_user(can_book_free_offers=False, departement_code='74')
        user_not_activated = create_user(can_book_free_offers=False, email='email2@test.com')
        PcObject.save(user_activated, user_not_activated)

        # When
        number_of_active_users = count_all_activated_users_by_departement('74')

        # Then
        assert number_of_active_users == 0

    @clean_database
    def test_returns_0_when_no_active_user_in_departement(self, app):
        # Given
        user_activated = create_user(can_book_free_offers=True, departement_code='76')
        user_not_activated = create_user(can_book_free_offers=False, email='email2@test.com')
        PcObject.save(user_activated, user_not_activated)

        # When
        number_of_active_users = count_all_activated_users_by_departement('74')

        # Then
        assert number_of_active_users == 0


class CountUsersHavingBookedTest:
    @clean_database
    def test_returns_one_when_user_with_one_cancelled_and_one_non_cancelled_bookings(self, app):
        # Given
        user_having_booked = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue)
        offer2 = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer1, price=0)
        stock2 = create_stock(offer=offer2, price=0)
        booking1 = create_booking(user_having_booked, stock1, is_cancelled=False)
        booking2 = create_booking(user_having_booked, stock2, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_users_having_booked = count_users_having_booked()

        # Then
        assert number_of_users_having_booked == 1

    @clean_database
    def test_returns_two_when_two_users_with_cancelled_bookings(self, app):
        # Given
        user_having_booked1 = create_user()
        user_having_booked2 = create_user(email='test1@email.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        booking1 = create_booking(user_having_booked1, stock, is_cancelled=True)
        booking2 = create_booking(user_having_booked2, stock, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_users_having_booked = count_users_having_booked()

        # Then
        assert number_of_users_having_booked == 2

    @clean_database
    def test_returns_zero_when_no_user_with_booking(self, app):
        # Given
        user = create_user()
        PcObject.save(user)

        # When
        number_of_users_having_booked = count_users_having_booked()

        # Then
        assert number_of_users_having_booked == 0

    @clean_database
    def test_returns_zero_when_user_with_only_activation_booking(self, app):
        # Given
        user_having_booked1 = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
        stock = create_stock(offer=offer, price=0)
        booking1 = create_booking(user_having_booked1, stock, is_cancelled=True)
        PcObject.save(booking1)

        # When
        number_of_users_having_booked = count_users_having_booked()

        # Then
        assert number_of_users_having_booked == 0


class CountUsersHavingBookedByDepartementTest:
    @clean_database
    def test_counts_only_user_from_the_right_departement(self, app):
        # Given
        user_having_booked_from_73 = create_user(departement_code='73', email='email73@example.net')
        user_having_booked_from_32 = create_user(departement_code='32', email='email32@example.net')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer1, price=0)
        booking1 = create_booking(user_having_booked_from_73, stock1)
        booking2 = create_booking(user_having_booked_from_32, stock1)
        PcObject.save(booking1, booking2)

        # When
        number_of_users_having_booked = count_users_having_booked_by_departement_code('73')

        # Then
        assert number_of_users_having_booked == 1

    @clean_database
    def test_returns_one_when_user_with_one_cancelled_and_one_non_cancelled_bookings(self, app):
        # Given
        user_having_booked = create_user(departement_code='73')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue)
        offer2 = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer1, price=0)
        stock2 = create_stock(offer=offer2, price=0)
        booking1 = create_booking(user_having_booked, stock1, is_cancelled=False)
        booking2 = create_booking(user_having_booked, stock2, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_users_having_booked = count_users_having_booked_by_departement_code('73')

        # Then
        assert number_of_users_having_booked == 1

    @clean_database
    def test_returns_two_when_two_users_with_cancelled_bookings(self, app):
        # Given
        user_having_booked1 = create_user(departement_code='87')
        user_having_booked2 = create_user(email='test1@email.com', departement_code='87')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        booking1 = create_booking(user_having_booked1, stock, is_cancelled=True)
        booking2 = create_booking(user_having_booked2, stock, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_users_having_booked = count_users_having_booked_by_departement_code('87')

        # Then
        assert number_of_users_having_booked == 2

    @clean_database
    def test_returns_zero_when_no_user_with_booking(self, app):
        # Given
        user = create_user()
        PcObject.save(user)

        # When
        number_of_users_having_booked = count_users_having_booked_by_departement_code('73')

        # Then
        assert number_of_users_having_booked == 0

    @clean_database
    def test_returns_zero_when_user_with_only_activation_booking(self, app):
        # Given
        user_having_booked1 = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
        stock = create_stock(offer=offer, price=0)
        booking1 = create_booking(user_having_booked1, stock, is_cancelled=True)
        PcObject.save(booking1)

        # When
        number_of_users_having_booked = count_users_having_booked_by_departement_code('73')

        # Then
        assert number_of_users_having_booked == 0


def _create_balances_for_user2(stock3, user2, venue):
    deposit3 = create_deposit(user2, amount=200)
    booking4 = create_booking(user2, venue=venue, stock=stock3, quantity=3, is_cancelled=False, is_used=False)
    PcObject.save(deposit3, booking4)


def _create_balances_for_user1(stock1, stock2, stock3, user1, venue):
    deposit1 = create_deposit(user1, amount=100)
    deposit2 = create_deposit(user1, amount=50)
    booking1 = create_booking(user1, venue=venue, stock=stock1, quantity=1, is_cancelled=True, is_used=False)
    booking2 = create_booking(user1, venue=venue, stock=stock2, quantity=2, is_cancelled=False, is_used=True)
    booking3 = create_booking(user1, venue=venue, stock=stock3, quantity=1, is_cancelled=False, is_used=False)
    PcObject.save(deposit1, deposit2, booking1, booking2, booking3)
