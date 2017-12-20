# -*- coding: utf-8 -*-

import argparse
from fbchat import Client
from fbchat.models import *
import getpass
import os
import sys
import time
import datetime
import csv
import json
import re
#import numpy as np

parser = argparse.ArgumentParser()

parser.add_argument('-p','--password', action="store", dest="password", help="Your facebook password")
parser.add_argument('-a','--email_address', action="store", dest="address", help="Your email address")

args = parser.parse_args()

def printFriends(client): #prints friend list with IDs
    def getKey(user):
        return user.name

    users = client.fetchAllUsers()
    print("Name\t\t\t\t| ID")
    for user in sorted(users,key=getKey): 
	    #next lines are just for formatting 
        a=4
        if len(user.name) > 6:
            a = 3
        if len(user.name) > 14:
            a = 2
        if len(user.name) > 22:
            a = 1
        if len(user.name) > 30:
            a = 0
        if user.uid != "0" and user.uid != 0:
            print(user.name,a*"\t",user.uid)

#checks that we haven't double-included a message in a list
#maybe replace "true" by an exception
def check_for_duplication(liste): #https://stackoverflow.com/questions/1541797/check-for-duplicates-in-a-flat-list
    
  seen = set()
  
  for i,msg in enumerate(liste):
      
    if msg.uid in seen: 
        
        print("Duplication at " + str(i))
        
        return True
    
    seen.add(msg.uid)
    
  return False

#checks that there is no time discontinuity in the list
def check_for_time(liste): 
    
    for i in range(1,len(liste)):
        
        if int(liste[i].timestamp) > int(liste[i-1].timestamp): #assuming that the lastest message is at index 0
            
            print("Fails at index " + str(i))
            
            return False
        
    return True

def get_attachment_indexes(liste): #returns a list with the indexes of all objects having an attachment
    
    attached = []
    
    for i,msg in enumerate(liste):
        
        if msg.attachments != [] and msg.attachments != None:
            
            attached = attached + [i]
            
    return attached

#returns a dictionnary classifying the indexes of the list according to what kind of attachment do they have
def classify_attachments(liste):
    
    indexes = get_attachment_indexes(liste)
    classified = {}
    
    for i in indexes:
        
        for ii,attachment in enumerate(liste[i].attachments):
            
            if attachment['__typename'] not in classified.keys():
                
                classified[attachment['__typename']] = [(i,ii)]#we put two indexes, i and ii in the dictionnary, because i corresponds to the position in the list, and ii to the position of the attachment in the message

            else:
                
                classified[attachment['__typename']].append((i,ii))
                
    return classified

def write_datetime_from_timestamp(liste, utc = False):
    
    if not utc:
        
        for msg in liste:
            
            msg.datetime = datetime.datetime.fromtimestamp(int(msg.timestamp[:-3])) #we stripe the last 3 digits because python doesn't handle it

    else:
        
        for msg in liste:
            
            msg.datetime = datetime.datetime.utcfromtimestamp(int(msg.timestamp[:-3]))
            
def get_name_from_id(client,ID):
   return client.fetchUserInfo(ID)[ID].name

def write_name_from_id(client, liste):
    
    id_to_name = {}
    
    for i in liste:
        if i.author not in id_to_name.keys(): #a bit of dynamic programming, otherwise it takes ages

            id_to_name[i.author] = get_name_from_id(client,i.author)

        i.author_name = id_to_name[i.author]

    return id_to_name #originally, it isn't the purpose of the function to return the dictionnary, but why waste it? 

def remove_timestamp_overhead(liste,timestamp):
    
    print('Removing timestamp overhead...')
    
    while int(liste[-1].timestamp) < timestamp:
        
        liste.pop()
        
def remove_counter_overhead(liste,upper_bound):
    
    print('Removing counter overhead...')
    
    while len(liste) > upper_bound:
        
        liste.pop()

