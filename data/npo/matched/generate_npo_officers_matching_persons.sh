#!/bin/bash
workon connectedafrica
cd data/npo/matched

if [ ! -f .persons_to_npo_officers.csv ]; then
    python find_matching_persons.py 0.7 1> .persons_to_npo_officers.csv
fi

SCRIPT="
# coding: utf8
import os
import sys
from unicodecsv import DictReader, DictWriter


def get_matches():
    officer_ids = set()
    with open('.persons_to_npo_officers.csv') as f:
        reader = DictReader(f)
        for data in reader:
            officer_ids.add(data['officer_id (from npo_officers)'])
    return officer_ids


def print_matching_officers(matched_officer_ids):
    with open('../npo_officers.csv') as f:
        reader = DictReader(f)
        writer = DictWriter(sys.stdout, reader.fieldnames)
        writer.writeheader()
        for data in reader:
            if data['officer_id'] in matched_officer_ids:
                writer.writerow(data)


print_matching_officers(get_matches())
"

echo "$SCRIPT" | python > npo_officers.csv
