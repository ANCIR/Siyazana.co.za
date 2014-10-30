#!/bin/bash
workon connectedafrica
cd data/npo/

if [ ! -f persons_to_npo_officers.csv ]; then
    python find_matching_persons.py 0.7 1> persons_to_npo_officers.csv
fi

SCRIPT="
# coding: utf8
import os
import sys
from unicodecsv import DictReader, DictWriter


def get_officer_data():
    officer_data = {}
    with open('npo_officers.csv') as f:
        reader = DictReader(f)
        for data in reader:
            officer_data[data['officer_id']] = data
    return officer_data


def print_matching_officers(officer_data):
    writer = DictWriter(sys.stdout, officer_data.values()[0].keys())
    with open('persons_to_npo_officers.csv') as f:
        reader = DictReader(f)
        for data in reader:
            officer_id = data['officer_id (from npo_officers)']
            writer.writerow(officer_data[officer_id])


print_matching_officers(get_officer_data())
"

echo "$SCRIPT" | python > npo_officers_matching_persons.csv
