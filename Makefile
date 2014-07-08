install:
	bower install

web:
	python connectedafrica/manage.py runserver -p 5001

loadschema:
	granoloader schema data/schema.yaml

loadjse:
	granoloader csv -t 5 data/jse_entities.csv.yaml data/jse_entities.csv
	granoloader csv -t 5 data/jse_links.csv.yaml data/jse_links.csv

loadpa:
	granoloader csv -t 5 data/pa_persons.csv.yaml data/pa_persons.csv
	granoloader csv -t 5 data/pa_parties.csv.yaml data/pa_parties.csv
	granoloader csv -t 5 data/pa_committees.csv.yaml data/pa_committees.csv
	granoloader csv -t 5 data/pa_memberships.csv.yaml data/pa_memberships.csv
	granoloader csv -t 5 data/pa_directorships.csv.yaml data/pa_directorships.csv
	granoloader csv -t 5 data/pa_financial.csv.yaml data/pa_financial.csv

loadnpo:
	granoloader csv -t 5 data/npo_organisations.csv.yaml data/npo_organisations.csv
	granoloader csv -t 5 data/npo_officers.csv.yaml data/npo_officers.csv

# Google docs
loadgdocs: gdocs
	granoloader csv -t 5 data/directorships.csv.yaml data/directorships.csv
	granoloader csv -t 5 data/litigation.csv.yaml data/litigation.csv

gdocs: data/directorships.csv data/litigation.csv

data/directorships.csv:
	wget -O data/directorships.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=465508635"
	sed -i '/,,,,,,,,/d' data/directorships.csv  # remove blank lines

data/litigation.csv:
	wget -O data/litigation.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1973809171"

cleangdocs:
	rm data/litigation.csv data/directorships.csv
