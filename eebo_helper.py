from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from time import sleep
from os import path
import json


def reject_cookies_if_present(driver, loading_seconds=5):

    try:
        reject_btn = driver.find_element(By.ID,
                                         "onetrust-reject-all-handler")
        reject_btn.click()
        sleep(loading_seconds)

    except NoSuchElementException:
        # No cookies prompt on the page
        pass


def read_plain_entries_file(json_path):

    with open(json_path, "r") as inf:
        in_json = json.loads(inf.read())
        return in_json["entries"]


def read_url_entries_file(json_path):

    if path.exists(json_path):
        with open(json_path, "r") as outf:
            out_json = json.loads(outf.read())
            # Field "processed" in the JSON is used to save the number of scraped entries.
            # If this exists, it indicates where we restart execution from.
            try:
                previously_processed = int(out_json["processed"])
                if previously_processed > 0:
                    return out_json["entries"], previously_processed

            except json.decoder.JSONDecodeError:
                # No 'processed' field detected, so nowhere to resume from.
                pass

    return None, 0
