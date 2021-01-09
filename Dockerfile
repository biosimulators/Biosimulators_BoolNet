# Base OS
FROM continuumio/miniconda3:4.9.2

ARG VERSION="0.1.0"
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
    base_image="continuumio/miniconda3:4.9.2" \
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
ENV CONDA_ENV=py38
RUN conda config --add channels conda-forge \
    && conda update -y -n base -c defaults conda \
    && conda create -y -n ${CONDA_ENV} python=3.8 \
    && conda install -y r-boolnet=${SIMULATOR_VERSION}
ENV PATH=/opt/conda/envs/${CONDA_ENV}/bin:${PATH}
RUN /bin/bash -c "source activate ${CONDA_ENV}"

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_BoolNet
RUN pip install /root/Biosimulators_BoolNet \
    && rm -rf /root/Biosimulators_BoolNet
ENV MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["boolnet"]
CMD []
