# Digitising Franklin B. Williams' *Index of Dedications and Commendatory Verses*

## Setup

This project depends on Python 3 and Selenium 4.5 for scraping work. Ensure **Firefox** and the following libraries are **all** installed. (This is a macOS & Homebrew example.)

```Bash
brew install geckodriver
pip install selenium
pip install webdriver-manager
```

## Using the Williams parser

`extract_entries.py` parses the entries from Williams text provided to `stdin` and writes them to `stdout` in JSON format.

Below is an example of the JSON output.

```JSON
{
  "entries": [
    {
      "dedicatee": "",
      "stc_nos": {
        "12345": ["verse", "*"],
        "67890": [],
      }
    }
  ]
}
```

## Using the EEBO scraper

`add_urls.py` reads JSON in this format, looking up each STC number on EEBO. Each STC number's attribute list is enriched with the URLs of EEBO pages possibly matching it.

We resume scraping at the last processed entry by default. Use flag `'--overwrite'` to change this behaviour, e.g.: `python3 add_urls.py --overwrite`

To avoid authorisation issues with EEBO, the script initially asks that you use the scraping window to log in with a user account. 90 seconds are allocated for this by default, and scraping begins automatically after this time elapses. Use flag `--login-timer <seconds>` to change this behaviour.

The input and output files can be specified with `--inf` and `--outf`: looks for `resource/williams.json` and `resource/williams_with_urls.json` by default.

Below is an example of the JSON output. This follows a similar format to the above; note the field `processed` in the root element, which indicates how many of the entries below have been processed by the scraper.

```JSON
{
  "processed": 1,
  "entries": [
    {
      "dedicatee": "",
      "stc_nos": {
        "12345": [
          "https://www.proquest.com/eebo/docview/111/222/333/",
          "https://www.proquest.com/eebo/docview/444/555/666",
          "https://www.proquest.com/eebo/docview/777/888/999/",
          "verse",
          "*"],
        "67890": [
          "https://www.proquest.com/eebo/docview/123/456/789",
        ],
      }
    }
  ]
}
```
