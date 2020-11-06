![Latest version](https://img.shields.io/github/v/tag/biosimulators/Biosimulators_BoolNet)
[![PyPI](https://img.shields.io/pypi/v/biosimulators_boolnet)](https://pypi.org/project/biosimulators_boolnet/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/biosimulators/Biosimulators_BoolNet/workflow-id)](https://github.com/biosimulators/Biosimulators_BoolNet/actions?query=workflow%3Aworkflow-id)
[![Documentation](https://img.shields.io/github/license/biosimulators/Biosimulators_BoolNet?badges-awesome-green.svg)](https://biosimulators.github.io/Biosimulators_BoolNet/)
[![Issues](https://img.shields.io/github/issues/biosimulators/Biosimulators_BoolNet)](https://github.com/biosimulators/Biosimulators_BoolNet/issues)
[![License](https://img.shields.io/github/license/biosimulators/Biosimulators_BoolNet?badges-awesome-green.svg)](https://github.com/biosimulators/Biosimulators_BoolNet/blob/dev/LICENSE)

# BioSimulators-BoolNet
BioSimulators-compliant command-line interface to the [BoolNet](https://sysbio.uni-ulm.de/?Software:BoolNet) simulation program.

This command-line interface and Docker image enable users to use BoolNet to execute [COMBINE/OMEX archives](https://combinearchive.org/) that describe one or more simulation experiments (in [SED-ML format](https://sed-ml.org)) of one or more models (in [SBML format](http://sbml.org])).

A list of the algorithms and algorithm parameters supported by BoolNet is available at [BioSimulators](https://biosimulators.org/simulators/boolnet).

A simple web application and web service for using BoolNet to execute COMBINE/OMEX archives is also available at [runBioSimulations](https://run.biosimulations.org).

## Contents
* [Installation](#installation)
* [Usage](#usage)
* [Documentation](#documentation)
* [License](#license)
* [Development team](#development-team)
* [Questions and comments](#questions-and-comments)

## Installation

### Install Docker image
```
docker pull ghcr.io/biosimulators/boolnet
```

## Usage

### Local usage
```
usage: boolnet [-h] [-d] [-q] -i ARCHIVE [-o OUT_DIR] [-v]

BioSimulators-compliant command-line interface to the BoolNet simulation program <https://sysbio.uni-ulm.de/?Software:BoolNet>.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           full application debug mode
  -q, --quiet           suppress all console output
  -i ARCHIVE, --archive ARCHIVE
                        Path to OMEX file which contains one or more SED-ML-
                        encoded simulation experiments
  -o OUT_DIR, --out-dir OUT_DIR
                        Directory to save outputs
  -v, --version         show program's version number and exit
```

### Usage through Docker container
```
docker run \
  --tty \
  --rm \
  --mount type=bind,source="$(pwd)"/tests/fixtures,target=/root/in,readonly \
  --mount type=bind,source="$(pwd)"/tests/results,target=/root/out \
  ghcr.io/biosimulators/boolnet:latest \
    -i /root/in/BIOMD0000000297.omex \
    -o /root/out
```

## Documentation
Documentation is available at https://biosimulators.github.io/Biosimulators_BoolNet/.

## License
This package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Center for Reproducible Biomedical Modeling](http://reproduciblebiomodels.org) and the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York.

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
