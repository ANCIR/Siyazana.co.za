all: data/directorships.csv data/litigation.csv

data/directorships.csv:
	wget -O data/directorships.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=465508635"
	sed -i '/,,,,,,,,/d' data/directorships.csv  # remove blank lines

data/litigation.csv:
	wget -O data/litigation.csv "https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1973809171"

clean:
	rm data/*.csv

install:
	bower install

web:
	python connectedafrica/manage.py runserver -p 5001
