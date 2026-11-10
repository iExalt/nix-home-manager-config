# #7: `--lines` misses a last line without a trailing newline

`python3 wc.py --lines notes.txt` prints 1 for a file containing `first\nsecond`. It should print 2,
like `--words` counts the second word. Files ending in a newline must keep their current count.

Out of scope: `--words`, and any new flags.
