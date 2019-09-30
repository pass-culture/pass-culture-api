from datetime import datetime, timedelta

from models import PcObject, EventType, ThingType, Venue
from tests.test_utils import create_offerer, create_bank_information, create_venue, create_offer_with_event_product, \
    create_event_occurrence, create_stock, create_stock_from_event_occurrence, create_user, create_deposit, \
    create_booking, create_offer_with_thing_product, create_recommendation
from utils.logger import logger

now = datetime.utcnow()
three_days = timedelta(days=3)
two_hours = timedelta(hours=2)


def save_users_with_deposits():
    user1 = create_user(email='user1@test.com', can_book_free_offers=True)
    user2 = create_user(email='user2@test.com', can_book_free_offers=True)
    user3 = create_user(email='user3@test.com', can_book_free_offers=True)
    user4 = create_user(email='user4@test.com', can_book_free_offers=True)
    user5 = create_user(email='user5@test.com', can_book_free_offers=True)
    deposit1 = create_deposit(user1, amount=500)
    deposit2 = create_deposit(user2, amount=500)
    deposit3 = create_deposit(user3, amount=500)
    deposit4 = create_deposit(user4, amount=500)
    deposit5 = create_deposit(user5, amount=500)
    PcObject.save(deposit1, deposit2, deposit3, deposit4, deposit5)
    logger.info('created 5 users with 500 € deposits')
    return user1, user2, user3, user4, user5


def save_offerer_with_iban():
    offerer_with_iban = create_offerer(siren='180046021', name='Philarmonie')
    venue_with_siret = create_venue(offerer=offerer_with_iban, siret='18004602100026', is_virtual=False)
    venue_without_siret = create_venue(offerer=offerer_with_iban, siret=None, is_virtual=False, comment='pas de siret')
    venue_online = create_venue(offerer=offerer_with_iban, siret=None, is_virtual=True)
    bank_information = create_bank_information(
        offerer=offerer_with_iban, bic='TRPUFRP1',
        iban='FR7610071750000000100420866', application_id=1,
        id_at_providers=offerer_with_iban.siren
    )
    PcObject.save(bank_information, venue_online, venue_with_siret, venue_without_siret)
    logger.info('created 1 offerer with iban and 1 virtual venue, 1 venue with siret and 1 venue without siret')
    return venue_online, venue_with_siret, venue_without_siret


def save_offerer_without_iban():
    offerer_without_iban = create_offerer(siren='213400328', name='Béziers')
    venue_with_siret_with_iban = create_venue(offerer=offerer_without_iban, siret='21340032800018', is_virtual=False)
    venue_with_siret_without_iban = create_venue(offerer=offerer_without_iban, siret='21340032800802', is_virtual=False)
    venue_online = create_venue(offerer=offerer_without_iban, siret=None, is_virtual=True)

    bank_information = create_bank_information(
        venue=venue_with_siret_with_iban, bic='BDFEFRPPCCT',
        iban='FR733000100206C343000000066', application_id=2,
        id_at_providers=venue_with_siret_with_iban.siret
    )
    PcObject.save(bank_information, venue_online, venue_with_siret_with_iban, venue_with_siret_without_iban)
    logger.info('created 1 offerer without iban and 1 virtual venue, 1 venue with siret with iban and 1 venue with siret without iban')
    return venue_online, venue_with_siret_with_iban, venue_with_siret_without_iban


def save_free_event_offer_with_stocks(venue: Venue):
    free_event_offer = create_offer_with_event_product(venue, event_name='Free event',
                                                       event_type=EventType.SPECTACLE_VIVANT)
    past_occurrence = create_event_occurrence(free_event_offer, beginning_datetime=now - three_days,
                                              end_datetime=now - three_days + two_hours)
    future_occurrence = create_event_occurrence(free_event_offer, beginning_datetime=now + three_days,
                                                end_datetime=now + three_days + two_hours)
    past_free_event_stock = create_stock_from_event_occurrence(past_occurrence, price=0)
    future_free_event_stock = create_stock_from_event_occurrence(future_occurrence, price=0)
    PcObject.save(past_free_event_stock, future_free_event_stock)
    logger.info('created 1 event offer with 1 past and 1 future occurrence with 1 free stock each')
    return past_free_event_stock, future_free_event_stock


def save_non_reimbursable_thing_offer(venue: Venue):
    paid_non_reimbursable_offer = create_offer_with_thing_product(venue, thing_name='Concert en ligne',
                                                                  thing_type=ThingType.JEUX_VIDEO, url='http://my.game.fr')
    non_reimbursable_stock = create_stock(price=30, offer=paid_non_reimbursable_offer)
    PcObject.save(non_reimbursable_stock)
    logger.info('created 1 non reimbursable thing offer with 1 paid stock of 30 €')
    return non_reimbursable_stock


