load: loadschema loadgdocs loadwikipedia loadjse loadpa loadnpo

install:
	bower install

web:
	python connectedafrica/manage.py runserver -p 5001

loadschema:
	@granoloader --create-project schema data/schema.yaml

loadjse:
	@granoloader csv -t 5 data/jse_entities.csv.yaml data/jse_entities.csv
	@granoloader csv -t 5 data/jse_links.csv.yaml data/jse_links.csv

loadpa:
	@granoloader csv -t 5 data/pa_persons.csv.yaml data/pa_persons.csv
	@granoloader csv -t 5 data/pa_parties.csv.yaml data/pa_parties.csv
	@granoloader csv -t 5 data/pa_committees.csv.yaml data/pa_committees.csv
	@granoloader csv -t 5 data/pa_memberships.csv.yaml data/pa_memberships.csv
	@granoloader csv -t 5 data/pa_directorships.csv.yaml data/pa_directorships.csv
	@granoloader csv -t 5 data/pa_financial.csv.yaml data/pa_financial.csv

loadnpo:
	@granoloader csv -t 5 data/npo_organisations.csv.yaml data/npo_organisations.csv
	@granoloader csv -t 5 data/npo_officers.csv.yaml data/npo_officers.csv

loadwhoswho:
	@granoloader csv -t 5 data/whoswho_persons.csv.yaml data/whoswho_persons.csv
	@granoloader csv -t 5 data/whoswho_memberships.csv.yaml data/whoswho_memberships.csv
	@granoloader csv -t 5 data/whoswho_qualifications.csv.yaml data/whoswho_qualifications.csv

loadwikipedia:
	python connectedafrica/scrapers/wikipedia.py
	@granoloader csv -t 5 data/wikipedia_images.csv.yaml data/wikipedia_images.csv

# Google docs
loadgdocs:
	@wget -q -O data/family.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1752160727"
	@granoloader csv -t 5 -f data/family.csv.yaml data/family.csv
	@wget -q -O data/directorships.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=465508635"
	@granoloader csv -t 5 -f data/directorships.csv.yaml data/directorships.csv
	@wget -q -O data/litigation.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1973809171"
	@granoloader csv -t 5 -f data/litigation.csv.yaml data/litigation.csv
	@wget -q -O data/persons.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1657155089"
	@granoloader csv -t 5 -f data/persons.csv.yaml data/persons.csv

cleangdocs:
	rm data/litigation.csv data/directorships.csv data/family.csv data/persons.csv
