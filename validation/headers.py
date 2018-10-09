from utils.config import API_URL, ENV


def check_origin_header_validity(header, endpoint):
    endpoint_exceptions = _get_endpoint_exceptions()
    if endpoint in endpoint_exceptions:
        return True
    white_list = _get_origin_header_whitelist()
    return header in white_list


def _get_origin_header_whitelist():
    valid_urls = []
    if ENV == 'development':
        return [
            'http://localhost:3000',
            'http://localhost',
            'https://localhost',
            'localhost',
            'https://localhost:3000',
            'localhost:3000',
            'http://localhost:3001',
            'https://localhost:3001',
            'localhost:3001'
        ]
    # Handle migration to Scalingo
    elif ENV == 'testing':
        valid_urls = [
            'https://app-passculture-testing.scalingo.io'
        ]
    valid_urls.extend(_get_origin_header_whitelist_for_non_dev_environments(API_URL))
    return valid_urls


def _get_endpoint_exceptions():
    return ['patch_booking_by_token', 'get_booking_by_token', 'send_storage_file', 'health', 'list_export_urls', 'export_table', 'get_users_per_date_per_department', 'get_users_stats', 'get_bookings_stats', 'get_bookings_per_date_per_departement', 'get_offers_per_date_per_department', 'get_offerers_per_date_per_departement', 'get_venue_per_department', 'get_tracked_activity_from_id', 'get_offerers_users_offers_bookings', 'get_recommendations', 'validate']


def _get_origin_header_whitelist_for_non_dev_environments(api_url):
    url_variations = [api_url, api_url.replace('https', 'http'), api_url.replace('https://', '')]
    valid_urls = []
    for url in url_variations:
        valid_urls.append(url.replace('backend', 'pro'))
        valid_urls.append(url.replace('backend', 'app'))
    return valid_urls
