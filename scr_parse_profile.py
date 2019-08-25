from FIT.profile import parse


def main():
    profile = parse('Profile.xlsx')

    print(profile)


if __name__ == "__main__":
    main()