FROM python:3.7.6-slim AS api-flask

ENV PYTHONUNBUFFERED 1
WORKDIR /usr/local/bin
RUN apt update && apt -y install gcc libpq-dev && apt clean
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt
RUN python -m nltk.downloader punkt stopwords
EXPOSE 5000

FROM api-flask
WORKDIR /usr/src/app
RUN apt update && \
    apt -y install postgresql-client curl git && \
    apt clean
COPY . .
COPY src/pcapi .
RUN pip --no-cache-dir install -e .
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
