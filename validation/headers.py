import re

from utils.config import API_URL, ENV


def check_origin_header_validity(header, endpoint, path):
    endpoint_exceptions = _get_endpoint_exceptions()

    if endpoint in endpoint_exceptions or 'back-office' in path:
        return True

    white_list = _get_origin_header_whitelist()
    combined_white_list = "(" + ")|(".join(white_list) + ")"
    return re.match(combined_white_list, header) is not None


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
            'https://[a-zA-Z]+.passculture.app',
            'https://app-passculture-testing.scalingo.io',
            'https://passculture-team.netlify.com',
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
    valid_urls.extend(_get_origin_header_whitelist_for_non_dev_environments(API_URL))
    return valid_urls


def _get_endpoint_exceptions():
    return ['patch_booking_by_token', 'get_booking_by_token', 'send_storage_file', 'health',
        'list_export_urls', 'export_table', 'validate', 'validate_venue',
        'get_all_offerers_with_managing_user_information', 
        'get_all_offerers_with_managing_user_information_and_venue',
        'get_all_offerers_with_managing_user_information_and_not_virtual_venue',
        'get_all_offerers_with_venue', 'get_pending_validation',
        'get_export_venues', 'get_export_offerers', 'get_bookings_csv']


def _get_origin_header_whitelist_for_non_dev_environments(api_url):
    url_variations = [api_url, api_url.replace('https', 'http'), api_url.replace('https://', '')]
    valid_urls = []
    for url in url_variations:
        valid_urls.append(url.replace('backend', 'pro'))
        valid_urls.append(url.replace('backend', 'app'))
        valid_urls.append(url.replace('backend', 'team'))

    return valid_urls
    
