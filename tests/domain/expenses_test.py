from domain.expenses import get_expenses
from models import ThingType, EventType
from tests.test_utils import create_booking_for_event, \
    create_booking_for_thing


class ExpensesTest:
    class ThingsTest:
        class AudiovisuelTest:
            def test_online_offer_is_a_digital_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url='http://on.line', type=ThingType.AUDIOVISUEL)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 50
                assert expenses['physical']['actual'] == 0

            def test_offline_offer_is_a_physical_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.AUDIOVISUEL)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 50

        class JeuxVideoTest:
            def test_online_offer_is_a_digital_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url='http://on.line', type=ThingType.JEUX_VIDEO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 50
                assert expenses['physical']['actual'] == 0

        class MusiqueTest:
            def test_online_offer_is_a_digital_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url='http://on.line', type=ThingType.MUSIQUE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 50
                assert expenses['physical']['actual'] == 0

            def test_offline_offer_is_a_physical_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.MUSIQUE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 50

        class PresseAboTest:
            def test_online_offer_is_a_digital_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url='http://on.line', type=ThingType.PRESSE_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 50
                assert expenses['physical']['actual'] == 0

        class LivreEditionTest:
            def test_online_offer_is_a_physical_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url='http://on.line', type=ThingType.LIVRE_EDITION)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['physical']['actual'] == 50
                assert expenses['digital']['actual'] == 0

            def test_offline_offer_is_a_physical_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.LIVRE_EDITION)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 50

        class JeuxTest:
            def test_offline_offer_is_a_physical_expense(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.JEUX)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 50

        class PratiqueArtistiqueAboTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.PRATIQUE_ARTISTIQUE_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class MusiqueAboTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.MUSIQUE_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class MuseesPatrimoineAboTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.MUSEES_PATRIMOINE_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class CinemaAboTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.CINEMA_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class InstrumentTest:
            def test_offline_offer_is_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.INSTRUMENT)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 50

        class JeuxAboTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_thing(amount=50, url=None, type=ThingType.JEUX_VIDEO_ABO)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

    class EventsTest:
        class CinemaTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.CINEMA)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class ConferenceDebatDedicaceTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.CONFERENCE_DEBAT_DEDICACE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class JeuxTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.JEUX)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class MusiqueTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.MUSIQUE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class MuseesPatrimoineTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.MUSEES_PATRIMOINE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class PratiqueArtistiqueTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.PRATIQUE_ARTISTIQUE)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

        class SpectacleVivantTest:
            def test_offline_offer_is_not_capped(self):
                # Given
                bookings = [
                    create_booking_for_event(amount=50, type=EventType.SPECTACLE_VIVANT)
                ]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital']['actual'] == 0
                assert expenses['physical']['actual'] == 0

    class ComputationTest:
        class MaxTest:
            def test_returns_max_500_and_actual_210(self):
                # Given
                booking_1 = create_booking_for_thing(amount=90)
                booking_2 = create_booking_for_event(amount=60, quantity=2)
                booking_3 = create_booking_for_event(amount=20, isCancelled=True)
                bookings = [booking_1, booking_2, booking_3]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['all'] == {'max': 500, 'actual': 210}

            def test_returns_max_500_and_actual_0(self):
                # Given
                bookings = []

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['all'] == {'max': 500, 'actual': 0}

        class PhysicalCapTest:
            def test_max_200_and_actual_50(self):
                # Given
                physical_cap_booking = create_booking_for_thing(amount=50, type=ThingType.AUDIOVISUEL)
                digital_cap_booking = create_booking_for_thing(url='http://test.com', amount=60,
                                                               type=ThingType.AUDIOVISUEL)

                bookings = [physical_cap_booking, digital_cap_booking]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['physical'] == {'max': 200, 'actual': 50}

            def test_max_200_and_actual_0(self):
                # Given
                booking_1 = create_booking_for_thing(url='http://test.com', amount=60)
                bookings = [booking_1]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['physical'] == {'max': 200, 'actual': 0}

        class DigitalCapTest:
            def test_returns_max_200_and_actual_110(self):
                # Given
                physical_cap_booking = create_booking_for_thing(amount=50, type=ThingType.CINEMA_ABO)
                digital_cap_booking = create_booking_for_thing(url='http://test.com', amount=110,
                                                               type=ThingType.MUSIQUE)

                bookings = [physical_cap_booking, digital_cap_booking]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital'] == {'max': 200, 'actual': 110}

            def test_returns_max_200_and_actual_0(self):
                # Given
                booking_1 = create_booking_for_thing(amount=50)
                bookings = [booking_1]

                # When
                expenses = get_expenses(bookings)

                # Then
                assert expenses['digital'] == {'max': 200, 'actual': 0}
