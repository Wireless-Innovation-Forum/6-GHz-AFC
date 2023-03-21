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
"""AFC Spectrum Inquiry Response Validation - SDI Protocol v1.3

Validation functions will attempt to exhaustively test all fields (i.e.,
validation does not stop on the first failure, but will report all
observed failures). Multiple failures may be reported for the same
root cause."""

import math
from datetime import datetime

import available_spectrum_inquiry_response as afc_resp
from interface_common import ResponseCode
import sdi_validator_common as sdi_validate

class InquiryResponseValidator(sdi_validate.SDIValidatorBase):
  """Provides validation functions for AFC Response-specific types"""

  @sdi_validate.common_sdi_validator
  def validate_supplemental_info(self, suppl_info: afc_resp.SupplementalInfo):
    """Validates that a SupplementalInfo object satisfies the SDI spec

    Checks:
      No more than one supplemental info field may be present
      Disallows empty lists for all fields

    Parameters:
      suppl_info (SupplementalInfo): SupplementalInfo to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True
    # Current spec states that SupplementalInfo should only have one non-empty field
    num_active_fields = sum(1 for field_value in vars(suppl_info).values()
                            if field_value is not None)
    if num_active_fields > 1:
      is_valid = False
      self._warning(f'SupplementalInfo has {num_active_fields} non-empty fields; should be 0 or 1')

    # Empty list should not satisfy list[str] requirement
    for field_name in [x for x in vars(suppl_info).keys() if getattr(suppl_info, x) is not None]:
      try:
        if len(getattr(suppl_info, field_name)) < 1:
          is_valid = False
          self._warning(f'SupplementalInfo contains an empty list for {field_name}')
      except TypeError as ex:
        is_valid = False
        self._warning(f'Could not validate length of SupplementalInfo {field_name}: {ex}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_response(self, resp: afc_resp.Response):
    """Validates that a Response object satisfies the SDI spec

    Checks:
      supplementalInfo is valid
      supplementalInfo only contains fields permitted by the response code

    Parameters:
      resp (Response): Response to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True

    if resp.supplementalInfo is not None:
      # supplementalInfo is valid
      is_valid &= self.validate_supplemental_info(resp.supplementalInfo)
      try:
        match ResponseCode.get_raw_value(resp.responseCode):
          case ResponseCode.MISSING_PARAM.value:
            disallowed_params = [x for x in vars(resp.supplementalInfo).keys()
                                 if x != 'missingParams']
          case ResponseCode.INVALID_VALUE.value:
            disallowed_params = [x for x in vars(resp.supplementalInfo).keys()
                                 if x != 'invalidParams']
          case ResponseCode.UNEXPECTED_PARAM.value:
            disallowed_params = [x for x in vars(resp.supplementalInfo).keys()
                                 if x != 'unexpectedParams']
          case _:
            disallowed_params = vars(resp.supplementalInfo).keys()

        # supplementalInfo only contains fields permitted by the response code
        for param in disallowed_params:
          if getattr(resp.supplementalInfo, param, None) is not None:
            is_valid = False
            self._warning(f'Response supplementalInfo contains {param} field '
                          f'for {resp.responseCode} code: {getattr(resp.supplementalInfo, param)}')
      except TypeError as ex:
        is_valid = False
        self._warning(f'Could not get members of supplementalInfo object: {ex}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_frequency_info(self, info: afc_resp.AvailableFrequencyInfo):
    """Validates that an AvailableFrequencyInfo object satisfies the SDI spec

    Checks:
      frequencyRange is valid
      maxPsd is a valid, finite number

    Parameters:
      info (AvailableFrequencyInfo): AvailableFrequencyInfo to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    # frequencyRange is valid
    is_valid = self.validate_frequency_range(info.frequencyRange)

    # maxPsd is a valid, finite number
    try:
      if not math.isfinite(info.maxPsd):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'maxPsd ({info.maxPsd}) must be a single finite numeric value')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_channel_info(self, info: afc_resp.AvailableChannelInfo):
    """Validates that an AvailableChannelInfo object satisfies the SDI spec

    Checks:
      channelCfi and maxEirp must have equal lengths
      All values for channelCfi, maxEirp and globalOperatingClass must be valid, finite numbers

    Parameters:
      info (AvailableChannelInfo): AvailableChannelInfo to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = True
    try:
      # channelCfi and maxEirp must have equal lengths
      if len(info.channelCfi) != len(info.maxEirp):
        is_valid = False
        self._warning(f'Length of channelCfi list ({info.channelCfi}) does '
                      f'not match length of maxEirp list ({info.maxEirp})')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Could not validate lengths of channel and eirp lists: {ex}')

    # All values for channelCfi, maxEirp and globalOperatingClass must be valid, finite numbers
    try:
      if not all(math.isfinite(eirp) for eirp in info.maxEirp):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'maxEirp ({info.maxEirp}) must be a list of finite numeric values')
    try:
      if not all(math.isfinite(channel_cfi) for channel_cfi in info.channelCfi):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'channelCfi ({info.channelCfi}) must be a list of finite numeric values')
    try:
      if not math.isfinite(info.globalOperatingClass):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'globalOperatingClass ({info.globalOperatingClass}) '
                     'must be a finite numeric value')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_spectrum_inquiry_response(self,
        resp: afc_resp.AvailableSpectrumInquiryResponse):
    """Validates that an AvailableSpectrumInquiryResponse object satisfies the SDI spec

    Checks:
      response (code, description, supplemental info) is valid
      Availability info is only included if response code is Success
      Expiration time is included if response code is Success
      At least one availability type is included if response code is Success
      All availability info is valid
      availabilityExpireTime is valid datetime
      vendorExtensions are valid

    Parameters:
      resp (AvailableSpectrumInquiryResponse): AvailableSpectrumInquiryResponse to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    # response (code, description, supplemental info) is valid
    is_valid = self.validate_response(resp.response)

    try:
      if ResponseCode.get_raw_value(resp.response.responseCode) != ResponseCode.SUCCESS.value:
        disallowed_fields = ["availableFrequencyInfo",
                             "availableChannelInfo",
                             "availabilityExpireTime"]
        # Availability info is only included if response code is Success
        for field in disallowed_fields:
          if getattr(resp, field) is not None:
            is_valid = False
            self._warning(f'ResponseCode is not SUCCESS but {field} is provided')

      else:
        # Expiration time is included if response code is Success
        if resp.availabilityExpireTime is None:
          is_valid = False
          self._warning('ResponseCode is SUCCESS but availabilityExpireTime is not provided')

        # At least one availability type is included if response code is Success
        if (resp.availableChannelInfo is None) and (resp.availableFrequencyInfo is None):
          is_valid = False
          self._warning('ResponseCode is SUCCESS but no availability information is provided')
    except AttributeError as ex:
      is_valid = False
      self._warning(f'Could not get response code value: {ex}')

    # All availability info is valid
    if resp.availableFrequencyInfo is not None:
      try:
        is_valid &= all(self.validate_available_frequency_info(x)
                        for x in resp.availableFrequencyInfo)
      except TypeError as ex:
        self._warning(f'Exception caught validating frequency info: {ex}')
        is_valid = False
    if resp.availableChannelInfo is not None:
      try:
        is_valid &= all([self.validate_available_channel_info(x)
                         for x in resp.availableChannelInfo])
      except TypeError as ex:
        self._warning(f'Exception caught validating channel info: {ex}')
        is_valid = False

    # availabilityExpireTime is valid datetime
    if resp.availabilityExpireTime is not None:
      try:
        if resp.availabilityExpireTime[-1] != 'Z':
          raise ValueError()
        # fromisoformat expects no trailing Z character, so strip it
        datetime.fromisoformat(resp.availabilityExpireTime[0:-1])
      except(ValueError, IndexError, TypeError):
        self._warning(f'availabilityExpireTime has invalid format: {resp.availabilityExpireTime}')
        is_valid = False

    # vendor extensions are valid
    is_valid &= self.validate_vendor_extension_list(resp.vendorExtensions)
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_spectrum_inquiry_response_message(self,
        msg: afc_resp.AvailableSpectrumInquiryResponseMessage):
    """Validates that an AvailableSpectrumInquiryResponseMessage object satisfies the SDI spec

    Checks:
      version string is valid
      availableSpectrumInquiryResponses exist and are all valid
      Each AvailableSpectrumInquiryResponse has a unique requestId
      vendorExtensions are valid

    Parameters:
      msg (AvailableSpectrumInquiryResponseMessage): Message to be validated

    Returns:
      True if all checks are satisfied
      False otherwise"""
    is_valid = self.validate_version(msg.version)
    try:
      if len(msg.availableSpectrumInquiryResponses) < 1:
        is_valid = False
        self._warning(f'Length of availableSpectrumInquiryResponses '
                      f'list must be at least 1: {msg.availableSpectrumInquiryResponses}')
      else:
        # availableSpectrumInquiryResponses exist and are all valid
        is_valid &= all([self.validate_available_spectrum_inquiry_response(x)
                        for x in msg.availableSpectrumInquiryResponses])

        # Each AvailableSpectrumInquiryResponse has a unique requestID
        resp_ids = [sub_resp.requestId for sub_resp in msg.availableSpectrumInquiryResponses]
        # [list(set(list_val)) gives all unique values in list]
        if len(resp_ids) != len(list(set(resp_ids))):
          is_valid = False
          self._warning('Response should have no more than one occurrence of any given requestId')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception caught validating responses: {ex}')

    # vendorExtensions are valid
    is_valid &= self.validate_vendor_extension_list(msg.vendorExtensions)
    return is_valid

def main():
  """Demonstrates use of the validator functions"""
  logging.basicConfig()
  logger = logging.getLogger()

  validator = InquiryResponseValidator(logger=logger)

  with open('src/harness/response_sample.json', encoding="UTF-8") as sample_file:
    sample_json = json.load(sample_file)
    sample_conv = afc_resp.AvailableSpectrumInquiryResponseMessage(**sample_json)
    print('Example response is valid: '
         f'{validator.validate_available_spectrum_inquiry_response_message(sample_conv)}')
    sample_conv.availableSpectrumInquiryResponses[0].response.responseCode = 0
    print('Integer can be used instead of ResponseCode enum: '
         f'{validator.validate_available_spectrum_inquiry_response_message(sample_conv)}')

    print('Can validate sub-fields with JSON dict directly: '
         f'{validator.validate_available_spectrum_inquiry_response(sample_json["availableSpectrumInquiryResponses"][0])}')
    print('Can validate root message with JSON dict directly: '
         f'{validator.validate_available_spectrum_inquiry_response_message(sample_json)}')
    sample_conv.availableSpectrumInquiryResponses = []
    empty_list_is_valid = validator.validate_available_spectrum_inquiry_response_message(sample_conv)
    print('^Errors logged to console by default logger config^')
    print(f'Empty response list is not valid: {not empty_list_is_valid}')

if __name__ == '__main__':
  import json
  import logging
  main()
