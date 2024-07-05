FROM python:3.12.4-slim AS builder
WORKDIR /code
RUN apt-get update \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
COPY pyproject.toml poetry.lock ./
RUN pip3 install --upgrade pip \
  && pip3 install poetry \
  && poetry config virtualenvs.create false
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY src/ .

FROM builder AS develop
RUN poetry install
ENTRYPOINT [ "sh", "/entrypoint.sh" ]

FROM builder AS production
RUN poetry install --without dev
ARG GROUP
ARG USER
RUN groupadd ${GROUP} \
 && useradd -m -g ${GROUP} ${USER} \
 && mv /code /home/${USER}/code \
 && chown ${USER}:${GROUP} -R /home/${USER}/code \
 && mv /entrypoint.sh /home/${USER}/entrypoint.sh
WORKDIR /home/${USER}/code
USER ${USER}
ENTRYPOINT [ "sh", "/home/app/entrypoint.sh" ]
