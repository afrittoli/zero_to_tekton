FROM tiangolo/uwsgi-nginx-flask:python3.8

ENV STATIC_PATH /app/cats/static

COPY ./app /app
