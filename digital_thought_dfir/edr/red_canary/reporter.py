import time

from digital_thought_commons.internet.requester import RequesterSession

import logging
import sys


class Reporter(object):

    MAX_RETRIES = 10

    def __init__(self, subdomain: str, auth_token: str, api_endpoint: str, request_session: RequesterSession) -> None:
        self.subdomain = subdomain
        self.auth_token = auth_token
        self.request_session = request_session
        self.api_endpoint = api_endpoint
        self.maximum_retries = self.MAX_RETRIES

    def __collect(self, start_url):
        data = []
        try:
            req_url = start_url
            total_items = sys.maxsize
            pause_count = 0
            while len(data) < total_items:
                try:
                    response = self.request_session.get(req_url)
                    if response.status_code == 200:
                        resp = response.json()
                        data.extend(resp['data'])
                        req_url = resp['links']['next']
                        total_items = resp['meta']['total_items']
                        pause_count = 0
                    elif response.status_code == 429:
                        if pause_count >= self.maximum_retries:
                            logging.error(f"Failed to retrieve response after maximum ({self.maximum_retries}) retry amount.")
                            break
                        logging.warning(f"Received 'Too Many Requests'.  Will pause for 10 seconds")
                        time.sleep(10)
                        pause_count += 1
                    else:
                        logging.error(f"Received a response of {response.status_code} -> '{response.text}'")
                        break
                except Exception as ex:
                    if pause_count >= self.maximum_retries:
                        logging.error(f"Failed to retrieve response after maximum ({self.maximum_retries}) retry amount.")
                        break
                    logging.warning(f'{str(ex)}, waiting for 10 seconds')
                    time.sleep(10)
                    pause_count += 1
        except Exception as ex:
            logging.exception(str(ex))

        return data

    def endpoint_users(self):
        logging.info("Collecting endpoint_users for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "endpoint_users", self.auth_token)
        return self.__collect(req_url)

    def endpoints(self):
        logging.info("Collecting endpoints for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "endpoints", self.auth_token)
        return self.__collect(req_url)

    def detections(self):
        logging.info("Collecting detections for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "detections", self.auth_token)
        return self.__collect(req_url)

    def marked_indicators_of_compromise(self):
        logging.info("Collecting detections/marked_indicators_of_compromise for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "detections/marked_indicators_of_compromise", self.auth_token)
        return self.__collect(req_url)

    def audit_logs(self):
        logging.info("Collecting audit_logs for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "audit_logs", self.auth_token)
        return self.__collect(req_url)

    def events(self):
        logging.info("Collecting events for Red Canary subdomain: {}".format(self.subdomain))
        req_url = self.api_endpoint.format(self.subdomain, "events", self.auth_token)
        return self.__collect(req_url)
