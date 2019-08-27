# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.decoder import Decoder


def main():
    # This sample code shows how to decode a FIT file into a File object
    # A File object is a low level representation of the FIT file

    # Modify to fit your directory setup
    file_name = './data/FIT/MY_ACTIVITY_FILE.fit'

    file = Decoder.decode_fit_file(file_name)

    print(file)


if __name__ == "__main__":
    main()
