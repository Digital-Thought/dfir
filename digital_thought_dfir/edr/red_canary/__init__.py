from digital_thought_commons import internet
from .reporter import Reporter


class Client(object):

    API_ENDPOINT = 'https://{}.my.redcanary.co/openapi/v3/{}?auth_token={}&per_page=100'

    def __init__(self, subdomain: str, auth_token: str) -> None:
        self.subdomain = subdomain
        self.auth_token = auth_token
        self.request_session = internet.new_requester()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.request_session.close()

    def reporter(self) -> Reporter:
        return Reporter(subdomain=self.subdomain, auth_token=self.auth_token, request_session=self.request_session, api_endpoint=self.API_ENDPOINT)
