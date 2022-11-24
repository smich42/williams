from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import json


def get_hits_for_stc(stc, driver, loading_seconds=5):
    driver.get("https://www.proquest.com/eebo/commandline")

    sleep(loading_seconds)

    try:
        reject_cookies = driver.find_element(By.ID,
                                             "onetrust-reject-all-handler")
        reject_cookies.click()
        sleep(loading_seconds)

    except NoSuchElementException:
        # No cookies prompt on the page
        pass

    searchbox = driver.find_element(By.ID, "searchTerm")
    submit = driver.find_element(By.ID, "submit_5")

    searchbox.clear()
    searchbox.send_keys(f"COLL(STC) AND BIBNO({stc})")

    submit.click()

    # Ensure results load
    sleep(loading_seconds)

    return [hit.get_attribute("href") for hit in driver.find_elements(By.ID, "citationDocTitleLink")]


def request_user_login(driver, wait_seconds=90):
    driver.get("https://www.proquest.com/eebo/myresearch/signin")

    print("Please log in.", wait_seconds, "seconds allocated.")
    sleep(wait_seconds)


def write_entries_to_file(entries, path):
    with open(path, "w") as f:
        return f.write(json.dumps(entries))


if __name__ == "__main__":
    WILLIAMS_INPUT_PATH = "resource/williams.json"
    WILLIAMS_OUTPUT_PATH = "resource/williams_with_urls.json"
    # The number of newly updated entries required for a JSON write.
    PROCESSED_ENTRIES_FOR_WRITE = 5

    driver = webdriver.Firefox()

    request_user_login(driver)
    print("Assuming user logged in; proceeding.")

    entries = {}

    with open(WILLIAMS_INPUT_PATH, "r") as f:
        # Well-behaved test entry:
        # '{"dedicatee":"ABELL, William, Alderman (DNB).","stc_nos":{"347":[],"11347":["*"],"22532":["*"]}}'
        entries_json = f.read()
        entries = json.loads(entries_json)["entries"]

        for n_processed, entry in enumerate(entries, 1):

            print(f"Processing dedicatee: '{entry['dedicatee']}'")

            for stc in entry["stc_nos"].keys():
                hits = get_hits_for_stc(stc, driver)
                # Insert a JSON array of urls to the beginning of the entry attributes list.
                entry["stc_nos"][stc].insert(0, hits)

                print(
                    f"\tLooked up STC code: '{stc}', writing {len(hits)} URL(s) to entry.")

            # Write for every `PROCESSED_ENTRIES_FOR_WRITE` processed.
            # Make sure to also write on the final entry.
            if n_processed % PROCESSED_ENTRIES_FOR_WRITE == 0 or n_processed == len(entries):

                write_entries_to_file(entries, WILLIAMS_OUTPUT_PATH)
                print(f"Wrote {n_processed} URL-populated entries to {WILLIAMS_OUTPUT_PATH}.",
                      f"({len(entries) - n_processed} remaining.)")

    driver.close()
