import argparse
import sys
import os
import re
import time
import sqlite3
from datetime import datetime, timedelta
from termcolor import colored
from constants import *

class IOOperator:
    def log(message, logFile):
        logFile.write(message+'\n')

class DBOperator():

    def close_db_conn(db_conn):
        if not db_conn is None:
            db_conn.close()
        #try:
        #    os.remove(db_path)
        #except (Exception, OSError):
            #self.log(Level.SEVERE, "Error deleting temporary DB: " + db_path)
        #    print("ERROR TODO")

    def create_db_conn(database):
        try:
            #config = SQLiteConfig()
            #config.setEncoding(SQLiteConfig.Encoding.UTF8)
            # config.setJournalMode(JournalMode.WAL)
            # config.setReadOnly(True)
            connection = sqlite3.connect(database)
            # execute_query(self, "PRAGMA wal_checkpoint", db_conn, file.getName())
            return connection
        except Exception as e:
            if(VERBOSE): 
                IOOperator.log("Could not create database connection for " + database + " (" + str(e) + ")")
        return None

    def execute_query(query, db_conn, db_name, logFile):
        db_name = "[" + db_name + "] "
        try:
            result = db_conn.cursor().execute(query).fetchall()
            db_conn.commit()
            if(VERBOSE): 
                IOOperator.log(db_name + "Executed query: " + query, logFile)
            return result
        except Exception as e:
            if(VERBOSE): 
                IOOperator.log(db_name + "Failed to execute query: " + query + ", due to " + str(e), logFile)
        return None

class YourPhoneParser():
    def __init__(self, logFile, contactDB, phoneDB, callingDB, photosDB, settingsDB):
        self.logFile = logFile
        self.contactDB = contactDB
        self.phoneDB = phoneDB
        self.callingDB = callingDB
        self.photosDB = photosDB
        self.settings = settingsDB

    def ldap2datetime(self,timestamp):
        return datetime(1601, 1, 1) + timedelta(seconds=timestamp/10000000)
        # print(ldap2datetime(132255350424395239).isoformat())
        # https: // newbedev.com/how-to-convert-ldap-timestamp-to-unix-timestamp
        # https://stackoverflow.com/questions/5951157/if-in-select-statement-choose-output-value-based-on-column-values
    
    def process_contactsDB(self):
        print(colored('Parsing contacts, calls, sms and mms\n','cyan'))
        
        try:
            contactDB_conn = DBOperator.create_db_conn(self.contactDB)  # contact.db DATABASE
            contacts_info = DBOperator.execute_query(CONTACT_INFO_QUERY, contactDB_conn, self.contactDB, self.logFile)

            country_code_regex = re.compile(COUNTRY_CODE_REGEX)
            i = 0
            for contact in contacts_info:
                i = i+1
                contact = list(contact)
                contact[10] = self.ldap2datetime(contact[10]).isoformat(" ", "seconds")
                print(contact[1:])
                phone_numbers = DBOperator.execute_query(CONTACT_PHONE_QUERY+' WHERE contact_id='+str(contact[0]), contactDB_conn, self.contactDB, self.logFile)

                for phone in phone_numbers:
                    raw_phone_number = country_code_regex.sub('', phone[1])
                    phone = list(phone)
                    phone[3] = PHONE_TYPE[phone[3]]
                    print(phone[1:])
                    callingDB_conn = DBOperator.create_db_conn(self.callingDB)  # calling.db DATABASE
                    calls =  DBOperator.execute_query(CALLING_QUERY+' WHERE phone_number LIKE \'%'+str(raw_phone_number)+'%\'',callingDB_conn, self.callingDB, self.logFile)

                    for call in calls:
                        call = list(call)
                        call[3] = CALL_TYPE[call[3]]
                        call[4] = IS_READ_TYPE[call[4]]
                        call[5] = self.ldap2datetime(call[5]).isoformat(" ", "seconds")
                        call[6] = self.ldap2datetime(call[6]).isoformat(" ", "seconds")
                        print('Call ->\t'+str(call[2:]))

                    phoneDB_conn = DBOperator.create_db_conn(self.phoneDB)   # phone.db DATABASE
                    sms_mms_conversation = DBOperator.execute_query(CONVERSATION_SMS_MMS_QUERY +' WHERE recipient_list LIKE \'%'+str(raw_phone_number)+'%\'',phoneDB_conn, self.phoneDB, self.logFile)

                    for conversation in sms_mms_conversation:
                        conversation = list(conversation)
                        conversation[6] = self.ldap2datetime(conversation[6]).isoformat(" ", "seconds")
                        print('Conv ->'+str(conversation[1:]))
                        sms_list = DBOperator.execute_query('SELECT '+SMS_QUERY+' FROM message WHERE thread_id=' +str(conversation[0])+' ORDER BY timestamp ASC',phoneDB_conn, self.phoneDB, self.logFile)
                        
                        for sms in sms_list:
                            sms = list(sms)
                            sms[2] = SMS_TYPE[sms[2]]
                            sms[3] = self.ldap2datetime(sms[3]).isoformat(" ", "seconds")
                            sms[4] = SMS_STATUS[sms[4]]
                            sms[5] = SMS_PC_STATUS[sms[5]]
                            
                            if(sms[2] == SMS_TYPE[1]):
                                print(colored('+\t'+str(sms[3:]), 'green'))
                            elif(sms[2] == SMS_TYPE[2]):
                                print(colored('-\t'+str(sms[3:]), 'blue'))
                            else:
                                print(colored('Unexpected TODO', 'red'))
                print()
            print('Total contacts:',i)    
            DBOperator.close_db_conn(phoneDB_conn)
            DBOperator.close_db_conn(callingDB_conn)
            DBOperator.close_db_conn(contactDB_conn)
        except Exception as e:
            print(colored('Contact/call/sms/mms parser failed: '+str(e), 'red'))

    def process_mediaDB(self):
        print(colored('Extracting photo (thumbnails and media)\n','cyan'))
        try:
            photosDB_conn = DBOperator.create_db_conn(self.photosDB)  # contact.db DATABASE
            images = DBOperator.execute_query(MEDIA_QUERY, photosDB_conn, self.photosDB, self.logFile)
            if not os.path.exists(EXPORT_FOLDERS['thumb']):
                os.makedirs(EXPORT_FOLDERS['thumb'])
            if not os.path.exists(EXPORT_FOLDERS['media']):
                os.makedirs(EXPORT_FOLDERS['media'])
            for image in images:
                image = list(image)
                image[1] = self.ldap2datetime(image[1]).isoformat(" ", "seconds")
                image[2] = self.ldap2datetime(image[2]).isoformat(" ", "seconds")
                image[3] = self.ldap2datetime(image[3]).isoformat(" ", "seconds")
                # print(image[:9])
                if image[11] == None and image[10] == None:
                    if(VERBOSE):
                        IOOperator.log(image[0]+' not available for export.',self.logFile)
                else:
                    if image[10] != None:
                        f = open(EXPORT_FOLDERS['thumb']+'/'+image[0], "wb")
                        f.write(image[10])  # Media
                    else:
                        f = open(EXPORT_FOLDERS['media']+'/'+image[0], "wb")
                        f.write(image[11])  # Thumbnail
                    f.close()
            DBOperator.close_db_conn(photosDB_conn)

        except Exception as e:
            print(colored('Photo export failed: '+str(e), 'red'))

    def process_settings(self):
        print(colored('Parsing settings\n','cyan'))
        try:
            settingsDB_conn = DBOperator.create_db_conn(self.settings)  # contact.db DATABASE
            phoneApps = DBOperator.execute_query(SETTINGS_QUERY, settingsDB_conn, self.settings, self.logFile)
            for app in phoneApps:
                app = list(app)
                app[3] = self.ldap2datetime(app[3]).isoformat(" ", "seconds")
                print(app)
        except Exception as e:
            print(colored('Settings parser failed: '+str(e), 'red'))           

