# Google Form Auto-Filler

This Python script automatically fills and submits a Google Form with realistic, human-like responses. It handles multi-page forms, skips "Other" options, and can be configured to submit any number of entries.

## Features

- **Realistic demographics**: Generates age‑appropriate marital status and level of study.
- **Human‑like delays**: Random pauses between clicks to mimic a real user.
- **Multi‑language support**: Works with English, Dutch, and Chinese form labels.
- **Skips "Other" options**: Prevents triggering text‑input fields.
- **Automatically finds "Submit another response"**: Reloads if necessary.
- **Detailed logging**: Shows progress and selected answers in the terminal.

## Prerequisites

- **Python 3.8+** installed on your system.
- **Google Chrome** browser (latest version).
- **Internet connection** (to download ChromeDriver automatically).

## Installation

1. **Clone or download** this script into a folder (e.g., `Google_form_filler`).

2. **Install the required Python packages**:

   ```bash
   pip install selenium webdriver-manager