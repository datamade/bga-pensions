# Extend the base Python image
# See https://hub.docker.com/_/python for version options
# N.b., there are many options for Python images. We used the plain
# version number in the pilot. YMMV. See this post for a discussion of
# some options and their pros and cons:
# https://pythonspeed.com/articles/base-image-python-docker-images/
FROM nikolaik/python-nodejs:python3.7-nodejs12

# Give ourselves some credit
LABEL maintainer "DataMade <info@datamade.us>"

RUN mkdir /app
WORKDIR /app

# Copy the requirements file into the app directory, and install them. Copy
# only the requirements file, so Docker can cache this build step. Otherwise,
# the requirements must be reinstalled every time you build the image after
# the app code changes. See this post for further discussion of strategies
# for building lean and efficient containers:
# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./package.json /app/package.json
RUN npm install

# Copy the contents of the current host directory (i.e., our app code) into
# the container.
COPY . /app

# Bogus env var to make sure that we can run 'collectstatic' later on
ENV DJANGO_SECRET_KEY 'foobar'
# Bake static files into the container
RUN python manage.py collectstatic --noinput && python manage.py compress