def setup_args():
    parser = argparse.ArgumentParser(description='Forensic analyzer of Microsoft Your Phone App')
    parser.add_argument('-i', '--input', type=str, help='Path for database folder')
    parser.add_argument('-o', '--output', type=str, help='Path for output results and media export')
    parser.add_argument('-p', '--photos', action='store_true', help='Flag for photos and media extraction')
    parser.add_argument('-v', '--verbose', action='store_true', help='Extensive logging and printout')
    parser.add_argument('-cn', '--contactName', type=str, help='Search by contact name')
    parser.add_argument('-cp', '--contactPhone', type=str, help='Search by contact phone')
    return vars(parser.parse_args())

def main(args):
    start_time = time.time()
    print(colored('Your Phone forensic analyzer.\n','cyan'))

    input_path = args['input']
    output_path = args['output']
    exportPhotos = args['photos']
    VERBOSE = args['verbose']
    contactName = args['contactName']
    contactPhone = args['contactPhone']
            
    if(output_path == None):
        output_path = os. getcwd()
    elif not os.path.exists(output_path):
            os.makedirs(output_path)
    
    contactDB = input_path+'/'+DATABASES['contacts']
    phoneDB = input_path+'/'+DATABASES['phone']
    callingDB = input_path+'/'+DATABASES['calls']
    photosDB = input_path+'/'+DATABASES['photos']
    settingsDB = input_path+'/'+DATABASES['settings']
    logFile = open(output_path+'/log.txt', "w")

    YourPhone = YourPhoneParser(logFile, contactDB, phoneDB, callingDB, photosDB, settingsDB)
    YourPhone.process_contactsDB()
    YourPhone.process_settings()

    if exportPhotos:
        YourPhone.process_mediaDB()

    total_time = round(time.time() - start_time, 2)
    print('Elapsed time: ' + str(total_time) + 's')

    logFile.close

if __name__ == "__main__":
    args = setup_args()
    main(args)