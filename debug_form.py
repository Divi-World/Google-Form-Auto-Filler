# ============================================================
# DEBUG SCRIPT – Full extraction with auto-filling
# ============================================================

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 10)

def sleep(ms):
    time.sleep(ms / 1000.0)

def safe_click(element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.1)
    element.click()

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

def fill_radios():
    radios = driver.find_elements(By.XPATH, "//input[@type='radio'] | //*[@role='radio']")
    groups = {}
    for r in radios:
        try:
            parent = r.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
            parent_id = parent.get_attribute("data-item-id") or parent.get_attribute("id") or parent.text[:30]
            key = parent_id
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
        time.sleep(0.1)
        selected.append(get_label(chosen) or "(no label)")
    return selected

def fill_checkboxes():
    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox'] | //*[@role='checkbox']")
    groups = {}
    for cb in checkboxes:
        try:
            parent = cb.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
            parent_id = parent.get_attribute("data-item-id") or parent.get_attribute("id") or parent.text[:30]
            key = parent_id
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
        num = random.randint(1, min(2, len(group)))
        chosen = random.sample(group, num)
        for cb in chosen:
            safe_click(cb)
            time.sleep(0.1)
            selected.append(get_label(cb) or "(no label)")
    return selected

def extract_page():
    print("\n" + "="*60)
    print("EXTRACTING CURRENT PAGE")
    print("="*60)
    
    # Radios
    radios = driver.find_elements(By.XPATH, "//input[@type='radio'] | //*[@role='radio']")
    print(f"Radios: {len(radios)}")
    groups = {}
    for r in radios:
        try:
            parent = r.find_element(By.XPATH, "./ancestor::*[@role='listitem']")
            parent_text = parent.text[:50] if parent.text else "(no text)"
            key = parent_text
        except:
            key = "ungrouped"
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    print(f"Unique groups: {len(groups)}")
    for i, (key, items) in enumerate(groups.items()):
        print(f"Group {i+1}: {key[:50]}")
        for r in items[:2]:  # show first 2 for brevity
            label = get_label(r)
            print(f"   {label}")

    # Checkboxes
    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox'] | //*[@role='checkbox']")
    print(f"Checkboxes: {len(checkboxes)}")
    for cb in checkboxes:
        label = get_label(cb)
        print(f"   {label}")

    # Text inputs
    text_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    print(f"Text inputs: {len(text_inputs)}")
    for inp in text_inputs:
        if inp.is_displayed():
            aria = inp.get_attribute("aria-label") or ""
            val = inp.get_attribute("value") or ""
            print(f"   aria='{aria}', value='{val}'")
    
    # Buttons
    buttons = driver.find_elements(By.XPATH, "//*[@role='button']")
    print(f"Buttons: {len(buttons)}")
    for b in buttons:
        if b.is_displayed():
            text = b.text.strip()
            aria = b.get_attribute("aria-label") or ""
            jsname = b.get_attribute("jsname") or ""
            print(f"   text='{text}', aria='{aria}', jsname='{jsname}'")

# ============================================================
# MAIN – Navigate all pages with filling
# ============================================================
try:
    driver.get("https://docs.google.com/forms/d/e/1FAIpQLSc0ROYN67nzVvLcBlyuy_EHXqMWFIO168qeMiVLjNLfUoc1xQ/formResponse")
    sleep(3000)
    page = 1

    while True:
        print(f"\n--- PAGE {page} ---")
        extract_page()

        # Fill radios and checkboxes to enable "Next"
        radio_sel = fill_radios()
        check_sel = fill_checkboxes()
        # Also fill faculty text (if any)
        faculty_input = driver.find_elements(By.XPATH, "//input[@type='text']")
        for inp in faculty_input:
            if inp.is_displayed() and not inp.get_attribute("value"):
                aria = inp.get_attribute("aria-label") or ""
                if "Other response" not in aria:
                    inp.send_keys("Faculty of Law")
                    break

        # Check if Submit is present
        try:
            submit_btn = driver.find_element(By.XPATH, "//*[@jsname='LgbsSe']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                print("Reached Submit. Stopping.")
                break
        except:
            pass

        # Click Next using jsname='OCpkoe'
        try:
            next_btn = driver.find_element(By.XPATH, "//*[@jsname='OCpkoe']")
            if next_btn.is_displayed() and next_btn.is_enabled():
                safe_click(next_btn)
                sleep(2000)
                page += 1
                continue
        except:
            pass

        # Fallback: try aria-label
        try:
            btn = driver.find_element(By.XPATH, "//*[@aria-label='Next' or @aria-label='下一页']")
            if btn.is_displayed() and btn.is_enabled():
                safe_click(btn)
                sleep(2000)
                page += 1
                continue
        except:
            pass

        print("No Next or Submit button found. Stopping.")
        break

except Exception as e:
    print(f"Error: {e}")
finally:
    # Keep browser open
    pass