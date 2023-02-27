# The 6 GHz AFC Test Harness

This directory contains code for the 6 GHz Automated Frequency Coordination (AFC) System Under Test (SUT) test harness.

## Code prerequisites
* Python 3.10 (https://www.python.org/downloads/release/python-3108/)
* Requests: HTTP for Humans (https://requests.readthedocs.io/en/latest/)
* Tomli (https://github.com/hukkin/tomli)

## Executing the test harness
Configure the test harness according to [Harness Configuration](#harness-configuration), then execute:

`python ./test_main.py`

Two command line arguments are available to override the default harness configuration files. These are:
* **--harness_cfg**: Specify the path to the overall harness configuration file (default: `./cfg/harness.toml`)
* **--sut_cfg**: Specify the path to the AFC connection configuration file (default: set in `harness_cfg`). This option overrides any sut_cfg provided by harness_cfg.

Any combination of these arguments is permitted. For example:
* `python ./test_main.py --harness_cfg some/other/path/config.toml`
* `python ./test_main.py --sut_cfg some/other/other/path/sut.toml`
* `python ./test_main.py --harness_cfg some/other/path/config.toml --sut_cfg some/other/other/path/sut.toml`

## Harness configuration
### Required configuration
The only required option that must be configured before use is setting the address for the AFC SUT. By default, this option is configured in `./cfg/afc.toml` using the `base_url` field (line 31).


### Authentication methods
The test harness supports client authentication using client certificates and python classes that accept a single argument to `__init__()` and follow the interface set by the [requests library's AuthBase interface](https://requests.readthedocs.io/en/latest/user/authentication/#new-forms-of-authentication). Files related to authentication are stored in `./auth`. An example authentication method using a file-based bearer token is included in `./auth/custom_auth.py`. This file can be used as a starting place for other authentication methods.
### Configuration file descriptions
Harness configuration files are located in `./cfg`. Detailed descriptions of each configuration file and documentation for all permitted options is available within each config file. Files with a `.toml` extension follow the [TOML standard](https://toml.io/en/). Summaries of the provided configuration files are below:
*   **./cfg/harness.toml**: Specifies the AFC configuration file, test list module, and input/output directories.
*   **./cfg/afc.toml**: AFC SUT connection options, including any authentication information. See the documentation for the `AfcConnectionHandler` class in `./afc.py` or the descriptions in `./cfg/afc.toml` for more details.
*   **./cfg/tests_to_run.py**: Specify tests to run from the `{inquiries_dir}` directory. If 'all' is listed first, harness executes on all `(test_name).json` files in `{inquiries_dir}`. Corresponding response masks should be placed in the `{masks_dir}` directory, named as `(test_name)_mask.json`. This file should contain a valid python function that returns a list of test names.
    *   By default, the `{inquiries_dir}` directory is `./inquiries` and the `{masks_dir}` directory is `./masks`.

## Specification versions
AFC communication and message validation is performed according to the current version of the Wi-Fi Alliance AFC System to AFC Device Interface Specification Protocol (protocol v1.3, as defined in specification v1.4).

Tests are executed and evaluated according to the current version of the Wi-Fi Alliance AFC System Under Test (SUT) Compliance Test Plan (v1.4).

These specifications and test vectors are available from the [Wi-Fi Alliance website](https://www.wi-fi.org/discover-wi-fi/specifications) under "AFC Specification and Test Plans."

## Sample files
Example json files for the inquiry request, response, and response mask are provided as:
*   **./request_sample.json**
*   **./response_sample.json**
*   **./mask_sample.json**

## Harness output
*   **Console output**
    *   Validation warnings, mask violations, test errors, and summary of test results (expected/unexpected/skipped)
*   **{logs_dir}/harness_main.log**
    *   All harness output, including ingested requests, responses, and response masks (overwritten each time `./test_main.py` is executed)
    *   By default, `logs_dir` is `./logs`
*   **{logs_dir}/(test_name)\_log\_(datetime).log**
    *   Test-specific copies of output from `{logs_dir}/harness_main.log`
    *   By default, `logs_dir` is `./logs`
*   **{response_dir}/(test_name)\_response\_(datetime).json**
    *   Copies of the received response for `test_name`
    *   By default, `response_dir` is `./responses`

## Code location
* Test framework:
    *   **./test_main.py**: Main entry point to run all test cases
    *   **./response_mask_runner.py**: Logic for comparing responses against an expected response definition
    *   **./available_spectrum_inquiry_request.py**: Defines expected structure of inquiry requests
    *   **./available_spectrum_inquiry_response.py**: Defines expected structure of inquiry responses
    *   **./expected_inquiry_response.py**: Defines expected structure of response masks
    *   **./request_validator.py**: Validates that a specific request is valid according to the SDI spec
    *   **./response_validator.py**: Validates that a specific response is valid according to the SDI spec
    *   **./response_mask_validator.py**: Validates that a specific response mask is valid according to the definition in `./expected_inquiry_response.py`
    *   **./afc.py**: Handles AFC SUT communication
    *   **./test_harness_logging.py**, **./sdi_validator_common.py**, **./interface_common.py**: Helper code for common validation and logging functionality