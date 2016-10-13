# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re
import unicodedata
import io
import os.path
import shutil

def greetingText():
    greeting = ''
    greetingHeader = """_______________________________________________________________________"""
    printInCenter = lambda text : ' '*((len(greetingHeader)-len(text))/2) + text
    greetingLogo = """                         _____     _                  _
                        |  ___|   | |                | |
    _ __ ___   ___  ___ | |____  _| |_ _ __ __ _  ___| |_ ___  _ __
   | '_ ` _ \ / _ \/ __||  __\ \/ / __| '__/ _` |/ __| __/ _ \| '__|
   | | | | | |  __/\__ \| |___>  <| |_| | | (_| | (__| || (_) | |
   |_| |_| |_|\___||___/\____/_/\_\\__|_|  \__,_|\___|\__\___/|_|
   """
    greetingFooter = greetingHeader
    greeting = greeting + greetingHeader + "\n"
    greeting = greeting + greetingLogo + "\n"
    greeting = greeting + printInCenter("----Facebook Message Extractor----") + "\n"
    greeting = greeting + printInCenter("A simple python script that extract all messages") + "\n"
    greeting = greeting + printInCenter(" of a conversation from the copy of your Facebook data") + "\n"
    greeting += greetingFooter
    return greeting

def normalizeAccountName(s):
    """Forming the facebook account name to english form, lower case
    """
    # s = s.decode('utf-8')
    s = re.sub(u'Đ', 'D', s)
    s = re.sub(u'đ', 'd', s)
    return unicodedata.normalize('NFKD', unicode(s)).encode('ASCII', 'ignore').lower()

def linePrepender(filename, line):
    """Write a lines to the beginning of a file
    """
    # Make file and directory if not exist
    if not os.path.isfile(filename):
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, "w") as f: pass

    # Write the content at the beginning of file
    with io.open(filename, 'r+', encoding='utf-8') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content)

def getConversationMembers():
    """Get all member of a conversation from user input
    """
    inputGroupMembers = []
    print "Please put all member of the conversation (in english form, lower case)"
    # print "Put **not anymore** to finish this putting member step"
    # print "------------------------------------------"
    while(True):
        member = raw_input('Member facebook account: ')
        inputGroupMembers.append(normalizeAccountName(member))
        continueCommand = raw_input('Wanna add more member? (yes/no): ')
        if continueCommand == "no":
            break
        else:
            continue
    return inputGroupMembers

def extractMessageThread(content, inputGroupMembers):
    """Select the message threads that have the same members with user-input members.
    All selected message threads will be put to allThread list
    """
    startThreadString = """<div class="thread">"""
    endThreadString = """</p></div>"""
    groupMembersRegex = re.compile(r'<div class=\"thread\">(.*?)<div ')
    startThreadIndex = 0
    allThread = []
    print "Getting all message threads that have the same members with user-input members..."
    while startThreadIndex != -1:
        startThreadIndex = content.find(startThreadString)
        endThreadIndex = content.find(endThreadString)
        if startThreadIndex == -1 : break
        thread = content[startThreadIndex:endThreadIndex+len(endThreadString)]

        # Just choose the right message thread
        groupMembers = groupMembersRegex.findall(thread[:max(len(thread),500)])[0].split(', ')
        for i in range(len(groupMembers)):
            groupMembers[i] = normalizeAccountName(groupMembers[i])
        if inputGroupMembers == sorted(groupMembers):
            allThread.append(thread)

        # Update content: remove the retrieved thread
        content = content[endThreadIndex+len(endThreadString):]
    print "Done!"
    return allThread

def writeMessageToFiles(allThread, resultFolderName):
    """
    Extracting all message in the message threads.
    Then write to files in structure ./year/month/date(day_of_week).txt
    """
    print "Extracting all message in the conversation..."
    for thread in allThread:
        # chatContent = []
        threadSoup = BeautifulSoup(thread, 'html.parser')
        users = threadSoup.find_all("span", class_="user")
        times = threadSoup.find_all("span", class_="meta")
        messages = threadSoup.find_all("p")
        for i in range(len(users)):
            time = times[i].string.split(' ')
            dayOfWeek, dateOfMonth, month, year, hour = time[0][:-1], time[1], time[2], time[3], time[5]
            fileToWrite = './' + resultFolderName + '/{0}/{1}/{2}({3}).txt'.format(year, month, dateOfMonth, dayOfWeek)
            message = messages[i].string if messages[i].string != None else '**sticker**'
            contentToWrite = users[i].string+ '---------------------' + hour + '\n' +  message
            linePrepender(fileToWrite, '\n' + contentToWrite)

if __name__ == "__main__":
    print greetingText() + "\n"
    sourceFileName = raw_input("Input the location of your messages.htm file (default is ./messages.htm):\n")
    sourceFileName = "./messages.htm" if sourceFileName == "" else sourceFileName
    try:
        with io.open(sourceFileName, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
        print "Reading file done!"
    except:
        exit("Error: file not found!")
    resultFolderName = ''
    inputGroupMembers = sorted(getConversationMembers())
    for i in range(len(inputGroupMembers)):
        resultFolderName += '({0})'.format(inputGroupMembers[i])

    # Remove the old result if exist
    if os.path.exists('./'+resultFolderName):
        shutil.rmtree('./'+resultFolderName)
        print 'Deleted the old result'

    allThread = extractMessageThread(content, inputGroupMembers)
    if len(allThread) == 0:
        print "Error! Can not find any conversation of above members!"
        exit()
    writeMessageToFiles(allThread, resultFolderName)
    print "Done! Happy reading!"
