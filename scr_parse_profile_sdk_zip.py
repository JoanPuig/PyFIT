# Copyright 2019 Joan Puig
# See LICENSE for details

from FIT.profile import parse_sdk_zip


def main():
    # This sample code shows how to read a Profile object from the SDK zip file

    # Modify to fit your directory setup
    sdk_zip_file = './SDK/FitSDKRelease_Latest.zip'

    profile = parse_sdk_zip(sdk_zip_file)

    print(profile)


if __name__ == "__main__":
    main()
