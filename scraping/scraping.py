# -*- coding: utf-8 -*-

import argparse
import fbchat
from fbchat.models import *
import getpass
import os
import sys
import time
import datetime
import csv
import json
import re
import urllib.request
#import numpy as np

parser = argparse.ArgumentParser()

parser.add_argument('-p','--password', action="store", dest="password", help="Your facebook password")
parser.add_argument('-a','--email_address', action="store", dest="address", help="Your email address")

args = parser.parse_args()

def printFriends(client): #prints friend list with IDs
    
    check_for_client(client)
    
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
            
def check_for_list(liste):
    if type(liste) != list:
        raise TypeError("The argument should be of type list")

def check_for_msg(item):
    if type(item) != fbchat.models.Message:
        raise TypeError("The item should of type fbchat.models.Message")
        
def check_for_client(instance):
    if type(instance) != fbchat.client.Client:
        raise TypeError("The parameter should be a fbchat.client object")

#checks that we haven't double-included a message in a list
#maybe replace "true" by an exception
def check_for_duplication(liste): #https://stackoverflow.com/questions/1541797/check-for-duplicates-in-a-flat-list

  check_for_list(liste)

  seen = set()
  
  for i,msg in enumerate(liste):
    
    check_for_msg(msg)
      
    if msg.uid in seen: 
        
        raise ValueError("Duplication at index " + str(i) + " in the list")
    
    seen.add(msg.uid)
    

#checks that there is no time discontinuity in the list
def check_for_time(liste): 
    
    check_for_list(liste)
    
    check_for_msg(liste[0])
    
    for i in range(1,len(liste)):
        
        check_for_msg(liste[i])
        
        if int(liste[i].timestamp) > int(liste[i-1].timestamp): #assuming that the lastest message is at index 0
            
            raise ValueError("Time discontinuity at index " + str(i) + "in the list")

def get_attachment_indexes(liste): #returns a list with the indexes of all objects having an attachment
    
    check_for_list(liste)
    
    attached = []
    
    for i,msg in enumerate(liste):
        
        check_for_msg(msg)
        
        if msg.attachments != [] and msg.attachments != None:
            
            attached = attached + [i]
            
    return attached

#returns a dictionnary classifying the indexes of the list according to what kind of attachment do they have
def classify_attachments(liste, indexes=-1):
    
    check_for_list(liste)
    
    if indexes == -1:
        indexes = get_attachment_indexes(liste)
    else:
        check_for_list(indexes)
    
    classified = {}
    
    for i in indexes:
        
        check_for_msg(liste[i])
        
        for ii,attachment in enumerate(liste[i].attachments):
            
            if attachment['__typename'] not in classified.keys():
                
                classified[attachment['__typename']] = [(i,ii)]#we put two indexes, i and ii in the dictionnary, because i corresponds to the position in the list, and ii to the position of the attachment in the message

            else:
                
                classified[attachment['__typename']].append((i,ii))
                
    return classified


