FROM granoproject/base:latest

# Node dependencies
RUN npm --quiet --silent install -g bower uglify-js less

COPY . /siyazana
WORKDIR /siyazana
RUN python setup.py -qq install

CMD gunicorn -w 3 connectedafrica.manage:app
