from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from os import path
import json
import argparse


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


def request_user_login(driver, login_timer):

    driver.get("https://www.proquest.com/eebo/myresearch/signin")

    print("Please log in.", login_timer, "seconds allocated.")
    sleep(login_timer)


def write_entries_to_file(entries, previously_processed, save_path):

    with open(save_path, "w") as f:
        f.write(json.dumps({
            "processed": previously_processed,
            "entries": entries
        }))

    print(f"Wrote {previously_processed} URL-populated entries to '{save_path}'.",
          f"({len(entries) - previously_processed} remaining.)")


def retrieve_partially_processed(out_path):

    if not path.exists(out_path):
        return None, 0

    with open(out_path, "r") as outf:
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


def retrieve_entries(in_path, out_path, overwrite=False):

    entries = None
    # Try to resume processing.
    if not overwrite:
        entries, previously_processed = retrieve_partially_processed(out_path)

        if entries is not None:
            return entries, previously_processed

    # Processing not resumed, or user asked to overwrite; read from unprocessed Williams entries
    with open(in_path, "r") as inf:
        in_json = json.loads(inf.read())
        entries = in_json["entries"]

    return entries, 0


def scrape_entry_urls(entries, driver, previously_processed, save_every, save_path):

    print(f"Beginning at entry {previously_processed + 1}.")

    processed = previously_processed

    for entry in entries[previously_processed:]:
        print(f"Processing dedicatee: '{entry['dedicatee']}'")

        for stc in entry["stc_nos"].keys():
            hits = get_hits_for_stc(stc, driver)
            # Insert a JSON array of urls to the beginning of the entry attributes list.
            entry["stc_nos"][stc].insert(0, hits)

            print(
                f"\tLooked up STC code: '{stc}', writing {len(hits)} URL(s) to entry.")

        # Write for every `entries_per_write` processed.
        # Make sure to also write on the final entry.
        processed += 1

        if processed % save_every == 0 or processed == len(entries):
            write_entries_to_file(entries, processed, save_path)


if __name__ == "__main__":

    WILLIAMS_INPUT_PATH_DEFAULT = "resource/williams.json"
    WILLIAMS_OUTPUT_PATH_DEFAULT = "resource/williams_with_urls.json"

    parser = argparse.ArgumentParser()
    parser.add_argument("-W", "--overwrite", action="store_true")
    parser.add_argument("-T", "--login-timer", type=int, default=90)
    parser.add_argument("-S", "--save-every", type=int, default=20)
    parser.add_argument("-I", "--inf", default=WILLIAMS_INPUT_PATH_DEFAULT)
    parser.add_argument("-O", "--outf", default=WILLIAMS_OUTPUT_PATH_DEFAULT)
    args = parser.parse_args()

    driver = webdriver.Firefox()

    try:
        request_user_login(driver, login_timer=args.login_timer)
        # Well-behaved test entry:
        # '{"dedicatee":"ABELL, William, Alderman (DNB).","stc_nos":{"347":[],"11347":["*"],"22532":["*"]}}'
        entries, previously_processed = retrieve_entries(args.inf, args.outf,
                                                         overwrite=args.overwrite)
        scrape_entry_urls(entries, driver, previously_processed,
                          args.save_every, args.outf)

    finally:
        driver.close()
