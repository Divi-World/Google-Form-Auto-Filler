#!/usr/bin/env python3
# ============================================================
# UNIVERSAL GOOGLE FORM AUTO-FILLER
# Works for ANY Google Form – no manual configuration needed.
# ============================================================

import random
import time
import re
import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ============================================================
# CONFIGURATION (can be overridden by command line)
# ============================================================
DEFAULT_URL = "https://docs.google.com/forms/d/e/FAKE_ID/viewform"  # replace
DEFAULT_COUNT = 50
DEFAULT_DELAY = 2  # seconds between submissions

# Realistic data for text inputs (categorized by label keywords)
TEXT_INPUT_DATA = {
    "faculty": [
        "Faculty of Arts", "Faculty of Science", "Faculty of Social Sciences",
        "Faculty of Communication and Media Studies", "Faculty of Management Sciences",
        "Faculty of Law", "Faculty of Education", "College of Health Sciences"
    ],
    "department": [
        "Computer Science", "Business Administration", "Economics", "Psychology",
        "Engineering", "Medicine", "Law", "Education"
    ],
    "name": [
        "John Doe", "Jane Smith", "Michael Johnson", "Emily Davis", "David Wilson",
        "Sarah Brown", "James Taylor", "Maria Garcia"
    ],
    "email": [
        "student@university.edu", "test@example.com", "user@gmail.com"
    ],
    "phone": [
        "+234 801 234 5678", "+1 555 123 4567", "+44 20 7946 0958"
    ],
    "other": [
        "N/A", "Not applicable", "I prefer not to say"
    ]
}

# ============================================================
# ARGUMENT PARSING
# ============================================================
parser = argparse.ArgumentParser(description="Universal Google Form Auto-Filler")
parser.add_argument("--url", help="Google Form URL", default=DEFAULT_URL)
parser.add_argument("--count", type=int, help="Number of submissions", default=DEFAULT_COUNT)
parser.add_argument("--delay", type=int, help="Delay between submissions (seconds)", default=DEFAULT_DELAY)
parser.add_argument("--headless", action="store_true", help="Run in headless mode (no visible browser)")
args = parser.parse_args()

FORM_URL = args.url
TOTAL_SUBMISSIONS = args.count
DELAY_BETWEEN = args.delay
HEADLESS = args.headless

# ============================================================
# SETUP DRIVER
# ============================================================
options = webdriver.ChromeOptions()
if HEADLESS:
    options.add_argument("--headless")
options.add_argument("--start-maximized")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

def sleep(ms):
    time.sleep(ms / 1000.0)

def human_delay():
    time.sleep(random.uniform(0.2, 0.6))

def safe_click(element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.1)
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
    except Exception:
        ActionChains(driver).move_to_element(element).click().perform()

# ============================================================
# TEXT NORMALIZATION
# ============================================================
def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[–—]', '-', text)
    text = ' '.join(text.split())
    return text.strip()

# ============================================================
# DETECT ELEMENTS (RADIO, CHECKBOX, TEXT, SELECT, BUTTON)
# ============================================================
def get_all_radios():
    inputs = driver.find_elements(By.XPATH, "//input[@type='radio']")
    roles = driver.find_elements(By.XPATH, "//*[@role='radio']")
    all_radios = []
    seen = set()
    for r in inputs + roles:
        if r not in seen:
            seen.add(r)
            all_radios.append(r)
    return all_radios

def get_all_checkboxes():
    inputs = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
    roles = driver.find_elements(By.XPATH, "//*[@role='checkbox']")
    all_cb = []
    seen = set()
    for r in inputs + roles:
        if r not in seen:
            seen.add(r)
            all_cb.append(r)
    return all_cb

def get_all_text_inputs():
    return driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @type='number' or @type='url']")

def get_all_selects():
    return driver.find_elements(By.TAG_NAME, "select")

def get_label(el):
    # Try aria-label first
    lbl = el.get_attribute("aria-label")
    if lbl:
        return normalize_text(lbl)
    # Try data-value
    lbl = el.get_attribute("data-value")
    if lbl:
        return normalize_text(lbl)
    # Try ancestor label
    try:
        lbl = el.find_element(By.XPATH, "./ancestor::label")
        return normalize_text(lbl.text)
    except:
        pass
    # Try sibling spans
    try:
        parent = el.find_element(By.XPATH, "..")
        spans = parent.find_elements(By.XPATH, ".//span[not(@aria-hidden)]")
        for s in spans:
            txt = normalize_text(s.text)
            if txt:
                return txt
        divs = parent.find_elements(By.XPATH, ".//div")
        for d in divs:
            txt = normalize_text(d.text)
            if txt and not d.find_elements(By.XPATH, ".//input | .//*[@role='radio']"):
                return txt
    except:
        pass
    return ""

