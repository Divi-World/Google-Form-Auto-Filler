# ============================================================
# GOOGLE FORM AUTO-FILLER
# ============================================================

import random
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ============================================================
# 1. CONFIGURATION
# ============================================================

TOTAL_SUBMISSIONS = 50
WAIT_BEFORE_NEXT = 3000
WAIT_AFTER_NEXT = 4000
FORM_URL = "https://docs.google.com/forms/u/3/d/12bC7eVunnF8tAT34mWYXKfDrA7QYPKXjIzLFX_LSj88/viewform"

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
# 3. TEXT NORMALISATION
# ============================================================

def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[–—]', '-', text)
    text = ' '.join(text.split())
    return text.strip()

# ============================================================
# 4. ROBUST ELEMENT HELPERS
# ============================================================

def safe_click(element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
    except Exception:
        ActionChains(driver).move_to_element(element).click().perform()

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

def get_radio_label(radio):
    lbl = radio.get_attribute("aria-label")
    if lbl:
        return normalize_text(lbl)
    lbl = radio.get_attribute("data-value")
    if lbl:
        return normalize_text(lbl)
    try:
        lbl = radio.find_element(By.XPATH, "./ancestor::label")
        return normalize_text(lbl.text)
    except:
        pass
    try:
        parent = radio.find_element(By.XPATH, "..")
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

def get_checkbox_label(cb):
    lbl = cb.get_attribute("aria-label")
    if lbl:
        return normalize_text(lbl)
    lbl = cb.get_attribute("data-value")
    if lbl:
        return normalize_text(lbl)
    try:
        lbl = cb.find_element(By.XPATH, "./ancestor::label")
        return normalize_text(lbl.text)
    except:
        pass
    try:
        parent = cb.find_element(By.XPATH, "..")
        spans = parent.find_elements(By.XPATH, ".//span[not(@aria-hidden)]")
        for s in spans:
            txt = normalize_text(s.text)
            if txt:
                return txt
        divs = parent.find_elements(By.XPATH, ".//div")
        for d in divs:
            txt = normalize_text(d.text)
            if txt and not d.find_elements(By.XPATH, ".//input | .//*[@role='checkbox']"):
                return txt
    except:
        pass
    return ""

def is_other_option(label):
    if not label:
        return True
    lower = normalize_text(label).lower()
    # Explicit matches
    if lower in ("other", "anders", "andere", "__other_option__"):
        return True
    if label.startswith("__"):
        return True
    if "other" in lower or "anders" in lower or "andere" in lower:
        return True
    return False

def click_radio_by_text(text):
    target = normalize_text(text)
    radios = get_all_radios()
    for r in radios:
        if get_radio_label(r) == target:
            safe_click(r)
            human_delay()
            return True
    for r in radios:
        if get_radio_label(r).lower() == target.lower():
            safe_click(r)
            human_delay()
            return True
    for r in radios:
        lbl = get_radio_label(r)
        if target in lbl or lbl in target:
            safe_click(r)
            human_delay()
            return True
    return False

def get_radio_groups():
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
    groups = get_radio_groups()
    selected = []
    for key, radios in groups.items():
        already = any(r.get_attribute("aria-checked") == "true" or r.is_selected() for r in radios)
        if not already:
            valid = []
            for r in radios:
                lbl = get_radio_label(r)
                if not is_other_option(lbl):
                    valid.append(r)
                else:
                    print(f"   ⚠️ Skipping 'Other' radio in group '{key}' with label: '{lbl}'")
            if not valid:
                print(f"   ⚠️ No non-Other options in group '{key}' – skipping.")
                continue
            chosen = random.choice(valid)
            safe_click(chosen)
            human_delay()
            label = get_radio_label(chosen) or "(no label)"
            selected.append(f"{key} → {label}")
    return selected

def debug_all_radio_labels():
    radios = get_all_radios()
    if not radios:
        print("   🔍 No radio elements found.")
    else:
        print(f"   🔍 Found {len(radios)} radio elements:")
        for i, r in enumerate(radios):
            label = get_radio_label(r) or "(no label)"
            checked = r.get_attribute("aria-checked") == "true" or r.is_selected()
            other = " (Other)" if is_other_option(label) else ""
            print(f"      {i+1}: {label}{other} {checked and '✓' or ''}")

# ============================================================
# 5. PROFILE GENERATION (old form fallback)
# ============================================================

def generate_profile():
    age_options = ['15–19 years', '20–24 years', '25–29 years', '30 years and above']
    faculty_options = [
        'Communication and Media Studies',
        'Social Sciences',
        'Arts',
        'Management Sciences',
        'Education',
        'Engineering',
        'Sciences',
        'College of Health Sciences'
    ]
    age_weights = [0.45, 0.35, 0.15, 0.05]
    age_label = random.choices(age_options, weights=age_weights)[0]

    if age_label == '15–19 years':
        marital = 'Single'
    elif age_label == '20–24 years':
        marital = random.choices(['Single', 'Married'], weights=[0.95, 0.05])[0]
    elif age_label == '25–29 years':
        marital = random.choices(['Single', 'Married'], weights=[0.4, 0.6])[0]
    else:
        marital = random.choices(['Married', 'Single', 'Divorced', 'Widowed'], weights=[0.7, 0.15, 0.1, 0.05])[0]

    if age_label == '15–19 years':
        level = random.choices(['100 Level', '200 Level'], weights=[0.6, 0.4])[0]
    elif age_label == '20–24 years':
        level = random.choices(['200 Level', '300 Level', '400 Level and above'], weights=[0.4, 0.45, 0.15])[0]
    elif age_label == '25–29 years':
        level = random.choices(['300 Level', '400 Level and above'], weights=[0.3, 0.7])[0]
    else:
        level = random.choices(['400 Level and above', '300 Level'], weights=[0.8, 0.2])[0]

    gender = random.choice(['Male', 'Female'])
    faculty = random.choice(faculty_options)
    return {'gender': gender, 'age': age_label, 'marital': marital, 'level': level, 'faculty': faculty}

# ============================================================
# 6. NAVIGATION HELPERS
# ============================================================

def click_next_or_submit():
    human_delay()
    # aria-label – includes 'Volgende' for Dutch
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='Next' or @aria-label='Volgende' or @aria-label='下一页' or @aria-label='Submit' or @aria-label='提交' or @aria-label='Verzenden' or @aria-label='Indienen']")))
        if btn.is_enabled():
            label = btn.get_attribute("aria-label")
            safe_click(btn)
            return label not in ('Submit', '提交', 'Verzenden', 'Indienen')
    except:
        pass
    # role="button" with text
    try:
        buttons = driver.find_elements(By.XPATH, "//*[@role='button']")
        for b in buttons:
            text = b.text.strip().lower()
            if any(n in text for n in ['next', 'volgende', '下一页', 'verder']):
                if b.is_enabled():
                    safe_click(b)
                    return True
            elif any(s in text for s in ['submit', 'verzenden', 'indienen', '提交', 'send', 'verstuur']):
                if b.is_enabled():
                    safe_click(b)
                    return False
    except:
        pass
    # Google Forms specific classes
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, ".freebirdFormviewerViewNavigationNextButton:not(.disabled), [jsname='LgbsSe']")
        if next_btn.is_enabled():
            safe_click(next_btn)
            text = next_btn.text.lower()
            if any(s in text for s in ['submit', 'verzenden', 'indienen', '提交', 'verstuur']):
                return False
            return True
    except:
        pass
    print("⚠️ Could not find Next/Submit button.")
    return False

