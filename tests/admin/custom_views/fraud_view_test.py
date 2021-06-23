import pytest

import pcapi.core.fraud.factories as fraud_factories
import pcapi.core.fraud.models as fraud_models
import pcapi.core.users.factories as users_factories
import pcapi.core.users.models as users_models


@pytest.mark.usefixtures("db_session")
class BeneficiaryFraudListViewTest:
    def test_list_view(self, client):
        admin = users_factories.UserFactory(email="admin@example.com", isAdmin=True)
        client.with_auth(admin.email)

        user = users_factories.UserFactory()
        fraud_factories.BeneficiaryFraudCheckFactory(user=user)
        fraud_factories.BeneficiaryFraudResultFactory(user=user)
        response = client.get("/pc/back-office/beneficiary_fraud/")
        assert response.status_code == 200


@pytest.mark.usefixtures("db_session")
class BeneficiaryFraudDetailViewTest:
    def test_detail_view(self, client):
        admin = users_factories.UserFactory(email="admin@example.com", isAdmin=True)
        user = users_factories.UserFactory()
        fraud_factories.BeneficiaryFraudCheckFactory(user=user)
        fraud_factories.BeneficiaryFraudResultFactory(user=user)
        client.with_auth(admin.email)
        response = client.get("/pc/back-office/beneficiary_fraud/?id={user.id}")
        assert response.status_code == 200


@pytest.mark.usefixtures("db_session")
class BeneficiaryFraudValidationViewTest:
    def test_validation_view_auth_required(self, client):
        user = users_factories.UserFactory()
        response = client.post(f"/pc/back-office/beneficiary_fraud/validate/beneficiary/{user.id}")
        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/pc/back-office/"

    def test_validation_view_validate_user(self, client):
        user = users_factories.UserFactory(isBeneficiary=False)
        admin = users_factories.UserFactory(isAdmin=True)
        client.with_auth(admin.email)

        response = client.post(
            f"/pc/back-office/beneficiary_fraud/validate/beneficiary/{user.id}",
            form={"user_id": user.id, "reason": "User is granted", "review": "OK"},
        )
        assert response.status_code == 302

        review = fraud_models.BeneficiaryFraudReview.query.filter_by(user=user, author=admin).one()
        assert review.review == fraud_models.FraudReviewStatus.OK
        assert review.reason == "User is granted"
        user = users_models.User.query.get(user.id)
        assert user.isBeneficiary is True
        assert len(user.deposits) == 1

    def test_validation_view_validate_user_wrong_args(self, client):
        user = users_factories.UserFactory(isBeneficiary=False)
        admin = users_factories.UserFactory(isAdmin=True)

        client.with_auth(admin.email)

        response = client.post(
            f"/pc/back-office/beneficiary_fraud/validate/beneficiary/{user.id}",
            form={"user_id": user.id, "badkey": "User is granted", "review": "OK"},
        )
        assert response.status_code == 302
        review = fraud_models.BeneficiaryFraudReview.query.filter_by(user=user, author=admin).one_or_none()
        assert review is None

        user = users_models.User.query.get(user.id)
        assert user.isBeneficiary is False
        assert user.deposits == []

    def test_validation_view_validate_user_already_reviewed(self, client):
        user = users_factories.UserFactory(isBeneficiary=False)
        admin = users_factories.UserFactory(isAdmin=True)
        expected_review = fraud_factories.BeneficiaryFraudReviewFactory(user=user, author=admin)
        client.with_auth(admin.email)

        response = client.post(
            f"/pc/back-office/beneficiary_fraud/validate/beneficiary/{user.id}",
            form={"user_id": user.id, "reason": "User is granted", "review": "OK"},
        )
        assert response.status_code == 302
        review = fraud_models.BeneficiaryFraudReview.query.filter_by(user=user, author=admin).one()
        assert review.reason == expected_review.reason
