FROM python:3.9.4-slim

ENV PYTHONUNBUFFERED 1
WORKDIR /usr/local/bin
RUN apt update && apt-get -y install gcc
RUN apt-get install -y libpq-dev
COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt
RUN python -m nltk.downloader punkt stopwords
