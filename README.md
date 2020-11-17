# Simple UNSC Sanctions checker with a GUI and fuzzy matching.

Simple GUI for checking names against the UNSC Sanctions List.

Uses fuzzy matching score for hits. For single name matches, we recommend using 90 Score.

Loads sanctions list in xml format. You can supply your own list or download it
from the UNSC website from within the program.

# Usage

You can run the script directly through the terminal:

`python UNSC_Sanctions_Checker.py`

Or in python you can do:

```
import UNSC_Sanctions_Checker

app = UNSC_Sanctions_Checker.Application()
app.main()
```
