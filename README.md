# PyFIT
PyFIT is a library that allows reading .FIT files into Python.


### Getting started ###
* First, you will need to download the FIT SDK file https://www.thisisant.com/resources/fit/
* In the SDK zip file there is a Profile.xlsx that has the necessary information on how to generate the FIT message types
* Generate the code by running [example_generate_code.py](examples/example_generate_code.py). It is important to adjust it to match your directory setup
* You are now ready to go and read some FIT files. Take a look at [example_fit_reader.py](examples/example_fit_reader.py) for how to do that


### Under the hood ###
* FIT files are a binary format specified by Garmin, see the PDF documents in the FIT SDK for details
* The low lever layer will read the bytes, into a File object (see [scr_decode_fit_file.py](examples/scr_decode_fit_file.py))
* In order to help give meaning to the data, Garmin provides the Profiles.xlsx file, which explains the messages (see [scr_profile_from_sdk_zip.py](examples/scr_profile_from_sdk_zip.py) or [scr_profile_from_xlsx.py](examples/scr_profile_from_xlsx.py))
* A code generator is used to generate classes for each one of this message types [example_generate_code.py](examples/example_generate_code.py)


### Device support ###
In theory, all the devices that conform to the FIT specification are supported. That said, there is probably some corner cases that are specific to a particular device or manufacturer. If you are having trouble with a particular file, feel free to attach it to a bug report. 

We have access to the following devices for testing:
* Garmin Fenix 3 HR
* Garmin Index Smart Scale


### Getting your data ###
In order to download the FIT file corresponding to one activity:
* Load the activity in Garmin Connect (https://connect.garmin.com/)
* On the "More" menu (top right gear) select "Export Original"
* Extract the .FIT file from the zip file that will be downloaded

In order to download all your FIT files in bulk from Garmin Connect:
* Visit: https://www.garmin.com/en-GB/account/datamanagement/ 
* Export your data
* You will get an e-mail with a link to download a zip file
* Open that zip file and navigate to \DI_CONNECT\DI-Connect-Fitness-Uploaded-Files where you will find all your FIT files


### How to collaborate ###
Here are a few ideas depending on your level of comfort with the code base:
* Provide .FIT file examples to test corner cases
* File bug reports
* Submit pull requests


### Getting help ###
* If you have any questions, please, feel free to reach out to: Joan Puig at <joan.puig@gmail.com>


### Copyright ###
Copyright 2019 Joan Puig. See LICENSE for details.
