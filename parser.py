import argparse
import sys
import os
import re
import time
import sqlite3
from datetime import datetime, timedelta

# pip install termcolor
from termcolor import colored
# print colored('hello', 'red'), colored('world', 'green')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    # print(f"{bcolors.WARNING}Warning: No active frommets remain. Continue?{bcolors.ENDC}")


def ldap2datetime(timestamp):
    return datetime(1601, 1, 1) + timedelta(seconds=timestamp/10000000)
    # print(ldap2datetime(132255350424395239).isoformat())
    # https: // newbedev.com/how-to-convert-ldap-timestamp-to-unix-timestamp
    # https://stackoverflow.com/questions/5951157/if-in-select-statement-choose-output-value-based-on-column-values


COUNTRY_CODE_REGEX = '\+(?:998|996|995|994|993|992|977|976|975|974|973|972|971|970|968|967|966|965|964|963|962|961|960|886|880|856|855|853|852|850|692|691|690|689|688|687|686|685|683|682|681|680|679|678|677|676|675|674|673|672|670|599|598|597|595|593|592|591|590|509|508|507|506|505|504|503|502|501|500|423|421|420|389|387|386|385|383|382|381|380|379|378|377|376|375|374|373|372|371|370|359|358|357|356|355|354|353|352|351|350|299|298|297|291|290|269|268|267|266|265|264|263|262|261|260|258|257|256|255|254|253|252|251|250|249|248|246|245|244|243|242|241|240|239|238|237|236|235|234|233|232|231|230|229|228|227|226|225|224|223|222|221|220|218|216|213|212|211|98|95|94|93|92|91|90|86|84|82|81|66|65|64|63|62|61|60|58|57|56|55|54|53|52|51|49|48|47|46|45|44\D?1624|44\D?1534|44\D?1481|44|43|41|40|39|36|34|33|32|31|30|27|20|7|1\D?939|1\D?876|1\D?869|1\D?868|1\D?849|1\D?829|1\D?809|1\D?787|1\D?784|1\D?767|1\D?758|1\D?721|1\D?684|1\D?671|1\D?670|1\D?664|1\D?649|1\D?473|1\D?441|1\D?345|1\D?340|1\D?284|1\D?268|1\D?264|1\D?246|1\D?242|1)\D?'
# https://www.ideone.com/AsuVYw
CONTACT_INFO_QUERY = "SELECT c.contact_id, c.display_name, c.nickname, c.company, c.job_title, c.notes, c.name_prefix, c.name_suffix, c.middle_name, c.family_name, c.last_updated_time FROM contact c"
CONTACT_PHONE_QUERY = "SELECT contact_id, phone_number, display_phone_number, phone_number_type FROM phonenumber"
CALLING_QUERY = "SELECT call_id, phone_number, duration, call_type, is_read, start_time, last_updated_time, phone_account_id FROM call_history"
MEDIA_QUERY = "SELECT name, last_updated_time, taken_time, last_seen_time, orientation, mime_type, height, width, size,	uri, thumbnail,	media, checksum FROM media"
# subscription_iD, checksum
CONVERSATION_SMS_MMS_QUERY = "SELECT thread_id, recipient_list, msg_count, unread_count, has_rcs, phone_unread_count, timestamp FROM conversation"  # checksum
SMS_QUERY_TEMPLATE = "thread_id, from_address, type, timestamp, status, pc_status, body"  # subject

PHONE_TYPE = {
    1: 'Home phone number',
    2: 'Mobile phone number',
    3: 'Office phone number',
    4: 'Work mobile',
    5: 'Main phone number',
    6: 'Other phone number'
}
CALL_TYPE = {
    1: 'Incoming',
    2: 'Outgoing',
    3: 'Missed',
    4: 'Unknown',
    5: 'Declined',
    6: 'Blocked'
}
IS_READ_TYPE = {
    0: 'Taken',
    1: 'Missed'
}
SMS_STATUS = {
    1: 'Unread',
    2: 'Read'
}
SMS_PC_STATUS = {
    1: 'Read',
    2: 'Unread'
}
SMS_TYPE = {
    1: 'Received',
    2: 'Sent'
}
EXPORT_FOLDERS = {
    'thumb': 'thumbnails',
    'media': 'media'
}

def main(args):
    start_time = time.time()
    input_path = args['input']
    output_path = args['output']
    exportPhotos = args['photos']
    contactName = args['contactName']
    contactPhone = args['contactPhone']

    if output_path:
        print("Path to databases is required.")
        exit()
    #if not contactName and not contactPhone:
    #    print("Search criteria must be provided.")
    #    exit()

    data = process_contactsDB(input_path+'\contacts.db', input_path+'\phone.db', input_path+'\calling.db')

    if exportPhotos:
        data = process_mediaDB(input_path+'\photos.db', exportPhotos)


