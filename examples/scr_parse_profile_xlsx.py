# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.profile import parse_xlsx, ProfileVersion


def main():
    # This sample code shows how to read the Profile.xlsx (found inside the SDK zip file) file into a Profile object

    # Modify to fit your directory setup
    profile_file = '../data/SDK/Profile.xlsx'

    # Ensure that the correct ProfileVersion is provided otherwise, code generation might fail
    profile = parse_xlsx(profile_file, ProfileVersion.current())

    print(profile)


if __name__ == "__main__":
    main()
