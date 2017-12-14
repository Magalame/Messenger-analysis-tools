# -*- coding: utf-8 -*-

import argparse
from fbchat import log, Client
from fbchat.models import *
import getpass
import os
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-p','--password', action="store", dest="password", help="Your facebook password")
parser.add_argument('-a','--email_address', action="store", dest="address", help="Your email address")

args = parser.parse_args()

def appendItems(source, target): #appends the elements of a list to another one
    for i in source:
        target.append(i)

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

#checks that we haven't double included a message in a list
def check_for_duplication(liste): #https://stackoverflow.com/questions/1541797/check-for-duplicates-in-a-flat-list
  seen = set()
  for i,x in enumerate(liste):
    if x.uid in seen: 
        print(i)
        return True
    seen.add(x.uid)
  return False

def printMsg(liste, personnes): #print the messeges in a list of message objects
    personnes = {}#dictionnary with the persons in the chat
    for i in liste:
        print(personnes[i.author] + ": " + i.text)


#if scraping for a one-to-one chat then set thread_type = ThreadType.USER
# for groups use ThreadType.GROUP
#client should be the Client object we just created
#and "thread_id" the ID of the thread you're interested in
def getMessageList(client, thread_id, thread_type):
    
    print("Scraping the message list...")

    msg_list = []
    count = 1
    #print("Count: " + str(count))
    messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000)

    appendItems(messages, msg_list)

    while True:
        print(str(count*10000) + "th message loaded")
        messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000, before=messages[-1].timestamp)
        appendItems(messages[1:], msg_list)  #we remove the first one because of the way the fetchThread function works. We could use "before=messages[-1].timestamp-1" and keep the first element for clarity's sake but it works as well without
        count = count + 1
        #print("Count: " + str(count))
    
        if messages[0].uid == messages[-1].uid:#as we remove the last one, we do not double count the last list (which will have only one element)
            break
    print("All messages are loaded")
    
    return msg_list

def scrapeMessages(address='', password='', thread_id='', is_group=False):
    
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
        if choice == 'u':
            is_group = False
            while choice.lower() != "y" and choice.lower() != "n":
                choice = input("Do you want to print your friends list, with their ID? (Press \'y\' if you're not sure) [y/n]:")
    
            if choice.lower() == "y":
                printFriends(client)
        
        if choice == 'g':
            is_group = True
            
    while not thread_id:    
        thread_id = input("Please enter the ID: ")
        
    if is_group:#we keep it outside of the "if not thread_id:" condition because we also want it to work for parameters
        thread_type = ThreadType.GROUP
    else:
        thread_type = ThreadType.USER
        
    return getMessageList(client, thread_id, thread_type)

if __name__ == "__main__":
    if args.address and args.password:
        scrapeMessages(args.address, args.password)