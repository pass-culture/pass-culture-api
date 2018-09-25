import secrets
from unittest.mock import patch, Mock

import pytest

from domain.user_emails import send_user_driven_cancellation_email_to_user, \
    send_user_driven_cancellation_email_to_offerer, send_offerer_driven_cancellation_email_to_user, \
    send_offerer_driven_cancellation_email_to_offerer, \
    send_booking_confirmation_email_to_user, send_booking_recap_emails, send_final_booking_recap_email, \
    send_validation_confirmation_email
from models import Offerer, UserOfferer, User, RightsType
from tests.utils_mailing_test import HTML_USER_BOOKING_EVENT_CONFIRMATION_EMAIL, \
    SUBJECT_USER_EVENT_BOOKING_CONFIRMATION_EMAIL
from utils.config import IS_PROD, ENV
from utils.mailing import MailServiceException
from utils.test_utils import create_user, create_booking, create_stock_with_event_offer, create_offerer, create_venue, \
    create_user_offerer, create_thing_offer, create_stock_with_thing_offer


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_user_when_feature_send_mail_to_users_enabled(app):
    # Given
    user = create_user(email='user@email.fr')
    booking = create_booking(user)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_user_booking_recap_email',
            return_value={'Html-part': ''}) as make_user_recap_email:
        # When
        send_user_driven_cancellation_email_to_user(booking, mocked_send_create_email)

        # Then
        make_user_recap_email.assert_called_once_with(booking, is_cancellation=True)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'user@email.fr'
    mocked_send_create_email.reset_mock()
    make_user_recap_email.reset_mock()


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_user_when_feature_send_mail_to_users_disabled(app):
    # Given
    user = create_user(email='user@email.fr')
    booking = create_booking(user)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=False), patch(
            'domain.user_emails.make_user_booking_recap_email',
            return_value={'Html-part': ''}) as make_user_recap_email:
        # When
        send_user_driven_cancellation_email_to_user(booking, mocked_send_create_email)

        # Then
        make_user_recap_email.assert_called_once_with(booking, is_cancellation=True)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture-dev@beta.gouv.fr'
    assert 'This is a test' in args[1]['data']['Html-part']
    mocked_send_create_email.reset_mock()
    make_user_recap_email.reset_mock()


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_user_when_status_code_400(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer, booking_email='booking@email.fr')
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock, venue)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 400
    mocked_send_create_email.return_value = return_value

    # When
    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=False), patch(
            'domain.user_emails.make_offerer_booking_recap_email_after_user_action',
            return_value={'Html-part': ''}), pytest.raises(MailServiceException):
        send_user_driven_cancellation_email_to_user(booking, mocked_send_create_email)


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_offerer_when_feature_send_mail_to_users_enabled(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer, booking_email='booking@email.fr')
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock, venue)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_booking_recap_email_after_user_action',
            return_value={'Html-part': ''}) as make_offerer_recap_email:
        # When
        send_user_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)

        # Then
        make_offerer_recap_email.assert_called_once_with(booking, is_cancellation=True)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'booking@email.fr'
    mocked_send_create_email.reset_mock()
    make_offerer_recap_email.reset_mock()


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_offerer_when_feature_send_mail_to_users_disabled(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer, booking_email='booking@email.fr')
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock, venue)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=False), patch(
            'domain.user_emails.make_offerer_booking_recap_email_after_user_action',
            return_value={'Html-part': ''}) as make_offerer_recap_email:
        # When
        send_user_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)

        # Then
        make_offerer_recap_email.assert_called_once_with(booking, is_cancellation=True)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture-dev@beta.gouv.fr'
    assert 'This is a test' in args[1]['data']['Html-part']
    mocked_send_create_email.reset_mock()
    make_offerer_recap_email.reset_mock()


@pytest.mark.standalone
def test_send_user_driven_cancellation_email_to_offerer_when_status_code_400(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer, booking_email='booking@email.fr')
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock, venue)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 400
    mocked_send_create_email.return_value = return_value

    # When
    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=False), patch(
            'domain.user_emails.make_offerer_booking_recap_email_after_user_action',
            return_value={'Html-part': ''}), pytest.raises(MailServiceException):
        send_user_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)


@pytest.mark.standalone
def test_send_offerer_driven_cancellation_email_to_user_when_feature_send_mail_to_users_enabled(app):
    # Given
    user = create_user(email='user@email.fr')
    booking = create_booking(user)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_driven_cancellation_email_for_user',
            return_value={'Html-part': ''}) as make_cancellation_email:
        # When
        send_offerer_driven_cancellation_email_to_user(booking, mocked_send_create_email)

        # Then
        make_cancellation_email.assert_called_once_with(booking)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'user@email.fr'
    mocked_send_create_email.reset_mock()
    make_cancellation_email.reset_mock()


