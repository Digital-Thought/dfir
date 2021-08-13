from cbc_sdk.platform import Device
from cbc_sdk import CBCloudAPI
from cbc_sdk.platform import User
from typing import List
from .live_response import LiveResponse

import logging


class Client(object):

    def __init__(self, url: str, org_key: str, api_id: str, api_secret_key: str) -> None:
        self.org_key = org_key
        self.cbc_api = CBCloudAPI(url=url, token=f"{api_secret_key}/{api_id}", org_key=org_key)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cbc_api = None

    def users(self) -> List[dict]:
        query = self.cbc_api.select(User)
        for user in list(query):
            yield user

    def devices(self) -> List[dict]:
        query = self.cbc_api.select(Device)
        for device in list(query):
            yield device

    def create_user(self, first_name: str, last_name: str, email_address: str, role_name: str):
        try:
            builder = User.create(self.cbc_api)
            builder.set_first_name(first_name).set_last_name(last_name)
            builder.set_email(email_address)
            builder.set_role(f'psc:role:{self.org_key}:{role_name}')
            builder.build()
            logging.info(f'Created user {last_name}, {first_name} <{email_address}>')
        except Exception as ex:
            logging.exception(str(ex))

    def create_users(self, users: List[dict], role_name: str = None) -> dict:
        response = {"success": [], "failed": []}
        for user in users:
            try:
                builder = User.create(self.cbc_api)
                builder.set_first_name(user['first_name']).set_last_name(user['last_name'])
                builder.set_email(user['email_address'])
                assigned_role_name = user.get("role_name", role_name)
                if assigned_role_name is None:
                    raise Exception("Role Name was None. A Role Name must be provided")
                builder.set_role(f'psc:role:{self.org_key}:{assigned_role_name}')
                builder.build()
                logging.info(f'Created user {user["last_name"]}, {user["first_name"]} <{user["email_address"]}>')
                response["success"].append(user)
            except Exception as ex:
                user['error'] = str(ex)
                response["failed"].append(user)
                logging.exception(str(ex))

        return response

    def live_response(self, device_name: str = None, device: dict = None) -> LiveResponse:
        if device_name is not None:
            query = self.cbc_api.select(Device)
            for device_inst in list(query):
                if device_inst.name.lower() == device_name.lower():
                    device = device_inst

        if device is None and device_name is not None:
            raise Exception(f'Unable to identify device: {device_name}')

        if device is None:
            raise Exception(f'No Device was specified')

        return LiveResponse(device)
