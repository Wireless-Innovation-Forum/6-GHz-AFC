#    Copyright 2022 AFC Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

''' Top main script of the test harness.

Before running:
  - Edit cfg/harness.toml and cfg/afc.toml to configure the harness and provide connection info
    for the SUT
  - Edit cfg/tests_to_run.py to indicate which spectrum inquiry tests to run, and be sure that
    the files end in .json
  - Be sure that a json file for each spectrum inquiry to be tested is in the ./inquiries directory

Note: The above files and directories can be overridden via config files and cmd-line options:
  - --harness_cfg path/to/config.toml will override the default harness config of cfg/harness.toml
  - --sut_cfg path/to/config.toml will override the AFC config file specified in harness.toml
  - The path and name of the function that provides the list of tests to be run can be overridden
    in the harness.toml file
  - The paths used for input/output (logs, inquiries, masks, etc.) can be overridden in the
    harness.toml file
'''

# Standard python modules
from datetime import datetime
from enum import Enum, unique, auto
import glob
from importlib import import_module
import json
import os
import logging
import sys
from argparse import ArgumentParser

# Third-party modules
import tomli
from requests.exceptions import JSONDecodeError

# Modules specific to the AFC System test harness
from afc import AfcConnectionHandler
from response_mask_validator import ResponseMaskValidator
from response_validator import InquiryResponseValidator
from request_validator import InquiryRequestValidator
from available_spectrum_inquiry_response import (AvailableSpectrumInquiryResponseMessage,
                                                ResponseCode)
from expected_inquiry_response import ExpectedSpectrumInquiryResponseMessage
from response_mask_runner import ResponseMaskRunner
from test_harness_logging import ConsoleInfoModuleFilter
from cfg.tests_to_run import tests_to_run

@unique
class TestResult(Enum):
  """Enum for defining results of SUT tests

  EXPECTED:  Received response fits the response mask
  UNEXPECTED:  Received response violates the response mask
  SKIPPED: An error was encountered in parsing the request, response, or response mask.
           No determination about EXPECTED/UNEXPECTED is implied by a SKIPPED result."""
  EXPECTED  = auto()
  UNEXPECTED  = auto()
  SKIPPED = auto()

class TestResultStorage():
  """Storage class for summarizing results of all tests"""
  _named_results = {}
  _count_results = {}

  def __init__(self):
    for result_type in TestResult:
      self._named_results[result_type] = []
      self._count_results[result_type] = 0

  def add_result(self, test_name: str, test_result: TestResult):
    """Adds the result of a completed test to the storage object

    Parameters:
      test_name (str): Name of test performed
      test_result (str): Result of performed test"""
    self._named_results[test_result].append(test_name)
    self._count_results[test_result] += 1

  def named_results(self):
    """Get list of all expected/unexpected/skipped test results by name as string"""
    return (f"  Expected results: {', '.join(self._named_results[TestResult.EXPECTED])}\n"
            f"Unexpected results: {', '.join(self._named_results[TestResult.UNEXPECTED])}\n"
            f"     Skipped tests: {', '.join(self._named_results[TestResult.SKIPPED])}")

  def count_results(self):
    """Get summary of all expected/unexpected/skipped tests by # of occurrence as string"""
    return (f'  Expected results: {self._count_results[TestResult.EXPECTED]}\n'
            f'Unexpected results: {self._count_results[TestResult.UNEXPECTED]}\n'
            f'     Skipped tests: {self._count_results[TestResult.SKIPPED]}')

