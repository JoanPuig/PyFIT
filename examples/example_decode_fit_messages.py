# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.decoder import Decoder


def main():
    # This sample code shows how to decode a FIT file into a list of Messages

    # Modify to fit your directory setup
    file_name = './data/FIT/MY_ACTIVITY_FILE.fit'

    messages = Decoder.decode_fit_messages(file_name)

    print(messages)


if __name__ == "__main__":
    main()
