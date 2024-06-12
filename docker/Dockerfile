FROM python:3.8.19-slim-bookworm
RUN apt-get update \
    && apt-get install -y \
    curl \
    gcc \
    git \
    ruby-sass \
    gnupg2 \
    libc6-dev \
    libdpkg-perl \
    make \
    gettext \
    libpq-dev
RUN touch /etc/apt/preferences.d/nodejs && \
    echo "Package: nodejs\nPin: origin deb.nodesource.com\nPin-Priority: 1001" > /etc/apt/preferences.d/nodejs
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - && apt install nodejs -y
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN /root/.local/bin/poetry config virtualenvs.create false
COPY ./ /ej-application
WORKDIR ej-application
# Installs main and dev groups dependencies
RUN /root/.local/bin/poetry install --with main,dev --no-root
