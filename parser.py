import argparse
import csv
import sys
import os
import io
import re
import time
import sqlite3
from datetime import datetime, timedelta
from halo import Halo                       #Pip3 install Halo          https://github.com/manrajgrover/halo
from termcolor import colored               #Pip3 install colored       https://pypi.org/project/colored/
from PIL import Image                       #Pip3 install Image         https://pillow.readthedocs.io/en/stable/handbook/tutorial.html
from constants import *

#TODO#
#

class IOOperator:

    def createFolder(folder):            
        if not os.path.exists(folder):
            os.makedirs(folder)

    def createCSV(filename):
        f = open(filename, 'w', newline='', encoding='utf-8')
        csvWriter = csv.writer(f)
        return f,csvWriter
        
    def openLog(output_path):
        if VERBOSE:
            logFile = open(output_path+'/log.txt','w',encoding='utf-8')
        else:
            logFile = None
        return logFile

    def log(message, logFile):
        if(logFile !=  None and VERBOSE):
            logFile.write(message+'\n')

    def closeLog(logFile):
        if logFile != None:
            logFile.close()
    
    def printOut(message=''):
        if(VERBOSE):
            print(message)

    def startSpinner(spinner,text='',color='white'):
        if(not VERBOSE):
           spinner.start(colored(text,color))

    def stop_and_persist_spinner(spinner,symbol,text,color):
        spinner.stop_and_persist(symbol=symbol.encode('utf-8'),text=colored(text,color))
            
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
            IOOperator.log("Could not create database connection for " + database + " (" + str(e) + ")")
        return None

    def execute_query(query, db_conn, db_name, logFile):
        db_name = "[" + db_name + "] "
        try:
            result = db_conn.cursor().execute(query).fetchall()
            db_conn.commit()
            IOOperator.log(db_name + "Executed query: " + query, logFile)
            return result
        except Exception as e:
            IOOperator.log(db_name + "Failed to execute query: " + query + ", due to " + str(e), logFile)
        return None

