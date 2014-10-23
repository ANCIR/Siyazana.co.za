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


# Windeeds

**split_windeeds_memberships.sh** splits **windeeds_directors_gn.csv** and **windeeds_companies_gn.csv** into directors, officers and members.

All good!


# gdocs (INCOMPLETE)


# whoswho (INCOMPLETE)

**whoswho_persons.csv** is fine.

**whoswho_qualifications.csv** is fine.

**whoswho_memberships.csv** needs to be organized somehow. It contains a mix of relation types, e.g. political posts, committee memberships, company offices, etc. For now we are not loading it.
