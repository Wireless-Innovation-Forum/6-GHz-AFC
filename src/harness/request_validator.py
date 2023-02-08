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

"""AFC Spectrum Inquiry Request Validation - SDI Protocol v1.3

Validates a text file containing a spectrum inquiry request in the WFA
standard format. Checks:

  File is parsable as json text
  Valid interface version
  The existence of a readable version of all required elements
  Each input data value is of the proper type
  Each requestId (if more than one) is unique within the message

Vendor extensions are not checked.

TODO:
  linearPolygon_is_valid
  radialPolygon_is_valid"""

import inspect

import sdi_validator_common as sdi_validate
from interface_common import FrequencyRange

DEBUG = False

class InquiryRequestValidator(sdi_validate.SDIValidatorBase):
  """Provides validation functions for AFC Inquiry-specific types"""

  def validate_available_spectrum_inquiry_response_message(self, request):
    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.item_is_readable(request, 'version'):
      if self.get_as_type(request['version'], str) is not None:
        is_valid &= self.validate_version(request['version'])
      else:
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(request, 'availableSpectrumInquiryRequests'):
      if not self.validate_available_spectrum_inquiry_requests(
                  request['availableSpectrumInquiryRequests']):
        is_valid = False

      request_ids = []
      for request in request['availableSpectrumInquiryRequests']:
        # Check item as optional to prevent double logging error
        # (already logged by validate_requests)
        if self.item_is_readable(request, 'requestId', item_is_required=False):
          request_ids.append(request['requestId'])
      if len(request_ids) != len(list(set(request_ids))):
        is_valid = False
        self._warning('Request message contains duplicate requestIDs. '
                     f'All requestIDs: {request_ids}')
    else:
      is_valid = False

    return is_valid

  def validate_available_spectrum_inquiry_requests(self, request):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    number_of_requests = 0

    for availableSpectrumInquiryRequest in request:

      number_of_requests += 1
      if self.item_is_readable(availableSpectrumInquiryRequest, 'requestId'):
        if not self.validate_request_id(availableSpectrumInquiryRequest['requestId']):
          is_valid = False
      else:
        is_valid = False

      if self.item_is_readable(availableSpectrumInquiryRequest, 'deviceDescriptor'):
        if not self.validate_device_descriptor(availableSpectrumInquiryRequest['deviceDescriptor']):
          is_valid = False
      else:
        is_valid = False

      if self.item_is_readable(availableSpectrumInquiryRequest, 'location'):
        if not self.validate_location(availableSpectrumInquiryRequest['location']):
          is_valid = False
      else:
        is_valid = False

      valid_inquiry_present = False
      if self.item_is_readable(availableSpectrumInquiryRequest,
                          'inquiredFrequencyRange', item_is_required = False):
        if len(availableSpectrumInquiryRequest['inquiredFrequencyRange']) > 0:
          valid_inquiry_present = True
        if not self.validate_inquired_frequency_range(availableSpectrumInquiryRequest['inquiredFrequencyRange']):
          is_valid = False

      if self.item_is_readable(availableSpectrumInquiryRequest,
                          'inquiredChannels', item_is_required=False):
        if len(availableSpectrumInquiryRequest['inquiredChannels']) > 0:
          valid_inquiry_present = True
        if not self.validate_inquired_channels(availableSpectrumInquiryRequest['inquiredChannels']):
          is_valid = False

      if not valid_inquiry_present:
        log_message = 'Neither frequency- nor channel-based inquiry is present'
        self._warning(log_message)
        is_valid = False

      if self.item_is_readable(availableSpectrumInquiryRequest, 'minDesiredPower',
                          item_is_required = False):
        if type(availableSpectrumInquiryRequest['minDesiredPower']) not in [int, float]:
          is_valid = False

    return is_valid

  def validate_certification_id(self, certificationId):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    allowed_nras = ['FCC']

    is_valid = True

    if not self.item_is_readable(certificationId, 'nra'):
      is_valid = False
    else:
      if not self.type_is_correct(certificationId['nra'], 'nra', 'str'):
        is_valid = False
      else:
        if certificationId['nra'] not in allowed_nras:
          is_valid = False
    if not self.item_is_readable(certificationId, 'id'):
      is_valid = False
    else:
      if not self.type_is_correct(certificationId['id'], 'id', 'str'):
        is_valid = False

    return is_valid

  def validate_certification_ids(self, certificationIds):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if not self.type_is_correct(certificationIds, 'certificationId', 'list'):
      is_valid = False
    else:
      for certificationId in certificationIds:
        if not self.validate_certification_id(certificationId):
          is_valid = False

    return is_valid

  def validate_channels(self, channels):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.item_is_readable(channels, 'globalOperatingClass'):
      if type(channels['globalOperatingClass']) not in [int, float]:
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(channels, 'channelCfi', item_is_required = False):
      if self.type_is_correct(channels['channelCfi'], 'channelCfi', 'list'):
        for channelCfi in channels['channelCfi']:
          if type(channelCfi) not in [int, float]:
            is_valid = False
      else:
        is_valid = False

    return is_valid

  def validate_device_descriptor(self, deviceDescriptor):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.item_is_readable(deviceDescriptor, 'serialNumber'):
      if not self.validate_serial_number(deviceDescriptor['serialNumber']):
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(deviceDescriptor, 'certificationId'):
      if not self.validate_certification_ids(deviceDescriptor['certificationId']):
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(deviceDescriptor, 'rulesetIds'):
      if not self.validate_ruleset_ids(deviceDescriptor['rulesetIds']):
        is_valid = False
    else:
      is_valid = False

    return is_valid

  def validate_elevation(self, elevation):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    allowed_heightTypes = ['AGL', 'AMSL']

    if self.item_is_readable(elevation, 'height'):
      if not self.type_is_correct(elevation['height'], 'height', 'number'):
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(elevation, 'heightType'):
      if self.type_is_correct(elevation['heightType'], 'heightType', 'str'):
        if elevation['heightType'] not in allowed_heightTypes:
          log_message = 'Invalid heightType: ' + str(elevation['heightType'])
          self._warning(log_message)
          is_valid = False
      else:
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(elevation, 'verticalUncertainty'):
      if not self.type_is_correct(elevation['verticalUncertainty'], 'verticalUncertainty', 'int'):
        is_valid = False
    else:
      is_valid = False

    return is_valid

  def validate_ellipse(self, ellipse):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if not self.item_is_readable(ellipse, 'center') or not self.validate_point(ellipse['center']):
      is_valid = False

    if self.item_is_readable(ellipse, 'majorAxis'):
      if not self.type_is_correct(ellipse['majorAxis'], 'majorAxis', 'int'):
        is_valid = False
      elif ellipse['majorAxis'] < 0:
        log_message = 'majorAxis must be a positive integer: ' + \
                      str(ellipse['majorAxis'])
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(ellipse, 'minorAxis'):
      if not self.type_is_correct(ellipse['minorAxis'], 'minorAxis', 'int'):
        is_valid = False
      elif ellipse['minorAxis'] < 0:
        log_message = 'minorAxis must be a positive integer: ' + \
                      str(ellipse['minorAxis'])
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(ellipse, 'orientation'):
      if not self.type_is_correct(ellipse['orientation'], 'orientation', 'number'):
        is_valid = False
      elif ellipse['orientation'] < 0 or ellipse['orientation'] > 180:
        log_message = 'orientation value is outside of 0-180: ' + \
                      str(ellipse['orientation'])
        self._warning(log_message)
    else:
      is_valid = False

    return is_valid

  def validate_inquired_channels(self, inquiredChannels):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.type_is_correct(inquiredChannels, 'inquiredChannels', 'list'):
      for channels in inquiredChannels:
        if not self.validate_channels(channels):
          is_valid = False
      if len(inquiredChannels) == 0:
        log_message = 'inquiredChannels is present but array is empty'
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    return is_valid

  def validate_inquired_frequency_range(self, inquiredFrequencyRange):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.type_is_correct(inquiredFrequencyRange, 'inquiredFrequencyRange', 'list'):
      for frequencyRange in inquiredFrequencyRange:
        # Temporary patch to use sdi_validator_common implementation of validate_frequency_range
        if all(self.item_is_readable(frequencyRange, val)
               for val in ['lowFrequency', 'highFrequency']):
          if not self.validate_frequency_range(FrequencyRange(**frequencyRange)):
            is_valid = False
        else:
          is_valid = False
      if len(inquiredFrequencyRange) == 0:
        log_message = 'inquiredFrequencyRange is present but array is empty'
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    return is_valid


  def item_is_readable(self, request, item, item_is_required=True):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    try:
      temp = request[item]
    except:
      if item_is_required:
        log_message = item + ' is missing or otherwise unreadable'
        self._warning(log_message)
      return False

    return is_valid


  def validate_linear_polygon(self, linearPolygon):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    # TODO: Write this
    is_valid = True
    self._warning('Validation of request linearPolygon not yet implemented, presumed valid')

    return is_valid


  def validate_location(self, location):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    # Exactly one of ellipse, linearPolygon, or radialPolygon must be present
    # and valid
    num_location_types = 0

    if self.item_is_readable(location, 'ellipse', item_is_required=False):
      num_location_types += 1
      if not self.validate_ellipse(location['ellipse']):
        is_valid = False

    if self.item_is_readable(location, 'linearPolygon', item_is_required=False):
      num_location_types += 1
      if not self.validate_linear_polygon(location['linearPolygon']):
        is_valid = False

    if self.item_is_readable(location, 'radialPolygon', item_is_required=False):
      num_location_types += 1
      if not self.validate_radial_polygon(location['radialPolygon']):
        is_valid = False

    if num_location_types != 1:
      log_message = 'The number of location descriptions must be equal to 1. '
      log_message += 'Number found: ' + str(num_location_types)
      self._warning(log_message)
      is_valid = False

    if self.item_is_readable(location, 'elevation'):
      if not self.validate_elevation(location['elevation']):
        is_valid = False
        self._warning(f'Elevation field is not valid: {location["elevation"]}')
    else:
      is_valid = False

    allowed_indoorDeployments = [0, 1, 2]
    if self.item_is_readable(location, 'indoorDeployment', item_is_required=False):
      if self.type_is_correct(location['indoorDeployment'], 'indoorDeployment', 'int'):
        if location['indoorDeployment'] not in allowed_indoorDeployments:
          is_valid = False
      else:
        is_valid = False

    return is_valid

  def validate_point(self, point):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    if self.item_is_readable(point, 'longitude'):
      if not self.type_is_correct(point['longitude'], 'longitude', 'number'):
        is_valid = False
      elif point['longitude'] < -180 or point['longitude'] > 180:
        log_message = 'longitude is outside of -180..180: ' + \
                      str(point['longitude'])
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    if self.item_is_readable(point, 'latitude'):
      if not self.type_is_correct(point['latitude'], 'latitude', 'number'):
        is_valid = False
      elif point['latitude'] < -90 or point['latitude'] > 90:
        log_message = 'latitude is outside of -90..90: ' + \
                      str(point['latitude'])
        self._warning(log_message)
        is_valid = False
    else:
      is_valid = False

    return is_valid


  def validate_radial_polygon(self, radialPolygon):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    # TODO: Write this
    is_valid = True
    self._warning('Validation of request radialPolygon not yet implemented, presumed valid')

    return is_valid


  def validate_request_id(self, requestId):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    if not self.type_is_correct(requestId, 'requestId', 'str'):
      return False
    else:
      return True


  def validate_ruleset_ids(self, rulesetIds):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    is_valid = True

    valid_rulesetIds = ['US_47_CFR_PART_15_SUBPART_E']

    if self.type_is_correct(rulesetIds, 'rulesetIds', 'list'):
      for rulesetId in rulesetIds:
        if rulesetId not in valid_rulesetIds:
          log_message = 'Invalid rulesetId: ' + str(rulesetId)
          self._warning(log_message)
          is_valid = False
    else:
      is_valid = False

    return is_valid


  def validate_serial_number(self, serialNumber):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    if not self.type_is_correct(serialNumber, 'serialNumber', 'str'):
      return False
    else:
      return True


  def type_is_correct(self, variable, variable_name, expected_type):

    if DEBUG:
      print(inspect.currentframe().f_code.co_name)

    if expected_type == 'str':
      if type(variable) != str:
        log_message = variable_name + ' is not of type string: ' \
                      + str(variable)
        self._warning(log_message)
        return False
      else:
        return True
    elif expected_type == 'int':
      if type(variable) != int:
        log_message = variable_name + ' is not of type int: ' \
                      + str(variable)
        self._warning(log_message)
        return False
      else:
        return True
    elif expected_type == 'float':
      if type(variable) != float:
        log_message = variable_name + ' is not of type float: ' \
                      + str(variable)
        self._warning(log_message)
        return False
      else:
        return True
    elif expected_type == 'number':
      if type(variable) not in [int, float]:
        log_message = variable_name + ' is not of type number (float or int): ' \
                      + str(variable)
        self._warning(log_message)
        return False
      else:
        return True
    elif expected_type == 'list':
      if type(variable) != list:
        log_message = variable_name + ' is not of type list: ' \
                      + str(variable)
        self._warning(log_message)
        return False
      else:
        return True
    else:
      self._fatal(f'Requested type {expected_type} not supported by '
                   'request_validator.type_is_correct')
      raise ValueError(f'Requested type {expected_type} not supported by '
                        'request_validator.type_is_correct')

def main():

  # Setup logger
  logging.basicConfig()
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  validator = InquiryRequestValidator(logger=logger)

  in_file = 'request_sample.json'
  log_file = in_file + '_log.txt'

  logger.addHandler(logging.FileHandler(log_file, mode='w', encoding='utf-8'))

  is_valid = True

  if not os.path.exists(in_file):
    log_message = 'File does not exist: ' + in_file
    logger.fatal(log_message)
    is_valid = False

  with open(in_file, encoding='utf-8') as f:
    try:
      request = json.load(f)
    except:
      log_message = 'File not parsable as JSON: ' + in_file
      logger.error(log_message)
      is_valid = False

  if is_valid:
    if validator.validate_available_spectrum_inquiry_response_message(request):
      log_message = 'No errors found in ' + in_file
      logger.info(log_message)
    else:
      logger.error('*** Errors found ***\nPlease see log file: ' + log_file)
  else:
    logger.error('*** Errors found ***\nPlease see log file: ' + log_file)

if __name__ == "__main__":
  import logging
  import os
  import json
  main()