def is_other_option(label):
    if not label:
        return True
    lower = label.lower()
    return lower in ("other", "anders", "andere") or "other" in lower or "anders" in lower

# ============================================================
# FILL FUNCTIONS
# ============================================================
def fill_radios():
    radios = get_all_radios()
    groups = {}
    for r in radios:
        name = r.get_attribute("name")
        if not name or "_sentinel" in name:
            try:
                container = r.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
                name = container.get_attribute("data-item-id") or container.get_attribute("id") or "group_" + container.text[:20]
            except:
                name = "ungrouped"
        if name not in groups:
            groups[name] = []
        groups[name].append(r)
    selected = []
    for group in groups.values():
        already = any(r.is_selected() for r in group)
        if already:
            continue
        valid = [r for r in group if not is_other_option(get_label(r))]
        if not valid:
            continue
        chosen = random.choice(valid)
        safe_click(chosen)
        human_delay()
        selected.append(get_label(chosen) or "(no label)")
    return selected

def fill_checkboxes():
    cbs = get_all_checkboxes()
    groups = {}
    for cb in cbs:
        name = cb.get_attribute("name")
        if not name or "_sentinel" in name:
            try:
                container = cb.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
                name = container.get_attribute("data-item-id") or container.get_attribute("id") or "group_" + container.text[:20]
            except:
                name = "ungrouped"
        if name not in groups:
            groups[name] = []
        groups[name].append(cb)
    selected = []
    for group in groups.values():
        already = any(cb.is_selected() for cb in group)
        if already:
            continue
        if not group:
            continue
        num = random.randint(1, min(2, len(group)))
        chosen = random.sample(group, num)
        for cb in chosen:
            safe_click(cb)
            human_delay()
            selected.append(get_label(cb) or "(no label)")
    return selected

def fill_text_inputs():
    inputs = get_all_text_inputs()
    filled = []
    for inp in inputs:
        if not inp.is_displayed() or not inp.is_enabled():
            continue
        if inp.get_attribute("value"):
            continue
        label = get_label(inp).lower()
        value = None
        # Check for known categories
        for category, options in TEXT_INPUT_DATA.items():
            if category in label:
                value = random.choice(options)
                break
        if not value:
            # If label contains "other" skip
            if "other" in label:
                continue
            # Default: generate a random word
            value = random.choice(["Yes", "No", "N/A", "Student", "Test response"])
        inp.clear()
        inp.send_keys(value)
        human_delay()
        filled.append(value)
    return filled

def fill_selects():
    selects = get_all_selects()
    filled = []
    for sel in selects:
        if not sel.is_displayed() or not sel.is_enabled():
            continue
        options = sel.find_elements(By.TAG_NAME, "option")
        valid_opts = [opt for opt in options if opt.text.strip() and opt.get_attribute("value")]
        if not valid_opts:
            continue
        chosen = random.choice(valid_opts)
        safe_click(sel)
        chosen.click()
        human_delay()
        filled.append(chosen.text)
    return filled

# ============================================================
# PAGE NAVIGATION
# ============================================================
def is_submit_present():
    try:
        btn = driver.find_element(By.XPATH, "//*[@jsname='LgbsSe']")
        return btn.is_displayed() and btn.is_enabled()
    except:
        pass
    try:
        btn = driver.find_element(By.XPATH, "//*[@aria-label='Submit' or @aria-label='提交' or @aria-label='Verzenden' or @aria-label='Indienen']")
        return btn.is_displayed() and btn.is_enabled()
    except:
        pass
    try:
        btn = driver.find_element(By.XPATH, "//*[@role='button' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]")
        return btn.is_displayed() and btn.is_enabled()
    except:
        pass
    return False

def click_next_or_submit():
    # Submit by jsname
    try:
        btn = driver.find_element(By.XPATH, "//*[@jsname='LgbsSe']")
        if btn.is_displayed() and btn.is_enabled():
            safe_click(btn)
            return False
    except:
        pass
    # aria-label
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='Next' or @aria-label='下一页' or @aria-label='Submit' or @aria-label='提交' or @aria-label='Volgende' or @aria-label='Verzenden' or @aria-label='Indienen']")))
        label = btn.get_attribute("aria-label")
        if label in ('Submit', '提交', 'Verzenden', 'Indienen'):
            safe_click(btn)
            return False
        else:
            safe_click(btn)
            return True
    except:
        pass
    # role="button"
    try:
        btns = driver.find_elements(By.XPATH, "//*[@role='button']")
        for b in btns:
            text = b.text.strip().lower()
            if 'next' in text or 'volgende' in text or '下一页' in text:
                safe_click(b)
                return True
            elif 'submit' in text or 'verzenden' in text or 'indienen' in text or '提交' in text:
                safe_click(b)
                return False
    except:
        pass
    # Google Forms specific
    try:
        btn = driver.find_element(By.CSS_SELECTOR, ".freebirdFormviewerViewNavigationNextButton:not(.disabled), [jsname='LgbsSe']")
        if btn.is_enabled():
            jsname = btn.get_attribute("jsname") or ""
            if jsname == "LgbsSe":
                safe_click(btn)
                return False
            else:
                safe_click(btn)
                return True
    except:
        pass
    return True  # assume Next if unknown

