FROM --platform=linux/amd64 python:3.8-slim-buster as build

LABEL maintainer="Atharva Deshpande"
LABEL version="1.0"
LABEL description="This is a Tracker Application..."

RUN apt-get update \
        && apt-get install -y --no-install-recommends \
                python3-dev \
                default-libmysqlclient-dev \
                build-essential \
                pkg-config \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the app using python app.py (for development or testing)
CMD ["python3", "app.py"]
