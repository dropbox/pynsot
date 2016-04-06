from __future__ import unicode_literals

"""
Utilities and stuff.
"""


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

    if 'results' in payload:
        return payload['results']

    # Or just return the payload... (next-gen)
    return payload

