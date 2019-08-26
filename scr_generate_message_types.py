# Copyright 2019 Joan Puig
# See LICENSE for details

from FIT.profile import parse


def main():
    # This sample code shows how to read the Profile.xlsx file into a Profile object and generate the FIT.types file

    # Modify to fit your directory setup
    profile_file = 'Profile.xlsx'
    types_file = 'FIT/types.py'

    profile = parse(profile_file)

    print(profile)


if __name__ == "__main__":
    main()
