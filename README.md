# Google Form Auto‑Filler

Universal Python script that automatically fills and submits **any** Google Form – no manual configuration required.

---

## ✅ Features

- Works with **any** Google Form (radios, checkboxes, text inputs, dropdowns)
- Auto‑detects questions, picks random non‑“Other” answers
- Smart text‑input filling (faculty, department, name, email, phone, etc.)
- Handles multi‑page forms & “Submit another response” loop
- Command‑line interface (URL, submission count, delay, headless mode)
- Supports English, Chinese, and Dutch button labels

---

## 📦 Installation

### 1. Clone / Download this repository

### 2. Create a virtual environment (recommended)

**Git Bash (Windows):**
```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows Command Prompt / PowerShell:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install selenium webdriver-manager
```

---

## 🚀 Usage

```bash
python universal_form_filler.py --url "FORM_URL" --count 50
```

### Arguments

| Arg | Description | Default |
|-----|-------------|---------|
| `--url` | Google Form URL | (required) |
| `--count` | Number of submissions | `50` |
| `--delay` | Delay (seconds) between submissions | `2` |
| `--headless` | Run without browser window | `False` |

### Examples
```bash
# Submit 100 forms with 3s delay
python universal_form_filler.py --url "https://docs.google.com/forms/d/e/.../viewform" --count 100 --delay 3

# Headless mode
python universal_form_filler.py --url "..." --headless
```

---

## ⚙️ Customisation

Edit `universal_form_filler.py` to add more text‑input categories:

```python
TEXT_INPUT_DATA = {
    "faculty": ["Faculty of Arts", "Faculty of Science", ...],
    "department": ["Computer Science", "Business", ...],
    # add your own
}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip` not found | Use `python -m pip install ...` |
| ChromeDriver download fails | Download manually from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) and place `chromedriver.exe` in the project folder |
| “Next” button not found | Add your language’s translation in `click_next_or_submit()` |
| “Other” options selected | Add your language’s “Other” word to `is_other_option()` |

---

## 📄 License

For educational and testing purposes only. Use responsibly.