def process_contactsDB(contactDB, phoneDB, callingDB):

    try:
        connection = sqlite3.connect(contactDB)  # contact.db DATABASE
        cursor0 = connection.cursor()             # Contact TABLE
        cursor0.execute(CONTACT_INFO_QUERY)
        contacts_info = cursor0.fetchall()

        country_code_regex = re.compile(COUNTRY_CODE_REGEX)
        i = 0
        for contact in contacts_info:
            i = i+1
            contact = list(contact)
            contact[10] = ldap2datetime(contact[10]).isoformat(" ", "seconds")
            print(contact[1:])

            cursor0.execute(CONTACT_PHONE_QUERY + ' WHERE contact_id='+str(contact[0]))
            phone_numbers = cursor0.fetchall()

            for phone in phone_numbers:
                raw_phone_number = country_code_regex.sub('', phone[1])
                phone = list(phone)
                phone[3] = PHONE_TYPE[phone[3]]
                print(phone[1:])

                connection = sqlite3.connect(callingDB)  # calling.db DATABASE
                cursor1 = connection.cursor()            # calling_history TABLE
                cursor1.execute(CALLING_QUERY+' WHERE phone_number LIKE \'%'+str(raw_phone_number)+'%\'')
                calls = cursor1.fetchall()

                for call in calls:
                
                    call = list(call)
                    call[3] = CALL_TYPE[call[3]]
                    call[4] = IS_READ_TYPE[call[4]]
                    call[5] = ldap2datetime(call[5]).isoformat(" ", "seconds")
                    call[6] = ldap2datetime(call[6]).isoformat(" ", "seconds")
                    print('Call ->\t'+str(call[2:]))

                connection = sqlite3.connect(phoneDB)   # phone.db DATABASE
                cursor2 = connection.cursor()           # conversation TABLE
                cursor2.execute(CONVERSATION_SMS_MMS_QUERY +' WHERE recipient_list LIKE \'%'+str(raw_phone_number)+'%\'')
                sms_mms_conversation = cursor2.fetchall()

                for conversation in sms_mms_conversation:
                    conversation = list(conversation)
                    conversation[6] = ldap2datetime(conversation[6]).isoformat(" ", "seconds")
                    print('Conv ->'+str(conversation[1:]))
                    cursor3 = connection.cursor()
                    cursor3.execute('SELECT '+SMS_QUERY_TEMPLATE+' FROM message WHERE thread_id=' +str(conversation[0])+' ORDER BY timestamp ASC')
                    sms_list = cursor3.fetchall()

                    for sms in sms_list:
                        sms = list(sms)
                        sms[2] = SMS_TYPE[sms[2]]
                        sms[3] = ldap2datetime(sms[3]).isoformat(" ", "seconds")
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
        cursor0.close()
        cursor1.close
        cursor2.close
        cursor3.close
        connection.close()

    except Exception as e:
        db_info = None
        print(str(e))


def process_mediaDB(photosDB, output_path):
    try:
        connection = sqlite3.connect(photosDB)  # contact.db DATABASE
        cursor = connection.cursor()            # media TABLE
        cursor.execute(MEDIA_QUERY)
        images = cursor.fetchall()
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        if not os.path.exists(EXPORT_FOLDERS['thumb']):
            os.makedirs(EXPORT_FOLDERS['thumb'])
        if not os.path.exists(EXPORT_FOLDERS['media']):
            os.makedirs(EXPORT_FOLDERS['media'])
        for image in images:
            image = list(image)
            image[1] = ldap2datetime(image[1]).isoformat(" ", "seconds")
            image[2] = ldap2datetime(image[2]).isoformat(" ", "seconds")
            image[3] = ldap2datetime(image[3]).isoformat(" ", "seconds")
            # print(image[:9])
            if image[11] == None and image[10] == None:
                print(image[0]+' not available for export')
            else:

                if image[10] != None:
                    f = open(EXPORT_FOLDERS['thumb']+'/'+image[0], "wb")
                    f.write(image[10])  # Media
                else:
                    f = open(EXPORT_FOLDERS['media']+'/'+image[0], "wb")
                    f.write(image[11])  # Thumbnail
                f.close()
        cursor.close()
        connection.close()
    except Exception as e:
        db_info = None
        print(str(e))

def setup_args():
    parser = argparse.ArgumentParser(description='Forensic analyzer of Microsoft Your Phone App')
    parser.add_argument('-i', '--input', type=str, help='Path to database folder', required=True)
    parser.add_argument('-o', '--output', type=str, help='Path for results')
    parser.add_argument('-p', '--photos', type=str, help='Extract photos from database')
    parser.add_argument('-cn', '--contactName', type=str, help='Search by contact name')
    parser.add_argument('-cp', '--contactPhone', type=str, help='Search by contact phone')
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = setup_args()
    main(args)
