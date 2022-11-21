from curses.ascii import isalpha, isupper
from dataclasses import replace
import sys
import re
import json


def begins_entry(line):
    """
    Checks that the given line is the start of a new entry.
    New entries start with an uppercase last name:
    - ABBOT
    - M.
    - H.E.
    """

    if line == "" or line.isspace():
        return False

    # Do not allow "lastname" or "lASTNAME"
    if not line[0].isupper():
        return False

    # Do not allow "Lastname"
    if line[0].isupper() and line[1].islower():
        return False

    first_token = line.split(".")[0] + "."
    # Require more than two uppercase characters,
    # or one uppercase character followed by full stop.
    return re.match(r"([A-Z]\.|[A-Z]{2,})", first_token)


def extract_dedicatee(line):
    """
    Returns the part of the line relating to the dedicatee's name
    and origin or occupation.
    """

    parts = line.split(".")
    dedicatee = parts[0] + "."

    for part in parts[1:]:
        # Add more tokens to the dedicatee name
        # as long as they are single uppercase characters.
        # For example, we want to keep the final tokens in "PENNYPACKER, H., E."
        if not re.fullmatch(r"[^A-Za-z]*[A-Z]", part):
            break

        dedicatee += part + "."

    return clean_dedicatee(dedicatee)


def clean_dedicatee(dedicatee):
    dedicatee = remove_unrecognised_unicode(dedicatee)

    dedicatee = dedicatee.strip()

    dedicatee = re.sub(r"\s*,\s*", ", ", dedicatee)
    dedicatee = re.sub(r"\s*\(\s*", " (", dedicatee)
    dedicatee = re.sub(r"(\s*\))(?=[^.,])", ") ", dedicatee)
    dedicatee = re.sub(r"\s+", " ", dedicatee)

    for match in re.findall(r"[A-Z]{2,}[a-z]", dedicatee):
        dedicatee = dedicatee.replace(match, match[:-1] + " " + match[-1])

    for match in re.findall(r"[a-z][A-Z]", dedicatee):
        dedicatee = dedicatee.replace(match, match[0] + " " + match[1])

    return dedicatee


def remove_unrecognised_unicode(text):
    for unrec in ["\u00ad", "\u2022", "\u00b7", "\ufffd", "\u00a3", "\u00b0"]:
        text = text.replace(unrec + " ", "")
        text = text.replace(unrec, "")
    return text


def extract_stcs(line):
    """
    Produces a dictionary of all STC numbers and their tags contained in the line.
    """

    # Tags are: prose, verse, epistle, edits, by editor,
    # or any of ",r", "t", "*" followed by a number or another of those symbols.
    # OCR is not ideal so the paragraph symbol is ",r", the cross is "t" and the star "*".
    possible_tags = [r"prose", r"verse", r"epistle", r"edits", r"by editor",
                     r"(,r)(?=[1-9|t|\*]+)", r"(t)(?=[1-9|,r|\*]+)", r"(\*)(?=[1-9|t|,r]+)"]

    possible_digit_misreadings = {
        "u": ["11"],
        "n": ["11"],
        "q": ["14"],
        "o": ["0"],
        "O": ["0"],
        "I": ['1']
    }

    stc_to_tags = {}
    parts = line.replace(".", ",").replace(
        ":", ",").replace(";", ",").split(",")

    for part in parts:
        for alt in generate_digit_misreadings(part, possible_digit_misreadings):
            # Check number contained in line.
            match = re.search(r"\d+", alt)

            if match:
                stc = match.group(0)
                tags = match_any(alt, possible_tags)

                stc_to_tags[stc] = tags

    return stc_to_tags


def generate_digit_misreadings(text, substitutions):

    misreading_pos = find_next_near_digits(text, substitutions.keys())

    if misreading_pos == -1:
        return [text]

    misreading = text[misreading_pos]

    remaining_text = text[misreading_pos + 1:]
    remaining_alts = generate_digit_misreadings(remaining_text, substitutions)

    alts = []

    for sub in [misreading] + substitutions[misreading]:
        for remaining_alt in remaining_alts:
            alts.append(text[:misreading_pos] + sub + remaining_alt)

    return alts


def find_next_near_digits(text, chars_to_match):
    index = 0

    for i in range(len(text)):
        adjacent_to_digit = False

        if i > 0:
            adjacent_to_digit |= text[i-1].isdigit()
        if i < len(text) - 1:
            adjacent_to_digit |= text[i+1].isdigit()

        if adjacent_to_digit and text[i] in chars_to_match:
            return index

        index += 1

    return -1


def match_any(text, patterns):
    """
    Returns all matches of the patterns in the text. Case insensitive.
    """

    matches = []

    for pattern in patterns:
        # Case insensitive.
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            # Convert to lowercase so that tags are uniformly formatted.
            matches.append(match.group(0).lower())

    return matches


if __name__ == "__main__":

    entries = []
    dedicatee = None
    stcs = {}

    for line in sys.stdin:
        if begins_entry(line):
            if dedicatee != None:
                entries.append(
                    {
                        "dedicatee": dedicatee,
                        "stc_nos": stcs
                    })

            dedicatee = extract_dedicatee(line)
            stcs = extract_stcs(line)
        else:
            stcs |= extract_stcs(line)

    print(json.dumps({"entries": entries}))
