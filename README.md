# PyFIT
PyFIT is a library that allows reading .FIT files into Python.

### Motivation ###
As someone that loves playing around with data and code, I felt that being able to decode the files from my activity trackers would motivate me to be more fit. I hope this project does the same for you.


### Running the code ###
All the example scripts contain a section with configuration, directory and file names, etc. Before you run any scripts, make sure you adapt them to match your setup and desired outcomes.


### Getting started ###
* First, you will need to download the FIT SDK file https://www.thisisant.com/resources/fit/
* In the SDK zip file there is a Profile.xlsx that has the necessary information on how to generate the FIT message types
* Generate the code by running [example_generate_code.py](examples/example_generate_code.py)
* You are now ready to go and read some FIT files. Take a look at [example_decode_fit_activity.py](examples/example_decode_fit_activity.py) for an example of how to do that


### Under the hood ###
* FIT files are a binary format specified by Garmin, see the PDF documents in the FIT SDK for details
* The low lever layer will read the bytes, into a File object (see [example_decode_fit_file.py](examples/example_decode_fit_file.py))
* In order to help give meaning to the data, Garmin provides the Profiles.xlsx file, which explains the messages (see [example_profile_from_sdk_zip.py](examples/example_profile_from_sdk_zip.py) or [example_profile_from_xlsx.py](examples/example_profile_from_xlsx.py))
* A code generator is used to generate classes for each one of this message types [example_generate_code.py](examples/example_generate_code.py)
* The next layer translates those low level Records in the File object into Message objects: [example_decode_fit_messages.py](examples/example_decode_fit_messages.py). Messages can be understood by humans, much better than records can, but are still fairly low level
* The most user friendly way to analyze the data is by using Activity objects. This data is ready to be used as a Pandas dataframe. For an example: [example_decode_fit_activity.py](examples/example_decode_fit_activity.py)


### Device support ###
In theory, all the devices that conform to the FIT specification are supported. That said, there is probably some corner cases that are specific to a particular device or manufacturer. If you are having trouble with a particular file, feel free to attach it to a bug report. 

We have access to the following devices for testing:
* Garmin Fenix 3 HR
* Garmin Index Smart Scale


### Custom data handling ###
It is possible to customize the way a given message is interpreted. Normally this is useful if you know the meaning of some undocumented messages or fields or would like to do some special processing of the developer fields. See [example_decode_custom_message.py](examples/example_decode_custom_message.py).

It is also possible to have custom activities. For an example of how to do that: [example_decode_custom_activity.py](examples/example_decode_custom_activity.py).


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
If you have any questions, please, feel free to reach out to: Joan Puig at <joan.puig@gmail.com>.


### Copyright ###
Copyright 2019 Joan Puig. See LICENSE for details.
