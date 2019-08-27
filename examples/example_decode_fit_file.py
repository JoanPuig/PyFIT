# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.decoder import ByteReader, Decoder


def main():
    # This sample code shows how to decode a FIT file into a File object
    # A File object is a low level representation of the FIT file

    # Modify to fit your directory setup
    file_name = './data/FIT/MY_ACTIVITY_FILE.fit'

    # Reads the binary data of the .FIT file
    file_bytes = open(file_name, "rb").read()

    # Constructs a ByteReader and Decoder object
    byte_reader = ByteReader(file_bytes)
    decoder = Decoder(byte_reader)

    # Decodes the file
    file = decoder.decode_file()

    print(file)


if __name__ == "__main__":
    main()
