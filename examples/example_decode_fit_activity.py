# Copyright 2019 Joan Puig
# See LICENSE for details


from FIT.activities import ActivityDecoder


def main():
    # This sample code shows how to decode a FIT file into an activity

    # Modify to fit your directory setup
    file_name = './data/FIT/MY_ACTIVITY_FILE.fit'

    activity = ActivityDecoder.decode_activity(file_name)

    print(activity)


if __name__ == "__main__":
    main()

