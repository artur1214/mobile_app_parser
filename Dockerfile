# syntax=docker/dockerfile:1
FROM python:3.10-alpine
WORKDIR /code
ENV PROXY_ENABLED=0
RUN apk add --no-cache make gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8080
COPY . .
CMD ["python", "main.py"]