def save_reimbursable_thing_offer(venue: Venue):
    paid_reimbursable_offer = create_offer_with_thing_product(venue, thing_name='Roman cool',
                                                              thing_type=ThingType.LIVRE_EDITION)
    reimbursable_stock = create_stock(price=30, offer=paid_reimbursable_offer)
    PcObject.save(reimbursable_stock)
    logger.info('created 1 reimbursable thing offer with 1 paid stock of 30 €')
    return reimbursable_stock


def save_paid_online_book_offer(venue: Venue):
    paid_reimbursable_offer = create_offer_with_thing_product(venue, thing_name='Roman cool',
                                                              thing_type=ThingType.LIVRE_EDITION, url='https://mycoolbook.fr')
    reimbursable_stock = create_stock(price=20, offer=paid_reimbursable_offer)
    PcObject.save(reimbursable_stock)
    logger.info('created 1 online book offer with 1 paid stock of 20 €')
    return reimbursable_stock


def save_paid_reimbursable_event_offer(venue: Venue):
    paid_reimbursable_event_offer = create_offer_with_event_product(venue, event_name='Paid event',
                                                                    event_type=EventType.SPECTACLE_VIVANT)
    past_occurrence = create_event_occurrence(paid_reimbursable_event_offer, beginning_datetime=now - three_days,
                                              end_datetime=now - three_days + two_hours)
    future_occurrence = create_event_occurrence(paid_reimbursable_event_offer, beginning_datetime=now + three_days,
                                                end_datetime=now + three_days + two_hours)
    past_event_stock = create_stock_from_event_occurrence(past_occurrence, price=10)
    future_event_stock = create_stock_from_event_occurrence(future_occurrence, price=10)
    PcObject.save(past_event_stock, future_event_stock)
    logger.info('created 1 event offer with 1 past and 1 future occurrence with 1 paid stock of 10 € each')
    return past_event_stock, future_event_stock


