import pytest

from datetime import datetime
from repository import repository
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_user
from models import User
from use_cases.update_user_informations import AlterableUserInformations, update_user_informations

class UpdateUserInformationsTest:
    @clean_database
    def test_should_return_user_with_proper_infos(self, app):
        # Given
        user = create_user()
        repository.save(user)

        user_informations = AlterableUserInformations(
            id=user.id,
            has_seen_tutorials=True,
            cultural_survey_id=None,
            cultural_survey_filled_date=datetime(2020, 4, 22),
            department_code='27',
            email='han@solo.sw',
            needs_to_fill_cultural_survey=False,
            phone_number='05 55 55 55 55',
            postal_code='27200',
            public_name='Han Solo',
        )

        # When
        user = update_user_informations(user_informations)

        # Then
        assert user.hasSeenTutorials == True
        assert user.culturalSurveyId == None
        assert user.culturalSurveyFilledDate == datetime(2020, 4, 22)
        assert user.departementCode == '27'
        assert user.email == 'han@solo.sw'
        assert user.needsToFillCulturalSurvey == False
        assert user.phoneNumber == '05 55 55 55 55'
        assert user.postalCode == '27200'
        assert user.publicName == 'Han Solo'


    @clean_database
    def test_should_not_update_user_info_if_not_given(self, app):
        # Given
        user = create_user(phone_number='01 02 03 04 05')
        repository.save(user)

        user_informations = AlterableUserInformations(
            id=user.id,
            has_seen_tutorials=True,
        )

        # When
        updatedUser = update_user_informations(user_informations)

        # Then
        assert updatedUser.hasSeenTutorials == True
        assert updatedUser.phoneNumber == '01 02 03 04 05'
