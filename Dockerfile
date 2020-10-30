FROM python:3.7.6-slim

ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app
RUN apt update && apt-get -y install gcc postgresql-client libpq-dev curl git && apt-get clean

COPY requirements.txt ./

RUN pip install -r requirements.txt
RUN python -m nltk.downloader punkt stopwords

COPY . .
COPY src/pcapi .
RUN pip install -e .

EXPOSE 5000

COPY --from=us-docker.pkg.dev/berglas/berglas/berglas:latest /bin/berglas /bin/berglas
CMD exec /bin/berglas exec -- gunicorn \
                    -w $UNICORN_N_WORKERS \
                    --timeout $UNICORN_TIMEOUT \
                    --access-logformat '{"request_id":"%({X-Request-Id}i)s",\
                                        "response_code":"%(s)s","request_method":"%(m)s",\
                                        "request_path":"%(U)s","request_querystring":"%(q)s",\
                                        "request_duration":"%(D)s","response_length":"%(B)s", \
                                        "from":"gunicorn"}' \
                    pcapi.app:app
