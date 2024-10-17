FROM python:3.12.6-bullseye

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# dependencies
RUN pip install --upgrade pip
RUN pip install setuptools
RUN pip install torch --index-url https://download.pytorch.org/whl/cu124
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy app
COPY . .
