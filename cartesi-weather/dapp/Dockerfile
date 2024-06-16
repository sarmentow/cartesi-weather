# syntax=docker.io/docker/dockerfile:1
FROM --platform=linux/riscv64 cartesi/python:3.10-slim-jammy

ARG MACHINE_EMULATOR_TOOLS_VERSION=0.14.1
ADD https://github.com/cartesi/machine-emulator-tools/releases/download/v${MACHINE_EMULATOR_TOOLS_VERSION}/machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb /
RUN dpkg -i /machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb \
  && rm /machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb

LABEL io.cartesi.rollups.sdk_version=0.6.2
LABEL io.cartesi.rollups.ram_size=2048Mi

ARG DEBIAN_FRONTEND=noninteractive
RUN set -e
RUN apt-get update
RUN apt-get install -y --no-install-recommends busybox-static=1:1.30.1-7ubuntu3
RUN apt-get -y --no-install-recommends install libatomic1
RUN rm -rf /var/lib/apt/lists/* /var/log/* /var/cache/*
RUN useradd --create-home --user-group dapp


ENV PATH="/opt/cartesi/bin:${PATH}"

WORKDIR /opt/cartesi/dapp
COPY ./requirements.txt .
RUN mkdir wheels
COPY ./wheels/*.whl ./wheels
RUN ls ./wheels

RUN set -e
RUN pip install -r requirements.txt --no-cache
RUN find /usr/local/lib -type d -name __pycache__ -exec rm -r {} +


COPY ./deps/*.deb .
RUN apt-get install -y --no-install-recommends ./libgomp1_12.3.0-1ubuntu1~22.04_riscv64.deb
RUN apt-get install -y --no-install-recommends ./libgfortran5_12.3.0-1ubuntu1~22.04_riscv64.deb
RUN apt-get install -y --no-install-recommends ./libopenblas0-pthread_0.3.20+ds-1_riscv64.deb
RUN apt-get install -y --no-install-recommends ./libopenblas0_0.3.20+ds-1_riscv64.deb

COPY ./dapp.py .
COPY ./model-2.pth .
COPY ./model.py .
COPY private_key.pem .
RUN chmod 666 private_key.pem

RUN touch client_public_key.pem
RUN chmod 666 client_public_key.pem


ENV ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004"

ENTRYPOINT ["rollup-init"]
CMD ["python3", "dapp.py"]
