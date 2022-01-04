COUNTRY_CODE_REGEX = '\+(?:998|996|995|994|993|992|977|976|975|974|973|972|971|970|968|967|966|965|964|963|962|961|960|886|880|856|855|853|852|850|692|691|690|689|688|687|686|685|683|682|681|680|679|678|677|676|675|674|673|672|670|599|598|597|595|593|592|591|590|509|508|507|506|505|504|503|502|501|500|423|421|420|389|387|386|385|383|382|381|380|379|378|377|376|375|374|373|372|371|370|359|358|357|356|355|354|353|352|351|350|299|298|297|291|290|269|268|267|266|265|264|263|262|261|260|258|257|256|255|254|253|252|251|250|249|248|246|245|244|243|242|241|240|239|238|237|236|235|234|233|232|231|230|229|228|227|226|225|224|223|222|221|220|218|216|213|212|211|98|95|94|93|92|91|90|86|84|82|81|66|65|64|63|62|61|60|58|57|56|55|54|53|52|51|49|48|47|46|45|44\D?1624|44\D?1534|44\D?1481|44|43|41|40|39|36|34|33|32|31|30|27|20|7|1\D?939|1\D?876|1\D?869|1\D?868|1\D?849|1\D?829|1\D?809|1\D?787|1\D?784|1\D?767|1\D?758|1\D?721|1\D?684|1\D?671|1\D?670|1\D?664|1\D?649|1\D?473|1\D?441|1\D?345|1\D?340|1\D?284|1\D?268|1\D?264|1\D?246|1\D?242|1)\D?' # https://www.ideone.com/AsuVYw
CONTACT_INFO_QUERY = "SELECT contact_id, display_name, nickname, company, job_title, notes, name_prefix, name_suffix, middle_name, family_name, last_updated_time FROM contact"
CONTACT_PHONE_QUERY = "SELECT phone_number_id, contact_id, phone_number, display_phone_number, phone_number_type FROM phonenumber"
CALLING_QUERY = "SELECT call_id, phone_number, duration, call_type, is_read, start_time, last_updated_time, phone_account_id FROM call_history"
CONVERSATION_SMS_MMS_QUERY = "SELECT thread_id, recipient_list, msg_count, unread_count, has_rcs, phone_unread_count, timestamp FROM conversation"  # checksum
SMS_QUERY = "SELECT thread_id, from_address, type, timestamp, status, pc_status, body FROM message"  # subject
SETTINGS_QUERY = "SELECT app_name, version, favorite_rank, last_updated_time FROM phone_apps"
SETTINGS_CSV = ['Application', 'Version', 'Favorite rank', 'Last updated time']
MEDIA_QUERY = "SELECT name, last_updated_time, taken_time, last_seen_time, orientation, mime_type, height, width, size,	uri, thumbnail,	media FROM media" #checksum
WALLPAPER_QUERY = "SELECT blob FROM wallpaper"
PHOTOS_CSV = ['Name', 'Last updated time', 'Taken time', 'Last seen time', 'Orientation', 'Mime type', 'Height', 'Width', 'Size', 'Uri', 'Is Thumbnail','Is Media', 'Is Wallpaper']

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
DATABASES ={
    'contacts': 'contacts.db',
    'calls': 'calling.db',
    'phone':'phone.db',
    'photos':'photos.db',
    'notifications.db': 'notifications.db',
    'settings': 'settings.db',
    'sharedcontent': 'sharedcontent.db',
    'deviceData':'deviceData.db'
}
EXPORT_FOLDERS = {
    'thumb': 'thumbnails',
    'media': 'media',
    'wallpaper': 'wallpaper',
    'faces': 'faces_found'
}
EXPORT_FILES = {
    'settings': 'settings.csv',
    'images':'images.csv'
}

MAGIC_NUMBERS = {'png': bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
                 'jpg': bytes([0xFF, 0xD8, 0xFF, 0xE0]),
                 #*********************#
                 'doc': bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),
                 'xls': bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),
                 'ppt': bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),
                 #*********************#
                 'docx': bytes([0x50, 0x4B, 0x03, 0x04, 0x14, 0x00, 0x06, 0x00]),
                 'xlsx': bytes([0x50, 0x4B, 0x03, 0x04, 0x14, 0x00, 0x06, 0x00]),
                 'pptx': bytes([0x50, 0x4B, 0x03, 0x04, 0x14, 0x00, 0x06, 0x00]),
                 #*********************#
                 'pdf': bytes([0x25, 0x50, 0x44, 0x46]),
                 #*********************#
                 'dll': bytes([0x4D, 0x5A, 0x90, 0x00]),
                 'exe': bytes([0x4D, 0x5A]),
                 }