def click_submit_another():
    sleep(1000)
    strategies = [
        "//a[text()='Submit another response']",
        "//a[text()='Nog een antwoord indienen']",
        "//a[text()='提交另一个回复']",
        "//a[contains(text(),'Submit another')]",
        "//a[contains(text(),'Nog een')]",
        "//a[contains(text(),'提交另一个')]",
        "//*[@role='button' and contains(.,'Submit another')]",
        "//*[@role='button' and contains(.,'Nog een')]",
        "//*[@role='button' and contains(.,'提交另一个')]",
        ".freebirdFormviewerViewResponseConfirmationLink"
    ]
    for selector in strategies:
        try:
            if selector.startswith('.'):
                el = driver.find_element(By.CSS_SELECTOR, selector)
            else:
                el = driver.find_element(By.XPATH, selector)
            if el.is_displayed() and el.is_enabled():
                safe_click(el)
                return True
        except:
            continue
    return False

# ============================================================
# FILL ONE FORM (Universal)
# ============================================================
def fill_one_form(iteration):
    print(f"\n🔄 Submission #{iteration+1}/{TOTAL_SUBMISSIONS}")
    page = 1
    max_pages = 10  # safety

    while page <= max_pages:
        if is_submit_present():
            print(f"   Page {page} – Submit detected. Clicking...")
            if click_next_or_submit() is False:
                print("   🏁 Form submitted!")
                return True
            else:
                print("   ❌ Submit click failed.")
                return False

        print(f"   Page {page}")

        # Fill all element types
        r = fill_radios()
        if r:
            print(f"      Radios: {len(r)} selected")
        c = fill_checkboxes()
        if c:
            print(f"      Checkboxes: {len(c)} selected")
        t = fill_text_inputs()
        if t:
            print(f"      Text inputs: {len(t)} filled")
        s = fill_selects()
        if s:
            print(f"      Selects: {len(s)} filled")

        # Check Submit again
        if is_submit_present():
            print("   Submit detected after filling. Clicking...")
            if click_next_or_submit() is False:
                print("   🏁 Form submitted!")
                return True
            else:
                print("   ❌ Submit click failed.")
                return False

        # Navigate
        result = click_next_or_submit()
        if result is False:
            print("   🏁 Form submitted!")
            return True
        elif result is True:
            print("   ➡️ Next clicked.")
            sleep(1000)
            page += 1
        else:
            print("   ⚠️ No button found – assuming done.")
            return True

    # fallback
    print("   ⚠️ Max pages reached – final submit attempt.")
    if is_submit_present():
        if click_next_or_submit() is False:
            print("   🏁 Form submitted!")
            return True
    else:
        try:
            btn = driver.find_element(By.XPATH, "//*[@jsname='LgbsSe']")
            safe_click(btn)
            print("   🏁 Form submitted (by jsname)!")
            return True
        except:
            pass
        print("   ❌ Could not submit.")
        return False

# ============================================================
# MAIN LOOP
# ============================================================
def main():
    print(f"🚀 Universal Form Filler started.")
    print(f"   URL: {FORM_URL}")
    print(f"   Submissions: {TOTAL_SUBMISSIONS}")
    print(f"   Delay between submissions: {DELAY_BETWEEN}s")
    if HEADLESS:
        print("   Headless mode enabled")
    print()

    driver.get(FORM_URL)
    sleep(3000)

    for i in range(TOTAL_SUBMISSIONS):
        if i > 0:
            print("⏳ Waiting for 'Submit another response'...")
            found = False
            for attempt in range(20):
                sleep(1000)
                if click_submit_another():
                    found = True
                    print("   Clicked 'Submit another response'.")
                    break
            if not found:
                print("   Reloading page.")
                driver.refresh()
                sleep(5000)
            else:
                sleep(1500)

        success = fill_one_form(i)
        if not success:
            print(f"❌ Submission #{i+1} failed – stopping loop.")
            break

        if i < TOTAL_SUBMISSIONS - 1:
            sleep(DELAY_BETWEEN * 1000)

    print("🎉 All submissions completed!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        # Keep browser open unless headless
        if not HEADLESS:
            input("Press Enter to close the browser...")
        driver.quit()