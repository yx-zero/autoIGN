import random
import os
import re
import string
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ========== auto generate username ==========
try:
    from nltk.corpus import words as nltk_words
    import nltk
    nltk_available = True
except ImportError:
    nltk_available = False

bad_words = {"ass", "damn", "hell", "shit", "fuck", "bitch", "dick", "cock", "pussy", "suck", "hitler"}
common_words = {"time", "person", "year", "way", "day", "thing", "man", "world", "life", "hand", "part", "child", "eye", "woman", "place"}

def is_clean(word):
    lower_word = word.lower()
    return all(bad not in lower_word for bad in bad_words)

def generate_clean_wordlist(limit=500):
    if not nltk_available:
        raise ImportError("NLTK not installed, please run pip install nltk")
    nltk.download('words')
    word_set = set(nltk_words.words())
    filtered = []
    for word in word_set:
        if not word.isalpha():
            continue
        if not (4 <= len(word) <= 9):
            continue
        if word.lower() in common_words:
            continue
        if not word[0].isupper():
            continue
        if is_clean(word):
            filtered.append(word)
        if len(filtered) >= limit:
            break
    return filtered

def load_used_words(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_used_words(words, filepath):
    with open(filepath, 'a', encoding='utf-8') as f:
        for word in words:
            f.write(word + '\n')

def append_username_to_list(username, filepath):
    usernames = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                usernames = eval(content)
    usernames.append(username)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(repr(usernames))

def remove_used_words(all_words, used):
    return [word for word in all_words if word not in used]

def generate_username():
    used_words_path = 'usedwords.txt'
    output_usernames_path = 'words.txt'
    max_length = 16

    all_words = generate_clean_wordlist()
    used_words = load_used_words(used_words_path)
    available_words = remove_used_words(all_words, used_words)

    if len(available_words) < 2:
        raise Exception("Too few available words. Please clear usedwords.txt or expand the word list.")

    while True:
        word1, word2 = random.sample(available_words, 2)
        username = word1 + word2 + str(random.randint(10, 99))
        if is_clean(username):
            if len(username) > max_length:
                username = username[-max_length:]
            save_used_words([word1, word2], used_words_path)
            append_username_to_list(username, output_usernames_path)
            return username

# ========== auto generate username end ==========

def get_accounts():
    valid_accounts = []
    with open("input.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    for line in lines:
        parts = line.split(":", 1)
        if len(parts) == 2:
            valid_accounts.append(parts)
    with open("input.txt", "w", encoding="utf-8") as f:
        f.writelines("\n".join(lines[len(valid_accounts):]))
    return valid_accounts

def process_account(email, password):
    random_name = generate_username()
    print(f"processing account: {email}, new name: {random_name}")

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://sisu.xboxlive.com/connect/XboxLive/?state=login&cobrandId=8058f65d-ce06-4c30-9559-473c9275a65d&tid=896928775&ru=https%3A%2F%2Fwww.minecraft.net%2Fen-us%2Flogin&aid=1142970254")

        email_input = wait.until(EC.presence_of_element_located((By.ID, "usernameEntry")))
        email_input.send_keys(email + Keys.RETURN)

        password_input = wait.until(EC.presence_of_element_located((By.ID, "passwordEntry")))
        password_input.send_keys(password + Keys.RETURN)

        while True:
            try:
                skip_button = driver.find_element(By.ID, "iShowSkip")
                skip_button.click()
                time.sleep(2)
            except NoSuchElementException:
                break

        try:
            no_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="secondaryButton"]')))
            no_button.click()
        except TimeoutException:
            pass

        wait.until(EC.url_contains("msaprofile"))

        try:
            change_name_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@data-aem-contentname="Change Profile Name"]')))
            change_name_link.click()
        except TimeoutException:
            print(f"Change profile name option not found for account {email}.")
            raise Exception("change profile name option not found")

        name_input = wait.until(EC.element_to_be_clickable((By.ID, "change-java-profile-name")))
        name_input.clear()
        name_input.send_keys(random_name)

        update_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "change-profile-name__update-btn")]')))
        update_button.click()

        time.sleep(3)

        with open("output.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{email}----{password}----{random_name}")

        print(f"account {email} changed successfully, recorded")

    except Exception as e:
        print(f"account {email} error: {e}")
        with open("fail.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{email}----{password}")
    finally:
        driver.quit()

if __name__ == "__main__":
    accounts = get_accounts()
    if not accounts:
        print("❌ no valid accounts to process, please check input.txt format")
    else:
        print(f"🔄 detected {len(accounts)} accounts, will process them in order")
        for email, password in accounts:
            process_account(email, password)
            print(f"✅ account {email} completed, waiting 1 second to process the next one...")
            time.sleep(1)
