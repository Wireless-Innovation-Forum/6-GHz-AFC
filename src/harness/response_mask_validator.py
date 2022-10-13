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
"""AFC Spectrum Inquiry Expected Response Validation - SDI v1.3

Validation functions will exhaustively test all fields (i.e.,
validation does not stop on the first failure, but will report all
observed failures. Multiple failures may be reported for the same
root cause."""

from math import isnan
import expected_inquiry_response as afc_exp
import available_spectrum_inquiry_response as afc_resp
from response_validator import InquiryResponseValidator
import sdi_validator_common as sdi_validate

class ResponseMaskValidator(sdi_validate.SDIValidatorBase):
  """Provides validation functions for AFC Response-specific types"""

  def __init__(self, *args, **kwargs):
    super().__init__(args, kwargs)

    log_copy = self._log_file if self._log_file is not None else self._logger
    self._resp_validator = InquiryResponseValidator(logger=log_copy, echo_log=self.echo_log,
                                                    append_level=self.append_msg_level)

  @sdi_validate.common_sdi_validator
  def validate_expected_power_range(self, pow_range: afc_exp.ExpectedPowerRange):
    """Validates that an ExpectedPowerRange object satisfies the test harness spec

    Checks:
      Values must satisfy lowerBound <= nominalValue <= upperBound
      Values cannot be NaN

    Parameters:
      pow_range (ExpectedPowerRange): ExpectedPowerRange to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True

    try:
      for field_name, _ in pow_range.__dataclass_fields__.items():
        field_value = getattr(pow_range, field_name)
        if field_value is not None and isnan(field_value):
          is_valid = False
          self._warning(f'Value for {field_name} cannot be NaN')

      if pow_range.lowerBound is not None and pow_range.lowerBound > pow_range.upperBound:
        is_valid = False
        self._warning(f'Lower bound of power range ({pow_range.lowerBound}) must be less than '
                      f'or equal to upper bound ({pow_range.upperBound})')
      if pow_range.nominalValue is not None and pow_range.nominalValue > pow_range.upperBound:
        is_valid = False
        self._warning(f'Nominal value of power range ({pow_range.nominalValue}) must be less than '
                      f'or equal to upper bound ({pow_range.upperBound})')
      if (pow_range.nominalValue is not None and pow_range.lowerBound is not None
          and pow_range.lowerBound > pow_range.nominalValue):
        is_valid = False
        self._warning(f'Lower bound of power range ({pow_range.lowerBound}) must be less than '
                      f'or equal to nominal value ({pow_range.nominalValue})')
    except TypeError:
      is_valid = False
      self._warning(f'Value for {field_name} must be a single, comparable value, '
                    f'but got: {field_value}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_expected_frequency_info(self, info: afc_exp.ExpectedAvailableFrequencyInfo):
    """Validates that an ExpectedAvailableFrequencyInfo object satisfies the test harness spec

    Checks:
      FrequencyInfo is valid
      maxPsd must be a valid ExpectedPowerRange

    Parameters:
      info (ExpectedAvailableFrequencyInfo): ExpectedAvailableFrequencyInfo to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = self.validate_frequency_range(info.frequencyRange)
    is_valid &= self.validate_expected_power_range(info.maxPsd)
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_expected_channel_info(self, info: afc_exp.ExpectedAvailableChannelInfo):
    """Validates that an ExpectedAvailableChannelInfo object satisfies the test harness spec

    Checks:
      Channel info data satisfies requirements for AvailableChannelInfo
      All values for maxEirp are valid ExpectedPowerRanges
      No duplicate channelCfis

    Parameters:
      info (ExpectedAvailableChannelInfo): ExpectedAvailableChannelInfo to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True

    # Transfer channel info (minus eirp data) to AvailableChannelClass for validation
    try:
      mock_eirp = [0] * len(info.maxEirp)
    except TypeError as ex:
      is_valid = False
      self._warning(f'Exception caught getting length of maxEirp ({info.maxEirp}): {ex}')
      # Fall back to using channelCfi for mock analysis (channelCfis should be "valid" maxEirps)
      mock_eirp = info.channelCfi

    mock_available_info = afc_resp.AvailableChannelInfo(
                            globalOperatingClass=info.globalOperatingClass,
                            channelCfi=info.channelCfi,
                            maxEirp=mock_eirp)

    # Channel info data satisfies requirements for AvailableChannelInfo
    is_valid &= self._resp_validator.validate_available_channel_info(mock_available_info)

    # All values for maxEirp are valid ExpectedPowerRanges
    try:
      is_valid &= all([self.validate_expected_power_range(eirp) for eirp in info.maxEirp])
    except TypeError as ex:
      is_valid = False
      self._warning(f'Exception caught validating power ranges: {ex}')

    # No duplicate channelCfis
    # [list(set(list_val)) gives all unique values in list]
    try:
      if len(info.channelCfi) != len(list(set(info.channelCfi))):
        is_valid = False
        self._warning('ExpectedAvailableChannelInfo contains duplicate '
                    f'channelCFIs: {info.channelCfi}')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Exception caught while looking for duplicate channelCfis: {ex}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_expected_spectrum_inquiry_response(self,
        exp: afc_exp.ExpectedSpectrumInquiryResponse):
    """Validates that an ExpectedSpectrumInquiryResponse mask satisfies the test harness spec

    Checks:
      vendorExtensions are valid
      At least one expectedResponseCode is given
      expectedResponseCodes are valid
      If SUCCESS is expected response code:
        No other codes are expected
        At least one of expectedChannelInfo and expectedFrequencyInfo is given
      If SUCCESS is not expected response code:
        No availability info is given
      If expectedChannelInfo is provided:
        Each ExpectedAvailableChannelInfo object is valid
        No ExpectedAvailableChannelInfos with same globalOperatingClass
      If expectedFrequencyInfo is provided:
        Each ExpectedAvailableFrequencyInfo object is valid
        No ExpectedAvailableFrequencyInfo have overlapping frequency ranges

    Parameters:
      exp (ExpectedSpectrumInquiryResponse): Mask to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    # vendorExtensions are valid
    is_valid = self.validate_vendor_extension_list(exp.vendorExtensions)

    # At least one expectedResponseCode is given
    try:
      if len(exp.expectedResponseCodes) < 1:
        is_valid = False
        self._warning('Length of expectedResponseCodes list must be at least 1: '
                      f'{exp.expectedResponseCodes}')
      else:
        # expectedResponseCodes are valid
        is_valid &= all([afc_exp.afc_resp.ResponseCode.get_raw_value(code) is not None
                        for code in exp.expectedResponseCodes])

        # If SUCCESS is expected response code:
        if any(afc_exp.afc_resp.ResponseCode.get_raw_value(code) ==
              afc_exp.afc_resp.ResponseCode.SUCCESS.value for code in exp.expectedResponseCodes):
          # No other codes are expected
          if len(exp.expectedResponseCodes) > 1:
            is_valid = False
            self._warning('Cannot expect SUCCESS and other response codes in the same message')

          # At least one of expectedChannelInfo and expectedFrequencyInfo is given
          if exp.expectedChannelInfo is None and exp.expectedFrequencyInfo is None:
            is_valid = False
            self._warning('Expected response is SUCCESS but no availability info is provided')

        # If SUCCESS is not expected response code:
        else:
          # No availability info is given
          disallowed_fields = ["expectedFrequencyInfo", "expectedChannelInfo"]
          for field in disallowed_fields:
            if getattr(exp, field) is not None:
              is_valid = False
              self._warning(f'SUCCESS code is not expected, but mask expects data in {field}')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Exception caught validating expectedResponseCodes: {ex}')

    # If expectedChannelInfo is provided:
    if exp.expectedChannelInfo is not None:
      # Each ExpectedAvailableChannelInfo object is valid
      try:
        is_valid &= all([self.validate_expected_channel_info(x) for x in exp.expectedChannelInfo])
      except TypeError as ex:
        is_valid = False
        self._warning(f'Exception caught validating expected channel info: {ex}')

      # No ExpectedAvailableChannelInfos with same globalOperatingClass
      try:
        all_gocs = [getattr(info, "globalOperatingClass") for info in exp.expectedChannelInfo]
        # [list(set(list_val)) gives all unique values in list]
        if len(all_gocs) != len(list(set(all_gocs))):
          is_valid = False
          self._warning('Response mask should have no more than one occurrence of any given '
                        'globalOperatingClass value')
      except (AttributeError, TypeError) as ex:
        is_valid = False
        self._warning(f'Exception caught checking for non-repeating globalOperatingClass: {ex}')

      # If expectedFrequencyInfo is provided:
      if exp.expectedFrequencyInfo is not None:
        # Each ExpectedAvailableFrequencyInfo object is valid
        try:
          is_valid &= all([self.validate_expected_frequency_info(x)
                           for x in exp.expectedFrequencyInfo])
        except TypeError as ex:
          is_valid = False
          self._warning(f'Exception caught validating expected frequency info: {ex}')

        # No ExpectedAvailableFrequencyInfo have overlapping frequency ranges
        try:
          for idx1, info1 in enumerate(exp.expectedFrequencyInfo):
            for info2 in exp.expectedFrequencyInfo[idx1+1:]:
              if info1.frequencyRange.overlaps(info2.frequencyRange):
                is_valid = False
                self._warning(f'Frequency info  (low: {info1.frequencyRange.lowFrequency}, '
                              f'high: {info1.frequencyRange.highFrequency}) overlaps range '
                              f'(low: {info2.frequencyRange.lowFrequency}, '
                              f'high: {info2.frequencyRange.highFrequency})')
        except (TypeError, AttributeError) as ex:
          is_valid = False
          self._warning(f'Exception caught checking for overlapping expected frequency info: {ex}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_expected_spectrum_inquiry_response_message(self,
        exp: afc_exp.ExpectedSpectrumInquiryResponseMessage):
    """Validates that an ExpectedSpectrumInquiryResponseMessage satisfies the test harness spec

    Checks:
      Version string is valid
      expectedSpectrumInquiryResponses exist and are all valid
      Each ExpectedSpectrumInquiryResponse has a unique requestID
      vendorExtensions are all valid

    Parameters:
      exp (ExpectedSpectrumInquiryResponseMessage): Mask to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""

    # Version string is valid
    is_valid = self.validate_version(exp.version)
    # expectedSpectrumInquiryResponses exist
    try:
      if len(exp.expectedSpectrumInquiryResponses) < 1:
        is_valid = False
        self._warning(f'Length of expectedSpectrumInquiryResponses '
                      f'list must be at least 1: {exp.expectedSpectrumInquiryResponses}')
      else:
        # All expectedSpectrumInquiryResponse are valid
        is_valid &= all([self.validate_expected_spectrum_inquiry_response(x)
                        for x in exp.expectedSpectrumInquiryResponses])

        # Each ExpectedSpectrumInquiryResponse has a unique requestID
        exp_ids = [sub_exp.requestId for sub_exp in exp.expectedSpectrumInquiryResponses]
        # [list(set(list_val)) gives all unique values in list]
        if len(exp_ids) != len(list(set(exp_ids))):
          is_valid = False
          self._warning('Response mask should have no more than one occurrence of any given '
                        'requestId')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception caught validating expected responses: {ex}')

    # vendorExtensions are all valid
    is_valid &= self.validate_vendor_extension_list(exp.vendorExtensions)
    return is_valid

def main():
  """Demonstrates use of the validator functions"""
  logging.basicConfig()
  logger = logging.getLogger()

  validator = ResponseMaskValidator(logger=logger)

  with open('src/harness/mask_sample.json', encoding='UTF-8') as sample_file:
    mask_json = json.load(sample_file)
    mask_obj = afc_exp.ExpectedSpectrumInquiryResponseMessage(**mask_json)

  print('Example mask is valid: '
       f'{validator.validate_expected_spectrum_inquiry_response_message(mask_obj)}')


if __name__ == '__main__':
  import json
  import logging
  main()
