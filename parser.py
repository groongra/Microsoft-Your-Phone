import argparse
import sys
import os
import time
import sqlite3
from datetime import datetime, timedelta


def ldap2datetime(timestamp):
    return datetime(1601, 1, 1) + timedelta(seconds=timestamp/10000000)
    # print(ldap2datetime(132255350424395239).isoformat())
    # https: // newbedev.com/how-to-convert-ldap-timestamp-to-unix-timestamp
    # https://stackoverflow.com/questions/5951157/if-in-select-statement-choose-output-value-based-on-column-values


# It's only used for formatting, so we don't want to crash due to it.
USER_VERSION = 'user_version'

# c.thumbnail CAST((convert(bigint, lastlogontimestamp) / 864000000000.0 - 109207) AS DATETIME) as lastLogonTimestamp,
CONTACT_INFO_QUERY = "SELECT c.contact_id, c.display_name, c.nickname, c.company, c.job_title, c.notes, c.name_prefix, c.name_suffix, c.middle_name, c.family_name, c.last_updated_time FROM contact c"
# CASE phone_number_type WHEN 1 then 'Casa' WHEN 2 then 'Movil' WHEN 3 then 'Trabajo' WHEN 4 then 'MovilDelTrabajo' WHEN 5 then 'Principal' WHEN 6 then 'Otros' WHEN 7 then 'Escuela' END as phone_number_type
CONTACT_PHONE_QUERY = "SELECT p.contact_id, p.phone_number, p.display_phone_number, p.phone_number_type FROM phonenumber p"
CALLING_QUERY = "SELECT call_id, phone_number, duration, call_type, is_read, start_time, last_updated_time, phone_account_id FROM call_history"
MEDIA_QUERY = "SELECT name, last_updated_time, taken_time, last_seen_time, orientation, mime_type, height, width, size,	uri, thumbnail,	media, checksum FROM media"
# MEDIA_QUERY = "SELECT id, name, last_updated_time, taken_time, orientation,	last_seen_time,	mime_type, height, width, size,	uri, thumbnail,	media, checksum FROM media"

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
EXPORT_FOLDERS = {
    'thumb': 'thumbnails',
    'media': 'media'
}


def main(args):
    start_time = time.time()
    input_path = args['input']
    output_path = args['output']
    contactName = args['contactName']
    contactPhone = args['contactPhone']

    if not input_path:
        print("Path to databases is required.")
        exit()
    if not output_path:
        print("JSON result path is required.")
        exit()
    if not contactName and not contactPhone:
        print("Search criteria must be provided.")
        exit()

    # callingDB_file = input_path.append('\calling.db')
    # phoneDB_file = input_path.append('\phone.db')

    # data = process_contactsDB(
    #    input_path+'\contacts.db', input_path+'\phone.db', input_path+'\calling.db')
    data = process_mediaDB(input_path+'\photos.db')


def process_contactsDB(contactDB, phoneDB, callingDB):
    try:
        connection = sqlite3.connect(contactDB)  # contact.db DATABASE
        cursor = connection.cursor()             # Contact TABLE
        cursor.execute(CONTACT_INFO_QUERY)
        contacts_info = cursor.fetchall()
        cursor2 = connection.cursor()            # Phonenumber TABLE
        cursor2.execute(CONTACT_PHONE_QUERY)
        phone_numbers = cursor2.fetchall()

        connection = sqlite3.connect(callingDB)  # calling.db DATABASE
        cursor3 = connection.cursor()            # calling_history TABLE
        cursor3.execute(CALLING_QUERY)
        calls = cursor3.fetchall()

        for contact in contacts_info:
            contact = list(contact)
            contact[10] = ldap2datetime(contact[10]).isoformat(" ", "seconds")
            print(contact[1:])
            for phone in phone_numbers:
                if phone[0] == contact[0]:
                    phone = list(phone)
                    phone[3] = PHONE_TYPE[phone[3]]
                    print(phone[1:])
                    for call in calls:
                        if call[1] in phone[1]:
                            call = list(call)
                            call[3] = CALL_TYPE[call[3]]
                            call[4] = IS_READ_TYPE[call[4]]
                            call[5] = ldap2datetime(
                                call[5]).isoformat(" ", "seconds")
                            call[6] = ldap2datetime(
                                call[6]).isoformat(" ", "seconds")
                            print('>\t'+str(call[2:]))
            print()
        cursor.close()
        cursor2.close()
        cursor3.close()
        connection.close()

    except Exception as e:
        db_info = None
        print(str(e))


def process_mediaDB(photosDB):
    try:
        connection = sqlite3.connect(photosDB)  # contact.db DATABASE
        cursor = connection.cursor()            # media TABLE
        cursor.execute(MEDIA_QUERY)
        images = cursor.fetchall()
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
    parser = argparse.ArgumentParser(
        description='Forensic analyzer of Microsoft Your Phone App')
    parser.add_argument('-i', '--input', type=str,
                        help='Path to database folder', required=True)
    parser.add_argument('-o', '--output', type=str,
                        help='Path to result file in JSON', required=True)
    parser.add_argument('-c', '--contactName', type=str,
                        help='search by contact name')
    parser.add_argument('-p', '--contactPhone', type=str,
                        help='search by contact phone')
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = setup_args()
    main(args)
