# Base OS
FROM python:3.7.9-slim-buster

ARG VERSION="0.0.1"
ARG SIMULATOR_VERSION=2.1.5

# metadata
LABEL \
    org.opencontainers.image.title="BoolNet" \
    org.opencontainers.image.version="${SIMULATOR_VERSION}" \
    org.opencontainers.image.description="Package for generation, reconstruction, simulation and analysis of synchronous, asynchronous and probabilistic Boolean networks." \
    org.opencontainers.image.url="https://sysbio.uni-ulm.de/?Software:BoolNet" \
    org.opencontainers.image.documentation="https://cran.r-project.org/web/packages/BoolNet/index.html" \
    org.opencontainers.image.source="https://github.com/biosimulators/Biosimulators_BoolNet" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="Artistic-2.0" \
    \
    base_image="python:3.7.9-slim-buster" \
    version="${VERSION}" \
    software="BoolNet" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Package for generation, reconstruction, simulation and analysis of synchronous, asynchronous and probabilistic Boolean networks." \
    about.home="https://sysbio.uni-ulm.de/?Software:BoolNet" \
    about.documentation="https://cran.r-project.org/web/packages/BoolNet/index.html" \
    about.license_file="https://cran.r-project.org/web/licenses/Artistic-2.0" \
    about.license="SPDX:Artistic-2.0" \
    about.tags="BioSimulators,mathematical model,logical model,simulation,systems biology,computational biology,SBML,SED-ML,COMBINE,OMEX" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# Install requirements
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        dirmngr \
        gnupg \
        apt-transport-https \
        ca-certificates \
        software-properties-common \
        build-essential \
        r-base \
        libcurl4-openssl-dev \
        libxml2-dev \
        libssl-dev \
        libfontconfig1-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libgit2-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
        gfortran \
        libblas-dev \
        liblapack-dev \
    \
    R -e "install.packages(\"devtools\", dependencies=TRUE);" \
    R -e "require(devtools); install_version(\"BoolNet\", version=\"${SIMULATOR_VERSION}\")"
    \
    && apt-get remove -y \
        dirmngr \
        gnupg \
        apt-transport-https \
        ca-certificates \
        software-properties-common \
        build-essential \
        libcurl4-openssl-dev \
        libxml2-dev \
        libssl-dev \
        libfontconfig1-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libgit2-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
        gfortran \
        libblas-dev \
        liblapack-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_boolnet
RUN pip install /root/Biosimulators_boolnet

# Entrypoint
ENTRYPOINT ["boolnet"]
CMD []
