from cbc_sdk.platform import Device


class LiveResponse(object):

    def __init__(self, device: dict) -> None:
        self.lr_session = device.lr_session()