class YourPhoneParser():

    def __init__(self, output_path, contactDB, phoneDB, callingDB, photosDB, settingsDB, deviceDataDB, exportFlag=False):
        self.output_path = output_path
        self.contactDB = contactDB
        self.phoneDB = phoneDB
        self.callingDB = callingDB
        self.photosDB = photosDB
        self.settingsDB = settingsDB
        self.deviceDataDB = deviceDataDB
        self.exportFlag = exportFlag
        self.logFile = IOOperator.openLog(output_path)
        self.spinner = Halo(text='', spinner='dots')
        
    def __del__(self):
        IOOperator.closeLog(self.logFile)

    def ldap2datetime(self,timestamp):
        return datetime(1601, 1, 1) + timedelta(seconds=timestamp/10000000)
        # print(ldap2datetime(132255350424395239).isoformat())
        # https://www.epochconverter.com/ldap
        # https://newbedev.com/how-to-convert-ldap-timestamp-to-unix-timestamp
        # https://stackoverflow.com/questions/5951157/if-in-select-statement-choose-output-value-based-on-column-values

    def process_phone(self):
        
        try:
            print(colored('Parsing databases:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')
            contactDB_conn = DBOperator.create_db_conn(self.contactDB)  # contact.db DATABASE

            ### Calls, sms and mms associated with contact
            smsCount = 0
            phone_Processed = []
            calls_Processed = []
            conversation_Processed = []
            country_code_regex = re.compile(COUNTRY_CODE_REGEX)
            contacts = DBOperator.execute_query(CONTACT_INFO_QUERY, contactDB_conn, self.contactDB, self.logFile)
            for contact in contacts:
                contact = list(contact)
                contact[10] = self.ldap2datetime(contact[10]).isoformat(" ", "seconds")
                IOOperator.printOut(contact[1:])
                phone_numbers = DBOperator.execute_query(CONTACT_PHONE_QUERY+' WHERE contact_id='+str(contact[0]), contactDB_conn, self.contactDB, self.logFile)
                for phone in phone_numbers:
                    phone_Processed.append(phone[0])
                    raw_phone_number = country_code_regex.sub('', phone[2])
                    phone = list(phone)
                    phone[4] = PHONE_TYPE[phone[4]]
                    IOOperator.printOut(phone[2:])
                    callingDB_conn = DBOperator.create_db_conn(self.callingDB)  # calling.db DATABASE
                    calls =  DBOperator.execute_query(CALLING_QUERY+' WHERE phone_number LIKE \'%'+str(raw_phone_number)+'%\'',callingDB_conn, self.callingDB, self.logFile)

                    for call in calls:
                        if call[0] not in calls_Processed:
                            calls_Processed.append(call[0])
                        call = list(call)
                        call[3] = CALL_TYPE[call[3]]
                        call[4] = IS_READ_TYPE[call[4]]
                        call[5] = self.ldap2datetime(call[5]).isoformat(" ", "seconds")
                        call[6] = self.ldap2datetime(call[6]).isoformat(" ", "seconds")
                        IOOperator.printOut('Call ->\t'+str(call[1:])) #[2:] TO SKIP PHONE NUMBER#
                        
                    phoneDB_conn = DBOperator.create_db_conn(self.phoneDB)   # phone.db DATABASE
                    sms_mms_conversation = DBOperator.execute_query(CONVERSATION_SMS_MMS_QUERY +' WHERE recipient_list LIKE \'%'+str(raw_phone_number)+'%\'',phoneDB_conn, self.phoneDB, self.logFile)
                    for conversation in sms_mms_conversation:
                        if conversation[0] not in conversation_Processed:
                            conversation_Processed.append(conversation[0])
                        conversation = list(conversation)
                        conversation[6] = self.ldap2datetime(conversation[6]).isoformat(" ", "seconds")
                        IOOperator.printOut('Conv ->'+str(conversation[1:]))
                        sms_list = DBOperator.execute_query(SMS_QUERY+' WHERE thread_id=' +str(conversation[0])+' ORDER BY timestamp ASC',phoneDB_conn, self.phoneDB, self.logFile)
                        for sms in sms_list:
                            smsCount = smsCount+1
                            sms = list(sms)
                            sms[2] = SMS_TYPE[sms[2]]
                            sms[3] = self.ldap2datetime(sms[3]).isoformat(" ", "seconds")
                            sms[4] = SMS_STATUS[sms[4]]
                            sms[5] = SMS_PC_STATUS[sms[5]]
                            if(sms[2] == SMS_TYPE[1]):
                                IOOperator.printOut(colored('+\t'+str(sms[3:]), 'green'))
                            elif(sms[2] == SMS_TYPE[2]):
                                IOOperator.printOut(colored('-\t'+str(sms[3:]), 'blue'))
                            else:
                                IOOperator.printOut(colored('Unexpected TODO', 'red'))
                IOOperator.printOut()

            IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Phone, calls, sms and mms from contacts',color='cyan')

            ### Unnasociated phone, calls, sms and mms ###
            #print(colored('Unnasociated phones, calls, sms and mms:','cyan'), end=' ')
            IOOperator.startSpinner(self.spinner,'Loading','cyan')
            phone_numbers = DBOperator.execute_query(CONTACT_PHONE_QUERY+' WHERE phone_number_id NOT IN ('+ ','.join(map(str, phone_Processed))+')', contactDB_conn, self.contactDB, self.logFile)
            for phone in phone_numbers:
                phone = list(phone)
                phone_Processed.append(phone[0])
                phone[4] = PHONE_TYPE[phone[4]]
                IOOperator.printOut(phone[2:])

            calls = DBOperator.execute_query(CALLING_QUERY+ ' WHERE call_id NOT IN ('+ ','.join(map(str, calls_Processed))+')',callingDB_conn, self.callingDB, self.logFile)
            for call in calls:
                calls_Processed.append(call[0])
                call = list(call)
                call[3] = CALL_TYPE[call[3]]
                call[4] = IS_READ_TYPE[call[4]]
                call[5] = self.ldap2datetime(call[5]).isoformat(" ", "seconds")
                call[6] = self.ldap2datetime(call[6]).isoformat(" ", "seconds")
                IOOperator.printOut('Call ->\t'+str(call[1:]))

            sms_mms_conversation = DBOperator.execute_query(CONVERSATION_SMS_MMS_QUERY +' WHERE thread_id NOT IN ('+ ','.join(map(str, conversation_Processed))+')',phoneDB_conn, self.phoneDB, self.logFile)
            for conversation in sms_mms_conversation:
                conversation_Processed.append(conversation[0])
                conversation = list(conversation)
                conversation[6] = self.ldap2datetime(conversation[6]).isoformat(" ", "seconds")
                IOOperator.printOut('Conv ->'+str(conversation[1:]))
                sms_list = DBOperator.execute_query(SMS_QUERY+' WHERE thread_id=' +str(conversation[0])+' ORDER BY timestamp ASC',phoneDB_conn, self.phoneDB, self.logFile)
                
                for sms in sms_list:
                    smsCount = smsCount+1
                    sms = list(sms)
                    sms[2] = SMS_TYPE[sms[2]]
                    sms[3] = self.ldap2datetime(sms[3]).isoformat(" ", "seconds")
                    sms[4] = SMS_STATUS[sms[4]]
                    sms[5] = SMS_PC_STATUS[sms[5]]
                    
                    if(sms[2] == SMS_TYPE[1]):
                        IOOperator.printOut(colored('+\t'+str(sms[3:]), 'green'))
                    elif(sms[2] == SMS_TYPE[2]):
                        IOOperator.printOut(colored('-\t'+str(sms[3:]), 'blue'))
                    else:
                        IOOperator.printOut(colored('Unexpected TODO', 'red'))
            
            IOOperator.printOut()
            #print(colored('Ok','green'))
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Unnasociated phones, calls, sms and mms',color='cyan')
            
            DBOperator.close_db_conn(phoneDB_conn)
            DBOperator.close_db_conn(callingDB_conn)
            DBOperator.close_db_conn(contactDB_conn)
            
            print('-> Total contacts:',len(contacts))
            print('-> Total phone:',len(phone_Processed))
            print('-> Total calls:',len(calls_Processed))
            print('-> Total sms chats:',len(conversation_Processed))
            print('-> Total sms exchanged:',smsCount)
                   
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Contacts, calls, sms and mms:',color='red')
            print(colored(str(e), 'red'))
        
    def process_images(self):
        try:
            print(colored('Extracting images:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')  
            if self.exportFlag:
                thumbFolder = self.output_path+'/'+EXPORT_FOLDERS['thumb']
                mediaFolder = self.output_path+'/'+EXPORT_FOLDERS['media'] 
                wallpaperFolder = self.output_path+'/'+EXPORT_FOLDERS['wallpaper'] 
                IOOperator.createFolder(thumbFolder)
                IOOperator.createFolder(mediaFolder)
                IOOperator.createFolder(wallpaperFolder)
            images_conn = DBOperator.create_db_conn(self.photosDB)  # photos.db DATABASE
            images = DBOperator.execute_query(MEDIA_QUERY, images_conn, self.photosDB, self.logFile)
            f,csvWritter =  IOOperator.createCSV(self.output_path+'/'+EXPORT_FILES['images'])
            csvWritter.writerow(PHOTOS_CSV)
            imgCount = 0
            #print(colored('-> Wallpaper:','cyan'), end=' ')   #Wallpaper
            try:
                images_conn = DBOperator.create_db_conn(self.deviceDataDB)  # deviceData.db DATABASE
                wallpaper = DBOperator.execute_query(WALLPAPER_QUERY, images_conn, self.deviceDataDB, self.logFile)
                extension = ''
                if(wallpaper == None):
                    warning = '<Warning: no wallpaper available for export>'
                    print(colored(warning,'yellow'), end=' ')
                    IOOperator.log(warning, self.logFile)
                else:
                    for raw in wallpaper:
                        imgCount = imgCount+1
                        for ext in MAGIC_NUMBERS:
                            if raw[0].startswith(MAGIC_NUMBERS[ext]):
                                extension = ext
                                break
                        if(extension == ''):
                            IOOperator.log('<Warning: Unknown extension for wallpaper>',self.logFile)
                        elif self.exportFlag:
                            f = open(wallpaperFolder+'/wallpaper.'+extension, "wb")
                            f.write(raw[0])
                            f.close()
                        image = Image.open(io.BytesIO(raw[0]))
                        csvrow =['wallpaper.'+extension, 'Null', 'Null', 'Null', 'Null', 'image/'+extension, image.height, image.width, 'Null', 'Null', 'False','False', 'True']
                        csvWritter.writerow(csvrow)                          
                        IOOperator.printOut(csvrow[:9])
                        IOOperator.log(str(csvrow[:9]),self.logFile)  
                DBOperator.close_db_conn(images_conn)
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Wallpaper',color='cyan')
                #print(colored('Wallpaper:','cyan'), end=' ')   #Wallpaper         
            except Exception as e:
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Wallpaper',color='red')
                print(colored('Wallpaper export failed: '+str(e), 'red'))
            
            try:
                IOOperator.startSpinner(self.spinner,'Loading','cyan')
                if(images == None):
                    warning = '<Warning: no media or thumbnails available for export>'
                    print(colored(warning,'yellow'), end=' ')
                    IOOperator.log(warning, self.logFile)
                else:                    
                    for image in images:
                        image = list(image)
                        image[1] = self.ldap2datetime(image[1]).isoformat(" ", "seconds")
                        image[2] = self.ldap2datetime(image[2]).isoformat(" ", "seconds")
                        image[3] = self.ldap2datetime(image[3]).isoformat(" ", "seconds")
                        if image[11] == None and image[10] == None:                           
                            warning = image[0]+' not available for export.'
                            IOOperator.printOut(warning)
                            IOOperator.log(warning,self.logFile)
                        else:
                            if image[10] != None:
                                if self.exportFlag:
                                    f = open(thumbFolder+'/'+image[0], "wb")    # Export Thumbnail
                                    f.write(image[10])
                                image[10] = 'False'
                                image[11] = 'True'
                                image.append('False')
                            else:
                                if self.exportFlag:
                                    f = open(mediaFolder+'/'+image[0], "wb")     #Export Media
                                    f.write(image[11]) 
                                image[10] = 'True'
                                image[11] = 'False'
                                image.append('False')                           
                            IOOperator.printOut(image[:9])
                            IOOperator.log(str(image[:9]),self.logFile)   
                            csvWritter.writerow(image)    
                            f.close()
                            imgCount = imgCount+1
                DBOperator.close_db_conn(images_conn)
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Thumbnails and media',color='cyan') 
                #print(colored('-> Thumbnails and media:','cyan'), end=' ')    #Thumbnail & Media
                #print(colored('Ok','green'))
            except Exception as e:
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Thumbnails and media',color='red')
                print(colored(str(e), 'red'))
                
            print('-> Images exported:',imgCount)
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Photos, thumbnails and wallpaper',color='red') 
            print(colored(str(e), 'red'))
            
    def process_settings(self):
        try:
            print(colored('Parsing settings:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')
            settingsDB_conn = DBOperator.create_db_conn(self.settingsDB)  # contact.db DATABASE
            phoneApps = DBOperator.execute_query(SETTINGS_QUERY, settingsDB_conn, self.settingsDB, self.logFile)
            f,csvWritter =  IOOperator.createCSV(self.output_path+'/'+EXPORT_FILES['settings'])
            csvWritter.writerow(SETTINGS_CSV)

            if(phoneApps == None):
                warning = '<Warning: empty settings database>'
                print(colored(warning,'yellow'), end=' ')
                IOOperator.log(warning, self.logFile)
            else: 
                for app in phoneApps:
                    app = list(app)
                    app[3] = self.ldap2datetime(app[3]).isoformat(" ", "seconds")
                    IOOperator.printOut(app)
                    csvWritter.writerow(app)
            f.close()
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Installed apps',color='cyan') 
            #print(colored('Ok','green'))  
            print('-> Total apps:',len(phoneApps))
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Installed apps',color='red') 
            print(colored(str(e), 'red'))
                 
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
    print()
    print(colored('<< Your Phone forensic analyzer >>','grey','on_white'))
    print()
    input_path = args['input']
    output_path = args['output']
    exportFlag = args['photos']
    
    global VERBOSE 
    VERBOSE = args['verbose']
    contactName = args['contactName']
    contactPhone = args['contactPhone']

    if(input_path == None):
        sys.exit('Invalid input path.')
    elif(not os.path.exists(input_path)):
        sys.exit('Input path doesnt exist.')

    if(output_path == None):
        output_path = os.getcwd()
    elif not os.path.exists(output_path):
        os.makedirs(output_path)
    
    contactDB = input_path+'/'+DATABASES['contacts']
    phoneDB = input_path+'/'+DATABASES['phone']
    callingDB = input_path+'/'+DATABASES['calls']
    photosDB = input_path+'/'+DATABASES['photos']
    settingsDB = input_path+'/'+DATABASES['settings']
    deviceDataDB = input_path+'/'+DATABASES['deviceData']

    YourPhone = YourPhoneParser(output_path, contactDB, phoneDB, callingDB, photosDB, settingsDB, deviceDataDB, exportFlag)
    YourPhone.process_phone()
    print()
    YourPhone.process_settings()
    print()
    YourPhone.process_images()
    print()
    total_time = round(time.time() - start_time, 2)
    print('Elapsed time: ' + str(total_time) + 's')

if __name__ == "__main__":
    args = setup_args()
    main(args)