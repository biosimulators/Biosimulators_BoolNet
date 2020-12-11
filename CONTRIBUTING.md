# Contributing to `BioSimulators-BoolNet`

We enthusiastically welcome contributions to BioSimulators-BoolNet!

## Coordinating contributions

Before getting started, please contact the lead developers at [info@biosimulators.org](mailto:info@biosimulators.org) to coordinate your planned contributions with other ongoing efforts. Please also use GitHub issues to announce your plans to the community so that other developers can provide input into your plans and coordinate their own work.

## Repository organization

* `README.md`: Overview of the repository
* `tests/`: unit tests for the command-line interface
* `LICENSE`: License
* `CONTRIBUTING.md`: Guide to contributing to BioSimulators-BoolNet (this document)
* `CODE_OF_CONDUCT.md`: Code of conduct for developers of BioSimulators-BoolNet

## Testing and continuous integration

We strive to have complete test coverage for BioSimulators-BoolNet.

## Submitting changes

Please use GitHub pull requests to submit changes. Each request should include a brief description of the new and/or modified features.

## Releasing new versions

To release changes, contact the [lead developers](mailto:info@biosimulators.org) to request their release.

Below are instructions for releasing a new version:

1. Make the required changes to the repository.
  * To update the version of the underyling simulator, update its version numbers in the following files:
    * `requirements.txt`
    * `Dockerfile`
    * `biosimulators.json`
2. Commit the changes to this repository.
3. Increment the `__version__` variable in `biosimulators_boolnet/_version.py`.
4. Commit this change to `biosimulators_boolnet/_version.py`.
5. Add a tag for the new version by running `git tag { version }`. `version` should be equal to the value of the
   `__version__` variable in `biosimulators_boolnet/_version.py`.
6. Push these commits and the new tag to GitHub by running `git push && git push --tags`.
7. This push will trigger a GitHub action which will execute the following tasks:
   * Create a GitHub release for the version.
   * Push the release to PyPI.
   * Compile the documentation and push the compiled documentation to the repository so that the new documentation is viewable at github.io.

## Reporting issues

Please use [GitHub issues](https://github.com/biosimulators/Biosimulators_BoolNet/issues) to report any issues to the development community.

## Getting help

Please use [GitHub issues](https://github.com/biosimulators/Biosimulators_BoolNet/issues) to post questions or contact the lead developers at [info@biosimulators.org](mailto:info@biosimulators.org).
