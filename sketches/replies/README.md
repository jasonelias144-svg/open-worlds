# What DeepSeek was given

The founder, 2026-11-16: "let's put it all in a single file and I will
provide the file. No link necessary. Just one long file within
everything included. But only what is needed to continue working."
And: "My hope is that you will find a way to integrate everything, and
allow me to continue with DeepSeek without ever requiring more than a
file to provide the current project state."

So each time the founder returns to DeepSeek, the technical lead
builds one file: the reply to DeepSeek's last record, the next steps,
and the code as it stands, each file whole. This folder keeps every
such file, as a record of what DeepSeek was given, with what it was
built from.

## For each reply, three files

Named for the record the reply answers:

| File | What it is |
|---|---|
| `NAME.txt` | The reply itself, written by the technical lead: all that comes before the code |
| `NAME.json` | What goes with it: the folder the code comes from, the files in order, a note for each, and the most bytes the file may have |
| `NAME-for-deepseek.txt` | The file as the founder was given it: the reply, then each file whole, then the line `END OF FILE`, which DeepSeek is asked to quote back |

`python3 docs/reply.py sketches/replies/NAME.json` writes the third
from the first two and the repository's files, and reads it back
from disk to compare each file with the repository. `--check` says whether the file
kept here is still what they make. `tests/test_reply.py` runs that
check for every reply here.

## Current, and past

A spec's `current` is true while the code in the repository is still
as the file has it. Then the file can be made again, byte for byte,
and the test holds it to that. When the code moves on, `current`
becomes false, in the same change: the file stays here, untouched, as
the record of what DeepSeek was given at the time, and a new reply is
written for the next return. What holds a past file to "untouched" is
its hash in the table below, which the test compares with the file.

## The limit

Each spec sets the most bytes its file may have, so that it can be
given whole, as one upload. The script refuses to write a longer one.

## The replies

| Reply | Answers | Given | Bytes | SHA-256 |
|---|---|---|---|---|
| `012-09-05` | Record 012-09-05: the first pass, the repairs, the answers to DeepSeek's two questions, three next steps, and the `chat-world` crate as it stands, sixteen files | 2026-11-16 | 95,149 | `f1f7435f21dbaf8d49de3aea07e83d502d38c6011323feb591b769c2c1c97447` |

## Found after a file was given

A file that was given is not changed. What was later found wrong in it
is said here, and in the next reply.

- `012-09-05`, part 1: "33 of your tests failed for that alone". All
  33 stopped first at those two causes, as written. But three of the
  sixteen still fail with the change applied, as part 2 of the same
  file says, and the home room's seventeen have not been run with its
  later additions joined. "For that first" is what was shown (#98's
  independent review).
