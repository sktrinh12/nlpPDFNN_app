FROM python:3.7-slim-buster

ADD . /app
WORKDIR /app
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
EXPOSE 8050
RUN mkdir -p static/uploads

ENV FLASK_APP /app/app.py
RUN python -m nltk.downloader stopwords && \
    python -m nltk.downloader punkt && \
    python -m nltk.downloader averaged_perceptron_tagger

ENV FLASK_ENV=production
