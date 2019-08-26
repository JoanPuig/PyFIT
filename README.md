# PyFIT
PyFIT is a library that allows reading .FIT files from Garmin devices into Python.


### Getting Started ###
* First, you will need to download the FIT SDK file https://www.thisisant.com/resources/fit/
* In the SDK zip file there is a Profile.xlsx that has the necessary information on how to generate the FIT message types
* Generate the code by running scr_generate_code.py. It is important to adjust it to match your directory setup
* You are now ready to go and read some FIT files. Take a look at scr_fit_reader for how to do that


### Under the Hood ###
* FIT files are a binary format specified by Garmin, see the PDF documents in the FIT SDK for details
* The low lever layer will read the bytes, into a File object (see scr_decode_fit_file.py)
* In order to help give meaning to the data, Garmin provides the Profiles.xlsx file, which explains the messages (see scr_parse_profile_sdk_zip.py or scr_parse_profile_xlsx.py)
* A code generator is used to generate classes for each one of this message types (see scr_generate_code.py)

### Getting Help ###
* If you have any questions, please, feel free to reach out to: Joan Puig at <joan.puig@gmail.com>



Copyright 2019 Joan Puig. See LICENSE for details
