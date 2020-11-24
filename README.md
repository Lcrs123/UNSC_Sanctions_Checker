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

`pip install UNSC_Sanctions_Checker`

This package uses pdfkit to create pdf reports. You need to download wkhtmltopdf
from https://wkhtmltopdf.org/downloads.html and extract the files (specifically
wkhtmltopdf.exe) to your working directory so pdfkit can function properly.
Without wkhtmltopdf, reports will be generated in html format.

You can run the script from the terminal:

`python UNSC_Sanctions_Checker.py`

Or in python you can do:

```
import UNSC_Sanctions_Checker

app = UNSC_Sanctions_Checker.Application()
app.main()
```
