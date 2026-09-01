# ============================================================
# CSR_FORM_CONFIG – Configuration for the CSR Awareness Survey
# ============================================================

import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- Form URL ----------
# Replace with your actual /viewform link (NOT /edit)
FORM_URL = "https://docs.google.com/forms/u/3/d/12bC7eVunnF8tAT34mWYXKfDrA7QYPKXjIzLFX_LSj88/viewform"

# ---------- Profile Generator (Section A) ----------
def generate_profile():
    """Generate a realistic demographic profile for the CSR survey."""
    age_options = ['15–19 years', '20–24 years', '25–29 years', '30 years and above']
    age_weights = [0.45, 0.35, 0.15, 0.05]
    age = random.choices(age_options, weights=age_weights)[0]

    if age == '15–19 years':
        marital = 'Single'
        education = random.choices(['Secondary', 'Tertiary'], weights=[0.6, 0.4])[0]
    elif age == '20–24 years':
        marital = random.choices(['Single', 'Married'], weights=[0.95, 0.05])[0]
        education = random.choices(['Tertiary', 'Postgraduate'], weights=[0.8, 0.2])[0]
    elif age == '25–29 years':
        marital = random.choices(['Single', 'Married'], weights=[0.4, 0.6])[0]
        education = random.choices(['Tertiary', 'Postgraduate'], weights=[0.3, 0.7])[0]
    else:  # 30+
        marital = random.choices(['Married', 'Single', 'Divorced', 'Widowed'], weights=[0.7, 0.15, 0.1, 0.05])[0]
        education = random.choices(['Postgraduate', 'Tertiary'], weights=[0.7, 0.3])[0]

    if education == 'Secondary' and age in ['15–19 years', '20–24 years']:
        occupation = random.choices(['Student', 'Unemployed'], weights=[0.8, 0.2])[0]
    elif education == 'Tertiary' and age in ['20–24 years', '25–29 years']:
        occupation = random.choices(['Student', 'Civil Servant', 'Self Employed'], weights=[0.6, 0.2, 0.2])[0]
    elif education == 'Postgraduate' or age == '30 years and above':
        occupation = random.choices(['Civil Servant', 'Self Employed', 'Retired'], weights=[0.5, 0.3, 0.2])[0]
    else:
        occupation = random.choice(['Student', 'Civil Servant', 'Self Employed', 'Unemployed', 'Retired', 'Others'])

    return {
        'gender': random.choice(['Male', 'Female']),
        'age': age,
        'marital': marital,
        'education': education,
        'occupation': occupation,
        'residence': random.choice(['Less than 1 year', '1–5 years', '6–10 years', 'Above 10 years']),
        'service_used': random.choices(['Yes', 'No'], weights=[0.6, 0.4])[0]
    }

# ---------- Custom fill function (dynamic loop) ----------
def fill_form_pages(driver, wait, debug=False):
    """
    Fill the CSR form dynamically, page by page, until submission.
    Uses globals from main: click_next_or_submit, fill_random_radios, etc.
    """
    import sys
    main_globals = sys.modules['__main__'].__dict__
    # Extract needed functions
    click_next_or_submit = main_globals.get('click_next_or_submit')
    human_delay = main_globals.get('human_delay')
    sleep = main_globals.get('sleep')
    debug_all_radio_labels = main_globals.get('debug_all_radio_labels')
    get_all_checkboxes = main_globals.get('get_all_checkboxes')
    get_checkbox_label = main_globals.get('get_checkbox_label')
    is_other_option = main_globals.get('is_other_option')
    safe_click = main_globals.get('safe_click')
    fill_random_radios = main_globals.get('fill_random_radios')
    normalize_text = main_globals.get('normalize_text')
    click_radio_by_text = main_globals.get('click_radio_by_text')

    if not all([click_next_or_submit, human_delay, sleep, debug_all_radio_labels,
                get_all_checkboxes, get_checkbox_label, is_other_option,
                safe_click, fill_random_radios, normalize_text, click_radio_by_text]):
        print("❌ Could not find required helper functions in main module.")
        return False

    profile = generate_profile()
    print(f"👤 Profile: {profile}")

    page_num = 1
    max_pages = 30  # safety limit

    while page_num <= max_pages:
        print(f"\n📄 Page {page_num}")
        if debug:
            debug_all_radio_labels()

        # --- Fill all radio groups on this page (skipping "Other") ---
        selections = fill_random_radios()
        if selections:
            print(f"   Selected {len(selections)} radio options on this page:")
            for s in selections:
                print(f"     - {s}")
        else:
            print("   ⚠️ No radio groups filled on this page (or all are 'Other').")

        # --- Fallback: on page 1, ensure demographics are set ---
        if page_num == 1:
            fields = [
                (profile['gender'], 'Gender'),
                (profile['age'], 'Age'),
                (profile['marital'], 'Marital Status'),
                (profile['education'], 'Educational Level'),
                (profile['occupation'], 'Occupation'),
                (profile['residence'], 'Length of Residence in Lokoja'),
                (profile['service_used'], 'Have you ever used service at the Hospital?')
            ]
            for label, desc in fields:
                if click_radio_by_text(label):
                    print(f"   ✓ (fallback) Selected '{label}' for '{desc}'")

        # --- Handle checkboxes if present on this page ---
        checkboxes = get_all_checkboxes()
        if checkboxes:
            print(f"   ℹ️ Found {len(checkboxes)} checkboxes on this page.")
            valid = []
            for cb in checkboxes:
                if not cb.is_selected():
                    label = get_checkbox_label(cb)
                    if not is_other_option(label):
                        valid.append(cb)
                    else:
                        print(f"   ⚠️ Skipping 'Other' checkbox with label: '{label}'")
            if valid:
                num = random.randint(1, min(3, len(valid)))
                for cb in random.sample(valid, num):
                    safe_click(cb)
                    human_delay()
                print(f"   ✓ Selected {num} checkbox(es) from this page.")
            else:
                print("   ⚠️ No suitable checkboxes found (all 'Other' or already selected).")
        else:
            print("   ℹ️ No checkboxes found on this page.")

        # --- Navigate to next page or submit ---
        print("⏳ Attempting to click Next/Submit...")
        is_next = click_next_or_submit()
        if is_next is None:
            print("⚠️ Could not find Next/Submit button – stopping.")
            break
        elif is_next is True:
            print("✅ Clicked 'Next' – moving to next page.")
            page_num += 1
            sleep(2000)
            # Wait for page to load
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='radio'] | //*[@role='radio'] | //input[@type='checkbox'] | //*[@role='checkbox']")))
            except:
                pass
            sleep(1500)
        else:
            # is_next is False → we clicked Submit or it's the end
            print("🏁 Reached final page – form submitted!")
            break

        if page_num > max_pages:
            print(f"⚠️ Reached maximum page limit ({max_pages}) – forcing stop.")
            break

    print("✅ Form submission process completed.")
    return True