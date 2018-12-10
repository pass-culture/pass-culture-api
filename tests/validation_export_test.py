import pytest

from models import ApiErrors
from validation.exports import check_get_venues_params, check_get_offerers_params


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_date(app):
    # given
    not_valid_date = {}
    not_valid_date['from_date'] = '12/52-0001'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_date)

    # then
    assert errors.value.errors['date_format'] == ['to_date and from_date are of type yyyy-mm-dd']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_dpt_in_list(app):
    # given
    not_valid_dpt_list = {}
    not_valid_dpt_list['dpt'] = ['93', '17', 'Paris']

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_dpt_list)

    # then
    assert errors.value.errors['dpt'] == ['dpt is a list of type xx or xxx (2 or 3 digits), or 2A, or 2B :\
                ["34", "37"]']


@pytest.mark.standalone
def test_check_get_venues_params_doesnt_raise_api_error_for_valid_dpt_in_list(app):
    # given
    valid_dpt_list = {}
    valid_dpt_list['dpt'] = ['93', '17', '01', '2a', '2B', '978']

    # when
    try:
        check_get_venues_params(valid_dpt_list)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_dpt_list_is_not_list(app):
    # given
    not_valid_dpt_list = {}
    not_valid_dpt_list['dpt'] = '93'
    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_dpt_list)

    # then
    assert errors.value.errors['dpt'] == ['dpt is a list of type xx or xxx (2 or 3 digits), or 2A, or 2B :\
                ["34", "37"]']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_zip_codes_list(app):
    # given
    not_valid_zip_codes_list = {}
    not_valid_zip_codes_list['zip_codes'] = ['69000', '13020', '78sang40RpZ']

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_zip_codes_list)

    # then
    assert errors.value.errors['zip_codes'] == \
        ['zip_codes is a list of type xxxxx (5 digits, ex: 78140 ou 2a000) : \
        ["78140", "69007"]']


