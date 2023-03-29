from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from time import sleep
from os import path
import json


def redirect_to_login(driver, login_timer):

    driver.get("https://www.proquest.com/eebo/myresearch/signin")

    print("Please log in.", login_timer, "seconds allocated.")
    sleep(login_timer)


def click_by_id_if_present(id, driver, loading_seconds):
    # Finds the element with the given ID and clicks it.
    try:
        clickable = driver.find_element(By.ID, id)
        clickable.click()

        sleep(loading_seconds)

    except NoSuchElementException:
        # Element not found in page.
        pass


def reject_cookies_if_present(driver, loading_seconds=5):

    click_by_id_if_present("onetrust-reject-all-handler",
                           driver, loading_seconds=loading_seconds)


def read_entries(json_path):

    with open(json_path, "r") as inf:
        in_json = json.loads(inf.read())
        return in_json["entries"]


def read_processed_entries_only(json_path):

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