@pytest.mark.standalone
def test_send_offerer_driven_cancellation_email_to_user_when_status_code_400(app):
    # Given
    user = create_user(email='user@email.fr')
    booking = create_booking(user)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 400
    mocked_send_create_email.return_value = return_value

    # When
    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_driven_cancellation_email_for_user',
            return_value={'Html-part': ''}), pytest.raises(MailServiceException):
        send_offerer_driven_cancellation_email_to_user(booking, mocked_send_create_email)


@pytest.mark.standalone
def test_send_offerer_driven_cancellation_email_to_offerer_when_booking_email(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer)
    venue.bookingEmail = 'booking@email.fr'
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_driven_cancellation_email_for_offerer',
            return_value={'Html-part': ''}) as make_cancellation_email:
        # When
        send_offerer_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)

        # Then
        make_cancellation_email.assert_called_once_with(booking)
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'booking@email.fr'
    mocked_send_create_email.reset_mock()
    make_cancellation_email.reset_mock()


@pytest.mark.standalone
def test_send_offerer_driven_cancellation_email_to_offerer_when_no_booking_email(app):
    # Given
    user = create_user(email='user@email.fr')
    offerer = create_offerer()
    venue = create_venue(offerer)
    venue.bookingEmail = None
    stock = create_stock_with_event_offer(offerer, venue)
    booking = create_booking(user, stock)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_driven_cancellation_email_for_offerer',
            return_value={'Html-part': ''}) as make_cancellation_email:
        # When
        send_offerer_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)

        # Then
        make_cancellation_email.assert_not_called()
    mocked_send_create_email.assert_not_called()
    mocked_send_create_email.reset_mock()
    make_cancellation_email.reset_mock()


@pytest.mark.standalone
def test_send_offerer_driven_cancellation_email_to_offerer_when_status_code_400(app):
    # Given
    user = create_user(email='user@email.fr')
    booking = create_booking(user)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 400
    mocked_send_create_email.return_value = return_value

    # When
    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_offerer_driven_cancellation_email_for_offerer',
            return_value={'Html-part': ''}), pytest.raises(MailServiceException):
        send_offerer_driven_cancellation_email_to_offerer(booking, mocked_send_create_email)


@pytest.mark.standalone
def test_send_booking_confirmation_email_to_user_should_call_mailjet_send_create(app):
    # Given
    venue = create_venue(None, 'Test offerer', 'reservations@test.fr', '123 rue test', '93000', 'Test city', '93')
    stock = create_stock_with_event_offer(offerer=None,
                                          venue=venue)
    user = create_user('Test', departement_code='93', email='test@email.com', can_book_free_offers=True)
    booking = create_booking(user, stock, venue, None)
    booking.token = '56789'
    mail_html = HTML_USER_BOOKING_EVENT_CONFIRMATION_EMAIL

    if IS_PROD:
        recipients = 'test@email.com'
    else:
        beginning_email = \
            '<p>This is a test (ENV={}). In production, email would have been sent to : test@email.com</p>'.format(ENV)
        recipients = 'passculture-dev@beta.gouv.fr'
        mail_html = beginning_email + mail_html

    expected_email = {
        "FromName": 'Pass Culture',
        'FromEmail': 'passculture-dev@beta.gouv.fr',
        'To': recipients,
        'Subject': SUBJECT_USER_EVENT_BOOKING_CONFIRMATION_EMAIL,
        'Html-part': mail_html
    }

    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    # When
    send_booking_confirmation_email_to_user(booking, mocked_send_create_email)

    # Then
    mocked_send_create_email.assert_called_once_with(data=expected_email)


@pytest.mark.standalone
def test_send_booking_recap_emails_does_not_send_email_to_offer_booking_email_if_feature_is_disabled(app):
    # given
    user = create_user()
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_thing_offer(venue, booking_email='offer.booking.email@test.com')
    stock = create_stock_with_thing_offer(offerer, venue, offer)
    booking = create_booking(user, stock)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users:
        send_mail_to_users.return_value = False
        # when
        send_booking_recap_emails(booking, mocked_send_create_email)

        # then
        mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture-dev@beta.gouv.fr'


