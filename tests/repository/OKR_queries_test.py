from datetime import datetime

import pandas
from freezegun import freeze_time

from models import ThingType, PcObject
from repository.OKR_queries import get_all_experimentation_users_details
from tests.conftest import clean_database
from tests.test_utils import create_user, create_offerer, create_venue, create_offer_with_thing_product, create_stock, \
    create_booking, create_recommendation


class getAllExperimentationUsersDetailsTest:
    @clean_database
    def test_should_not_return_details_for_users_who_cannot_book_free_offers(self, app):
        # Given
        user = create_user(can_book_free_offers=False)
        PcObject.save(user)

        # When
        experimentation_users = get_all_experimentation_users_details()
        # Then
        assert experimentation_users.empty

    class ExperimentationSessionColumnTest:
        @clean_database
        def test_should_be_a_Series_with_1_if_user_has_used_activation_booking(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            activation_offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
            stock = create_stock(offer=activation_offer, price=0)
            booking = create_booking(user, stock, is_used=True)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()
            # Then
            assert experimentation_users['Vague d\'expérimentation'].equals(
                pandas.Series(data=[1], name='Vague d\'expérimentation'))

        @clean_database
        def test_should_be_a_Series_with_2_if_user_has_unused_activation_booking(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            activation_offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
            stock = create_stock(offer=activation_offer, price=0)
            booking = create_booking(user, stock, is_used=False)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()
            # Then
            assert experimentation_users['Vague d\'expérimentation'].equals(
                pandas.Series(data=[2], name='Vague d\'expérimentation'))

        @clean_database
        def test_should_be_a_Series_with_2_if_user_does_not_have_activation_booking(self, app):
            # Given
            user = create_user()
            PcObject.save(user)

            # When
            experimentation_users = get_all_experimentation_users_details()
            # Then
            assert experimentation_users['Vague d\'expérimentation'].equals(
                pandas.Series(data=[2], name='Vague d\'expérimentation'))

    class DepartmentColumnTest:
        @clean_database
        def test_should_return_user_departement_code(self, app):
            # Given
            user = create_user(departement_code='01')
            PcObject.save(user)

            # When
            experimentation_users = get_all_experimentation_users_details()
            print(experimentation_users)
            # Then
            assert experimentation_users['Département'].equals(
                pandas.Series(data=['01'], name='Département'))

    class ActivationDateColumnTest:
        @clean_database
        def test_should_return_date_when_activation_booking_was_used_if_it_is_used(self, app):
            # Given
            beginning_test_date = datetime.utcnow()
            user = create_user(date_created=datetime(2019, 8, 31))
            offerer = create_offerer()
            venue = create_venue(offerer)
            activation_offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
            stock = create_stock(offer=activation_offer, price=0)
            booking = create_booking(user, stock)
            PcObject.save(booking)
            booking.isUsed = True
            PcObject.save(booking)
            date_after_used = datetime.utcnow()

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert beginning_test_date < experimentation_users.loc[0, 'Date d\'activation'] < date_after_used

        @clean_database
        def test_should_return_date_created_for_user_when_no_activation_booking(self, app):
            # Given
            user = create_user(date_created=datetime(2019, 8, 31))
            PcObject.save(user)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users['Date d\'activation'].equals(
                pandas.Series(data=[datetime(2019, 8, 31)], name='Date d\'activation'))

        @clean_database
        def test_should_return_date_created_for_user_when_non_used_activation_booking(self, app):
            # Given
            user = create_user(date_created=datetime(2019, 8, 31))
            offerer = create_offerer()
            venue = create_venue(offerer)
            activation_offer = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
            stock = create_stock(offer=activation_offer, price=0)
            booking = create_booking(user, stock)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users['Date d\'activation'].equals(
                pandas.Series(data=[datetime(2019, 8, 31)], name='Date d\'activation'))

    class TypeformFillingDateTest:
        @clean_database
        def test_returns_date_when_has_filled_cultural_survey_was_updated_to_false(self, app):
            # Given
            beginning_test_date = datetime.utcnow()
            user = create_user(needs_to_fill_cultural_survey=True)
            PcObject.save(user)
            user.needsToFillCulturalSurvey = False
            PcObject.save(user)
            date_after_used = datetime.utcnow()

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert beginning_test_date < experimentation_users.loc[
                0, 'Date de remplissage du typeform'] < date_after_used

        @clean_database
        def test_returns_None_when_has_filled_cultural_survey_never_updated_to_false(self, app):
            # Given
            user = create_user(needs_to_fill_cultural_survey=True)
            PcObject.save(user)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de remplissage du typeform'] is None

    class FirstConnectionTest:
        @clean_database
        def test_returns_min_recommandation_dateCreated_for_a_user_if_has_any_recommendation(self, app):
            # Given
            beginning_test_date = datetime.utcnow()
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            recommendation = create_recommendation(offer, user)
            PcObject.save(recommendation)
            date_after_recommendation = datetime.utcnow()


            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert beginning_test_date < experimentation_users.loc[0, 'Date de première connection'] < date_after_recommendation

        @clean_database
        def test_returns_None_if_no_recommendation(self, app):
            # Given
            user = create_user()
            PcObject.save(user)


            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première connection'] is None

    class FirstBookingTest:
        @clean_database
        def test_returns_booking_date_created_if_user_has_booked(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            first_booking_date = datetime(2019, 9, 19, 12, 0, 0)
            booking = create_booking(user, stock, date_created=first_booking_date)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première réservation'] == first_booking_date

        @clean_database
        def test_returns_none_if_user_has_not_booked(self, app):
            # Given
            user = create_user()
            PcObject.save(user)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première réservation'] is None

        @clean_database
        def test_returns_none_if_booking_on_activation_offer(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue, thing_type='ThingType.ACTIVATION')
            stock = create_stock(offer=offer, price=0)
            first_booking_date = datetime(2019, 9, 19, 12, 0, 0)
            booking = create_booking(user, stock, date_created=first_booking_date)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première réservation'] is None


    class SecondBookingTest:
        @clean_database
        def test_returns_date_created_of_second_booking_if_exists(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            first_booking_date = datetime(2019, 9, 19, 12, 0, 0)
            second_booking_date = datetime(2019, 9, 22, 12, 0, 0)
            first_booking = create_booking(user, stock, date_created=first_booking_date)
            second_booking = create_booking(user, stock, date_created=second_booking_date)
            PcObject.save(first_booking, second_booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de deuxième réservation'] == second_booking_date

        @clean_database
        def test_returns_none_if_user_has_only_one_booking(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            first_booking_date = datetime(2019, 9, 19, 12, 0, 0)
            booking = create_booking(user, stock, date_created=first_booking_date)
            PcObject.save(booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de deuxième réservation'] is None

        @clean_database
        def test_returns_none_if_booking_on_activation_offer(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            activation_offer = create_offer_with_thing_product(venue, thing_type='ThingType.ACTIVATION')
            activation_stock = create_stock(offer=activation_offer, price=0)
            first_booking_date = datetime(2019, 9, 19, 12, 0, 0)
            activation_booking = create_booking(user, activation_stock, date_created=first_booking_date)
            offer = create_offer_with_thing_product(venue)
            stock = create_stock(offer=offer, price=0)
            first_booking_date = datetime(2019, 9, 20, 12, 0, 0)
            booking = create_booking(user, stock, date_created=first_booking_date)
            PcObject.save(activation_booking, booking)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de deuxième réservation'] is None

    class BookingOnThirdProductTypeTest:
        @clean_database
        def test_returns_date_created_of_first_booking_on_more_than_three_types(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer_cinema = create_offer_with_thing_product(venue, thing_type=ThingType.CINEMA_ABO)
            stock_cinema = create_stock(offer=offer_cinema, price=0)
            booking_date_cinema = datetime(2019, 9, 19, 12, 0, 0)
            booking_cinema = create_booking(user, stock_cinema, date_created=booking_date_cinema)
            offer_audiovisuel = create_offer_with_thing_product(venue, thing_type=ThingType.AUDIOVISUEL)
            stock_audiovisuel = create_stock(offer=offer_audiovisuel, price=0)
            booking_date_audiovisuel = datetime(2019, 9, 20, 12, 0, 0)
            booking_audiovisuel = create_booking(user, stock_audiovisuel, date_created=booking_date_audiovisuel)
            offer_jeux_video1 = create_offer_with_thing_product(venue, thing_type=ThingType.JEUX_VIDEO)
            stock_jeux_video1 = create_stock(offer=offer_jeux_video1, price=0)
            booking_date_jeux_video1 = datetime(2019, 9, 21, 12, 0, 0)
            booking_jeux_video1 = create_booking(user, stock_jeux_video1, date_created=booking_date_jeux_video1)
            offer_jeux_video2 = create_offer_with_thing_product(venue, thing_type=ThingType.JEUX_VIDEO)
            stock_jeux_video2 = create_stock(offer=offer_jeux_video2, price=0)
            booking_date_jeux_video2 = datetime(2019, 9, 21, 12, 0, 0)
            booking_jeux_video2 = create_booking(user, stock_jeux_video2, date_created=booking_date_jeux_video2)
            PcObject.save(booking_cinema, booking_audiovisuel, booking_jeux_video1, booking_jeux_video2)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première réservation dans 3 catégories différentes'] == booking_date_jeux_video1


        @clean_database
        def test_does_not_count_type_activation(self, app):
            # Given
            user = create_user()
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer_cinema = create_offer_with_thing_product(venue, thing_type=ThingType.CINEMA_ABO)
            stock_cinema = create_stock(offer=offer_cinema, price=0)
            booking_date_cinema = datetime(2019, 9, 19, 12, 0, 0)
            booking_cinema = create_booking(user, stock_cinema, date_created=booking_date_cinema)
            offer_audiovisuel = create_offer_with_thing_product(venue, thing_type=ThingType.AUDIOVISUEL)
            stock_audiovisuel = create_stock(offer=offer_audiovisuel, price=0)
            booking_date_audiovisuel = datetime(2019, 9, 20, 12, 0, 0)
            booking_audiovisuel = create_booking(user, stock_audiovisuel, date_created=booking_date_audiovisuel)
            offer_activation = create_offer_with_thing_product(venue, thing_type=ThingType.ACTIVATION)
            stock_activation = create_stock(offer=offer_activation, price=0)
            booking_date_activation = datetime(2019, 9, 21, 12, 0, 0)
            booking_activation = create_booking(user, stock_activation, date_created=booking_date_activation)
            PcObject.save(booking_cinema, booking_audiovisuel, booking_activation)

            # When
            experimentation_users = get_all_experimentation_users_details()

            # Then
            assert experimentation_users.loc[0, 'Date de première réservation dans 3 catégories différentes'] == None

