from digital_thought_commons import logging as logger
from digital_thought_dfir.edr import red_canary
from digital_thought_commons.converters import json as json_converter
from digital_thought_commons.microsoft import excel
from datetime import datetime

import logging
import pathlib
import argparse
import os
import json


def collect(subdomain, auth_token):
    logging.info("Collecting information for Red Canary subdomain: {}".format(subdomain))
    with red_canary.Client(subdomain=subdomain, auth_token=auth_token) as red_canary_client:
        reporter = red_canary_client.reporter()
        return {'endpoints': reporter.endpoints(), 'endpoint_users': reporter.endpoint_users(), 'audit_logs': reporter.audit_logs(),
                'detections': reporter.detections(), 'events': reporter.events(),
                'marked_indicators_of_compromise': reporter.marked_indicators_of_compromise()}


def save_reports(data, output_folder, subdomain):
    if not os.path.exists(output_folder):
        os.makedirs(name=output_folder, exist_ok=True)

    time_stamp = datetime.now().timestamp()

    json_report_file = f'{output_folder}/{subdomain}_{time_stamp} + _report.json'
    excel_report_file = output_folder + "/" + subdomain + '_report.xlsx'
    template = "{}/../../_resources/reports/endpoints/excel_template.yaml".format(str(pathlib.Path(__file__).parent.absolute()))

    logging.info(f"Saving JSON report to: {json_report_file}")
    with open(json_report_file, 'w', encoding="UTF-8") as report_json:
        json.dump(data, report_json, indent=4)

    logging.info(f"Saving Excel report to: {excel_report_file}")
    workbook = excel.Spreadsheet(template=template, filename=excel_report_file)
    for key in data:
        if key != 'vr_clients':
            worksheet = workbook.get_worksheet_by_name(key)
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
                    worksheet.write(row, col, entry.get(header, ""))
                    col += 1

    vr_clients = workbook.get_worksheet_by_name('vr_clients')
    if 'vr_clients' in data:
        flattened = json_converter.flatten_json(data['vr_clients'])
        headers = json_converter.read_fields(flattened)
        row = 0
        col = 0
        for header in headers:
            if col == 15:
                vr_clients.write(row, col, 'LastSeen')
                vr_clients.write(row, col + 1, header)
            else:
                vr_clients.write(row, col, header)
            col += 1

        for entry in flattened:
            col = 0
            row += 1
            for header in headers:
                if col == 15:
                    vr_clients.write(row, col, f'=( (O{row + 1} / 86400000) + DATE(1970,1,1))+TIME(10,0,0)')
                    vr_clients.write(row, col + 1, entry.get(header, ""))
                else:
                    vr_clients.write(row, col, entry.get(header, ""))
                col += 1

    summary = workbook.get_worksheet_by_name("Summary")
    summary.write(0, 1, datetime.now().strftime("%d/%m/%Y %-I:%M"))
    endpoints = []
    for entry in data['endpoints']:
        hostname = entry['attributes']['hostname'].lower()
        if "\\" in hostname:
            hostname = hostname.split("\\")[1]
        if "." in hostname:
            hostname = hostname.split(".")[0]
        if hostname not in endpoints:
            endpoints.append(hostname)

    row = 2
    summary.write(1, 0, 'Host Name')
    summary.write(1, 1, 'In Red Canary')
    summary.write(1, 2, 'In Velociraptor')
    summary.write(1, 3, 'Red Canary Agent Online')
    summary.write(1, 4, 'Velociraptor Online')
    summary.write(1, 5, 'OS')
    for endpoint in endpoints:
        summary.write(row, 0, endpoint)
        summary.write(row, 1, f'=IF(COUNTIF(endpoints!C:C,"*" & Summary!A{row + 1} & "*")>0,"YES","NO")')
        summary.write(row, 2, f'=IF(COUNTIF(vr_clients!G:G, "*" & LOWER(Summary!A{row + 1} & "*"))>0,"YES","NO")')
        summary.write(row, 3, f'=IFERROR(VLOOKUP("*" & A{row + 1} & "*",endpoints!C:F,4,FALSE)="online","NO")')
        summary.write(row, 4, f'=IFERROR(IF(((($B$1-VLOOKUP("*" & A{row + 1} & "*",vr_clients!G:R,10,FALSE))*86400)/60)>20,"FALSE","TRUE"),"NO AGENT")')
        summary.write(row, 5, f'=VLOOKUP("*" & A{row + 1} & "*",endpoints!C:L,10,FALSE)')
        row += 1

    workbook.close()


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main():
    logger.init(app_name='digital-thought-endpoint-reporter')
    version_info = "Unknown"
    with open("{}/../../version".format(str(pathlib.Path(__file__).parent.absolute())), "r") as fh:
        version_info = fh.read()

    arg_parser = argparse.ArgumentParser(prog='python main.py',
                                         description='Script to export data from a Red Canary instance')
    arg_parser.add_argument('--subdomain', action='store', type=str, required=True, help="The subdomain of the instance to export")
    arg_parser.add_argument('--auth_token', action='store', type=str, required=True, help="The authentication token to use")
    arg_parser.add_argument('--output', action='store', type=str, required=True, help="The directory to save export")
    arg_parser.add_argument('--vr_yaml', action='store', type=str, required=False, help="Path to Velociraptor YAML Auth File")

    args = arg_parser.parse_args()

    logging.info(f"Red Canary & Velociraptor Endpoint Reporter, version: {version_info}")

    try:
        report = collect(subdomain=args.subdomain, auth_token=args.auth_token)
        if args.vr_yaml:
            logging.info("Collecting information for Velociraptor Endpoints")
            try:
                from digital_thought_dfir import velociraptor
                with velociraptor.Client(args.vr_yaml) as vr_client:
                    vr_clients = vr_client.clients()
                report['vr_clients'] = vr_clients
            except Exception as ex:
                logging.exception(str(ex))
        save_reports(data=report, output_folder=args.output, subdomain=args.subdomain)
    except Exception as ex:
        logging.exception(str(ex))

    logging.info("Report Complete.")


if __name__ == '__main__':
    main()