def main():
  '''Sends inquiry request to SUT for each requested test and validates responses'''

  ## Parse command line arguments
  parser = ArgumentParser()
  parser.add_argument('--harness_cfg', action='store', default='cfg/harness.toml')
  parser.add_argument('--sut_cfg', action='store', default=None)
  args = parser.parse_args()

  # Load harness configuration
  try:
    with open(args.harness_cfg, 'rb') as harness_cfg_file:
      harness_cfg = tomli.load(harness_cfg_file)
  except tomli.TOMLDecodeError as ex:
    print(f'Could not parse TOML in harness configuration file. Exception details: {ex}')
    sys.exit(1)
  except OSError as ex:
    print(f'Could not read harness configuration file. Exception details: {ex}')
    sys.exit(1)

  ## Setup directories
  paths_cfg = harness_cfg.get("paths", {})
  log_dir = paths_cfg.get("log_dir", "logs")
  request_dir = paths_cfg.get("inquiry_dir", "inquiries")
  response_dir = paths_cfg.get("response_dir", "responses")
  mask_dir = paths_cfg.get("mask_dir", "masks")

  ## Choose SUT config file
  if args.sut_cfg is not None:
    sut_config_path = args.sut_cfg
  else:
    sut_config_path = harness_cfg.get('sut_config')

  ## Setup logging
  # Base logger object
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)

  # Harness main log file
  file_handler = logging.FileHandler(filename=os.path.join(log_dir, 'harness_main.log'), mode='w',
                                     encoding='utf-8')
  file_log_fmt = '%(asctime)s - {} - %(levelname)s: %(message)s'
  file_handler.setLevel(logging.DEBUG)
  file_handler.setFormatter(logging.Formatter(file_log_fmt.format('Initial Setup')))
  logger.addHandler(file_handler)

  # Console output log
  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setLevel(logging.INFO)
  console_handler.addFilter(ConsoleInfoModuleFilter())
  console_log_fmt = '{} - %(levelname)s: %(message)s'
  console_handler.setFormatter(logging.Formatter(console_log_fmt.format('Initial Setup')))
  logger.addHandler(console_handler)

  # Log harness configuration settings
  logger.info(f'AFC SUT Test Harness - Started {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
  logger.info(f'Loaded with config info: {harness_cfg}')
  logger.info(f'Using AFC config: {sut_config_path}')

  ## Configure SUT
  if sut_config_path is None:
    logger.fatal('SUT Config not specified in harness config or via command line. Exiting...')
    sys.exit(1)
  else:
    if sut_config_path[-5:].lower() != '.toml':
      logger.warning('Expecting .toml file for SUT config, trying to parse anyway...')
    try:
      with open(sut_config_path, 'rb') as sut_config_file:
        sut_config = tomli.load(sut_config_file)
    except tomli.TOMLDecodeError as ex:
      logger.fatal('Could not parse TOML in harness configuration file. '
                  f'Exception details: {ex}. Exiting...')
      sys.exit(1)
    except OSError as ex:
      logger.fatal(f'Could not read harness configuration file. Exception details: {ex}.'
                    'Exiting...')
      sys.exit(1)

  # Log SUT configuration
  logger.info(f'Loaded AFC connection options: {sut_config}')

  # Create AFC connection handler using loaded config
  afc_obj = AfcConnectionHandler(**sut_config, logger=logger)

  ## Configure Tests
  # If first element of tests_to_run is 'all', run all inquiries in the
  # /inquiries directory. Otherwise just run the inquiries in the list.
  logger.debug('Loading test_to_run list...')
  try:
    if harness_cfg.get('tests') is None or harness_cfg['tests'].get('module') is None:
      tests = tests_to_run()
    else:
      list_module = import_module(harness_cfg['tests']['module'])
      tests = getattr(list_module, harness_cfg['tests']['list_func'])()

    if tests[0].lower().strip() == 'all':
      inlist = sorted([os.path.basename(x) for x in glob.glob(os.path.join(request_dir, '*'))])
      tests = [test[:-5] for test in inlist if test[-5:].lower() == '.json']
      # [TODO: Properly handle .json vs .JSON]
      # What should happen if both a.json and a.JSON exist for test "a"?
  except Exception as ex:
    logger.fatal(f'Exception occurred while loading tests to run: {ex}. Exiting...')
    sys.exit(1)

  logger.info(f'Harness will execute the following tests:\n{os.linesep.join(tests)}\n')

  ## Instantiate test objects
  # Create validators/test runner
  request_validator = InquiryRequestValidator(logger=logger)
  response_validator = InquiryResponseValidator(logger=logger)
  mask_validator = ResponseMaskValidator(logger=logger)
  mask_runner = ResponseMaskRunner(logger=logger)

  # Store test results for summary
  results = TestResultStorage()

  test_log_handler = None

  ## Run Tests
  for test_name in tests:
    ## Test Setup
    # Configure file paths
    dt_string = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = os.path.join(log_dir, f'{test_name}_log_{dt_string}.txt')
    response_file = os.path.join(response_dir, f'{test_name}_response_{dt_string}.json')
    request_file = os.path.join(request_dir, f'{test_name}.json')
    mask_file = os.path.join(mask_dir, f'{test_name}_mask.json')

    # Update persistent log formatters to use test name
    console_handler.setFormatter(logging.Formatter(console_log_fmt.format(test_name)))
    file_handler.setFormatter(logging.Formatter(file_log_fmt.format(test_name)))

    # Setup per-test log file
    if test_log_handler is not None:
      # Remove old handler if required (removal was skipped if last test errored out)
      logger.removeHandler(test_log_handler)
    test_log_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    test_log_handler.setLevel(logging.DEBUG)
    test_log_handler.setFormatter(logging.Formatter(file_log_fmt.format(test_name)))
    logger.addHandler(test_log_handler)

    logger.debug(f'Test {test_name} starting...')

    ## Run test
    try:
      # Read the contents of the mask file in text format
      logger.debug(f'Loading response mask {mask_file}...')
      with open(mask_file, encoding='utf-8') as fin:
        mask_raw = fin.read()

      # Log the opened mask file contents
      logger.debug(f'Opened response mask file {mask_file} with contents:\n{mask_raw}')

      # Convert mask text to JSON
      logger.debug('Parsing imported response mask file as JSON...')
      try:
        mask_json = json.loads(mask_raw)
      except Exception as ex:
        logger.fatal(f'Encountered exception while parsing response mask JSON: {ex}. '
                     f'Test SKIPPED.\n')
        results.add_result(test_name, TestResult.SKIPPED)
        continue

      # Validate mask JSON
      logger.debug('Validating imported response mask JSON...')
      if mask_validator.validate_expected_spectrum_inquiry_response_message(mask_json):
        logger.info('Response mask passes validation.')
        mask_obj = ExpectedSpectrumInquiryResponseMessage(**mask_json)
      else:
        logger.fatal('Response mask does not pass validation. Test SKIPPED.\n')
        results.add_result(test_name, TestResult.SKIPPED)
        continue

      # Read the contents of the request file in text format
      logger.debug(f'Loading request file {request_file}...')
      with open(request_file, encoding='utf-8') as fin:
        request_raw = fin.read()

      # Log the opened request file contents
      logger.debug(f'Opened request file {request_file} with contents:\n{request_raw}')

      # Convert request text to JSON
      logger.debug('Parsing imported request file as JSON...')
      try:
        request_json = json.loads(request_raw)
      except Exception as ex:
        logger.fatal(f'Encountered exception while parsing request JSON: {ex}. Test SKIPPED.\n')
        results.add_result(test_name, TestResult.SKIPPED)
        continue

      # Validate request JSON
      logger.debug('Validating imported request JSON...')
      if not request_validator.validate_available_spectrum_inquiry_request_message(request_json):
        logger.info('Request does not pass SDI validation--checking if mask expects an error...')
        if any(any(ResponseCode.get_raw_value(code) != ResponseCode.SUCCESS.value
                   for code in exp.expectedResponseCodes)
               for exp in mask_obj.expectedSpectrumInquiryResponses):
          logger.info('Mask expects an error code, so sending invalid request anyway.')
        else:
          logger.fatal('Request does not pass SDI validation, but response mask doesn\'t expect '
                       'an error. Test SKIPPED.\n')
          results.add_result(test_name, TestResult.SKIPPED)
          continue
      else:
        logger.info('Request passes SDI validation.')

      # Submit the request to the SUT
      logger.info(f'Sending request to AFC via {afc_obj.get_afc_url()}...')
      afc_obj.send_request(request_json)

      # Check for valid HTTP response and code
      resp_code = afc_obj.get_last_http_code()
      if resp_code is None:
        logger.error('Failed to receive an HTTP response from the AFC. Result UNEXPECTED.\n')
        results.add_result(test_name, TestResult.UNEXPECTED)
        continue
      if not 200 <= resp_code <= 299:
        logger.error(f'Expected response HTTP code of 2XX, got: {afc_obj.get_last_http_code()}. '
                      'Result UNEXPECTED.\n')
        results.add_result(test_name, TestResult.UNEXPECTED)
        continue

      # Ensure response can be decoded as JSON
      try:
        response = afc_obj.get_last_response()
      except JSONDecodeError as ex:
        logger.error('Received response could not be decoded as valid JSON. Raw response test: '
                    f'"{afc_obj.get_last_response(as_json=False)}". Result UNEXPECTED.\n')
        results.add_result(test_name, TestResult.UNEXPECTED)
        continue

      # Log received response contents
      logger.debug(f'Received response with contents:\n{json.dumps(response,indent=2)}')

      # Write the response to a stand-alone text file
      logger.debug(f'Logging received response in {response_file}...')
      with open(response_file, 'w', encoding='utf-8') as fresponse:
        fresponse.write(json.dumps(response, indent=2) + '\n')

      # Checking that response is valid
      if response_validator.validate_available_spectrum_inquiry_response_message(response):
        logger.info('Response appears valid.')
      else:
        logger.warning('Response does NOT appear valid. Will attempt test anyway...')

      logger.debug(f'Parsing received response as a response object...')
      try:
        response_obj = AvailableSpectrumInquiryResponseMessage(**response)
      except TypeError as ex:
        logger.error(f'Exception converting response for comparison: {ex}. Test SKIPPED.\n')
        results.add_result(test_name, TestResult.SKIPPED)
        continue

      # Compare response to mask
      logger.debug(f'Comparing response to mask...')
      try:
        if mask_runner.run_test_response_message(mask_obj, response_obj, validate_objects=False):
          logger.info('Response meets mask requirements. Result EXPECTED.\n')
          results.add_result(test_name, TestResult.EXPECTED)
        else:
          logger.error('Response does not meet mask requirements. Result UNEXPECTED.\n')
          results.add_result(test_name, TestResult.UNEXPECTED)
      except Exception as ex:
        logger.fatal(f'Encountered exception while evaluating response: {ex}. Test SKIPPED.\n')
        results.add_result(test_name, TestResult.SKIPPED)
    except Exception as ex:
      logger.fatal(f'Encountered exception while running test: {ex}. Test SKIPPED.\n')
      results.add_result(test_name, TestResult.SKIPPED)

    logger.removeHandler(test_log_handler)
    test_log_handler = None

  # Update persistent log formatters to use summary
  console_handler.setFormatter(logging.Formatter(console_log_fmt.format("Results")))
  file_handler.setFormatter(logging.Formatter(file_log_fmt.format("Results")))

  # Output accumulated results
  logger.debug(f"Full Test Results:\n{results.named_results()}")
  logger.info(f'Test Summary:\n{results.count_results()}\n')

  logger.info('Tests complete. See harness_main.log for full details.')

if __name__ == "__main__":
  main()
