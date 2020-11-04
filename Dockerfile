# Base OS
FROM python:3.7.9-slim-buster

# metadata
LABEL base_image="python:3.7.9-slim-buster"
LABEL version="0.0.1"
LABEL software="BoolNet"
LABEL software.version="2.1.5"
LABEL about.summary="Package for generation, reconstruction, simulation and analysis of synchronous, asynchronous and probabilistic Boolean networks."
LABEL about.home="https://sysbio.uni-ulm.de/?Software:BoolNet"
LABEL about.documentation="https://cran.r-project.org/web/packages/BoolNet/index.html"
LABEL about.license_file="https://cran.r-project.org/web/licenses/Artistic-2.0"
LABEL about.license="Artistic-2.0"
LABEL about.tags="BioSimulators,mathematical model,logical model,simulation,systems biology,computational biology,SBML,SED-ML,COMBINE,OMEX"
LABEL maintainer="BioSimulators Team <info@biosimulators.org>"

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
