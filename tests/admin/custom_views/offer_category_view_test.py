from unittest.mock import patch

import pytest

import pcapi.core.offers.factories as offers_factories
import pcapi.core.users.factories as users_factories

from tests.conftest import TestClient


@pytest.mark.usefixtures("db_session")
class OfferCategoryViewTest:
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    @patch("pcapi.admin.custom_views.offer_category_view.send_categories_modification_to_data")
    def test_create_category_and_send_mail_to_data(
        self,
        mocked_send_categories_modification_to_data,
        mocked_validate_csrf_token,
        app,
    ):
        # Given
        users_factories.UserFactory(email="admin@example.com", isAdmin=True)

        data = dict(name="category", appLabel="category", proLabel="category", action="save")
        client = TestClient(app.test_client()).with_auth("admin@example.com")

        # When
        response = client.post("/pc/back-office/offer_categories/new?", form=data)

        # Then
        assert response.status_code == 302
        assert response.headers["location"] == "http://localhost/pc/back-office/offer_categories/"
        mocked_send_categories_modification_to_data.assert_called_once_with(
            "category", "admin@example.com", "http://localhost:5000/pc/back-office/offer_categories/"
        )


@pytest.mark.usefixtures("db_session")
class OfferSubcategoryViewTest:
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    @patch("pcapi.admin.custom_views.offer_category_view.send_subcategories_modification_to_data")
    def test_create_subcategory_and_send_mail_to_data(
        self,
        mocked_send_subcategories_modification_to_data,
        mocked_validate_csrf_token,
        app,
    ):
        # Given
        users_factories.UserFactory(email="admin@example.com", isAdmin=True)
        offers_factories.OfferCategoryFactory(name="theatre")

        data = dict(
            name="subcategory",
            appLabel="subcategory",
            proLabel="subcategory",
            category="1",
            isActive="y",
            action="save",
        )
        client = TestClient(app.test_client()).with_auth("admin@example.com")

        # When
        response = client.post("/pc/back-office/offer_subcategories/new?", form=data)

        # Then
        assert response.status_code == 302
        assert response.headers["location"] == "http://localhost/pc/back-office/offer_subcategories/"
        mocked_send_subcategories_modification_to_data.assert_called_once_with(
            "subcategory", "admin@example.com", "http://localhost:5000/pc/back-office/offer_subcategories/"
        )