def download_attachments(liste, indexes = -1):
    
    check_for_list(liste)
    
    if indexes == -1:
        indexes = classify_attachments(liste)
    
    check_for_list(indexes)
    
    if 'MessageImage' in indexes.keys():
        for i in indexes['MessageImage']:
            
            check_for_msg(liste[i[0]])
        
            attachment = liste[i[0]].attachments[i[1]]
            url = attachment['large_preview']['uri']
            filename = attachment['filename']
            extension = url.split('?')[0][-4:]
        
            print(filename + extension)
        
            urllib.request.urlretrieve(url, filename + extension)
    
        print("------------------------------------")

    if 'MessageAudio' in indexes.keys():
        for i in indexes['MessageAudio']:
        
            check_for_msg(liste[i[0]])
            
            attachment = liste[i[0]].attachments[i[1]]
            url = attachment['playable_url']
            filename = attachment['filename']
            extension = url.split('?')[0][-4:]
            if extension == '.jpg':
                extension = '.mp3'
            elif extension == '.mp4':
                filename = filename[:-4]
                extension = '.mp3'
        
            print(filename + extension)
         
            urllib.request.urlretrieve(url, filename + extension)
        
        print("------------------------------------")

    if 'MessageAnimatedImage' in indexes.keys():
        for i in indexes['MessageAnimatedImage']:
            
            check_for_msg(liste[i[0]])
        
            attachment = liste[i[0]].attachments[i[1]]
            url = attachment['animated_image']['uri']
            filename = attachment['filename']
             #extension = url.split('?')[0][-4:]
        
            print(filename + '.gif')
        
            urllib.request.urlretrieve(url, filename + '.gif')
            
        print("------------------------------------")

    if 'MessageFile' in indexes.keys():
        for i in indexes['MessageFile']:
            
            check_for_msg(liste[i[0]])
        
            attachment = liste[i[0]].attachments[i[1]]
            url = attachment['url']
            filename = attachment['filename']
        
            print(filename)
        
            f = urllib.request.urlopen(url)
            out = f.read().decode('utf-8') #codes the bytes
            out2 = out.split('&u=')[-1].split('\"')[0] #we parse the string 
            out3 = out2[:-1].encode('utf8').decode('unicode-escape').encode('utf8').decode('unicode-escape') #we remove the unicode escaping
            out4 = urllib.request.unquote(out3) #removes the url escaping
        
            urllib.request.urlretrieve(out4, filename)
        #print(filename, url_is_alive(out4))
        print("------------------------------------")
    
    if 'MessageVideo' in indexes.keys():
        for i in indexes['MessageVideo']:
            
            check_for_msg(liste[i[0]])
        
            attachment = liste[i[0]].attachments[i[1]]
            url = attachment['playable_url']
            filename = attachment['filename']
        
            print(filename)
        
            urllib.request.urlretrieve(url, filename) 

def write_datetime_from_timestamp(liste, utc = False):
    
    check_for_list(liste)
    
    if type(utc) != bool:
        raise TypeError("utc should be of type bool")
    
    if not utc:
        
        for msg in liste:
            
            check_for_msg(msg)
            
            msg.datetime = datetime.datetime.fromtimestamp(int(msg.timestamp[:-3])) #we stripe the last 3 digits because python doesn't handle it

    else:
        
        for msg in liste:
            
            check_for_msg(msg)
            
            msg.datetime = datetime.datetime.utcfromtimestamp(int(msg.timestamp[:-3]))
            
def get_name_from_id(client,ID):
   check_for_client(client)
   return client.fetchUserInfo(ID)[ID].name

def write_name_from_id(client, liste):
    
    check_for_client(client)
    
    check_for_list(liste)
    
    id_to_name = {}
    
    for msg in liste:
        
        check_for_msg(msg)
        
        if msg.author not in id_to_name.keys(): #a bit of dynamic programming, otherwise it takes ages

            id_to_name[msg.author] = get_name_from_id(client,msg.author)

        msg.author_name = id_to_name[msg.author]

    return id_to_name #originally, it isn't the purpose of the function to return the dictionnary, but why waste it? 

def remove_timestamp_overhead(liste,timestamp):
    
    check_for_list(liste)
    
    if type(timestamp) != int:
        raise TypeError("timestamp should be of type int")
        
    
    print('Removing timestamp overhead...')
    
    check_for_msg(liste[-1])
    
    while int(liste[-1].timestamp) < timestamp:
        
        liste.pop()
        
        check_for_msg(liste[-1])
        
def remove_counter_overhead(liste,upper_bound):
    
    check_for_list(liste)
    
    if type(upper_bound) != int:
        raise TypeError("upper_bound should be of type int")
    
    print('Removing counter overhead...')
    
    while len(liste) > upper_bound:
        
        liste.pop()

#client should be the Client object we just created
#and "thread_id" the ID of the thread you're interested in
#messages_before should be a int representing a unix timestamp
def getMessageList(client, thread_id, verbose=1, messages_before=-1, messages_after=-1, upper_bound=-1):
    
    check_for_client(client)
    
    
    
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

def scrapeMessages(address, password, thread_id, readable_time=True, readable_name=True, verbose=1,messages_before=-1, messages_after=-1, upper_bound=-1):
    
    while not address:
        address = input("Please enter your email adress:")
    
    while not password:
        if any('SPYDER' in name for name in os.environ) or "pythonw.exe" in sys.executable:
            password = input("Please enter your password: ")
        else:
            password = getpass.getpass("Please enter your password: ")
            
    client = fbchat.Client(address, password)
            
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
        
    messageList = getMessageList(client, thread_id, verbose, messages_before, messages_after, upper_bound)
    
    if readable_time:
        write_datetime_from_timestamp(messageList)
    if readable_name:
        write_name_from_id(client,messageList)
    
    client.logout()
    
    return messageList

