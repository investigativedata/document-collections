FROM ghcr.io/investigativedata/ftm-docker:main

LABEL org.opencontainers.image.title "Memorious Crawlers"
LABEL org.opencontainers.image.source https://github.com/investigativedata/document-collections

RUN apt-get -qq -y install ca-certificates \
    python3-cryptography unzip lsb-release python3-lxml \
    git wget curl jq

RUN mkdir -p /crawlers
COPY . /crawlers
RUN pip install -e /crawlers
WORKDIR /crawlers
CMD ["bash"]
