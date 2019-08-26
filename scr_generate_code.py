# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.codegen import CodeWriter, CodeGenerator
from FIT.profile import parse


def main():
    # This sample code shows how to read the Profile.xlsx file into a Profile object and generate the FIT.types file

    # Modify to fit your directory setup
    profile_file = 'Profile.xlsx'
    types_file = 'FIT/types.py'

    profile = parse(profile_file)

    code_writer = CodeWriter()
    code_generator = CodeGenerator(code_writer, profile)
    code_generator.generate()

    print(code_writer.content)
    code_writer.write_to_file(types_file)


if __name__ == "__main__":
    main()
