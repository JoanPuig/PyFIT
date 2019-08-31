# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.codegen import TypeCodeGenerator, MessageCodeGenerator
from FIT.profile import Profile


def main():
    # This sample code shows how to read the Profile object from the SDK zip file and generate the FIT.types file

    # Modify to fit your directory setup
    sdk_file = './data/SDK/FitSDKRelease_Latest.zip'
    types_file = './FIT/types.py'
    messages_file = './FIT/messages.py'

    profile = Profile.from_sdk_zip(sdk_file)

    # This will generate the code but only print it
    # print(TypeCodeGenerator.generate(profile))
    # print(MessageCodeGenerator.generate(profile))

    # Generates the code and writes the file to disk
    TypeCodeGenerator.generate(profile, types_file)
    MessageCodeGenerator.generate(profile, messages_file)


if __name__ == "__main__":
    main()
