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

    CSV_COLNAME_DEDICATEE = "Dedicatee"
    CSV_COLNAME_STC = "STC number"
    CSV_COLNAME_TITLE = "Title"
    CSV_COLNAME_TITLE_OTHER = "Title (other)"
    CSV_COLNAME_USTC_CLASS = "USTC classification"
    CSV_COLNAME_AUTHOR = "Author"
    CSV_COLNAME_AUTHOR_OTHER = "Author(s) (other)"
    CSV_COLNAME_DATE_OF_PUB = "Date of publication"
    CSV_COLNAME_PRINTER_PUBLISHER = "Printer/publisher"
    CSV_COLNAME_PUB_LANGUAGE = "Language of publication"

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
            Citation.CSV_COLNAME_DEDICATEE,
            Citation.CSV_COLNAME_STC,
            Citation.CSV_COLNAME_TITLE,
            Citation.CSV_COLNAME_TITLE_OTHER,
            Citation.CSV_COLNAME_USTC_CLASS,
            Citation.CSV_COLNAME_AUTHOR,
            Citation.CSV_COLNAME_AUTHOR_OTHER,
            Citation.CSV_COLNAME_DATE_OF_PUB,
            Citation.CSV_COLNAME_PRINTER_PUBLISHER,
            Citation.CSV_COLNAME_PUB_LANGUAGE
        ]

    def to_dict(citation):

        return {
            field: val for field, val in zip(Citation.fieldnames(), [
                citation.dedicatee,
                citation.stc,
                citation.title,
                citation.title_other,
                citation.ustc_class,
                citation.author,
                citation.authors_other,
                citation.date_pub,
                citation.printpub,
                citation.language
            ])}

    def from_dict(dict):
        citation = Citation(
            dict[Citation.CSV_COLNAME_DEDICATEE], dict[Citation.CSV_COLNAME_STC], None)

        citation.title = dict[Citation.CSV_COLNAME_TITLE]
        citation.title_other = dict[Citation.CSV_COLNAME_TITLE_OTHER]
        citation.ustc_class = dict[Citation.CSV_COLNAME_USTC_CLASS]
        citation.author = dict[Citation.CSV_COLNAME_AUTHOR]
        citation.authors_other = dict[Citation.CSV_COLNAME_AUTHOR_OTHER]
        citation.date_pub = dict[Citation.CSV_COLNAME_DATE_OF_PUB]
        citation.printpub = dict[Citation.CSV_COLNAME_PRINTER_PUBLISHER]
        citation.language = dict[Citation.CSV_COLNAME_PUB_LANGUAGE]

        return citation

    def __str__(self):

        return dumps(Citation.to_dict(self), indent=4)


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
        writer.writerow(Citation.to_dict(citation))

        print(
            f"Appended citation for STC number '{citation.stc}' to '{save_path}'.")


def create_save_file(save_path):

    with open(save_path, "w") as outf:
        writer = csv.DictWriter(outf, fieldnames=Citation.fieldnames())
        writer.writeheader()

        print(f"Wrote header to '{save_path}'.")


def last_citation_saved(save_path):

    if not path.exists(save_path):
        return None

    with open(save_path, "r") as f:
        reader = csv.DictReader(f, fieldnames=Citation.fieldnames())
        rows = list(reader)

        if len(rows) > 1:
            return Citation.from_dict(rows[-1])


def find_and_write_citations(entries, driver, save_path, overwrite=False):

    if overwrite or not path.exists(save_path):
        create_save_file(save_path)

    last_processed = last_citation_saved(save_path)
    encountered_last_processed = False

    if last_processed != None:
        print(
            f"Beginning after entry '{last_processed.dedicatee}': '{last_processed.stc}'.")
    else:
        print("Beginning from first entry.")
        encountered_last_processed = True

    # Recall that each entry is a dictionary where each key as an stc number
    # And each value a list of dedication details.
    for entry in entries:
        dedicatee = entry["dedicatee"]

        for stc, details in entry["stc_nos"].items():

            if not encountered_last_processed:
                if last_processed.dedicatee == dedicatee and last_processed.stc == stc:
                    encountered_last_processed = True

                continue

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
