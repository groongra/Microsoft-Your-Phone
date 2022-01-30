import argparse
import uuid
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
import faces

#TODO#
#

class IOOperator:

    def createFolder(folder):            
        if not os.path.exists(folder):
            os.makedirs(folder)

    def csvWriter(filename):
        f = open(filename, 'w', newline='', encoding='utf-8')
        csvWriter = csv.writer(f)
        return f,csvWriter

    def csvReader(filename):
        f = open(filename, 'r', newline='', encoding='utf-8')
        csvReader = csv.reader(f, delimiter=',')
        next(csvReader, None)
        return f,csvReader
        
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

    def __init__(self, input_path, output_path, exportFlag=False, groupFaceImages=False, searchPhoneNumbers=None, searchFaceImages=None, searchFaceProfiles=None):
        self.input_path = input_path
        self.output_path = output_path
        self.contactDB = input_path+'/'+DATABASES['contacts']
        self.phoneDB = input_path+'/'+DATABASES['phone']
        self.callingDB = input_path+'/'+DATABASES['calls']
        self.photosDB = input_path+'/'+DATABASES['photos']
        self.settingsDB = input_path+'/'+DATABASES['settings']
        self.deviceDataDB = input_path+'/'+DATABASES['deviceData']
        self.exportFlag = exportFlag
        self.groupFaceImages = groupFaceImages
        self.searchPhoneNumbers = searchPhoneNumbers
        self.searchFaceImages = searchFaceImages
        self.searchFaceProfiles = searchFaceProfiles
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

    def contacts_calls_sms_mms(self):
        if(self.searchPhoneNumbers == None):
            self.search_contacts_calls_sms_mms()
        else:
            self.process_contacts_calls_sms_mms()

    def search_contacts_calls_sms_mms(self):
        try:
            print(colored('Parsing databases:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')
            contactDB_conn = DBOperator.create_db_conn(self.contactDB)  # contact.db DATABASE

            smsCount = 0
            phone_Processed = []
            calls_Processed = []
            conversation_Processed = []
            country_code_regex = re.compile(COUNTRY_CODE_REGEX)

            for searchPhone in self.searchPhones:
                IOOperator.printOut('? Search: '+searchPhone[0])
                raw_phone_number = country_code_regex.sub('', searchPhone[0])
                contacts = DBOperator.execute_query(CONTACT_INFO_QUERY+' WHERE contact_id = (SELECT contact_id FROM phonenumber WHERE phone_number LIKE \'%'+str(raw_phone_number)+'%\')', contactDB_conn, self.contactDB, self.logFile)
                for contact in contacts:
                    contact = list(contact)
                    contact[10] = self.ldap2datetime(contact[10]).isoformat(" ", "seconds")
                    IOOperator.printOut(contact[1:])
                    phone_numbers = DBOperator.execute_query(CONTACT_PHONE_QUERY+' WHERE contact_id ='+str(contact[0]), contactDB_conn, self.contactDB, self.logFile)
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
                            #csvCalls.writerow(call[:1])
                            
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
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Search',color='red')
            print(colored(str(e), 'red'))

    def process_contacts_calls_sms_mms(self):
        
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
                
                #contactFolder = self.output_path+'/'+contact[1]
                #IOOperator.createFolder(contactFolder)
                #fcall,csvCalls =  IOOperator.csvWriter(contactFolder+'/'+EXPORT_FOLDERS['csv']+'/calls.csv')
                #csvCalls.writerow(CALLS_CSV)
                phone_numbers = DBOperator.execute_query(CONTACT_PHONE_QUERY+' WHERE contact_id='+str(contact[0]), contactDB_conn, self.contactDB, self.logFile)
                for phone in phone_numbers:
                    phone_Processed.append(phone[0])
                    raw_phone_number = country_code_regex.sub('', phone[2])
                    phone = list(phone)
                    phone[4] = PHONE_TYPE[phone[4]]
                    IOOperator.printOut(phone[2:])
                    callingDB_conn = DBOperator.create_db_conn(self.callingDB)  # calling.db DATABASE
                    calls =  DBOperator.execute_query(CALLING_QUERY+' WHERE phone_number LIKE \'%'+str(raw_phone_number)+'%\'',callingDB_conn, self.callingDB, self.logFile)
                    #if calls == []:
                    #    csvCalls.writerow(NO_CALL_CSV)
                    for call in calls:
                        if call[0] not in calls_Processed:
                            calls_Processed.append(call[0])
                        call = list(call)
                        call[3] = CALL_TYPE[call[3]]
                        call[4] = IS_READ_TYPE[call[4]]
                        call[5] = self.ldap2datetime(call[5]).isoformat(" ", "seconds")
                        call[6] = self.ldap2datetime(call[6]).isoformat(" ", "seconds")
                        IOOperator.printOut('Call ->\t'+str(call[1:])) #[2:] TO SKIP PHONE NUMBER#
                        #csvCalls.writerow(call[:1])
                        
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
                #fcall.close()
                #fchat.close()
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
            
            print(' |-> Total contacts:',len(contacts))
            print(' |-> Total phone:',len(phone_Processed))
            print(' |-> Total calls:',len(calls_Processed))
            print(' |-> Total sms chats:',len(conversation_Processed))
            print(' |-> Total sms exchanged:',smsCount)
                   
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Contacts, calls, sms and mms:',color='red')
            print(colored(str(e), 'red'))
    
    def process_settings(self):
        try:
            print(colored('Parsing settings:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')
            settingsDB_conn = DBOperator.create_db_conn(self.settingsDB)  # contact.db DATABASE
            phoneApps = DBOperator.execute_query(SETTINGS_QUERY, settingsDB_conn, self.settingsDB, self.logFile)
            f,csvWriter =  IOOperator.csvWriter(self.output_path+'/'+EXPORT_FILES['settings'])
            csvWriter.writerow(SETTINGS_CSV)

            if(phoneApps == None):
                warning = '<Warning: empty settings database>'
                print(colored(warning,'yellow'), end=' ')
                IOOperator.log(warning, self.logFile)
            else: 
                for app in phoneApps:
                    app = list(app)
                    app[3] = self.ldap2datetime(app[3]).isoformat(" ", "seconds")
                    IOOperator.printOut(app)
                    csvWriter.writerow(app)
            f.close()
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Installed apps',color='cyan') 
            #print(colored('Ok','green'))  
            print(' |-> Total apps:',len(phoneApps))
        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Installed apps',color='red') 
            print(colored(str(e), 'red'))
                 
    def process_images(self):

        try:
            print(colored('Obtaining images:','cyan'))
            IOOperator.startSpinner(self.spinner,'Loading','cyan')  

            if self.exportFlag:
                exportFolder = self.output_path+'/'+EXPORT_FOLDERS['export']
                thumbFolder = exportFolder+'/'+EXPORT_FOLDERS['thumb']
                mediaFolder = exportFolder+'/'+EXPORT_FOLDERS['media'] 
                wallpaperFolder = exportFolder+'/'+EXPORT_FOLDERS['wallpaper']

                IOOperator.createFolder(exportFolder)
                IOOperator.createFolder(thumbFolder)
                IOOperator.createFolder(mediaFolder)
                IOOperator.createFolder(wallpaperFolder)

            analizeImages = False
            
            if (self.groupFaceImages) or (self.searchFaceImages != None) or (self.searchFaceProfiles != None):
                
                analizeImages = True

                if self.groupFaceImages:
                    groupFaceImagesFolder = self.output_path+'/'+EXPORT_FOLDERS['groupFaceImages']
                    IOOperator.createFolder(groupFaceImagesFolder)
                if self.searchFaceImages:
                    searchFaceImagesFolder = self.output_path+'/'+EXPORT_FOLDERS['searchFaceImages']
                    IOOperator.createFolder(searchFaceImagesFolder)
                if self.searchFaceProfiles:
                    searchFaceProfilesFolder = self.output_path+'/'+EXPORT_FOLDERS['searchFaceProfiles']
                    IOOperator.createFolder(searchFaceProfilesFolder)
                
            imgCount = 0
            img_face_tuples  = []
            faceOperator = faces.faceOperator('model_data/')
            f,csvWriter =  IOOperator.csvWriter(self.output_path+'/'+EXPORT_FILES['images'])
            csvWriter.writerow(PHOTOS_CSV)    

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
                        else:
                            filename = str(uuid.uuid4())+extension
                        if self.exportFlag:
                            f = open(wallpaperFolder+'/'+filename, "wb")
                            f.write(raw[0])
                            f.close()
                        if(analizeImages):
                            img_face_tuples.extend(faceOperator.find_faces_in_image(byteImg=raw[0],img_name=filename))
                            
                        image = Image.open(io.BytesIO(raw[0]))
                        csvrow =['wallpaper.'+extension, 'Null', 'Null', 'Null', 'Null', 'image/'+extension, image.height, image.width, 'Null', 'Null', 'False','False', 'True']
                        csvWriter.writerow(csvrow)                          
                        IOOperator.printOut(csvrow[:9])
                        IOOperator.log(str(csvrow[:9]),self.logFile)  
                DBOperator.close_db_conn(images_conn)
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Wallpaper',color='cyan')     
            except Exception as e:
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Wallpaper',color='red')
                print(colored('Wallpaper export failed: '+str(e), 'red'))
            
            try:
                images_conn = DBOperator.create_db_conn(self.photosDB)  # photos.db DATABASE
                images = DBOperator.execute_query(MEDIA_QUERY, images_conn, self.photosDB, self.logFile)
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
                                if analizeImages:  
                                    img_face_tuples.extend(faceOperator.find_faces_in_image(byteImg=image[10],img_name=image[0]))
                                image[10] = 'False'
                                image[11] = 'True'
                                image.append('False')
                            else:
                                if self.exportFlag:
                                    f = open(mediaFolder+'/'+image[0], "wb")     #Export Media
                                    f.write(image[11])
                                if analizeImages:  
                                    img_face_tuples.extend(faceOperator.find_faces_in_image(byteImg=image[11],img_name=image[0]))
                                image[10] = 'True'
                                image[11] = 'False'
                                image.append('False')                           
                            IOOperator.printOut(image[:9])
                            IOOperator.log(str(image[:9]),self.logFile)   
                            csvWriter.writerow(image)    
                            imgCount = imgCount+1 
                DBOperator.close_db_conn(images_conn)
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Thumbnails and media',color='cyan') 
            except Exception as e:
                IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Thumbnails and media',color='red')
                print(colored(str(e), 'red'))
        
            print(colored('Processing images:','cyan'))
            if(self.exportFlag):
                print(' |--> Exported images',imgCount)

            if(analizeImages):

                found_faces = len(img_face_tuples)
                recognizable_faces = faceOperator.delete_non_recognizable_faces(img_face_tuples)
                print(' |--> Found faces', found_faces)
                print(' |--> Recognizable faces', recognizable_faces)

                # Group faces
                if self.groupFaceImages:
                    try:
                        IOOperator.startSpinner(self.spinner,'Loading','cyan')
                        groupedFaces = faceOperator.group_faces(img_face_tuples, output_path=groupFaceImagesFolder)
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Group faces',color='cyan')
                        print(' |--> Grouped faces', groupedFaces)
                    except Exception as e:
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Group faces',color='red') 
                        print(colored(str(e), 'red'))
                    
                #Search face images
                if self.searchFaceImages != None:
                    search_faces_tuples = []
                    try:
                        IOOperator.startSpinner(self.spinner,'Loading','cyan')
                        search_faces_tuples = faceOperator.find_faces_in_folder(self.searchFaceImages)
                        found_faces_in_search_set = len(search_faces_tuples)
                        recognizable_faces_in_search_set = faceOperator.delete_non_recognizable_faces(search_faces_tuples)
                        matched_face_images = faceOperator.search_face_images(faces=img_face_tuples, searchFaces=search_faces_tuples, output_path=searchFaceImagesFolder)
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Search face images',color='cyan')
                        print(' |--> Found faces from search set:', found_faces_in_search_set)
                        print(' |--> Recognizable faces from search set', recognizable_faces_in_search_set)
                        print(' |--> Matched face images', matched_face_images)
                    except Exception as e:      
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Search face images',color='red') 
                        print(colored(str(e), 'red'))

                #Search faces profile
                if self.searchFaceProfiles != None:
                    try:
                        IOOperator.startSpinner(self.spinner,'Loading','cyan')
                        found_faces_in_search_profiles = faceOperator.search_face_profiles(faces=img_face_tuples, searchProfiles=self.searchFaceProfiles, output_path=searchFaceProfilesFolder)
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='✔',text='Search face profiles',color='cyan')
                        print(' |--> Matched face profiles',found_faces_in_search_profiles)
                    except Exception as e:
                        IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Search face profiles',color='red') 
                        print(colored(str(e), 'red'))

        except Exception as e:
            IOOperator.stop_and_persist_spinner(self.spinner, symbol='❌',text='Photos, thumbnails and wallpaper',color='red') 
            print(colored(str(e), 'red'))

def setup_args():
    parser = argparse.ArgumentParser(description='Forensic analyzer of Microsoft Your Phone App.')
    parser.add_argument('-i', '--input', type=str, help='Path for database folder.')
    parser.add_argument('-o', '--output', type=str, help='Path for output results and media export. When active the results get sent to the folder provided, otherwise all output data is sent to the current working directory.')
    parser.add_argument('-e', '--export', action='store_true', help='When active exports photos and media from input databases.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Extensive logging and printout through console.')
    parser.add_argument('-gfi', '--groupFaceImages', type=str, help='Group suspects by face similarity.')
    parser.add_argument('-spn', '--searchPhoneNumbers', type=str, help='Search by contact phone. Must input the csv path where all phone number searches are described (e.g -spn phones.csv).')
    parser.add_argument('-sfp', '--searchFaceProfiles', type=str, help='Search by face attributes. Must input the csv path where all face attributes searches are described (e.g -sfp faceAttributes.csv).')
    parser.add_argument('-sfi', '--searchFaceImages', type=str, help='Search by face images. Must input a directory path where all search images reside (e.g -spn ./searchImages)')
    
    return vars(parser.parse_args())

def main(args):
    start_time = time.time()
    print()
    print(colored('<< Your Phone forensic analyzer >>','grey','on_white'))
    print()

    global VERBOSE 
    VERBOSE = args['verbose']
    input_path = args['input']
    output_path = args['output']
    exportFlag = args['export']
    groupFaceImages = args['groupFaceImages']
    searchPhoneNumbers = args['searchPhoneNumbers']
    searchFaceImages = args['searchFaceImages']
    searchFaceProfiles = args['searchFaceProfiles']
    
    if(input_path == None):
        sys.exit('Invalid input path.')
    elif(not os.path.exists(input_path)):
        sys.exit('Input path doesnt exist.')

    if(output_path == None):
        output_path = os.getcwd()
    elif not os.path.exists(output_path):
        os.makedirs(output_path)

    if(searchFaceImages != None):
        if(not os.path.exists(searchFaceImages)):
            sys.exit('Face search folder doesnt exist.')

    if(searchFaceProfiles != None):
        if(not os.path.exists(searchFaceProfiles)):
            sys.exit('Face search profile csv doesnt exist.')
        else:
            fd_searchFaceProfiles,searchFaceProfiles =  IOOperator.csvReader(searchFaceProfiles)

    if(searchPhoneNumbers != None):
        if(not os.path.exists(searchPhoneNumbers)):
            sys.exit('Phone search csv provided doesnt exist.')
        else:
            fd_searchPhoneNumbers,searchPhoneNumbers =  IOOperator.csvReader(searchPhoneNumbers)

    YourPhone = YourPhoneParser(input_path, output_path, exportFlag=exportFlag, groupFaceImages=groupFaceImages, searchPhoneNumbers=searchPhoneNumbers, searchFaceImages=searchFaceImages, searchFaceProfiles=searchFaceProfiles)

    YourPhone.contacts_calls_sms_mms()
    print()
    YourPhone.process_settings()
    print()
    YourPhone.process_images()
    print()

    if(fd_searchFaceProfiles !=None): fd_searchFaceProfiles.close()
    if(fd_searchPhoneNumbers !=None):fd_searchPhoneNumbers.close()

    total_time = round(time.time() - start_time, 2)
    print('Elapsed time: ' + str(total_time) + 's')

if __name__ == "__main__":
    args = setup_args()
    main(args)