#client should be the Client object we just created
#and "thread_id" the ID of the thread you're interested in
#messages_before should be a int representing a unix timestamp
def getMessageList(client, thread_id, verbose=1, messages_before=-1, messages_after=-1, upper_bound=-1):
    
    print("Scraping the message list...")

    count = 1
    cur_size = 0
    if messages_before < 0:
        messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000)
    else:
        messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000, before=messages_before)
    msg_list = messages
    cur_time = start_time = time.time()

    print("At most 10000 messages loaded")
    
    while True:
        
        if messages_after >= 0:
            if int(messages[0].timestamp) < messages_after or int(messages[-1].timestamp) < messages_after:
                remove_timestamp_overhead(msg_list,messages_after)
                break
            
        if upper_bound >= 0:
            if len(msg_list) > upper_bound:
                remove_counter_overhead(msg_list,upper_bound)
                break
            elif len(msg_list) == upper_bound:
                break
        
        messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000, before=messages[-1].timestamp)
        
        msg_list = msg_list + messages[1:]  #we remove the first one because of the way the fetchThread function works. We could use "before=int(messages[-1].timestamp)-1" and keep the first element for clarity's sake but it works as well without

        count = count + 1
        
        if verbose == 2:
            
            print("At most " + str(count*10000) + " messages in " + str(time.time() - start_time)[:-13] + "s" + "\t| " + str(sys.getsizeof(msg_list)) + " B" + "\t increase: " + str(sys.getsizeof(msg_list)-cur_size) + "\t length: " + str(len(msg_list)) + "\t delay: " + str(time.time()-cur_time)[:-13] + "s")
            cur_time = time.time()
            cur_size = sys.getsizeof(msg_list)
            
        elif verbose == 1:
            
            print("At most",str(count*10000),"messages loaded")
    
        if messages[0].uid == messages[-1].uid:#as we remove the first one, we do not double count the last list (which will have only one element)
            break
    print("All messages are loaded")
    
    return msg_list

def scrapeMessages(address='', password='', thread_id='', readable_time=True, readable_name=True, verbose=1):
    
    while not address:
        address = input("Please enter your email adress:")
    
    while not password:
        if any('SPYDER' in name for name in os.environ) or "pythonw.exe" in sys.executable:
            password = input("Please enter your password: ")
        else:
            password = getpass.getpass("Please enter your password: ")
            
    client = Client(address, password)
            
    if not thread_id:
        choice = ""
        
        while choice.lower() != 'g' and choice.lower() != 'u':
            choice = input("Do you want to scrape a group chat (\'g\') or a simple chat (\'u\')")
        if choice.lower() == 'u':
            #is_group = False
            while choice.lower() != "y" and choice.lower() != "n":
                choice = input("Do you want to print your friends list, with their ID? (Press \'y\' if you're not sure) [y/n]:")
    
            if choice.lower() == "y":
                printFriends(client)
        
        if choice.lower() == 'g':
            pass
            #is_group = True
            
    while not thread_id:    
        thread_id = input("Please enter the ID: ")
        
    """if is_group:#we keep it outside of the "if not thread_id:" condition because we also want it to work for parameters
        thread_type = ThreadType.GROUP
    else:
        thread_type = ThreadType.USER"""
        
    messageList = getMessageList(client, thread_id, verbose)
    
    if readable_time:
        write_datetime_from_timestamp(messageList)
    if readable_name:
        write_name_from_id(client,messageList)
    
    client.logout()
    
    return messageList



#use: (yes it's not documented correctly yet):
# list_of_messages=scrape_Messages(your_args)
# save_msg_json(list_of_messages, 'data.json')
#https://stackoverflow.com/questions/24239613/memoryerror-using-json-dumps
def save_msg_json(liste, namefile):
    
    def handle_message(liste): #using a generator to not 1) modify the list 2) not load a second time the entire lsit
        for i in liste[::-1]:
            i.datetime = str(i.datetime)
            yield i
            
    with open(namefile, 'w') as f:
        f.write('[')
        
        for i in handle_message(liste[:-1]):
            json.dump(i.__dict__, f,indent=4, separators=(',', ': '))
            f.write(',')
            
        for i in handle_message(liste[-1:]): #we put the last element in each own loop too be able to control for the last comma to write
            json.dump(i.__dict__, f,indent=4, separators=(',', ': '))
            
        f.write(']')


        
