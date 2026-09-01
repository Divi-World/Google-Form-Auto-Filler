# ============================================================
# GOOGLE FORM AUTO-FILLER – WBSEQ (Final, Matrix Fixed)
# ============================================================

import random
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ============================================================
# CONFIGURATION
# ============================================================
TOTAL_SUBMISSIONS = 50
WAIT_AFTER_SUBMIT = 1000
WAIT_AFTER_NEXT = 1500
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc0ROYN67nzVvLcBlyuy_EHXqMWFIO168qeMiVLjNLfUoc1xQ/formResponse"
MAX_PAGES = 8

FACULTY_OPTIONS = [
    "Faculty of Arts",
    "Faculty of Science",
    "Faculty of Social Sciences",
    "Faculty of Communication and Media Studies",
    "Faculty of Management Sciences",
    "Faculty of Law",
    "Faculty of Education"
]

# ============================================================
# SETUP DRIVER
# ============================================================
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 10)

def sleep(ms):
    time.sleep(ms / 1000.0)

def human_delay():
    time.sleep(random.uniform(0.1, 0.3))

def safe_click(element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.05)
    try:
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)

# ============================================================
# GET LABEL
# ============================================================
def get_label(el):
    try:
        return el.find_element(By.XPATH, "./ancestor::label").text.strip()
    except:
        pass
    try:
        parent = el.find_element(By.XPATH, "..")
        spans = parent.find_elements(By.XPATH, ".//span[not(@aria-hidden)]")
        for s in spans:
            txt = s.text.strip()
            if txt:
                return txt
    except:
        pass
    return el.get_attribute("aria-label") or ""

def is_other_option(label):
    lower = label.lower()
    return "other" in lower or "anders" in lower

# ============================================================
# FILL RADIOS – group by statement (for matrix rows)
# ============================================================
def fill_radios():
    radios = driver.find_elements(By.XPATH, "//input[@type='radio'] | //*[@role='radio']")
    groups = {}
    for r in radios:
        aria = r.get_attribute("aria-label") or ""
        # For matrix rows, aria-label looks like "SA, response for <statement>"
        # We extract the statement as the group key.
        if "response for" in aria:
            # Split at "response for " and take the rest
            parts = aria.split("response for", 1)
            if len(parts) > 1:
                key = parts[1].strip()
            else:
                key = aria
        else:
            # Fallback: use parent container text
            try:
                parent = r.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
                parent_text = parent.text[:30] if parent.text else "unnamed"
                key = parent_text
            except:
                key = "ungrouped"
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    
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

# ============================================================
# FILL CHECKBOXES – group by parent container text
# ============================================================
def fill_checkboxes():
    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox'] | //*[@role='checkbox']")
    groups = {}
    for cb in checkboxes:
        try:
            parent = cb.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
            parent_text = parent.text[:30] if parent.text else "unnamed"
            key = parent_text
        except:
            key = "ungrouped"
        if key not in groups:
            groups[key] = []
        groups[key].append(cb)
    
    selected = []
    for group in groups.values():
        already = any(cb.is_selected() for cb in group)
        if already:
            continue
        if not group:
            continue
        # Select 1 or 2 options (random)
        num = random.randint(1, min(2, len(group)))
        chosen = random.sample(group, num)
        for cb in chosen:
            safe_click(cb)
            human_delay()
            selected.append(get_label(cb) or "(no label)")
    return selected

# ============================================================
# FACULTY TEXT INPUT
# ============================================================
def fill_faculty():
    inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    for inp in inputs:
        if not inp.is_displayed() or not inp.is_enabled():
            continue
        aria = inp.get_attribute("aria-label") or ""
        if "Other response" in aria:
            continue
        if not inp.get_attribute("value"):
            value = random.choice(FACULTY_OPTIONS)
            safe_click(inp)
            inp.clear()
            inp.send_keys(value)
            human_delay()
            return value
    return None

# ============================================================
# CHECK IF ALL RADIOS ON PAGE ARE FILLED
# ============================================================
def all_radios_filled():
    radios = driver.find_elements(By.XPATH, "//input[@type='radio'] | //*[@role='radio']")
    for r in radios:
        if not r.is_selected():
            return False
    return True

# ============================================================
# DETECT SUBMIT BUTTON
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

# ============================================================
# CLICK NEXT OR SUBMIT
# ============================================================
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

    # role="button" with text
    try:
        buttons = driver.find_elements(By.XPATH, "//*[@role='button']")
        for b in buttons:
            text = b.text.strip().lower()
            if 'next' in text or 'volgende' in text or '下一页' in text:
                safe_click(b)
                return True
            elif 'submit' in text or 'verzenden' in text or 'indienen' in text or '提交' in text:
                safe_click(b)
                return False
    except:
        pass

    # Google Forms class
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

    return True

# ============================================================
# CLICK SUBMIT ANOTHER RESPONSE
# ============================================================
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
# FILL ONE FORM
# ============================================================
def fill_one_form(iteration):
    print(f"\n🔄 Submission #{iteration+1}/{TOTAL_SUBMISSIONS}")
    page = 1

    while page <= MAX_PAGES:
        if is_submit_present():
            print(f"   Page {page} – Submit detected. Clicking...")
            result = click_next_or_submit()
            if result is False:
                print("   🏁 Form submitted!")
                return True
            else:
                print("   ❌ Submit click failed.")
                return False

        print(f"   Page {page}")

        # Fill radios (grouped by statement)
        radio_sel = fill_radios()
        if radio_sel:
            print(f"      Radios: {len(radio_sel)} selected")
        else:
            print("      No radios filled.")

        # Fill checkboxes
        check_sel = fill_checkboxes()
        if check_sel:
            print(f"      Checkboxes: {len(check_sel)} selected")
        else:
            print("      No checkboxes filled.")

        # Fill faculty
        faculty = fill_faculty()
        if faculty:
            print(f"      Faculty: {faculty}")

        # Check Submit after filling
        if is_submit_present():
            print("   Submit detected after filling. Clicking...")
            result = click_next_or_submit()
            if result is False:
                print("   🏁 Form submitted!")
                return True
            else:
                print("   ❌ Submit click failed.")
                return False

        # Try to proceed
        result = click_next_or_submit()
        if result is False:
            print("   🏁 Form submitted!")
            return True
        elif result is True:
            print("   ➡️ Next clicked.")
            sleep(1500)
            page += 1
        else:
            print("   ⚠️ No button found – assuming done.")
            return True

    # Final attempt
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
try:
    print(f"🚀 Starting {TOTAL_SUBMISSIONS} submissions for WBSEQ...")
    driver.get(FORM_URL)
    sleep(3000)

    for i in range(TOTAL_SUBMISSIONS):
        if i > 0:
            print("⏳ Waiting for 'Submit another response'...")
            found = False
            for attempt in range(15):
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
                sleep(WAIT_AFTER_NEXT)

        success = fill_one_form(i)
        if not success:
            print(f"❌ Submission #{i+1} failed – stopping loop.")
            break

        if i < TOTAL_SUBMISSIONS - 1:
            sleep(WAIT_AFTER_SUBMIT)

    print("🎉 All submissions completed!")

except Exception as e:
    print(f"⚠️ Error: {e}")
finally:
    # Keep browser open
    pass