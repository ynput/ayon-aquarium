FROM python:3.9-bullseye
ENV PYTHONUNBUFFERED=1
LABEL org.opencontainers.image.description "Aquarium leecher service for Ayon"
LABEL org.opencontainers.image.source https://github.com/ynput/ayon-aquarium

RUN apt-get update \
  && apt-get install -y curl python3-pip python3-virtualenv \
  && pip install poetry

RUN mkdir /service
COPY ./pyproject.toml /service/pyproject.toml
WORKDIR /service


RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

COPY ./aquarium_common /service/aquarium_common
COPY ./leecher /service/leecher

CMD ["python", "-m", "leecher"]
