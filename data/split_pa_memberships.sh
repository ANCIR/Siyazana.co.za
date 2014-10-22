cd data

COMMITTEE_LIST=`sed 's/^\(\([^,"]\+\)\|\("[^"]\+"\)\),.*/\1/g' pa_committees.csv | tr -d '"'`
rm pa_partymemberships.csv
touch pa_partymemberships.csv
head -n 1 pa_memberships.csv | sed 's/organization_name/committee_name/' > pa_committeememberships.csv
LINE_NUMBER=`wc -l pa_memberships.csv | cut -d " " -f 1`
let COUNTER=0

while read LINE; do
    ORG_NAME=`echo $LINE | sed 's/^\(\([^,"]\+\)\|\("[^"]\+"\)\),.*/\1/' | tr -d '"' | sed 's/^\([^()]\+\)\( \+(.\+)\)\?$/\1/'`
    echo $COMMITTEE_LIST | grep -q "$ORG_NAME"
    if [ $? -eq 0 ]; then
        echo $LINE >> pa_committeememberships.csv
    else
        echo $LINE >> pa_partymemberships.csv
    fi
    let COUNTER+=1
    echo -en "\e[1A"; echo -e "\e[0K\r $COUNTER / $LINE_NUMBER"
done <pa_memberships.csv

echo 'Done'