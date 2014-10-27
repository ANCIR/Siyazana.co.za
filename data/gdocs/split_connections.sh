#!/bin/bash
cd data/gdocs/

HEADER=`head -n 1 connections.csv`
echo $HEADER > personal.csv
echo $HEADER > family.csv
echo $HEADER > financialrelations.csv
echo $HEADER > partnerships.csv
echo $HEADER > donors.csv
echo $HEADER > memberships.csv

tail -n +2 connections.csv | while read LINE; do
    echo $LINE | sed -n "/Personal,Personal >/p" >> personal.csv
    echo $LINE | sed -n "/Family,Family >/p" >> family.csv
    echo $LINE | sed -n "/Financial > \(Family Trust\|Consultants\|Other\)/p" >> financialrelations.csv
    echo $LINE | sed -n "/Financial > Joint Owner/p" >> partnerships.csv
    echo $LINE | sed -n "/Financial > \(Charity\|Party support\)/p" >> donors.csv
    echo $LINE | sed -n "/Affiliations > \(Church\|Club\|Union\)/p" >> memberships.csv
done
