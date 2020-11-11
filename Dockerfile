# Base OS
FROM python:3.7.9-slim-buster

# metadata
LABEL \
    org.opencontainers.image.title="BoolNet" \
    org.opencontainers.image.version="2.1.5" \
    org.opencontainers.image.description="Package for generation, reconstruction, simulation and analysis of synchronous, asynchronous and probabilistic Boolean networks." \
    org.opencontainers.image.url="https://sysbio.uni-ulm.de/?Software:BoolNet" \
    org.opencontainers.image.documentation="https://cran.r-project.org/web/packages/BoolNet/index.html" \
    org.opencontainers.image.source="https://github.com/biosimulators/Biosimulators_BoolNet" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="Artistic-2.0" \
    \
    base_image="python:3.7.9-slim-buster" \
    version="0.0.1" \
    software="BoolNet" \
    software.version="2.1.5" \
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
        r-base \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_boolnet
RUN pip install /root/Biosimulators_boolnet

# Entrypoint
ENTRYPOINT ["boolnet"]
CMD []
