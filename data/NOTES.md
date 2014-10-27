# jse

All good!


# npo (INCOMPLETE)

**npo_organisations.csv** is fine.

**npo_officers.csv** needs to be split into directors, officers and members (complete **split_npo_memberships.sh**). This is tricky since spelling variations/misspellings abound. Best effort is probably good enough.


# pa

**split_pa_memberships.sh** splits **pa_memberships.csv** into:
* **pa_partymemberships.csv**
* **pa_committeememberships.csv**

These load Membership relations to PoliticalParty and Committee entities, respectively.

All good!


# windeeds

**split_windeeds_memberships.sh** splits **windeeds_directors_gn.csv** and **windeeds_companies_gn.csv** into directors, officers and members.

All good!


# gdocs (INCOMPLETE)

**litigation.csv** is fine.

**persons.csv** is being loaded but body, post and portfolio fields are skipped.

**split_connections.sh** splits **connections.csv** into **family.csv**, **personal.csv**, **donors.csv**, **partnerships.csv**, **financialrelations.csv** and **memberships.csv**. These load Family, Personal, Donor, Partnership, FinancialRelation and Membership relations respectively.

The following type and subtype values are being ignored:
* Affiliations > Exile, Affiliations > Political Party, Affiliations > Professional, Affiliations > Sports
    * We aren't sure how to load these yet.
* Affiliations > Organisation, Affiliations > Other
    * We'll classify these case by case.
* Affiliations > School
    * We get this data from Who's Who.
* Event
    * We aren't sure how to load this yet.
* Financial > Director
    * We get this data from Windeeds.
* Financial > Employee
    * We get this data from Who's Who.
* Geography
    * We have to assign these to Person properties at some stage.


# whoswho (INCOMPLETE)

**whoswho_persons.csv** is fine.

**whoswho_qualifications.csv** is fine.

**whoswho_memberships.csv** needs to be organized somehow. It contains a mix of relation types, e.g. political posts, committee memberships, company offices, etc. For now we are not loading it.
