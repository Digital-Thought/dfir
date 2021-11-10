import json
import time

from cbc_sdk.platform import Device
from digital_thought_commons import digests
from digital_thought_commons.converters import json as json_converters

import shutil
import os
import logging


class LiveResponse(object):

    def __init__(self, device: dict) -> None:
        self.device = device
        self.lr_session = device.lr_session()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.lr_session.close()

    def get_file(self, file_path):
        return self.lr_session.get_file(file_path)

    def __download_directory_(self, device_name, directory_path, destination, records, recursive):
        os.makedirs(name=destination, exist_ok=True)
        logging.info(f'Collecting files from {device_name} from path: {directory_path}')
        for dir_entry in self.lr_session.list_directory(directory_path):
            if dir_entry["filename"] != '.' and dir_entry["filename"] != '..':
                if "DIRECTORY" in dir_entry["attributes"] and recursive:
                    self.__download_directory_(device_name, f'{directory_path}{dir_entry["filename"]}\\', destination,
                                               records, recursive)
                else:
                    entry_id = digests.Digest()
                    entry_id.update_from_string(device_name)
                    entry_id.update_from_string(device_name)
                    entry_id.update_from_string(f'{directory_path}{dir_entry["filename"]}')
                    sub_dir = f'{destination}/{entry_id.md5[:2]}'
                    local_file = f'{destination}/{entry_id.md5[:2]}/{entry_id.md5}'
                    os.makedirs(name=sub_dir, exist_ok=True)

                    record = {'id': entry_id.md5, 'destination': local_file,
                              'source_file': f'{directory_path}{dir_entry["filename"]}', 'device': device_name}

                    for key in dir_entry:
                        record[key] = dir_entry[key]

                    retry_count = 0

                    while True:
                        try:
                            if os.path.exists(local_file):
                                os.remove(local_file)
                            with open(local_file, "wb") as fout:
                                data = self.lr_session.get_raw_file(f'{directory_path}{dir_entry["filename"]}')
                                shutil.copyfileobj(data, fout)
                                data.close()
                            file_digest = digests.calc_file_digest(local_file)
                            record['md5'] = file_digest.md5
                            record['sha1'] = file_digest.sha1
                            record['sha256'] = file_digest.sha256
                            record['success'] = True
                            record['retry_count'] = retry_count
                            break
                        except Exception as ex:
                            retry_count += 1
                            try:
                                if "Session command limit has been reached" in str(ex):
                                    logging.warning('Session command limit has been reached: Re-initialising Live Response Session')
                                    self.lr_session.close()
                                    time.sleep(10)
                                    self.lr_session = self.device.lr_session()
                                elif "Session not found" in str(ex):
                                    logging.warning('Session not found: Re-initialising Live Response Session')
                                    time.sleep(10)
                                    self.lr_session = self.device.lr_session()
                                logging.exception(f'Error {str(ex)} when collecting file {directory_path}{dir_entry["filename"]} from {device_name}')
                                record['success'] = False
                                record['error'] = str(ex)
                                record['retry_count'] = retry_count
                                if retry_count >= 5:
                                    break
                            except Exception as ex1:
                                logging.exception(f'Error {str(ex1)} when collecting file {directory_path}{dir_entry["filename"]} from {device_name}')
                                record['success'] = False
                                record['error'] = str(ex1)
                                record['retry_count'] = retry_count
                                break

                    records.append(record)

    def get_directory(self, directory_path, destination, recursive=True):
        records = []
        device_name = self.device.name.replace('/', '-').replace('\\', '-')
        destination = f'{destination}/{device_name}'
        self.__download_directory_(self.device.name, directory_path, destination, records, recursive)
        with open(f'{destination}/file_collection_report.json', mode='w') as out_file:
            json.dump(records, out_file)
        json_converters.json_array_to_csv(records, csv_file=f'{destination}/file_collection_report.csv')
        return records
