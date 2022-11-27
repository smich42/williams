from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import json
import sys
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

    request_user_login(driver, login_timer=args.login_timer)

    # Well-behaved test entry:
    # '{"dedicatee":"ABELL, William, Alderman (DNB).","stc_nos":{"347":[],"11347":["*"],"22532":["*"]}}'
    entries = {}
    previously_processed = 0

    # Ensure `outf` exists; if so do not modify.
    open(args.outf, "a").close()

    with open(args.inf, "r") as inf, open(args.outf, "r") as outf:
        # This flag indicates whether we resume scraping from a certain point in the entry list
        # or start from the beginning.
        resume = False

        if not args.overwrite:
            # Attempt to resume execution.
            out_json = outf.read()
            # Field "processed" in the JSON is used to save the number of scraped entries.
            # If this is greater than zero, then enable the `resume` flag.
            try:
                previously_processed = int(json.loads(out_json)["processed"])
                if (previously_processed > 0):
                    resume = True
            except json.decoder.JSONDecodeError:
                # No 'processed' field detected, so nowhere to resume from.
                pass

        if resume:
            entries = json.loads(out_json)["entries"]
        else:
            in_json = inf.read()
            entries = json.loads(in_json)["entries"]

    scrape_entry_urls(entries, driver, previously_processed,
                      args.save_every, args.outf)

    driver.close()