@pytest.mark.standalone
def test_check_get_venues_params_doesnt_raise_api_error_for_valid_zip_codes_list(app):
    # given
    valid_zip_codes_list = {}
    valid_zip_codes_list['zip_codes'] = ['69000', '13020', '2a250', '2B456', '00007']

    # when
    try:
        check_get_venues_params(valid_zip_codes_list)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_has_validated_offerer_param(app):
    # given
    not_valid_has_validated_offerer_param = {}
    not_valid_has_validated_offerer_param['has_validated_offerer'] = 'oui'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_has_validated_offerer_param)

    # then
    assert errors.value.errors['has_validated_offerer'] == ['has_validated_offerer is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_has_siret_param(app):
    # given
    not_valid_has_siret_param = {}
    not_valid_has_siret_param['has_siret'] = "peut-être"
    
    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_has_siret_param)

    # then
    assert errors.value.errors['has_siret'] == ['has_siret is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_is_virtual_param(app):
    # given
    not_valid_is_virtual_param = {}
    not_valid_is_virtual_param['is_virtual'] = "De type moderne"

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_is_virtual_param)

    # then
    assert errors.value.errors['is_virtual'] == ['is_virtual is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_is_validated_param(app):
    # given
    not_valid_is_validated_param = {}
    not_valid_is_validated_param['is_validated'] = 'plein'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_is_validated_param)

    # then
    assert errors.value.errors['is_validated'] == ['is_validated is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_has_offerer_with_siren_param(app):
    # given
    not_valid_has_offerer_with_siren_param = {}
    not_valid_has_offerer_with_siren_param['has_offerer_with_siren'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_has_offerer_with_siren_param)

    # then
    assert errors.value.errors['has_offerer_with_siren'] == ['has_offerer_with_siren is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_has_validated_user_offerer_param(app):
    # given
    not_valid_has_validated_user_offerer_param = {}
    not_valid_has_validated_user_offerer_param['has_validated_user_offerer'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_has_validated_user_offerer_param)

    # then
    assert errors.value.errors['has_validated_user_offerer'] == ['has_validated_user_offerer is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_has_validated_user_param(app):
    # given
    not_valid_has_validated_user_param = {}
    not_valid_has_validated_user_param['has_validated_user'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_has_validated_user_param)

    # then
    assert errors.value.errors['has_validated_user'] == ['has_validated_user is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_venues_params_raises_api_error_if_not_valid_offer_status_param(app):
    # given
    not_valid_offer_status_param = {}
    not_valid_offer_status_param['offer_status'] = 'I\'m not a valid status'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_venues_params(not_valid_offer_status_param)

    # then
    assert errors.value.errors['offer_status'] == ['offer_status accepte ALL ou VALID ou WITHOUT ou EXPIRED']


@pytest.mark.standalone
def test_check_get_venues_params_does_not_raise_api_error_if_good_param(app):
    # given
    params = {}
    params['dpt'] = ['32', '35', '36']
    params['has_validated_offerer'] = True
    params['zip_codes'] = ['32000', '35000', '36000']
    params['from_date'] = '2018-05-30'
    params['to_date'] = '2020-05-30'
    params['has_siret'] = False
    params['is_virtual'] = True
    params['offer_status'] = 'VALID'
    params["has_offerer_with_siren"] = True
    params["has_validated_user_offerer"] = True
    params["has_validated_user"] = False  

    # when
    try:
        check_get_venues_params(params)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_venues_params_does_not_raise_api_error_if_empty_param(app):
    # given
    params = {}
    
    # when
    try:
        check_get_venues_params(params)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_date(app):
    # given
    not_valid_date = {}
    not_valid_date['to_date'] = '12/52-0001'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_date)

    # then
    assert errors.value.errors['date_format'] == ['to_date and from_date are of type yyyy-mm-dd']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_dpt_in_list(app):
    # given
    not_valid_dpt_list = {}
    not_valid_dpt_list['dpt'] = ['93', '17', 'Paris']

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_dpt_list)

    # then
    assert errors.value.errors['dpt'] == ['dpt is a list of type xx or xxx (2 or 3 digits), or 2A, or 2B :\
                ["34", "37"]']


@pytest.mark.standalone
def test_check_get_offerers_params_doesnt_raise_api_error_for_valid_dpt_in_list(app):
    # given
    valid_dpt_list = {}
    valid_dpt_list['dpt'] = ['93', '17', '01', '2a', '2B', '978']

    # when
    try:
        check_get_offerers_params(valid_dpt_list)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_dpt_list_is_not_list(app):
    # given
    not_valid_dpt_list = {}
    not_valid_dpt_list['dpt'] = '93'
    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_dpt_list)

    # then
    assert errors.value.errors['dpt'] == ['dpt is a list of type xx or xxx (2 or 3 digits), or 2A, or 2B :\
                ["34", "37"]']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_zip_codes_list(app):
    # given
    not_valid_zip_codes_list = {}
    not_valid_zip_codes_list['zip_codes'] = ['69000', '13020', '78sang40RpZ', 78140]

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_zip_codes_list)

    # then
    assert errors.value.errors['zip_codes'] == \
        ['zip_codes is a list of type xxxxx (5 digits, ex: 78140 ou 2a000) : \
        ["78140", "69007"]']


@pytest.mark.standalone
def test_check_get_offerers_params_doesnt_raise_api_error_for_valid_siren_list(app):
    # given
    valid_siren_list = {}
    valid_siren_list['siren_list'] = ["123456789", "789654123"]

    # when
    try:
        check_get_offerers_params(valid_siren_list)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_siren_list(app):
    # given
    not_valid_siren_list = {}
    not_valid_siren_list['siren_list'] = ['69000', '13020', '78sang40RpZ', '121253654789', 123456789]

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_siren_list)

    # then
    assert errors.value.errors['siren_list'] == \
        ['siren_list is a list of 9 digits : ["123456789", "789654123"]']


