import pytest

from scripts.v14_clean_duplicate_offerers.connectors_google_spreadsheet import get_offerer_equivalence, \
    get_venue_equivalence


@pytest.mark.standalone
def test_get_offerer_equivalence_returns_dataframe_with_shape_85_2():
    # when
    offerer_equivalences = get_offerer_equivalence()

    # then
    assert offerer_equivalences.shape == (85, 2)


def test_get_offerer_equivalence_columns_dtype_are_int():
    # when
    offerer_equivalences = get_offerer_equivalence()

    # then
    assert offerer_equivalences.offerer_KO_id.dtype == int
    assert offerer_equivalences.offerer_OK_id.dtype == int


@pytest.mark.standalone
def test_get_venue_equivalence_returns_dataframe_with_shape_182_7():
    # when
    venue_equivalences = get_venue_equivalence()

    # then
    assert venue_equivalences.shape == (182, 7)