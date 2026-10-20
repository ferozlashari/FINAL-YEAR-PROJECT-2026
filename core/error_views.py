from django.http import HttpResponseBadRequest
from django.template.loader import render_to_string


def bad_request(request, exception=None):
    """400 page that never touches the request: with a forged Host header every
    context processor that asks for the host would raise again and turn a clean
    400 into a 500."""
    return HttpResponseBadRequest(render_to_string('400.html'))
