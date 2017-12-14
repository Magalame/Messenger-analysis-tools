# -*- coding: utf-8 -*-

import argparse
from fbchat import log, Client
from fbchat.models import *

parser = argparse.ArgumentParser()

parser.add_argument('-p','--password', action="store", dest="password", help="Your facebook password")
parser.add_argument('-a','--email_address', action="store", dest="address", help="Your email address")


client = Client(args.address, args.address)



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


def check_for_duplication(liste): #https://stackoverflow.com/questions/1541797/check-for-duplicates-in-a-flat-list
  seen = set()
  for i,x in enumerate(liste):
    if x.uid in seen: 
        print(i)
        return True
    seen.add(x.uid)
  return False

def printMsg(liste, personnes): #print the messeges in a list of message objects
    #personnes = {}#dictionnary with the persons in the chat
    for i in liste:
        print(personnes[i.author] + ": " + i.text)


#if scraping for a one-to-one chat then set thread_type = ThreadType.USER
# for groups use ThreadType.GROUP
#client should be the object created with "client = Client(args.address, args.address)"
#and "thread_id" the ID of the thread you're interested in
def getMessageList(client, thread_id, thread_type):

    msg_list = []
    count = 1
    #print("Count: " + str(count))
    messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000)

    appendItems(messages, msg_list)

    while True:
        messages = client.fetchThreadMessages(thread_id=thread_id, limit=10000, before=messages[-1].timestamp)
        appendItems(messages[1:], msg_list)  #we remove the first one because of the way the fetchThread function works. We could use "before=messages[-1].timestamp-1" and keep the first element for clarity's sake but it works as well without
        count = count + 1
        #print("Count: " + str(count))
    
        if messages[0].uid == messages[-1].uid:#as we remove the last one, we do not double count the last list (which will have only one element)
            break

    return msg_list