def save_msg_json_dev(liste, namefile, values_to_save = 'all'):
    def handle_message(liste):
        #implementer values to save
        for i in liste[::-1]:
            i.datetime = str(i.datetime)
            yield i
            
    with open(namefile, 'w') as f:
        f.write('[')
        
        for i in handle_message(liste[:-1]):
            json.dump(i.__dict__, f,indent=4, separators=(',', ': '))
            f.write(',')
            
        for i in handle_message(liste[-1:]):
            json.dump(i.__dict__, f,indent=4, separators=(',', ': '))
            
        f.write(']')

def create_lambda_values_msg(fieldnames):
    
    lambda_values = []
    fieldnames_checked = []
    
    for field in fieldnames:
        if field == "Datetime":
            lambda_values.append(lambda msg:str(msg.datetime))
            fieldnames_checked.append("Datetime")
        elif field == "Author":
            lambda_values.append(lambda msg:msg.author)
            fieldnames_checked.append("Author")
        elif field == "Text":
            lambda_values.append(lambda msg:msg.text)
            fieldnames_checked.append("Text")
        elif field == "MessageID":
            lambda_values.append(lambda msg:msg.uid)
            fieldnames_checked.append("MessageID")
        elif field == "AuthorName":
            lambda_values.append(lambda msg:msg.author_name)
            fieldnames_checked.append("AuthorName")
        elif field == "Timestamp":
            lambda_values.append(lambda msg:msg.timestamp)
            fieldnames_checked.append("Timestamp")
            
    return lambda_values, fieldnames_checked
            
def save_msg_csv(liste, namefile, values_to_save = ["Datetime","AuthorName","Text","MessageID"]):
    
    with open(namefile, "w", newline='',encoding='utf-8') as pfile:
        
        csv_writer = csv.writer(pfile)
        
        lambda_values, values_to_save_checked = create_lambda_values_msg(values_to_save)

        csv_writer.writerow(values_to_save_checked)
        
        for msg in liste[::-1]:
            if msg.text != '' and msg.text != None:
                #test(i)
                csv_writer.writerow([value(msg) for value in lambda_values])
              
def regex_command_text(liste, pattern):
    result_list = []
    
    try:
        compiled_pattern = re.compile(pattern) #faster using compile
    except Exception as e:
        if str(e) == 'nothing to repeat':
            raise ValueError("\'Nothing to repeat\' error from regex. If you happen to use \'*\' in your expression remember it is interpreted here as a a quantifier. It means it will multiply everything that is before it. See https://stackoverflow.com/questions/31386552/nothing-to-repeat-from-python-regex")
        
    for i in liste:
        if i.text != None:
            if compiled_pattern.search(i.text):
                result_list.append(i)
    
    return result_list
            
def regex_command(liste, pattern, fieldnames = ['Text']):
    result_list = []
    lambda_values = []
    
    try:
        compiled_pattern = re.compile(pattern) #faster using compile
    except Exception as e:
        if str(e) == 'nothing to repeat':
            raise ValueError("\'Nothing to repeat\' error from regex. If you happen to use \'*\' in your expression remember it is interpreted here as a a quantifier. It means it will multiply everything that is before it. See https://stackoverflow.com/questions/31386552/nothing-to-repeat-from-python-regex")
     
    lambda_values = create_lambda_values_msg(fieldnames)[0]
    
    for msg in liste:
        for value in lambda_values:
            if value(msg):
                if compiled_pattern.search(value(msg)):
                    result_list.append(msg)
                    break
    
    return result_list

if __name__ == "__main__":
    if args.address and args.password:
        scrapeMessages(args.address, args.password)
        

