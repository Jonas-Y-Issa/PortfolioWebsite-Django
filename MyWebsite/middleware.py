"""Limit forwarded scheme headers to the private gateway and local healthcheck."""

from ipaddress import ip_address

from django.conf import settings


class TrustedProxyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.trusted_peers = {
            ip_address(value) for value in settings.DJANGO_TRUSTED_PROXY_IPS
        }

    def __call__(self, request):
        try:
            peer = ip_address(request.META.get("REMOTE_ADDR", ""))
        except ValueError:
            peer = None
        if peer not in self.trusted_peers:
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
        return self.get_response(request)
