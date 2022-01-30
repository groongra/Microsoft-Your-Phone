# Microsoft-Your-Phone-parser
usage: parser.py [-h] [-i INPUT] [-o OUTPUT] [-e] [-v] [-gfi GROUPFACEIMAGES] [-spn SEARCHPHONENUMBERS] [-sfp SEARCHFACEPROFILES] [-sfi SEARCHFACEIMAGES]

Forensic analyzer of Microsoft Your Phone App.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path for database folder.
  -o OUTPUT, --output OUTPUT
                        Path for output results and media export. When active the results get sent to the folder provided, otherwise all output data is sent to the current working directory.
  -e, --export          When active exports photos and media from input databases.
  -v, --verbose         Extensive logging and printout through console.
  -gfi GROUPFACEIMAGES, --groupFaceImages GROUPFACEIMAGES
                        Group suspects by face similarity.
  -spn SEARCHPHONENUMBERS, --searchPhoneNumbers SEARCHPHONENUMBERS
                        Search by contact phone. Must input the csv path where all phone number searches are described (e.g -spn phones.csv).
  -sfp SEARCHFACEPROFILES, --searchFaceProfiles SEARCHFACEPROFILES
                        Search by face attributes. Must input the csv path where all face attributes searches are described (e.g -sfp faceAttributes.csv).
  -sfi SEARCHFACEIMAGES, --searchFaceImages SEARCHFACEIMAGES
                        Search by face images. Must input a directory path where all search images reside (e.g -spn ./searchImages)

# CSV format for Search phone numbers
  phone number

<Example>
  phone number 
  +123456789996
  971284456527
  
# CSV format for Search phone numbers
  compare_sign {<,>,=>,<=,!=,==,Null>},
  age,
  race {asian, white, middle eastern, indian, latino and black},
  emotion {angry, fear, neutral, sad, disgust, happy and surprise},
  gender {Man,Woman}

<Example>
  compare_sign,age,race,emotion,gender
  <=,30,white,happy,Man
  Null,Null,Null,neutral,Woman


