from __future__ import unicode_literals

"""
Utilities and stuff.
"""

# This is a list of all possible "result_key" values for pre-versioned API.
ALL_RESULT_KEYS = [
    'site', 'sites', 'attribute', 'attributes', 'value', 'values',
    'device', 'devices', 'network', 'networks', 'interface',
    'interfaces', 'user', 'users', 'change', 'changes', 'auth_token',
    'addresses',
]


def get_result_key(payload, result_keys=None):
    """
    Given a paylaod return the result_key (if any) for it.
    This should be depreceted when the API is fully-versioned.
    """
    if result_keys is None:
        result_keys = ALL_RESULT_KEYS
    try:
        if payload is True:
            return None
        return [k for k in payload if k in result_keys][0]
    except (IndexError, KeyError):
        return None


def get_result(response):
    """
    Get the desired result from an API response.
    :param response:
        Requests API response object
    """
    try:
        payload = response.json()
    except AttributeError:
        payload = response

    # This is a legacy payload. So complex!
    if 'data' in payload:
        data = payload['data']
        result_key = get_result_key(data)

        if result_key is not None:
            return data[result_key]

        # Or just return the data for real tho.
        return data

    # Or just return the payload... (next-gen)
    return payload
