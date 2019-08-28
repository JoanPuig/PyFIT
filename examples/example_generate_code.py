# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.codegen import CodeGenerator
from FIT.profile import Profile


def main():
    # This sample code shows how to read the Profile object from the SDK zip file and generate the FIT.types file

    # Modify to fit your directory setup
    sdk_file = './data/SDK/FitSDKRelease_Latest.zip'
    types_file = './FIT/types.py'

    profile = Profile.parse_sdk_zip(sdk_file)

    # This will generate the code and print it
    print(CodeGenerator.generate(profile))

    # If you actually want to write the file to disk
    CodeGenerator.generate(profile, types_file)


if __name__ == "__main__":
    main()
