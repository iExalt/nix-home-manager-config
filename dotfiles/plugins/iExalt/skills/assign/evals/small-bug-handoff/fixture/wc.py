"""Count lines and words in a text file: python3 wc.py [--lines | --words] FILE."""
import sys


def count_lines(text):
    return text.count("\n")


def count_words(text):
    return len(text.split())


def main(argv):
    mode, path = argv[1], argv[2]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    print(count_lines(text) if mode == "--lines" else count_words(text))


if __name__ == "__main__":
    main(sys.argv)
