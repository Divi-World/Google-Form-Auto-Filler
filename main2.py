# ============================================================
# GOOGLE FORM AUTO-FILLER – WBSEQ (WhatsApp Business Survey)
# 
# This script automatically fills and submits the
# "WHATSAPP BUSINESS AND STUDENT ENTREPRENEURSHIP QUESTIONNAIRE"
# with realistic, randomized responses.
# ============================================================

import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ============================================================
# 1. CONFIGURATION (EDIT THESE AS NEEDED)
# ============================================================

# Total number of forms to submit
TOTAL_SUBMISSIONS = 50

# Time (in milliseconds) to wait after each submission before looking
# for the "Submit another response" link
WAIT_BEFORE_NEXT = 3000

# Time (in milliseconds) to wait after clicking "Submit another response"
# before starting the next form
WAIT_AFTER_NEXT = 4000

# The URL of the Google Form to fill
# Replace this with your own form link if needed
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc0ROYN67nzVvLcBlyuy_EHXqMWFIO168qeMiVLjNLfUoc1xQ/formResponse"

# ============================================================
# 2. SETUP DRIVER
# ============================================================

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 15)

def sleep(ms):
    time.sleep(ms / 1000.0)

def human_delay():
    time.sleep(random.uniform(0.5, 1.5))

# ============================================================
# 3. HELPER FUNCTIONS FOR RADIO BUTTON HANDLING
# ============================================================

def get_all_radios():
    """Find all radio button elements on the current page."""
    inputs = driver.find_elements(By.XPATH, "//input[@type='radio']")
    roles = driver.find_elements(By.XPATH, "//*[@role='radio']")
    all_radios = []
    seen = set()
    for r in inputs + roles:
        if r not in seen:
            seen.add(r)
            all_radios.append(r)
    return all_radios

def get_radio_label(radio):
    """Extract the human-readable label text for a given radio button."""
    try:
        label = radio.find_element(By.XPATH, "./ancestor::label")
        return label.text.strip()
    except:
        pass
    try:
        parent = radio.find_element(By.XPATH, "..")
        spans = parent.find_elements(By.XPATH, ".//span[not(@aria-hidden)]")
        for s in spans:
            txt = s.text.strip()
            if txt:
                return txt
        divs = parent.find_elements(By.XPATH, ".//div")
        for d in divs:
            txt = d.text.strip()
            if txt and not d.find_elements(By.XPATH, ".//input | .//*[@role='radio']"):
                return txt
    except:
        pass
    return radio.get_attribute("aria-label") or ""

def is_other_option(label):
    """Skip options that are 'Other' or 'Anders' (Dutch) to avoid text inputs."""
    lower = label.lower()
    return lower in ("other", "anders") or \
           lower.startswith("other") or lower.startswith("anders") or \
           "other (please specify)" in lower or "anders:" in lower or "anders -" in lower or \
           "andere" in lower

def get_radio_groups():
    """Group radio buttons by question."""
    groups = {}
    radios = get_all_radios()
    for r in radios:
        group_key = r.get_attribute("name")
        if not group_key or "_sentinel" in group_key:
            try:
                container = r.find_element(By.XPATH, "./ancestor::*[@role='listitem' or contains(@class, 'freebirdFormviewerViewItemsItemItem')]")
                group_key = container.get_attribute("data-item-id") or container.get_attribute("id") or "group_" + container.text[:20]
            except:
                group_key = "ungrouped"
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(r)
    return groups

def fill_random_radios():
    """
    For each radio group on the current page, randomly select one non-'Other' option.
    Returns a list of strings describing what was selected.
    """
    groups = get_radio_groups()
    selected = []
    for key, radios in groups.items():
        already = any(r.get_attribute("aria-checked") == "true" or r.is_selected() for r in radios)
        if not already:
            valid = [r for r in radios if not is_other_option(get_radio_label(r))]
            if not valid:
                print(f"   ⚠️ No non-Other options in group '{key}' – skipping.")
                continue
            chosen = random.choice(valid)
            chosen.click()
            human_delay()
            label = get_radio_label(chosen) or "(no label)"
            selected.append(f"{key} → {label}")
    return selected

def debug_all_radio_labels():
    """Print all radio buttons on the current page with their labels."""
    radios = get_all_radios()
    if not radios:
        print("   🔍 No radio elements found on this page.")
    else:
        print(f"   🔍 Found {len(radios)} radio elements:")
        for i, r in enumerate(radios):
            label = get_radio_label(r) or "(no label)"
            checked = r.get_attribute("aria-checked") == "true" or r.is_selected()
            other = " (Other)" if is_other_option(label) else ""
            print(f"      {i+1}: {label}{other} {checked and '✓' or ''}")

# ============================================================
# 4. NAVIGATION HELPERS (Next / Submit buttons)
# ============================================================

