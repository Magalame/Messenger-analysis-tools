import json
import time
import datetime
import csv
import sys
sys.path.append('..')

from tools import preprocessing
from langdetect import detect

messages_path = sys.argv[1]
export_path = sys.argv[2]

def fill_language(messages, languages=None):
    # Adds a language field to the message dictionary
    filled_messages = []
    for key, value in messages.items():
        #if key > 10:   # Debugging
        #    break
        try:
            lang = detect(value['Text'])
        except:
            lang = "??"
        if languages != None and lang not in languages:
            lang = "other"
        value['lang'] = lang
        filled_messages.append(value)
    return filled_messages

def export_lang_csv(filled_messages, export_path):
    with open(export_path, 'w') as fp:
        w = csv.DictWriter(fp, filled_messages[0].keys())
        w.writeheader()
        w.writerows(filled_messages)

def lang_by_author_by_time(messages, languages=None, all_time=True, beg=None, end=None):
    # Get language for each message over a range of dates (format YYYY-MM-DD)
    by_author = {}
    if all_time == True:
        beg = messages[1]['Date']
        end = messages[len(messages)]['Date']

    beg = preprocessing.format_date(beg)
    end = preprocessing.format_date(end)

    counter = 0
    for key, value in messages.items(): # Debugging
        counter += 1
        if counter > 100:
            break

        date = preprocessing.format_date(value['Date'])
        if date < beg or date > end:
            continue

        author_name = value['AuthorName']
        if author_name not in by_author:
            by_author[author_name] = {}
        try:
            lang = detect(value['Text'])
        except:
            lang = "??"

        if languages != None and lang not in languages:
            lang = "other"

        if lang not in by_author[author_name]:
            by_author[author_name][lang] = 1
        else:
            by_author[author_name][lang] += 1

    print(by_author)
    return by_author

if __name__ == '__main__':
    # Load message data
    messages = preprocessing.load_messages(messages_path)

    # Fill with language
    #by_author = lang_by_author_by_time(messages, languages=['en', 'fr'], beg='2017-5-12', end='2017-5-20')
    filled_messages = fill_language(messages, languages=['en', 'fr'])
    export_lang_csv(filled_messages, export_path)
