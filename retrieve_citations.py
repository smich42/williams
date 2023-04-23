import argparse
import csv
from os import path
import eebo_helper
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from json import dumps


class Citation:
    # Represents an EEBO entry and its details.

    def __init__(self, dedicatee, stc, citation_table):

        if citation_table is None:
            citation_table = {}
        # Defines conversion from the citation table to an EntryDetails object.
        self.dedicatee = dedicatee
        self.stc = stc
        self.title = citation_table.get("title")
        self.title_other = citation_table.get("alternate title")
        self.ustc_class = citation_table.get("ustc subject classification")
        self.author = citation_table.get("author")
        self.authors_other = citation_table.get("other authors")
        self.date_pub = citation_table.get("publication date")
        self.printpub = citation_table.get("printer/publisher")
        self.language = citation_table.get("language of publication")

    def fieldnames():

        return [
            "Dedicatee",
            "STC number",
            "Title",
            "Title (other)",
            "USTC classification",
            "Author",
            "Author(s) (other)",
            "Date of publication",
            "Printer/publisher",
            "Language of publication"
        ]

    def as_dict(self):

        return {
            field: val for field, val in zip(Citation.fieldnames(), [
                self.dedicatee,
                self.stc,
                self.title,
                self.title_other,
                self.ustc_class,
                self.author,
                self.authors_other,
                self.date_pub,
                self.printpub,
                self.language
            ])}

    def __str__(self):

        return dumps(self.as_dict(), indent=4)


def show_document_formats_if_present(driver, loading_seconds=5):

    eebo_helper.click_by_id_if_present("showDocumentFormats",
                                       driver, loading_seconds=loading_seconds)


def click_citation_details_link_if_present(driver, loading_seconds=5):

    eebo_helper.click_by_id_if_present("link_prefix_addFlashPageParameterformat_citation",
                                       driver, loading_seconds=loading_seconds)


def extract_citation_table_from_html(page):

    soup = BeautifulSoup(page, features="html.parser")
    rows = soup.select('div[class*="display_record_indexing_row"]')

    table = {}

    for row in rows:
        # The row consists of two `div`s.
        # It's formatted, e.g., as [Author | William Shakespeare].
        tag_cell, data_cell = tuple(row.find_all("div"))

        tag = tag_cell.text.strip().lower()
        data = data_cell.text.strip()

        table[tag] = data

    return table


def page_contains_stc(driver, stc):

    return f"STC (2nd ed.) / {stc}." in driver.page_source


def scrape_citation_table(driver, url, stc, loading_seconds=5):

    driver.get(url)
    sleep(loading_seconds)
    eebo_helper.reject_cookies_if_present(driver)

    if page_contains_stc(driver, stc):
        # Navigate to citation details page.
        show_document_formats_if_present(driver)
        click_citation_details_link_if_present(driver)
        # Try to parse the table from the citation page.
        return extract_citation_table_from_html(driver.page_source)

    return None


def save_citation(citation, save_path):

    with open(save_path, "a") as outf:
        writer = csv.DictWriter(outf, fieldnames=Citation.fieldnames())
        writer.writerow(citation.as_dict())

        print(
            f"Appended citation for STC number '{citation.stc}' to '{save_path}'.")


def create_save_file(save_path):

    with open(save_path, "w") as outf:
        writer = csv.DictWriter(outf, fieldnames=Citation.fieldnames())
        writer.writeheader()

        print(f"Wrote header to '{save_path}'.")


def csv_linecount(filepath):

    if not path.exists(filepath):
        return 0

    with open(filepath, "r") as f:
        # Subtract 1 for the header.
        return sum(1 for _ in f) - 1


def find_and_write_citations(entries, driver, save_path, overwrite=False):

    previously_processed = 0 if overwrite else csv_linecount(save_path)

    if previously_processed <= 0:
        create_save_file(save_path)

    print(f"Beginning at entry {previously_processed}.")

    # Recall that each entry is a dictionary where each key as an stc number
    # And each value a list of dedication details.
    for entry in entries[previously_processed:]:
        dedicatee = entry["dedicatee"]

        for stc, details in entry["stc_nos"].items():
            print(f"Processing [{dedicatee} : {stc}].")
            # The first element in the dedication details is a list of all its potentially matching urls.
            for url in details[0]:

                table = scrape_citation_table(driver, url, stc)

                if table is None or len(table.keys()) == 0:
                    print(f"Skipped '{url}'.")
                    continue

                save_citation(Citation(dedicatee, stc, table), save_path)


if __name__ == "__main__":

    WILLIAMS_URL_PATH = "resource/williams_with_urls.json"
    WILLIAMS_DETAILS_PATH = "resource/citations.csv"

    parser = argparse.ArgumentParser()
    parser.add_argument("-W", "--overwrite", action="store_true")
    parser.add_argument("-T", "--login-timer", type=int, default=90)
    parser.add_argument("-I", "--inf", default=WILLIAMS_URL_PATH)
    parser.add_argument("-O", "--outf", default=WILLIAMS_DETAILS_PATH)
    args = parser.parse_args()

    driver = webdriver.Firefox()

    try:
        eebo_helper.redirect_to_login(driver, login_timer=args.login_timer)
        entries = eebo_helper.read_entries(args.inf)

        find_and_write_citations(entries, driver, args.outf,
                                 overwrite=args.overwrite)

    finally:
        driver.close()
