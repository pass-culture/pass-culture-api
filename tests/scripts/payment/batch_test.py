from unittest.mock import patch

import pytest

from pcapi.models import Feature
from pcapi.models.feature import FeatureToggle
from pcapi.repository import repository
from pcapi.scripts.payment.batch import generate_and_send_payments

from tests.test_utils import deactivate_feature


class GenerateAndSendPaymentsTest:
    @patch("pcapi.scripts.payment.batch.update_booking_used_after_stock_occurrence")
    @patch("pcapi.scripts.payment.batch.get_payments_by_message_id")
    @patch("pcapi.scripts.payment.batch.generate_new_payments", return_value=([], []))
    @patch("pcapi.scripts.payment.batch.set_not_processable_payments_with_bank_information_to_retry", return_value=[])
    @patch("pcapi.scripts.payment.batch.concatenate_payments_with_errors_and_retries", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_transactions", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_report", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_details", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_wallet_balances", return_value=[])
    @pytest.mark.usefixtures("db_session")
    def test_should_retrieve_all_steps_except_1_bis_when_message_id_is_none(
        self,
        send_wallet_balances,
        send_payments_details,
        send_payments_report,
        send_transactions,
        concatenate_payments_with_errors_and_retries,
        set_not_processable_payments_with_bank_information_to_retry,
        generate_new_payments,
        get_payments_by_message_id,
        update_booking_used_after_stock_occurrence,
        app,
    ):
        # Given
        feature = Feature.query.filter_by(name=FeatureToggle.DEGRESSIVE_REIMBURSEMENT_RATE).first()
        feature.isActive = False
        repository.save(feature)

        # When
        generate_and_send_payments(None)

        # Then
        generate_new_payments.assert_called_once()
        set_not_processable_payments_with_bank_information_to_retry.assert_called_once()
        concatenate_payments_with_errors_and_retries.assert_called_once()
        send_transactions.assert_called_once()
        send_payments_report.assert_called_once()
        send_payments_details.assert_called_once()
        send_wallet_balances.assert_called_once()
        update_booking_used_after_stock_occurrence.assert_called_once()
        get_payments_by_message_id.assert_not_called()

    @patch("pcapi.scripts.payment.batch.update_booking_used_after_stock_occurrence")
    @patch("pcapi.scripts.payment.batch.get_payments_by_message_id")
    @patch("pcapi.scripts.payment.batch.generate_new_payments", return_value=([], []))
    @patch("pcapi.scripts.payment.batch.set_not_processable_payments_with_bank_information_to_retry", return_value=[])
    @patch("pcapi.scripts.payment.batch.concatenate_payments_with_errors_and_retries", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_transactions", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_report", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_details", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_wallet_balances", return_value=[])
    @pytest.mark.usefixtures("db_session")
    def test_should_start_script_at_1_bis_step_when_message_id_is_provided(
        self,
        send_wallet_balances,
        send_payments_details,
        send_payments_report,
        send_transactions,
        concatenate_payments_with_errors_and_retries,
        set_not_processable_payments_with_bank_information_to_retry,
        generate_new_payments,
        get_payments_by_message_id,
        update_booking_used_after_stock_occurrence,
        app,
    ):
        # When
        generate_and_send_payments("ar5y65dtre45")

        # Then
        get_payments_by_message_id.assert_called_once()
        send_transactions.assert_called_once()
        send_payments_report.assert_called_once()
        send_payments_details.assert_called_once()
        send_wallet_balances.assert_called_once()
        generate_new_payments.assert_not_called()
        set_not_processable_payments_with_bank_information_to_retry.assert_not_called()
        concatenate_payments_with_errors_and_retries.assert_not_called()
        update_booking_used_after_stock_occurrence.assert_called_once()

    @patch("pcapi.scripts.payment.batch.update_booking_used_after_stock_occurrence")
    @patch("pcapi.scripts.payment.batch.get_payments_by_message_id")
    @patch("pcapi.scripts.payment.batch.generate_new_payments", return_value=([], []))
    @patch("pcapi.scripts.payment.batch.set_not_processable_payments_with_bank_information_to_retry", return_value=[])
    @patch("pcapi.scripts.payment.batch.concatenate_payments_with_errors_and_retries", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_transactions", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_report", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_payments_details", return_value=[])
    @patch("pcapi.scripts.payment.batch.send_wallet_balances", return_value=[])
    @pytest.mark.usefixtures("db_session")
    def test_should_not_update_booking_usage_if_corresponding_feature_is_disabled(
        self,
        send_wallet_balances,
        send_payments_details,
        send_payments_report,
        send_transactions,
        concatenate_payments_with_errors_and_retries,
        set_not_processable_payments_with_bank_information_to_retry,
        generate_new_payments,
        get_payments_by_message_id,
        update_booking_used_after_stock_occurrence,
        app,
    ):
        # Given
        deactivate_feature(FeatureToggle.UPDATE_BOOKING_USED)

        # When
        generate_and_send_payments("ar5y65dtre45")

        # Then
        update_booking_used_after_stock_occurrence.assert_not_called()