def save_sandbox():
    user1, user2, user3, user4, user5 = save_users_with_deposits()
    venue_online_of_offerer_with_iban, venue_with_siret_of_offerer_with_iban, venue_without_siret_of_offerer_with_iban \
        = save_offerer_with_iban()
    venue_online_of_offerer_without_iban, venue_of_offerer_without_iban_with_siret_with_iban,\
    venue_of_offerer_without_iban_with_siret_without_iban = save_offerer_without_iban()
    past_free_event_stock, future_free_event_stock = save_free_event_offer_with_stocks(
        venue_with_siret_of_offerer_with_iban)
    non_reimbursable_stock_of_offerer_with_iban = save_non_reimbursable_thing_offer(venue_online_of_offerer_with_iban)
    reimbursable_stock_of_offerer_with_iban = save_reimbursable_thing_offer(venue_with_siret_of_offerer_with_iban)
    past_event_stock_of_offerer_with_iban, future_event_stock_of_offerer_with_iban \
        = save_paid_reimbursable_event_offer(venue_without_siret_of_offerer_with_iban)

    past_event_stock_of_offerer_without_iban, future_event_stock_of_offerer_without_iban \
        = save_paid_reimbursable_event_offer(venue_of_offerer_without_iban_with_siret_without_iban)

    reimbursable_stock_of_offerer_without_iban = save_reimbursable_thing_offer(venue_of_offerer_without_iban_with_siret_with_iban)
    online_book_stock_of_offerer_without_iban = save_paid_online_book_offer(venue_online_of_offerer_with_iban)

    bookings = [
        create_booking(
            user1,
            recommendation=create_recommendation(offer=past_free_event_stock.resolvedOffer, user=user1),
            stock=past_free_event_stock,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKEN1',
            is_used=False
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=past_free_event_stock.resolvedOffer, user=user2),
            stock=past_free_event_stock,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKEN2',
            is_used=False
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=past_free_event_stock.resolvedOffer, user=user3),
            stock=past_free_event_stock,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKEN3',
            is_used=False
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=future_free_event_stock.resolvedOffer, user=user4),
            stock=future_free_event_stock,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKEN4',
            is_used=True
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=future_free_event_stock.resolvedOffer, user=user5),
            stock=future_free_event_stock,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKEN5',
            is_used=False
        ),
        create_booking(
            user1,
            recommendation=create_recommendation(offer=non_reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user1),
            stock=non_reimbursable_stock_of_offerer_with_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKEN6',
            is_used=True
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=non_reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user2),
            stock=non_reimbursable_stock_of_offerer_with_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKEN7',
            is_used=True
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=non_reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user3),
            stock=non_reimbursable_stock_of_offerer_with_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKEN8',
            is_used=True
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=non_reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user4),
            stock=non_reimbursable_stock_of_offerer_with_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKEN9',
            is_used=False
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=non_reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user5),
            stock=non_reimbursable_stock_of_offerer_with_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE10',
            is_used=False
        ),
        create_booking(
            user1,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user1),
            stock=reimbursable_stock_of_offerer_with_iban,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKE11',
            is_used=True
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user2),
            stock=reimbursable_stock_of_offerer_with_iban,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKE12',
            is_used=True
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user3),
            stock=reimbursable_stock_of_offerer_with_iban,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKE13',
            is_used=True
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user4),
            stock=reimbursable_stock_of_offerer_with_iban,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKE14',
            is_used=False
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user5),
            stock=reimbursable_stock_of_offerer_with_iban,
            venue=venue_with_siret_of_offerer_with_iban,
            token='TOKE15',
            is_used=False
        ),
        create_booking(
            user1,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_with_iban.resolvedOffer, user=user1),
            stock=past_event_stock_of_offerer_with_iban,
            venue=venue_without_siret_of_offerer_with_iban,
            token='TOKE16',
            is_used=True
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_with_iban.resolvedOffer, user=user2),
            stock=past_event_stock_of_offerer_with_iban,
            venue=venue_without_siret_of_offerer_with_iban,
            token='TOKE17',
            is_used=True
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_with_iban.resolvedOffer, user=user3),
            stock=past_event_stock_of_offerer_with_iban,
            venue=venue_without_siret_of_offerer_with_iban,
            token='TOKE18',
            is_used=False
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=future_event_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user4),
            stock=future_event_stock_of_offerer_with_iban,
            venue=venue_without_siret_of_offerer_with_iban,
            token='TOKE19',
            is_used=True
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=future_event_stock_of_offerer_with_iban.resolvedOffer,
                                                 user=user5),
            stock=future_event_stock_of_offerer_with_iban,
            venue=venue_without_siret_of_offerer_with_iban,
            token='TOKE20',
            is_used=False
        ),

        create_booking(
            user1,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user1),
            stock=past_event_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_without_iban,
            token='TOKE21',
            is_used=True
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user2),
            stock=past_event_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_without_iban,
            token='TOKE22',
            is_used=True
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=past_event_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user3),
            stock=past_event_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_without_iban,
            token='TOKE23',
            is_used=False
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=future_event_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user4),
            stock=future_event_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_without_iban,
            token='TOKE24',
            is_used=True
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=future_event_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user5),
            stock=future_event_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_without_iban,
            token='TOKE25',
            is_used=False
        ),
        create_booking(
            user1,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user1),
            stock=reimbursable_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_with_iban,
            token='TOKE26',
            is_used=False
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user2),
            stock=reimbursable_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_with_iban,
            token='TOKE27',
            is_used=False
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user3),
            stock=reimbursable_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_with_iban,
            token='TOKE28',
            is_used=False
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user4),
            stock=reimbursable_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_with_iban,
            token='TOKE29',
            is_used=True
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=reimbursable_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user5),
            stock=reimbursable_stock_of_offerer_without_iban,
            venue=venue_of_offerer_without_iban_with_siret_with_iban,
            token='TOKE30',
            is_used=True
        ),
        create_booking(
            user1,
            recommendation=create_recommendation(offer=online_book_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user1),
            stock=online_book_stock_of_offerer_without_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE31',
            is_used=False
        ),
        create_booking(
            user2,
            recommendation=create_recommendation(offer=online_book_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user2),
            stock=online_book_stock_of_offerer_without_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE32',
            is_used=False
        ),
        create_booking(
            user3,
            recommendation=create_recommendation(offer=online_book_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user3),
            stock=online_book_stock_of_offerer_without_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE33',
            is_used=False
        ),
        create_booking(
            user4,
            recommendation=create_recommendation(offer=online_book_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user4),
            stock=online_book_stock_of_offerer_without_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE34',
            is_used=True
        ),
        create_booking(
            user5,
            recommendation=create_recommendation(offer=online_book_stock_of_offerer_without_iban.resolvedOffer,
                                                 user=user5),
            stock=online_book_stock_of_offerer_without_iban,
            venue=venue_online_of_offerer_with_iban,
            token='TOKE35',
            is_used=True
        )
    ]

    logger.info('created %s bookings' % len(bookings))
    PcObject.save(*bookings)
