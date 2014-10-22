cd data/windeeds/

SCRIPT="
# coding: utf8
import csv
import sys
from StringIO import StringIO


def get_member_type(heading, line):
    sio = StringIO('\n'.join([heading.strip(), line.strip()]))
    reader = csv.DictReader(sio)
    fields = reader.next()
    if 'CIPC Type' in fields:
        return fields['CIPC Type']
    return fields['CIPC-Person Type']


sys.stdout.write(get_member_type('''"

let LINE_NUMBER=`wc -l windeeds_companies_gn.csv | cut -d " " -f 1`
let LINE_NUMBER+=`wc -l windeeds_directors_gn.csv | cut -d " " -f 1`
let LINE_NUMBER-=2
let COUNTER=0

HEADER=`head -n 1 windeeds_companies_gn.csv`
echo $HEADER > windeeds_companies_to_directors.csv
echo $HEADER > windeeds_companies_to_members.csv

tail -n +2 windeeds_companies_gn.csv | while read LINE; do
    MEMBER_TYPE=`echo "${SCRIPT}${HEADER}''','''${LINE}'''))" | python`
    echo $MEMBER_TYPE | grep -q --ignore-case "Director"
    if [ $? -eq 0 ]; then
        echo $LINE >> windeeds_companies_to_directors.csv
        let CHAR_COUNT=`echo -n $MEMBER_TYPE | wc -m`
        if [ $CHAR_COUNT -gt 9 ]; then
            # the individual plays other membership roles, not just director
            echo $LINE >> windeeds_companies_to_members.csv
        fi
    else
        echo $LINE >> windeeds_companies_to_members.csv
    fi
    let COUNTER+=1
    echo -en "\e[1A"; echo -e "\e[0K\r $COUNTER / $LINE_NUMBER"
done


HEADER=`head -n 1 windeeds_directors_gn.csv`
echo $HEADER > windeeds_directors_to_companies.csv
echo $HEADER > windeeds_members_to_companies.csv

tail -n +2 windeeds_directors_gn.csv | while read LINE; do
    MEMBER_TYPE=`echo "${SCRIPT}${HEADER}''','''${LINE}'''))" | python`
    echo $MEMBER_TYPE | grep -q --ignore-case "Director"
    if [ $? -eq 0 ]; then
        echo $LINE >> windeeds_directors_to_companies.csv
        let CHAR_COUNT=`echo -n $MEMBER_TYPE | wc -m`
        if [ $CHAR_COUNT -gt 9 ]; then
            # the individual plays other membership roles, not just director
            echo $LINE >> windeeds_members_to_companies.csv
        fi
    else
        echo $LINE >> windeeds_members_to_companies.csv
    fi
    let COUNTER+=1
    echo -en "\e[1A"; echo -e "\e[0K\r $COUNTER / $LINE_NUMBER"
done

echo 'Done'