def create_lambda_values_msg(fieldnames, attachments_as_string = False, datetime_as_string = True):
    
    lambda_values = []
    fieldnames_checked = []
    
    for field in fieldnames:
        if field == "Datetime":
            if datetime_as_string == True:
                lambda_values.append(lambda msg:str(msg.datetime))
            else:
                lambda_values.append(lambda msg:msg.datetime)
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
        elif field == "Is read":
            lambda_values.append(lambda msg:msg.is_read)
            fieldnames_checked.append("IsRead")
        elif field == "Extensible attachment":
            lambda_values.append(lambda msg:msg.extensible_attachment)
            fieldnames_checked.append("ExtensibleAttachment")
        elif field == "Attachments":
            if attachments_as_string == True:
                lambda_values.append(lambda msg:str(msg.attachments))
            else:
                lambda_values.append(lambda msg:msg.attachments)
            fieldnames_checked.append("Attachments")
        elif field == "Mentions":
            lambda_values.append(lambda msg:msg.mentions)
            fieldnames_checked.append("Mentions")
        elif field == "Reactions":
            lambda_values.append(lambda msg:msg.reactions)
            fieldnames_checked.append("Reactions")
            
    return lambda_values, fieldnames_checked

def build_attachment_list(liste):
    indexes = get_attachment_indexes(liste)
    result = []
    for i in indexes:
        result.append(liste[i])
    return result
        

os.path.isfile(fname) 

def save_msg_json(liste, namefile, fieldnames = ['Attachments','Author','AuthorName','Datetime','ExtensibleAttachment','IsRead','Mentions','Reactions','Sticker','Text','Timestamp','MessageID']):
    def handle_message(liste):
        #implementer values to save
        for i in liste[::-1]:
            i.datetime = str(i.datetime)
            yield i
            
    def build_dict(msg, lambda_values):
        
        out = {}
            
        for index,value in enumerate(lambda_values):
            out[fields_checked[index]] = value(msg)
            
        return out
    
    check_for_list(liste)
    
    if os.path.isfile(namefile):
        answer = ""
        while answer.lower() != "y" or answer.lower() != "n":
            answer = input(namefile + " already exist, do you want to overwrite it?")
    
    if answer == "n":
        return # we exit, as we cannot write 
    
    lambda_values, fields_checked = create_lambda_values_msg(fieldnames)
    
    with open(namefile, 'w') as f:
        f.write('[')
        
        for msg in handle_message(liste[:-1]):
            #print(msg.__dict__)
            json.dump(build_dict(msg, lambda_values), f,indent=4, separators=(',', ': '))
            f.write(',')
            
        for msg in handle_message(liste[-1:]):
            json.dump(build_dict(msg, lambda_values), f,indent=4, separators=(',', ': '))
            
        f.write(']')

def load_json(path):
    with open(path, 'r') as fp:
        return json.load(fp)
            
def save_msg_csv(liste, namefile, values_to_save = ["Datetime","AuthorName","Text","MessageID"]):
    
    
    if os.path.isfile(namefile):
        answer = ""
        while answer.lower() != "y" or answer.lower() != "n":
            answer = input(namefile + " already exist, do you want to overwrite it?")
    
    if answer == "n":
        return # we exit, as we cannot write 
    
    with open(namefile, "w", newline='',encoding='utf-8') as pfile:
        
        csv_writer = csv.writer(pfile)
        
        lambda_values, values_to_save_checked = create_lambda_values_msg(values_to_save)

        csv_writer.writerow(values_to_save_checked)
        
        for msg in liste[::-1]:
            if msg.text != '' and msg.text != None or True:
                #test(i)
                print(msg)
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
     
    lambda_values = create_lambda_values_msg(fieldnames, attachments_as_string = True)[0]
    
    for msg in liste:
        for value in lambda_values:
            if value(msg):
                try:
                    if compiled_pattern.search(value(msg)):
                        result_list.append(msg)
                        break
                except TypeError:
                    raise TypeError("The field you've entered contains a datatype that isn't supported, only strings and bytes-like objects are.")
    return result_list

if __name__ == "__main__":
    if args.address and args.password:
        scrapeMessages(args.address, args.password)
        

