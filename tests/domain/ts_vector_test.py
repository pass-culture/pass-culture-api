from pcapi.domain.ts_vector import _get_ts_queries_from_keywords_string


def test_get_ts_queries_from_keywords_string_parses_keywords_string_into_list_of_ts_strings():
    # given
    keywords_string = 'PNL chante Marx'

    # when
    keywords_result = _get_ts_queries_from_keywords_string(keywords_string)

    # then
    assert keywords_result == ['pnl:*', 'chante:*', 'marx:*']


def test_get_ts_queries_from_keywords_string_with_double_space_parses_keywords_string_ignoring_consecutive_spaces():
    # given
    keywords_string = 'PNL  chante Marx'

    # when
    keywords_result = _get_ts_queries_from_keywords_string(keywords_string)

    # then
    assert keywords_result == ['pnl:*', 'chante:*', 'marx:*']


def test_get_ts_queries_from_keywords_url_parses_keywords_string_ignoring_special_chars():
    # given
    keywords_string = "http://www.test.com"

    # when
    keywords_result = _get_ts_queries_from_keywords_string(keywords_string)

    # then
    assert keywords_result == ['http:*', 'www:*', 'test:*', 'com:*']


def test_get_ts_queries_from_keywords_string_with_coma_parses_keywords_string_ignoring_words_with_less_than_one_char():
    # given
    keywords_string = "Læetitia a mangé's'"

    # when
    keywords_result = _get_ts_queries_from_keywords_string(keywords_string)

    # then
    assert keywords_result == ['læetitia:*', 'mangé:*']
