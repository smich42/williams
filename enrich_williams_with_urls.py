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
    searchbox.send_keys(
        f"COLL(Early English Books, 1475-1640 (STC)) AND NOFT(STC (2nd ed.) / {stc}.)")

    submit.click()

    # Ensure results load
    sleep(loading_seconds)

    hits = driver.find_elements(By.ID, "citationDocTitleLink")

    return [hit.get_attribute("href") for hit in hits]


if __name__ == "__main__":
    WILLIAMS_INPUT_PATH = "resource/williams.json"
    WILLIAMS_OUTPUT_PATH = "resource/williams_with_urls.json"

    driver = webdriver.Firefox()

    entries = {}

    with open(WILLIAMS_INPUT_PATH, "r") as f:
        # For use as a test entry:
        # '{"dedicatee":"ABELL, William, Alderman (DNB).","stc_nos":{"347":[],"11347":["*"],"22532":["*"]}}'

        entries_json = f.read()

        # Only scraping a few entries here for testing (note slice)
        entries = json.loads(entries_json)["entries"][53:55]

        for entry in entries:
            print(f"Processing dedicatee: '{entry['dedicatee']}'")

            for stc in entry["stc_nos"].keys():
                print(f"\tLooking up STC code: '{stc}'", end=" | ")

                hits = get_hits_for_stc(stc, driver)
                # Insert a JSON array of urls to the beginning of the entry attributes list.
                entry["stc_nos"][stc].insert(0, hits)

                print(f"Wrote {len(hits)} URL(s) to entry.")

    with open(WILLIAMS_OUTPUT_PATH, "w") as f:
        f.write(json.dumps(entries))
        print("Wrote", len(entries), "entries to", WILLIAMS_OUTPUT_PATH)

    driver.close()
