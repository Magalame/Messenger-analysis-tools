import json
import csv
import time
import datetime

def load_messages(messages_path):
    if messages_path.endswith('.csv'):
        with open(messages_path, 'r') as fp:
            messages_csv = csv.reader(fp)
            messages = {}
            for i, row in enumerate(messages_csv):
                if i == 0:
                    headers = row
                    continue # Skip header row
                values = {}
                for j, header in enumerate(headers):
                    values[header] = row[j]
                    if header == 'Attachments':
                        values[header] = format_attachment(values[header])
                messages[i] = values
            return messages

    elif messages_path.endswith('.json'):
        with open(messages_path, 'r') as fp:
            messages_json = json.loads(messages_path)
        messages = {}
        for i, message in enumerate(message_json):
            messages[i] = message
        return messages

    else:
        raise IOError("Bad extension. Messages must be in a .csv or a .json format.")

def format_date(input_date):
    date = input_date.split(" ")[0].split("-")
    date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
    return date

def format_attachment(input_string):
    return json.loads(input_string.replace('\'','"').replace('None','null').replace("False","false").replace("True","true"))