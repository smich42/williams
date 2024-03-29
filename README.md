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
      "dedicatee": "G. H. Dedicatee",
      "stc_nos": {
        "12345": ["verse", "*"],
        "67890": []
      }
    }
  ]
}
```

## Using the EEBO entry scraper

`add_urls.py` reads JSON in this format, looking up each STC number on EEBO. Each STC number's attribute list is enriched with the URLs of EEBO pages possibly matching it.

We resume scraping at the last processed entry by default. Use flag `--overwrite` (or `-W`) to change this behaviour, e.g.: `python3 add_urls.py --overwrite`

To avoid authorisation issues with EEBO, the script initially asks that you use the scraping window to log in with a user account. 90 seconds are allocated for this by default, and scraping begins automatically after this time elapses. Use flag `--login-timer <seconds>` (or `-T`) to change this behaviour.

The input and output files can be specified with `--inf <path>` (or `-I`) and `--outf <path>` (or `-O`). The scraper looks for `resource/williams.json` and `resource/williams_with_urls.json` by default. Specify the backup path with `--backf <path>` (or `-B`). By default this is `resource/williams_with_urls-old.json`

The frequency at which changes are saved to disc may be modified with `--save-every <num>` (or `-S`). This indicates how many entries must be scraped to initiate a write to the output file.

To illustrate, the script could be run as follows.

```Bash
python3 add_urls.py --overwrite --login-timer 30 --outf custom/output/file.json --save-every 10
```

Below is an example of the JSON output. This follows a similar format to the above; note the field `processed` in the root element, which indicates how many of the entries below have been processed by the scraper.

```JSON
{
  "processed": 1,
  "entries": [
    {
      "dedicatee": "G. H. Dedicatee",
      "stc_nos": {
        "12345": [
          [
            "https://www.proquest.com/eebo/docview/111/222/333/",
            "https://www.proquest.com/eebo/docview/444/555/666",
            "https://www.proquest.com/eebo/docview/777/888/999/"
          ],
          "verse",
          "*"
        ],
        "67890": [
          ["https://www.proquest.com/eebo/docview/123/456/789"],
        ],
      }
    }
  ]
}
```

## Using the EEBO citation scraper

`retrieve_citations.py` looks at a given URL-enriched JSON file as above, follows each link and retrieves the citation details associated with it.
The results are written to disc as CSV values.

If the specified output file already exists, the script resumes processing after the last processed entry in it. This behaviour can be changed by setting the `--overwrite` (or `-W`) flag.

The script also asks the user to log in. Again, this is not mandatory. Change the time window given to log in with flag `--login-timer <seconds>` (or `-T`).

Lastly, the input and output files can be specified with `--inf <path>` (or `-I`) and `--outf <path>` (or `-O`). The scraper looks for `resource/williams_with_urls.json` and `resource/citations.csv` by default.

The resulting CSV looks as follows.

| Dedicatee  | STC number  | Title  | Title (other)  | USTC classification  | Author  | Author(s) (other)  | Date of publication  | Printer/publisher  | Language of publication  |
|---|---|---|---|---|---|---|---|---|---|
|   |   |   |   | . . .  |   |   |   |   |   |
| ELIZABETH I, Queen. | 17320 | A godly medytacyon of the christen sowle, concerninge a loue towardes God and hys Christe, compyled in frenche [...]  | Miroir de lâme pécherresse.  |  Women in publishing; Religious | Marguerite, Queen, consort of Henry II, King of Navarre, 1492-1549.  | Bale, John, 1495-1563.; Elizabeth I, Queen of England, 1533-1603.  | 1548  | Imprented [by Dirik van der Straten]  | English  |
| ELIZABETH I, Queen.  | 4939  | In laudem Henrici Octaui, Regis Angliæ præstantis. carmen panegiricum  |   | Poetry  | Chaloner, Thomas, Sir, 1521-1565.  |   | 1560  | [J. Day]  |  Latin |
|   |   |   |   | . . .  |   |   |   |   |   |