@pytest.mark.standalone
def test_send_booking_recap_emails_sends_email_to_offer_booking_email_if_feature_is_enabled(app):
    # given
    user = create_user()
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_thing_offer(venue, booking_email='offer.booking.email@test.com')
    stock = create_stock_with_thing_offer(offerer, venue, offer)
    booking = create_booking(user, stock)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users:
        send_mail_to_users.return_value = True
        # when
        send_booking_recap_emails(booking, mocked_send_create_email)

    # then
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert 'offer.booking.email@test.com' in args[1]['data']['To']
    assert 'passculture@beta.gouv.fr' in args[1]['data']['To']


@pytest.mark.standalone
def test_send_booking_recap_emails_email_sends_email_only_to_passculture_if_feature_is_enabled_but_no_offer_booking_email(
        app):
    # given
    user = create_user()
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_thing_offer(venue, booking_email=None)
    stock = create_stock_with_thing_offer(offerer, venue, offer, booking_email=None)
    booking = create_booking(user, stock)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users:
        send_mail_to_users.return_value = True
        # when
        send_booking_recap_emails(booking, mocked_send_create_email)

    # then
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture@beta.gouv.fr'


@pytest.mark.standalone
def test_send_final_booking_recap_email_does_not_send_email_to_offer_booking_email_if_feature_is_disabled(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    stock = create_stock_with_event_offer(offerer, venue, booking_email='offer.booking.email@test.com')
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users, patch(
            'domain.user_emails.set_booking_recap_sent_and_save') as set_booking_recap_sent_and_save:
        send_mail_to_users.return_value = False
        # when
        send_final_booking_recap_email(stock, mocked_send_create_email)

    # then
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture-dev@beta.gouv.fr'
    set_booking_recap_sent_and_save.assert_called_once_with(stock)


@pytest.mark.standalone
def test_send_final_booking_recap_email_sends_email_to_offer_booking_email_if_feature_is_enabled(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    stock = create_stock_with_event_offer(offerer, venue, booking_email='offer.booking.email@test.com')
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users, patch(
            'domain.user_emails.set_booking_recap_sent_and_save') as set_booking_recap_sent_and_save:
        send_mail_to_users.return_value = True
        # when
        send_final_booking_recap_email(stock, mocked_send_create_email)

    # then
    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert 'offer.booking.email@test.com' in args[1]['data']['To']
    assert 'passculture@beta.gouv.fr' in args[1]['data']['To']
    set_booking_recap_sent_and_save.assert_called_once_with(stock)


@pytest.mark.standalone
def test_send_final_booking_recap_email_sends_email_only_to_passculture_if_feature_is_enabled_but_no_offer_booking_email(
        app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    stock = create_stock_with_event_offer(offerer, venue, booking_email=None)
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled') as send_mail_to_users, patch(
            'domain.user_emails.set_booking_recap_sent_and_save') as set_booking_recap_sent_and_save:
        send_mail_to_users.return_value = True
        # when
        send_final_booking_recap_email(stock, mocked_send_create_email)

        # then
        mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'passculture@beta.gouv.fr'
    set_booking_recap_sent_and_save.assert_called_once_with(stock)


@pytest.mark.standalone
def test_send_validation_confirmation_email(app):
    # Given
    offerer = Offerer()
    user_offerer = UserOfferer()
    user_offerer.rights = RightsType.editor
    user_offerer.user = User(email='test@email.com')
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 200
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_validation_confirmation_email',
            return_value={'Html-part': ''}) as make_cancellation_email, patch(
        'domain.user_emails.find_all_admin_offerer_emails', return_value=['admin1@email.com', 'admin2@email.com']):
        # When
        send_validation_confirmation_email(user_offerer, offerer, mocked_send_create_email)

    # Then
    make_cancellation_email.assert_called_once_with(user_offerer, offerer)

    mocked_send_create_email.assert_called_once()
    args = mocked_send_create_email.call_args
    assert args[1]['data']['To'] == 'admin1@email.com, admin2@email.com'
    mocked_send_create_email.reset_mock()
    make_cancellation_email.reset_mock()


@pytest.mark.standalone
def test_send_validation_confirmation_email_when_status_code_400(app):
    # Given
    offerer = Offerer()
    user_offerer = UserOfferer()
    user_offerer.user = User(email='test@email.com')
    mocked_send_create_email = Mock()
    return_value = Mock()
    return_value.status_code = 400
    mocked_send_create_email.return_value = return_value

    with patch('domain.user_emails.feature_send_mail_to_users_enabled', return_value=True), patch(
            'domain.user_emails.make_validation_confirmation_email', return_value={'Html-part': ''}), patch(
            'domain.user_emails.find_user_offerer_email', return_value='test@email.com'), pytest.raises(
            MailServiceException):
        # When
        send_validation_confirmation_email(user_offerer, offerer, mocked_send_create_email)
