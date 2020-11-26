# Simple UNSC Sanctions checker with a GUI and fuzzy matching.

Simple GUI for checking names against the UNSC Sanctions List and generating
reports.

Uses fuzzy matching score for hits. For single name matches, we recommend using
90 Score.

Loads sanctions list in xml format. You can supply your own list or download it
from the UNSC website from within the program.

Comes with a list, but you should probably download the newest version the first
time you run the program.

# Installation and Usage

To install the package:

`pip install unsc_sanctions_checker`

You can run the script from the terminal:

`python -m unsc_sanctions_checker.py`

or just:

`unsc'

In python you can do:

```
import unsc_sanctions_checker

unsc_sanctions_checker.run()
```