@pytest.mark.standalone
def test_check_get_offerers_params_doesnt_raise_api_error_for_valid_zip_codes_list(app):
    # given
    valid_zip_codes_list = {}
    valid_zip_codes_list['zip_codes'] = ['69000', '13020', '2a250', '2B456', '00007']

    # when
    try:
        check_get_offerers_params(valid_zip_codes_list)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_validated_user_offerer_param(app):
    # given
    not_valid_has_validated_user_offerer_param = {}
    not_valid_has_validated_user_offerer_param['has_validated_user_offerer'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_validated_user_offerer_param)

    # then
    assert errors.value.errors['has_validated_user_offerer'] == ['has_validated_user_offerer is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_siren_param(app):
    # given
    not_valid_has_siren_param = {}
    not_valid_has_siren_param['has_siren'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_siren_param)

    # then
    assert errors.value.errors['has_siren'] == ['has_siren is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_not_virtual_venue_param(app):
    # given
    not_valid_has_not_virtual_venue_param = {}
    not_valid_has_not_virtual_venue_param['has_not_virtual_venue'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_not_virtual_venue_param)

    # then
    assert errors.value.errors['has_not_virtual_venue'] == ['has_not_virtual_venue is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_validated_venue_param(app):
    # given
    not_valid_has_validated_venue_param = {}
    not_valid_has_validated_venue_param['has_validated_venue'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_validated_venue_param)

    # then
    assert errors.value.errors['has_validated_venue'] == ['has_validated_venue is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_venue_with_siret_param(app):
    # given
    not_valid_has_venue_with_siret_param = {}
    not_valid_has_venue_with_siret_param['has_venue_with_siret'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_venue_with_siret_param)

    # then
    assert errors.value.errors['has_venue_with_siret'] == ['has_venue_with_siret is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_is_validated_param(app):
    # given
    not_valid_is_validated_param = {}
    not_valid_is_validated_param['is_validated'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_is_validated_param)

    # then
    assert errors.value.errors['is_validated'] == ['is_validated is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_validated_user_param(app):
    # given
    not_valid_has_validated_user_param = {}
    not_valid_has_validated_user_param['has_validated_user'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_validated_user_param)

    # then
    assert errors.value.errors['has_validated_user'] == ['has_validated_user is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_has_bank_information_param(app):
    # given
    not_valid_has_bank_information_param = {}
    not_valid_has_bank_information_param['has_bank_information'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_has_bank_information_param)

    # then
    assert errors.value.errors['has_bank_information'] == ['has_bank_information is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_is_active_param(app):
    # given
    not_valid_is_active_param = {}
    not_valid_is_active_param['is_active'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_is_active_param)

    # then
    assert errors.value.errors['is_active'] == ['is_active is a boolean, it accepts True or False']


@pytest.mark.standalone
def test_check_get_offerers_params_raises_api_error_if_not_valid_offer_status_param(app):
    # given
    not_valid_offer_status_param = {}
    not_valid_offer_status_param['offer_status'] = 'I\'m not a boolean'

    # when
    with pytest.raises(ApiErrors) as errors:
        check_get_offerers_params(not_valid_offer_status_param)

    # then
    assert errors.value.errors['offer_status'] == ['offer_status accepte ALL ou VALID ou WITHOUT ou EXPIRED']
    

@pytest.mark.standalone
def test_check_get_offerers_params_does_not_raise_api_error_if_good_param(app):
    # given
    params = {}
    params['siren_list'] = ['123456789', '123454789', '789654123']
    params['dpt'] = ['12', '2A', '56']
    params['zip_codes'] = ['12111', '2A250', '56698']
    params['from_date'] = '2018-05-30'
    params['to_date'] = '2018-12-31'
    params['has_siren'] = True 
    params['has_not_virtual_venue'] = False 
    params['has_validated_venue'] = True
    params['has_venue_with_siret'] = True
    params['offer_status'] = 'EXPIRED'
    params['is_validated'] = True
    params['has_validated_user'] = True
    params['has_bank_information'] = False
    params['is_active'] = True
    params['has_validated_user_offerer'] = False

    # when
    try:
        check_get_offerers_params(params)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")


@pytest.mark.standalone
def test_check_get_offerers_params_does_not_raise_api_error_if_empty_param(app):
    # given
    params = {}
    
    # when
    try:
        check_get_offerers_params(params)
    
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with valid params")