def click_next_or_submit():
    """
    Click the 'Next' or 'Submit' button on the current page.
    Supports English, Chinese, and Dutch labels.
    Returns True if it was a 'Next' button, False if it was 'Submit' or not found.
    """
    human_delay()
    # Strategy 1: aria-label
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='Next' or @aria-label='下一页' or @aria-label='Submit' or @aria-label='提交' or @aria-label='Volgende' or @aria-label='Verzenden' or @aria-label='Indienen']")))
        if btn.is_enabled():
            label = btn.get_attribute("aria-label")
            btn.click()
            return label not in ('Submit', '提交', 'Verzenden', 'Indienen')
    except:
        pass
    # Strategy 2: role="button" with text
    try:
        buttons = driver.find_elements(By.XPATH, "//*[@role='button']")
        next_texts = ['next', 'volgende', '下一页', 'verder']
        submit_texts = ['submit', 'verzenden', 'indienen', '提交', 'send', 'verstuur']
        for b in buttons:
            text = b.text.strip().lower()
            if any(n in text for n in next_texts):
                if b.is_enabled():
                    b.click()
                    return True
            elif any(s in text for s in submit_texts):
                if b.is_enabled():
                    b.click()
                    return False
    except:
        pass
    # Strategy 3: Google Forms specific classes
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, ".freebirdFormviewerViewNavigationNextButton:not(.disabled), [jsname='LgbsSe']")
        if next_btn.is_enabled():
            next_btn.click()
            text = next_btn.text.lower()
            if any(s in text for s in ['submit', 'verzenden', 'indienen', '提交', 'verstuur']):
                return False
            return True
    except:
        pass
    # Strategy 4: any role="button" containing "volgende" or "next"
    try:
        btns = driver.find_elements(By.XPATH, "//*[@role='button' and (contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'volgende') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next'))]")
        if btns:
            for b in btns:
                if b.is_enabled():
                    b.click()
                    return True
    except:
        pass
    print("⚠️ Could not find Next/Submit button.")
    return False

def click_submit_another():
    """
    Click the 'Submit another response' link after a successful submission.
    Tries multiple selectors for English, Chinese, and Dutch.
    """
    sleep(2000)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Nog een') or contains(text(),'Submit another') or contains(text(),'提交另一个')]")))
    except:
        pass

    strategies = [
        "//a[text()='Nog een antwoord indienen']",
        "//a[contains(text(),'Nog een')]",
        "//*[@role='button' and contains(.,'Nog een')]",
        "//*[@aria-label and contains(@aria-label,'Nog een')]",
        "//a[text()='Submit another response']",
        "//*[@role='button' and contains(.,'Submit another')]",
        "//*[contains(text(),'提交另一个')]",
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'another response')]",
        ".freebirdFormviewerViewResponseConfirmationLink",
    ]

    for selector in strategies:
        try:
            if selector.startswith('.'):
                el = driver.find_element(By.CSS_SELECTOR, selector)
            elif selector.startswith('//'):
                el = driver.find_element(By.XPATH, selector)
            else:
                el = driver.find_element(By.XPATH, f"//*[contains(text(), '{selector}')]")
            if el.is_enabled():
                el.click()
                human_delay()
                return True
        except:
            continue

    # Last resort: scan all <a> and role="button" elements
    try:
        all_elems = driver.find_elements(By.XPATH, "//a | //*[@role='button']")
        for el in all_elems:
            text = el.text.lower()
            if 'nog een' in text or 'another response' in text or '提交另一个' in text:
                if el.is_enabled():
                    el.click()
                    human_delay()
                    return True
    except:
        pass
    return False

# ============================================================
# 5. FILL ONE COMPLETE FORM (fully automatic – no hardcoded labels)
# ============================================================

def fill_one_form(iteration):
    """
    Fill and submit a single Google Form by detecting all questions
    and randomly selecting answers – works for any form.
    """
    print(f"\n🔄 Starting submission #{iteration + 1}/{TOTAL_SUBMISSIONS}")

    # --- Page 1 (and any subsequent pages) ---
    page_num = 1
    while True:
        print(f"📄 Page {page_num}")
        debug_all_radio_labels()

        selections = fill_random_radios()
        if not selections:
            print("   No non-Other radio groups found on this page (or no radios). Proceeding...")
        else:
            print(f"   Selected {len(selections)} options:")
            for s in selections:
                print(f"     - {s}")

        # Try to go to the next page
        if not click_next_or_submit():
            print("🏁 Reached final page – form submitted!")
            break

        sleep(2000)
        page_num += 1
        if page_num > 20:
            print("⚠️ Max pages reached – stopping.")
            break

    print(f"✅ Submission #{iteration + 1} completed.")
    return True

# ============================================================
# 6. MAIN LOOP
# ============================================================

try:
    print(f"🚀 Starting {TOTAL_SUBMISSIONS} submissions for WBSEQ...")
    driver.get(FORM_URL)
    sleep(3000)

    for i in range(TOTAL_SUBMISSIONS):
        if i > 0:
            print("⏳ Waiting for 'Submit another response' link...")
            found = False
            for attempt in range(30):
                sleep(1000)
                if click_submit_another():
                    found = True
                    print("✅ Clicked 'Submit another response'.")
                    break
            if not found:
                print("❌ Could not find 'Submit another response' – reloading page.")
                driver.refresh()
                sleep(5000)
            else:
                sleep(WAIT_AFTER_NEXT)

        success = fill_one_form(i)
        if not success:
            print(f"❌ Submission #{i+1} failed – stopping loop.")
            break

        if i < TOTAL_SUBMISSIONS - 1:
            sleep(WAIT_BEFORE_NEXT)

    print("🎉 All submissions completed successfully!")

except Exception as e:
    print(f"⚠️ An unexpected error occurred: {e}")
finally:
    # Keep browser open for inspection
    pass