import logging

import grpc
import yaml
import json
import time

from pyvelociraptor import api_pb2
from pyvelociraptor import api_pb2_grpc
from grpc._channel import Channel


class Client(object):

    def __init__(self, vr_yaml_file: str) -> None:
        with open(vr_yaml_file, mode='r') as yaml_file:
            self.vr_configuration = yaml.load(yaml_file, Loader=yaml.FullLoader)
        self.grpc_channel = self.__initialise__()

    def __initialise__(self) -> Channel:
        creds = grpc.ssl_channel_credentials(
            root_certificates=self.vr_configuration["ca_certificate"].encode("utf8"),
            private_key=self.vr_configuration["client_private_key"].encode("utf8"),
            certificate_chain=self.vr_configuration["client_cert"].encode("utf8"))
        options = (('grpc.ssl_target_name_override', "VelociraptorServer",),)
        return grpc.secure_channel(self.vr_configuration["api_connection_string"], creds, options)

    def __enter__(self):
        return self

    def __run_query__(self, query) -> dict:
        stub = api_pb2_grpc.APIStub(self.grpc_channel)
        request = api_pb2.VQLCollectorArgs(
            max_wait=1,
            max_row=100000000,
            Query=[api_pb2.VQLRequest(VQL=query, )])

        for response in stub.Query(request):
            if response.Response:
                results = json.loads(response.Response)
                return results

            elif response.log:
                logging.warning("%s: %s" % (time.ctime(response.timestamp / 1000000), response.log))

    def __exit__(self, type, value, traceback):
        self.grpc_channel.close()

    def clients(self) -> dict:
        query = """
                SELECT 
                    os_info as OSINFO,
                    os_info.fqdn as Hostname,
                    os_info.release as OS,
                    os_info.machine as Architecture,
                    first_seen_at as FirstSeen,
                    (last_seen_at / 1000) as LastSeen,
                    client_id as ClientId
                FROM clients()
                ORDER BY LastSeen DESC
            """
        return self.__run_query__(query=query)
