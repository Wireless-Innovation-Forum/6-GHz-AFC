# The 6 GHz AFC Test Harness

This directory contains code for AFC system testing.

## Code prerequisites
* Python 3.10 (https://www.python.org/downloads/release/python-3108/)
* PycURL (https://pypi.org/project/pycurl/)
* Six (https://pypi.org/project/six/)

## Executing the test harness
Configure the AFC connection properties and desired tests according to the next section, then execute:
`python ./test_main.py`

## Harness configuraton
* Configuration files:
    *   **./afc.cfg**: AFC SUT connection options. See afc.py [GetTestingAfc()] for more details
    *   **./tests_to_run.py**: Specify tests to run from the *./inquirires* directory. If 'all' is listed first, harness executes on all *(test_name).json* files in *./inquiries.* Corresponding response masks should be placed in the *./masks* directory, named as *(test_name)_mask.json*.

## Sample files
Example json files for the inquiry request, response, and response mask are provided as:
*   **./request_sample.json**
*   **./response_sample.json**
*   **./mask_sample.json**

## Harness output
*   **Console output**
    *   Validation warnings, mask violations, test errors, and summary of test results (passed/failed/skipped)
*   **./logs/harness_main.log**
    *   All harness output, including ingested requests, responses, and response masks. Overwritten each time *./test_main.py* is executed.
*   **./logs/(test_name)\_log\_(datetime).log**
    *   Test-specific copies of output from *./logs/harness_main.log*
*   **./responses/(test_name)\_response\_(datetime).json**
    * Copies of the received response for *test_name*

## Code location
* Test framework:
    *   **./test_main.py**: Main entrypoint to run all test cases
    *   **./available_spectrum_inquiry_request.py**: Defines expected structure of inquiry requests
    *   **./available_spectrum_inquiry_response.py**: Defines expected structure of inquiry responses
    *   **./expected_inquiry_response.py**: Defines expected structure of response masks
    *   **./request_validator.py**: Validates that a specific request is valid according to the SDI spec
    *   **./response_validator.py**: Validates that a specific response is valid according to the definition in *./available_spectrum_inquiry_response.py*
    *   **./response_mask_validator.py**: Validates that a specific response mask is valid according to the definition in *./expected_inquiry_response.py*
    *   **./afc_interface.py**, **./afc.py**, **./request_handler.py**: Handles AFC SUT communication
    *   **./test_harness_logging.py**, **./sdi_validator_common.py**, **./interface_common.py**: Helper code for common validation and logging functionality