def click_submit_another():
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
                safe_click(el)
                human_delay()
                return True
        except:
            continue

    try:
        all_elems = driver.find_elements(By.XPATH, "//a | //*[@role='button']")
        for el in all_elems:
            text = el.text.lower()
            if 'nog een' in text or 'another response' in text or '提交另一个' in text:
                if el.is_enabled():
                    safe_click(el)
                    human_delay()
                    return True
    except:
        pass
    return False

# ============================================================
# 7. FILL ONE FORM (old fallback)
# ============================================================

def fill_one_form(iteration):
    print(f"\n🔄 Starting submission #{iteration + 1}/{TOTAL_SUBMISSIONS}")
    profile = generate_profile()
    print(f"👤 Profile: {profile}")

    print("📄 Page 1: Demographics")
    debug_all_radio_labels()

    fields = [
        (profile['gender'], 'Gender'),
        (profile['age'], 'Age Bracket'),
        (profile['level'], 'Level of Study'),
        (profile['faculty'], 'Faculty/Colleges'),
        (profile['marital'], 'Marital Status')
    ]
    for label, desc in fields:
        if click_radio_by_text(label):
            print(f"   ✓ Selected '{label}' for '{desc}'")
        else:
            print(f"   ✗ Could not find '{label}' for '{desc}'")

    if not click_next_or_submit():
        print("⚠️ Could not click 'Next' after Page 1.")
        return False
    sleep(2000)

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='radio'] | //*[@role='radio']")))
    except:
        pass
    sleep(1500)

    page_num = 2
    while True:
        print(f"📄 Page {page_num}")
        selections = fill_random_radios()
        if not selections:
            print("   No non-Other radio groups found. Proceeding...")
        else:
            print(f"   Selected {len(selections)} options:")
            for s in selections:
                print(f"     - {s}")

        if not click_next_or_submit():
            print("🏁 Reached final page – form submitted!")
            break
        sleep(1500)
        page_num += 1
        if page_num > 20:
            print("⚠️ Max pages reached – stopping.")
            break

    print(f"✅ Submission #{iteration + 1} completed.")
    return True

# ============================================================
# 8. OPTIONAL CSR CONFIG OVERRIDE
# ============================================================

try:
    from csr_config import FORM_URL as CSR_URL, fill_form_pages
    FORM_URL = CSR_URL
    def fill_one_form(iteration):
        print(f"\n🔄 Starting CSR submission #{iteration + 1}/{TOTAL_SUBMISSIONS}")
        return fill_form_pages(driver, wait)
    print("✅ CSR configuration loaded – using the CSR survey form.")
except ImportError:
    print("ℹ️  CSR config not found – using the default form.")

# ============================================================
# 9. MAIN LOOP (GUARDED)
# ============================================================

if __name__ == "__main__":
    try:
        print(f"🚀 Starting {TOTAL_SUBMISSIONS} submissions...")
        driver.get(FORM_URL)
        sleep(3000)

        for i in range(TOTAL_SUBMISSIONS):
            if i > 0:
                print("⏳ Waiting for 'Submit another response' link...")
                found = False
                for _ in range(30):
                    sleep(1000)
                    if click_submit_another():
                        found = True
                        print("✅ Clicked 'Submit another response'.")
                        break
                if not found:
                    print("❌ Could not find link – reloading page.")
                    driver.refresh()
                    sleep(5000)
                else:
                    sleep(WAIT_AFTER_NEXT)

            success = fill_one_form(i)
            if not success:
                print(f"❌ Submission #{i+1} failed – stopping.")
                break

            if i < TOTAL_SUBMISSIONS - 1:
                sleep(WAIT_BEFORE_NEXT)

        print("🎉 All 50 submissions completed successfully!")

    except Exception as e:
        print(f"⚠️ An unexpected error occurred: {e}")
    finally:
        # driver.quit()
        pass