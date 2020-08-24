from subprocess import Popen, PIPE, check_output


COMMAND = 'zip -r - test/'


def archive1():
    process = Popen(COMMAND.split(), stdout=PIPE)
    stdout, _ = process.communicate()

    with open('archive1.zip', 'w+b') as file:
        file.write(stdout)


def archive2():
    archive = check_output(COMMAND.split())

    with open('archive2.zip', 'w+b') as file:
        file.write(archive)


def main():
    archive1()
    archive2()


if __name__ == "__main__":
    main()
