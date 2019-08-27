# PyFIT
PyFIT is a library that allows reading .FIT files into Python.


### Getting started ###
* First, you will need to download the FIT SDK file https://www.thisisant.com/resources/fit/
* In the SDK zip file there is a Profile.xlsx that has the necessary information on how to generate the FIT message types
* Generate the code by running scr_generate_code.py. It is important to adjust it to match your directory setup
* You are now ready to go and read some FIT files. Take a look at scr_fit_reader.py for how to do that


### Under the hood ###
* FIT files are a binary format specified by Garmin, see the PDF documents in the FIT SDK for details
* The low lever layer will read the bytes, into a File object (see scr_decode_fit_file.py)
* In order to help give meaning to the data, Garmin provides the Profiles.xlsx file, which explains the messages (see scr_parse_profile_sdk_zip.py or scr_parse_profile_xlsx.py)
* A code generator is used to generate classes for each one of this message types (see scr_generate_code.py)


### Device support ###
In theory, all the devices that conform to the FIT specification are supported. That said, there is probably some corner cases that are specific to a particular device or manufacturer. If you are having trouble with a particular file, feel free to attach it to a bug report. 

We have access to the following devices for testing:
* Garmin Fenix 3 HR
* Garmin Index Smart Scale

### Getting your data ###
In order to download all your FIT files in bulk from Garmin Connect visit: https://www.garmin.com/en-GB/account/datamanagement/ -> Export your data. You will get an e-mail with a link to download a zip file with all your data in it. If you open that zip file and navigate to \DI_CONNECT\DI-Connect-Fitness-Uploaded-Files you will find all your files.

### How to collaborate ###
Here are a few ideas depending on your level of comfort with the code base:
* Bug reports
* Pull requests
* .FIT file examples to test corner cases


### Getting help ###
* If you have any questions, please, feel free to reach out to: Joan Puig at <joan.puig@gmail.com>



Copyright 2019 Joan Puig. See LICENSE for details
