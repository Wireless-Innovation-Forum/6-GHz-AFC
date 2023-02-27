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
"""AFC Spectrum Inquiry Response Mask Runner - SDI Protocol v1.3, SUT Test Plan v1.4

Mask runner functions will compare the provided response mask to a received response
and provide an expected/unexpected result, logging results along the way. Comparison is performed
exhaustively (i.e., comparison does not stop on first unexpected value, but will attempt to report
all unexpected values. Multiple issues may be reported for the same root cause."""

import available_spectrum_inquiry_response as afc_resp
from response_validator import InquiryResponseValidator
from response_mask_validator import ResponseMaskValidator
import expected_inquiry_response as afc_exp
from test_harness_logging import TestHarnessLogger

class ResponseMaskRunner(TestHarnessLogger):
  """Provides mask comparison functions for AFC Response types"""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.exp_validator = ResponseMaskValidator()
    self.recv_validator = InquiryResponseValidator()

  def run_test_response(self, expected: afc_exp.ExpectedSpectrumInquiryResponse,
        received: afc_resp.AvailableSpectrumInquiryResponse, validate_objects = False):
    """Compares an AvailableSpectrumInquiryResponse to the expected response mask

    Checks:
      requestId matches
      rulesetId matches
      response.responseCode is not disallowed (permits expected codes or vendor extension codes)
        Logs warning on vendor extension codes--may merit manual review
      No response frequency ranges overlap disallowed ranges
      All response frequency range PSDs are within permitted ranges
      No response channels are granted that are not in mask
      All response channel EIRPs are within permitted ranges
      Does not provide availability info of basis not specified in mask

    Does NOT Check:
      VendorExtensions (warning printed if present)

    Parameters:
      expected (ExpectedSpectrumInquiryResponse): Response mask used as standard for comparison
      received (AvailableSpectrumInquiryResponse): Response subject to comparison
      validate_objects (Boolean): Enables validation of expected and received prior to comparison

    Returns:
      True if all checks are satisfied
      False otherwise

    Throws:
      ValueError if expected is not valid"""

    # Validate objects (if requested)
    if validate_objects:
      if not self.recv_validator.validate_available_spectrum_inquiry_response(received):
        self._warning('Received response does not pass validation; errors in comparison may result')
      else:
        self._info('Received response passes validation')

      # Mask validation failure is considered fatal--stop now instead of later
      if not self.exp_validator.validate_expected_spectrum_inquiry_response(expected):
        self._fatal('Response mask does not pass validation; stopping comparison')
        raise ValueError('Response mask is invalid; '
                         'see logs for more detail (enable logging if needed)')
      else:
        self._info('Response mask passes validation')

    received_expected = True
    # requestId matches
    if expected.requestId != received.requestId:
      received_expected = False
      self._error((f'Received requestId ({received.requestId}) '
                   f'does not match mask ({expected.requestId})'))
    else:
      self._info(f'Received requestId matches mask ({expected.requestId})')

    # rulesetId matches
    if expected.rulesetId != received.rulesetId:
      received_expected = False
      self._error(f'Received rulesetId ({received.rulesetId}) '
                  f'does not match mask ({expected.rulesetId})')
    else:
      self._info(f'Received rulesetId matches mask ({expected.rulesetId})')

    # response.responseCode is not disallowed
    if received.response.responseCode not in expected.expectedResponseCodes:
      if received.response.responseCode in expected.disallowedResponseCodes:
        received_expected = False
        self._error(f'Received disallowed response code: {received.response.responseCode} '
                    f'(Expected: {expected.expectedResponseCodes}')
      else:
        self._warning(f'Received unexpected response code: {received.response.responseCode}. '
                      f'Possibly vendor extension?')
    else:
      self._info(f'Received response code ({received.response.responseCode}) '
                 f'matches mask codes ({expected.expectedResponseCodes})')

    # Frequency range checks
    if received.availableFrequencyInfo is not None:
      # Does not provide availability info of basis not specified in mask
      if expected.expectedFrequencyInfo is None:
        received_expected = False
        self._error('Response contains frequency info but mask does not')
      else:
        for recv_freq_info in received.availableFrequencyInfo:
          curr_freq = recv_freq_info.frequencyRange.lowFrequency
          while curr_freq < recv_freq_info.frequencyRange.highFrequency:
            low_disallow_freq = recv_freq_info.frequencyRange.lowFrequency
            high_disallow_freq = recv_freq_info.frequencyRange.highFrequency
            for mask_info in expected.expectedFrequencyInfo:
              if mask_info.frequencyRange.highFrequency <= curr_freq:
                low_disallow_freq = max(low_disallow_freq, mask_info.frequencyRange.highFrequency)
              elif mask_info.frequencyRange.lowFrequency > curr_freq:
                high_disallow_freq = min(high_disallow_freq, mask_info.frequencyRange.lowFrequency)
              else:
                high_end_freq = min(mask_info.frequencyRange.highFrequency,
                                    recv_freq_info.frequencyRange.highFrequency)
                # All response frequency range PSDs are within permitted ranges
                if not mask_info.maxPsd.in_range(recv_freq_info.maxPsd):
                  received_expected = False
                  self._error(f'Mask violated on {curr_freq} - {high_end_freq} MHz. '
                              f'Permitted {recv_freq_info.maxPsd} dBm/MHz '
                              f'but expected {mask_info.maxPsd} dBm/MHz')
                else:
                  self._info(f'Mask matches on {curr_freq} - {high_end_freq} MHz. '
                            f'Permitted {recv_freq_info.maxPsd} dBm/MHz '
                            f'and expected {mask_info.maxPsd} dBm/MHz')
                curr_freq = mask_info.frequencyRange.highFrequency
                break
            # No response frequency ranges overlap disallowed ranges
            else:
              received_expected = False
              self._error(f'Transmission disallowed on {curr_freq} - {high_disallow_freq} MHz')
              curr_freq = high_disallow_freq

    if received.availableChannelInfo is not None:
      # Does not provide availability info of basis not specified in mask
      if expected.expectedChannelInfo is None:
        received_expected = False
        self._error('Response contains channel info but mask does not')
      else:
        for recv_class_info in received.availableChannelInfo:
          # Get any non-placeholder mask objects with same GOC
          matching_expected_class = [exp for exp in expected.expectedChannelInfo
                                    if exp.globalOperatingClass ==
                                        recv_class_info.globalOperatingClass and
                                        (len(exp.channelCfi) != 0 or len(exp.maxEirp) != 0)]
          # No response channels are granted that are not in mask (GOC check)
          match len(matching_expected_class):
            case 0:
              # Ensure received is not an empty placeholder (allowed)
              if len(recv_class_info.channelCfi) != 0 or len(recv_class_info.maxEirp) != 0:
                received_expected = False
                self._error('No allowed channels provided for GOC '
                           f'{recv_class_info.globalOperatingClass}, but response includes them')
              continue
            case 1:
              matching_expected_class = matching_expected_class[0]
            case _:
              received_expected = False
              self._fatal('Error in mask -- found multiple channel info objs with same '
                        f'globalOperatingClass ({recv_class_info.globalOperatingClass})')
              raise ValueError('Response mask has multiple channel info objs with same '
                              f'globalOperatingClass ({recv_class_info.globalOperatingClass})')

          # Channel checks
          for recv_cfi, recv_eirp in zip(recv_class_info.channelCfi, recv_class_info.maxEirp):
            matching_expected_info = [info for info in zip(matching_expected_class.channelCfi,
                                                          matching_expected_class.maxEirp)
                                      if info[0] == recv_cfi]
            # No response channels are granted that are not in mask (GOC/CFI pair check)
            match len(matching_expected_info):
              case 0:
                received_expected = False
                self._error(f'GOC {recv_class_info.globalOperatingClass} '
                            f'with CFI {recv_cfi} not permitted by mask, but response permits it')
                continue
              case 1:
                _, eirp = matching_expected_info[0]
              case _:
                received_expected = False
                self._fatal('Error in mask -- found multiple channel masks with GOC '
                          f'{matching_expected_class.globalOperatingClass} and channelCfi '
                          f'{recv_cfi}')
                raise ValueError('Response mask has multiple channel masks with GOC '
                                f'{matching_expected_class.globalOperatingClass} and channelCfi '
                                f'{recv_cfi}')

            # All response channel EIRPs are within permitted ranges
            if not eirp.in_range(recv_eirp):
              received_expected = False
              self._error(f'AFC response for GOC {recv_class_info.globalOperatingClass} '
                          f'and CFI {recv_cfi} outside allowed range. '
                          f'Permitted {recv_eirp} dBm but expected {eirp} dBm')
            else:
              self._info(f'AFC response for GOC {recv_class_info.globalOperatingClass} '
                        f'and CFI {recv_cfi} within allowed range. '
                        f'Permitted {recv_eirp} dBm and expected {eirp} dBm')

    # Ignore VendorExtensions
    if received.vendorExtensions is not None:
      self._warning('Received message contains VendorExtensions, '
                    'but extensions will not be tested')
    if expected.vendorExtensions is not None:
      self._warning('Expected response mask contains VendorExtensions, '
                    'but extensions will not be tested')

    return received_expected

  def run_test_response_message(self, expected: afc_exp.ExpectedSpectrumInquiryResponseMessage,
          received: afc_resp.AvailableSpectrumInquiryResponseMessage, validate_objects = False):
    """Compares an AvailableSpectrumInquiryResponseMessage to the expected response message mask

    Checks:
      version matches
      Number of responses within message matches
      Exactly one response per expected requestId
      No responses with an unexpected requestId
      Each expected response satisfies the corresponding response mask

    Does NOT Check:
      VendorExtensions (warning printed if present)

    Parameters:
      expected (ExpectedSpectrumInquiryResponseMessage): Mask used as standard for comparison
      received (AvailableSpectrumInquiryResponseMEssage): Message subject to comparison
      validate_objects (Boolean): Enables validation of expected and received prior to comparison

    Returns:
      True if all checks are satisfied
      False otherwise

    Throws:
      ValueError if expected is not valid"""

    if validate_objects:
      if not self.recv_validator.validate_available_spectrum_inquiry_response_message(received):
        self._warning('Received message does not pass validation; errors in comparison may result')
      else:
        self._info('Received response message passes validation')
      if not self.exp_validator.validate_expected_spectrum_inquiry_response_message(expected):
        self._fatal('Response mask does not pass validation; stopping comparison')
        raise ValueError('Response mask is invalid')
      else:
        self._info('Response message mask passes validation')

    received_expected = True
    # version matches
    # May wish to change response mask format to permit multiple version values in future
    if received.version != expected.version:
      self._error(f'Received version ({received.version}) does not match '
                  f'mask version ({expected.version})')
      received_expected = False

    # Number of responses within message matches
    if (len(received.availableSpectrumInquiryResponses) !=
       len(expected.expectedSpectrumInquiryResponses)):
      self._error('Received message has unexpected number of responses. '
                 f'Received {len(received.availableSpectrumInquiryResponses)} '
                 f'but expected {len(expected.expectedSpectrumInquiryResponses)}')
      received_expected = False

    # Response checks
    for sub_exp in expected.expectedSpectrumInquiryResponses:
      num_with_id = sum(resp.requestId == sub_exp.requestId
                        for resp in received.availableSpectrumInquiryResponses)
      # Only one response per expected requestId
      if num_with_id != 1:
        self._error(f'Expected one response with ID ({sub_exp.requestId}), but found {num_with_id}')
        received_expected = False
      else:
        for sub_resp in received.availableSpectrumInquiryResponses:
          if sub_resp.requestId == sub_exp.requestId:
            # Each expected response satisfies the corresponding response mask
            if not self.run_test_response(sub_exp, sub_resp):
              received_expected = False
              self._error(f'Response for requestID ({sub_resp.requestId}) '
                           'violated expected response mask')
            else:
              self._info(f'Response for requestID ({sub_resp.requestId}) '
                          'satisfies expected response mask')

    # No responses with an unexpected requestId
    for sub_resp in received.availableSpectrumInquiryResponses:
      num_with_id = sum(exp_resp.requestId == sub_resp.requestId
                        for exp_resp in expected.expectedSpectrumInquiryResponses)
      if num_with_id == 0:
        self._error(f'Received response with unexpected ID ({sub_resp.requestId})')
        received_expected = False

    # Ignore VendorExtensions
    if received.vendorExtensions is not None:
      self._warning('Received message contains VendorExtensions, but extensions will not be tested')
    if expected.vendorExtensions is not None:
      self._warning('Expected response mask contains VendorExtensions, but extensions will not be '
                    'tested')
    return received_expected

def main():
  """Demonstrates use of the mask runner functions"""
  logging.basicConfig()
  logger = logging.getLogger()
  logger.setLevel(logging.INFO) # Expected/passing results are logged as info
                                # Response validation errors are logged as warning
                                # Response mask violations are logged as error
                                # Mask validation errors are logged as fatal and throw ValueError

  runner = ResponseMaskRunner(logger=logger)

  with open(os.path.join(pathlib.Path(__file__).parent.resolve(), 'response_sample.json'),
            encoding="UTF-8") as sample_resp_file:
    sample_resp_json = json.load(sample_resp_file)
    sample_resp = afc_resp.AvailableSpectrumInquiryResponseMessage(**sample_resp_json)

  with open(os.path.join(pathlib.Path(__file__).parent.resolve(), 'mask_sample.json'),
       encoding="UTF-8") as sample_mask_file:
    sample_mask_json = json.load(sample_mask_file)
    sample_mask = afc_exp.ExpectedSpectrumInquiryResponseMessage(**sample_mask_json)

  print('Sample matches mask: '
       f'{runner.run_test_response_message(sample_mask, sample_resp, validate_objects=True)}')

if __name__ == '__main__':
  import json
  import logging
  import os
  import pathlib
  main()
