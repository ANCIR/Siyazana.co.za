load: loadschema loadgdocs loadwikipedia loadjse loadpa loadnpo

install:
	bower install

web:
	python connectedafrica/manage.py runserver -p 5001

loadschema:
	@granoloader --create-project schema data/schema.yaml

loadjse:
	@granoloader csv -t 5 data/jse/jse_entities.csv.yaml data/jse/jse_entities.csv
	@granoloader csv -t 5 data/jse/jse_links.csv.yaml data/jse/jse_links.csv

loadpa:
	@granoloader csv -t 5 data/pa/pa_persons.csv.yaml data/pa/pa_persons.csv
	@granoloader csv -t 5 data/pa/pa_parties.csv.yaml data/pa/pa_parties.csv
	@granoloader csv -t 5 data/pa/pa_committees.csv.yaml data/pa/pa_committees.csv
	@granoloader csv -t 5 data/pa/pa_partymemberships.csv.yaml data/pa/pa_partymemberships.csv
	@granoloader csv -t 5 data/pa/pa_committeememberships.csv.yaml data/pa/pa_committeememberships.csv
	@granoloader csv -t 5 data/pa/pa_directorships.csv.yaml data/pa/pa_directorships.csv
	@granoloader csv -t 5 data/pa/pa_financial.csv.yaml data/pa/pa_financial.csv

loadnpo:
	@granoloader csv -t 5 data/npo_organisations.csv.yaml data/npo_organisations.csv
	@granoloader csv -t 5 data/npo_officers.csv.yaml data/npo_officers.csv

loadwindeeds:
	@granoloader csv -t 5 data/windeeds_companies.csv.yaml data/windeeds_companies_gn.csv
	@granoloader csv -t 5 data/windeeds_directors.csv.yaml data/windeeds_directors_gn.csv

loadwhoswho:
	@granoloader csv -t 5 data/whoswho_persons.csv.yaml data/whoswho_persons.csv
	@granoloader csv -t 5 data/whoswho_memberships.csv.yaml data/whoswho_memberships.csv
	@granoloader csv -t 5 data/whoswho_qualifications.csv.yaml data/whoswho_qualifications.csv

loadwikipedia:
	python connectedafrica/scrapers/wikipedia.py
	@granoloader csv -t 5 data/wikipedia_images.csv.yaml data/wikipedia_images.csv

# Google docs
loadgdocs:
	@wget -q -O data/persons.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1657155089"
	@granoloader csv -t 5 -f data/persons.csv.yaml data/persons.csv
	@wget -q -O data/litigation.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1973809171"
	@granoloader csv -t 5 -f data/litigation.csv.yaml data/litigation.csv
	@wget -q -O data/connections.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1752160727"
	@head -n 1 data/connections.csv > data/personalconnections.csv
	@head -n 1 data/connections.csv > data/familyconnections.csv
	@sed -n "/Personal,Personal >/p" data/connections.csv >> data/personalconnections.csv
	@sed -n "/Family,Family >/p" data/connections.csv >> data/familyconnections.csv
	@granoloader csv -t 5 -f data/personalconnections.csv.yaml data/personalconnections.csv
	@granoloader csv -t 5 -f data/familyconnections.csv.yaml data/familyconnections.csv
	# TODO: also split up financial, affiliation, event connections

cleangdocs:
	rm data/litigation.csv data/persons.csv data/*connections.csv
