import json
import logging
import argparse
import pathlib
import os
import xlsxwriter

from digital_thought_commons import logging as logger
from digital_thought_commons.converters import json as json_converter
from . import Client


def save_reports(data, output_folder, org_key):
    if not os.path.exists(output_folder):
        os.makedirs(name=output_folder, exist_ok=True)

    json_report_file = output_folder + "/" + org_key + '_report.json'
    excel_report_file = output_folder + "/" + org_key + '_report.xlsx'

    logging.info(f"Saving JSON report to: {json_report_file}")
    with open(json_report_file, 'w', encoding="UTF-8") as report_json:
        json.dump(data, report_json, indent=4)

    logging.info(f"Saving Excel report to: {excel_report_file}")

    workbook = xlsxwriter.Workbook(excel_report_file)
    for key in data:
        worksheet = workbook.add_worksheet()
        worksheet.name = key
        flattened = json_converter.flatten_json(data[key])
        headers = json_converter.read_fields(flattened)
        row = 0
        col = 0

        for header in headers:
            worksheet.write(row, col, header)
            col += 1

        for entry in flattened:
            col = 0
            row += 1
            for header in headers:
                worksheet.write(row, col, entry.get(header, " - "))
                col += 1

    workbook.close()


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main():
    logger.init(app_name='digital-thought-cbc-user-provision')
    version_info = "Unknown"
    with open("{}/../../../version".format(str(pathlib.Path(__file__).parent.absolute())), "r") as fh:
        version_info = fh.read()
    logging.info(f"Carbon Black Cloud, User Provisioner, version: {version_info}")
    arg_parser = argparse.ArgumentParser(prog='cbc_user_provision',
                                         description='Script to provision user accounts within Carbon Black Cloud')
    arg_parser.add_argument('--cbc_url', action='store', type=str, required=True, help="Carbon Black Cloud URL e.g. https://defense-prodsyd.conferdeploy.net")
    arg_parser.add_argument('--api_secret_key', action='store', type=str, required=True, help="Carbon Black Cloud, API Secret Key")
    arg_parser.add_argument('--api_id', action='store', type=str, required=True, help="Carbon Black Cloud, API ID")
    arg_parser.add_argument('--org_key', action='store', type=str, required=True, help="Carbon Black Cloud, Org Key")
    arg_parser.add_argument('--input', action='store', type=str, required=True, help="Path to user JSON definition file")
    arg_parser.add_argument('--output', action='store', type=str, required=True, help="The directory to save result report")
    arg_parser.add_argument('--email_alias_addition', action='store', type=str, required=False, help="Optional email alias e.g. 'bob' -> email+bob@email.com")

    args = arg_parser.parse_args()
    if not os.path.exists(args.input) or not os.path.isfile(args.input):
        logging.error(f'The input file "{args.input}" does not exist or is not a file.')
        exit(-1)

    with Client(url=args.cbc_url, api_id=args.api_id, api_secret_key=args.api_secret_key, org_key=args.org_key) as client:
        try:
            with open(args.input, mode='r') as in_file:
                user_data = json.load(in_file)

            user_provision_set = []
            for user in user_data:
                if args.email_alias_addition:
                    new_email = f'{user["email_address"].split("@")[0]}+{args.email_alias_addition}@{user["email_address"].split("@")[1]}'
                    user["email_address"] = new_email
                user_provision_set.append(user)

            logging.info(f'Provisioning {len(user_provision_set)} user accounts to Carbon Black Cloud, Organisation ID: {args.org_key}')
            response = client.create_users(user_provision_set)
            if len(response["success"]) > 0 and len(response["failed"]) == 0:
                logging.info(f'Completed Provisioning. Created {len(response["success"])} user accounts, and failed to create {len(response["failed"])} user accounts')
            elif len(response["success"]) > 0 and len(response["failed"]) > 0:
                logging.warning(f'Completed Provisioning. Created {len(response["success"])} user accounts, and failed to create {len(response["failed"])} user accounts')
            elif len(response["success"]) == 0 and len(response["failed"]) > 0:
                logging.error(f'Completed Provisioning. Created {len(response["success"])} user accounts, and failed to create {len(response["failed"])} user accounts')

            save_reports(data=response, output_folder=args.output, org_key=args.org_key)

        except Exception as ex:
            logging.exception(str(ex))

    logging.info("Complete.")


if __name__ == '__main__':
    main()
