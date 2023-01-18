from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from os import path
import json
import argparse
import eebo_helper
import warnings


def scrape_result_urls(stc, driver, loading_seconds=5):

    driver.get("https://www.proquest.com/eebo/commandline")

    sleep(loading_seconds)

    eebo_helper.reject_cookies_if_present(driver)

    searchbox = driver.find_element(By.ID, "searchTerm")
    submit = driver.find_element(By.ID, "submit_5")

    searchbox.clear()
    searchbox.send_keys(f"COLL(STC) AND BIBNO({stc})")

    submit.click()

    # Ensure results load
    sleep(loading_seconds)

    return [hit.get_attribute("href") for hit in driver.find_elements(By.XPATH, "//*[starts-with(@id, 'citationDocTitleLink')]")]


def write_entries(entries, previously_processed, save_path, backup_path):

    # If we have an output file already, create a backup before overwriting.
    if path.exists(save_path):
        with open(save_path, "r") as sf, open(backup_path, "w") as bf:
            bf.write(sf.read())

    # Overwrite the old output file.
    with open(save_path, "w") as f:
        f.write(json.dumps({
            "processed": previously_processed,
            "entries": entries
        }))

    print(f"Wrote {previously_processed} URL-populated entries to '{save_path}'.",
          f"({len(entries) - previously_processed} remaining.)")


def get_entries(path_for_plain, path_for_urls, overwrite=False):

    entries = None
    # Try to resume processing.
    if not overwrite:
        entries, previously_processed = eebo_helper.read_url_entries_file(
            path_for_urls)

        if entries is not None:
            return entries, previously_processed

    # Processing not resumed, or user asked to overwrite; read from unprocessed Williams entries
    return eebo_helper.read_plain_entries_file(path_for_plain), 0


def add_urls(entries, driver, previously_processed, save_every, save_path, backup_path):

    print(f"Beginning at entry {previously_processed + 1}.")

    processed = previously_processed

    for entry in entries[previously_processed:]:
        print(f"Processing dedicatee: '{entry['dedicatee']}'")

        for stc in entry["stc_nos"].keys():
            hits = scrape_result_urls(stc, driver)
            # Insert a JSON array of urls to the beginning of the entry attributes list.
            entry["stc_nos"][stc].insert(0, hits)

            print(
                f"\tLooked up STC code: '{stc}', writing {len(hits)} URL(s) to entry.")

        # Write for every `entries_per_write` processed.
        # Make sure to also write on the final entry.
        processed += 1

        if processed % save_every == 0 or processed == len(entries):
            write_entries(entries, processed, save_path, backup_path)


if __name__ == "__main__":

    WILLIAMS_PLAIN_PATH = "resource/williams.json"
    WILLIAMS_URL_PATH = "resource/williams_with_urls.json"
    WILLIAMS_BACKUP_PATH = "resource/williams_with_urls-old.json"

    parser = argparse.ArgumentParser()
    parser.add_argument("-W", "--overwrite", action="store_true")
    parser.add_argument("-T", "--login-timer", type=int, default=90)
    parser.add_argument("-S", "--save-every", type=int, default=20)
    parser.add_argument("-I", "--inf", default=WILLIAMS_PLAIN_PATH)
    parser.add_argument("-O", "--outf", default=WILLIAMS_URL_PATH)
    parser.add_argument("-B", "--backf", default=WILLIAMS_BACKUP_PATH)
    args = parser.parse_args()

    driver = webdriver.Firefox()

    args.outf = path.normpath(args.outf)
    args.backf = path.normpath(args.backf)

    if args.outf == args.backf:
        warnings.warn(
            f"Backup path configured to be the same as save path: '{args.outf}'")

    try:
        eebo_helper.redirect_to_login(driver, login_timer=args.login_timer)
        # Well-behaved test entry:
        # '{"dedicatee":"ABELL, William, Alderman (DNB).","stc_nos":{"347":[],"11347":["*"],"22532":["*"]}}'
        entries, previously_processed = get_entries(args.inf, args.outf,
                                                    overwrite=args.overwrite)
        add_urls(entries, driver, previously_processed,
                 args.save_every, args.outf, args.backf)

    finally:
        driver.close()
