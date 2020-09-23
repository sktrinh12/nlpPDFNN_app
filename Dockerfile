FROM python:3.7-slim-buster

ADD . /app
WORKDIR /app
ADD ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
EXPOSE 8050
RUN mkdir -p static/uploads

ENV FLASK_APP /app/app.py
RUN python -m nltk.downloader stopwords && \
    python -m nltk.downloader punkt && \
    python -m nltk.downloader averaged_perceptron_tagger

ENV FLASK_ENV=production
