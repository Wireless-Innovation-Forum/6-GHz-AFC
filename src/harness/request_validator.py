#    Copyright 2022 SAS Project Authors. All Rights Reserved.
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

# Validates a text file containing a spectrum inquiry request in the WFA
# standard format. Checks:
#
#   File is parsable as json text
#   Valid interface version
#   The existence of a readable version all required elements
#   Each input data value is of the proper type
#   Each requestId (if more than one) is unique within the message
#
# Errors are logged to a file and echoed to the screen.
#
# Vendor extensions are not checked.
#
# TODO:
#   linearPolygon_is_valid
#   radialPolygon_is_valid

import datetime
import inspect
import json
import os

DEBUG = False
requestIds = []


def availableSpectrumInquiryRequestMessage_is_valid(request, log_file=''):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  if log_file != '':
    f = open(log_file, 'a')
    # f.write(str(datetime.datetime.now()) + '\n')
    f.close()

  is_valid = True

  if item_is_readable(request, 'version', log_file):
    if not version_is_valid(request['version'], log_file):
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(request, 'availableSpectrumInquiryRequests', log_file):
    if not availableSpectrumInquiryRequests_is_valid(
      request['availableSpectrumInquiryRequests'], log_file):
      is_valid = False
  else:
    is_valid = False
  
  return is_valid

  
def availableSpectrumInquiryRequests_is_valid(request, log_file=''):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  global requestIds
  
  is_valid = True

  number_of_requests = 0
  
  for availableSpectrumInquiryRequest in request:

    number_of_requests += 1
    if item_is_readable(availableSpectrumInquiryRequest, 'requestId', log_file):
      if not requestId_is_valid(availableSpectrumInquiryRequest['requestId'],
                                log_file):
        is_valid = False
      else:
        if availableSpectrumInquiryRequest['requestId'] not in requestIds:
          requestIds.append(availableSpectrumInquiryRequest['requestId'])
        else:
          log_message = '\nrequestId is not unique: ' + \
                      availableSpectrumInquiryRequest['requestId'] + '\n'
          log(log_message, log_file)
          is_valid = False
    else:
      is_valid = False

    if item_is_readable(availableSpectrumInquiryRequest, 'deviceDescriptor',
                        log_file):
      if not deviceDescriptor_is_valid(availableSpectrumInquiryRequest['deviceDescriptor'],
                                       log_file):
        is_valid = False
    else:
      is_valid = False

    if item_is_readable(availableSpectrumInquiryRequest, 'location', log_file):
      if not location_is_valid(availableSpectrumInquiryRequest['location'],
                               log_file):
        is_valid = False

    valid_inquiry_present = False
    if item_is_readable(availableSpectrumInquiryRequest,
                        'inquiredFrequencyRange', print_to_stdout = False):
      if len(availableSpectrumInquiryRequest['inquiredFrequencyRange']) > 0:
        valid_inquiry_present = True
      if not inquiredFrequencyRange_is_valid(availableSpectrumInquiryRequest['inquiredFrequencyRange'],
                                             log_file):
        is_valid = False

    if item_is_readable(availableSpectrumInquiryRequest,
                        'inquiredChannels', print_to_stdout=False):
      if len(availableSpectrumInquiryRequest['inquiredChannels']) > 0:
        valid_inquiry_present = True
      if not inquiredChannels_is_valid(availableSpectrumInquiryRequest['inquiredChannels'],
                                       log_file):
        is_valid = False

    if not valid_inquiry_present:
      log_message = '\nNeither frequency- nor channel-based inquiry is present\n'
      log(log_message, log_file)
      is_valid = False

    if item_is_readable(availableSpectrumInquiryRequest, 'minDesiredPower',
                        print_to_stdout = False):
      if type(availableSpectrumInquiryRequest['minDesiredPower']) not in [int, float]:
        is_valid = False

  return is_valid


def certificationId_is_valid(certificationId, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  allowed_nras = ['FCC']
  
  is_valid = True

  if not item_is_readable(certificationId, 'nra', log_file):
    is_valid = False
  else:
    if not type_is_correct(certificationId['nra'], 'nra', 'str', log_file):
      is_valid = False
    else:
      if certificationId['nra'] not in allowed_nras:
        is_valid = False
  if not item_is_readable(certificationId, 'id', log_file):
    is_valid = False
  else:
    if not type_is_correct(certificationId['id'], 'id', 'str', log_file):
      is_valid = False

  return is_valid


def certificationIds_is_valid(certificationIds, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True
  
  if not type_is_correct(certificationIds, 'certificationId', 'list', log_file):
    is_valid = False
  else:
    for certificationId in certificationIds:
      if not certificationId_is_valid(certificationId, log_file):
        is_valid = False
  
  return is_valid


def channels_is_valid(channels, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  if item_is_readable(channels, 'globalOperatingClass', log_file):
    if type(channels['globalOperatingClass']) not in [int, float]:
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(channels, 'channelCfi', print_to_stdout = False):
    if type_is_correct(channels['channelCfi'], 'channelCfi', 'list', log_file):
      for channelCfi in channels['channelCfi']:
        if type(channelCfi) not in [int, float]:
          is_valid = False
    else:
      is_valid = False

  return is_valid


def deviceDescriptor_is_valid(deviceDescriptor, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  if item_is_readable (deviceDescriptor, 'serialNumber', log_file):
    if not serialNumber_is_valid(deviceDescriptor['serialNumber'], log_file):
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(deviceDescriptor, 'certificationId', log_file):
    if not certificationIds_is_valid(deviceDescriptor['certificationId'],
                                    log_file):
      is_valid = False
  else:
      is_valid = False

  if item_is_readable(deviceDescriptor, 'rulesetIds', log_file):
    if not rulesetIds_is_valid(deviceDescriptor['rulesetIds'], log_file):
      is_valid = False
  else:
    is_valid = False
    
  return is_valid


def elevation_is_valid(elevation, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  is_valid = True

  allowed_heightTypes = ['AGL', 'AMSL']
  
  if item_is_readable(elevation, 'height', log_file):
    if not type_is_correct(elevation['height'], 'height', 'number', log_file):
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(elevation, 'heightType', log_file):
    if type_is_correct(elevation['heightType'], 'heightType', 'str', log_file):
      if elevation['heightType'] not in allowed_heightTypes:
        log_message = '\nInvalid heightType: ' + str(elevation['heightType'])\
                      + '\n'
        log(log_message, log_file)
        is_valid = False
    else:
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(elevation, 'verticalUncertainty', log_file):
    if not type_is_correct(elevation['verticalUncertainty'],
                           'verticalUncertainty', 'int', log_file):
      is_valid = False
  else:
    is_valid = False

  return is_valid


def ellipse_is_valid(ellipse, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  is_valid = True

  if item_is_readable(ellipse, 'center', log_file):
    if not point_is_valid(ellipse['center'], log_file):
      is_valid = False

  if item_is_readable(ellipse, 'majorAxis', log_file):
    if not type_is_correct(ellipse['majorAxis'], 'majorAxis', 'int', log_file):
      is_valid = False
    elif ellipse['majorAxis'] < 0:
      log_message = '\nmajorAxis must be a positive integer: ' + \
                    str(majorAxis) + '\n'
      log(log_message, log_file)
      is_valid = False

  if item_is_readable(ellipse, 'minorAxis', log_file):
    if not type_is_correct(ellipse['minorAxis'], 'minorAxis', 'int', log_file):
      is_valid = False
    elif ellipse['minorAxis'] < 0:
      log_message = '\nminorAxis must be a positive integer: ' + \
                    str(minorAxis) + '\n'
      log(log_message, log_file)
      is_valid = False

  if item_is_readable(ellipse, 'orientation', log_file):
    if not type_is_correct(ellipse['orientation'], 'orientation', 'float',
                           log_file):
      is_valid = False
    elif ellipse['orientation'] < 0 or ellipse['orientation'] > 180:
      log_message = '\norientation value is outside of 0-180: ' + \
                    str(orientation) + '\n'
      log(log_message, log_file)

    return is_valid


def frequencyRange_is_valid(frequencyRange, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  if item_is_readable(frequencyRange, 'lowFrequency', log_file):
    if not type_is_correct(frequencyRange['lowFrequency'], 'lowFrequency', 'int', log_file):
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(frequencyRange, 'highFrequency', log_file):
    if not type_is_correct(frequencyRange['highFrequency'], 'highFrequency', 'int', log_file):
      is_valid = False
  else:
    is_valid = False

  return is_valid


def inquiredChannels_is_valid(inquiredChannels, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  if type_is_correct(inquiredChannels, 'inquiredChannels', 'list', log_file):
    for channels in inquiredChannels:
      if not channels_is_valid(channels, log_file):
        is_valid = False
    if len(inquiredChannels) == 0:
      log_message = '\ninquiredChannels is present but array is empty\n'
      log(log_message, log_file)
      is_valid = False
  else:
    is_valid = False

  return is_valid


def inquiredFrequencyRange_is_valid(inquiredFrequencyRange, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  if type_is_correct(inquiredFrequencyRange, 'inquiredFrequencyRange', 'list', log_file):
    for frequencyRange in inquiredFrequencyRange:
      if not frequencyRange_is_valid(frequencyRange, log_file):
        is_valid = False
    if len(inquiredFrequencyRange) == 0:
      log_message = '\ninquiredFrequencyRange is present but array is empty\n'
      log(log_message, log_file)
      is_valid = False
  else:
    is_valid = False
    
  return is_valid


def item_is_readable(request, item, log_file='', print_to_stdout=True):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True
  
  try:
    temp = request[item]
  except:
    log_message = item + ' is missing or otherwise unreadable\n'
    log(log_message, log_file, print_to_stdout)
    return False

  return is_valid


def linearPolygon_is_valid(linearPolygon, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  # TODO: Write this
  is_valid = True

  return is_valid


def location_is_valid(location, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  is_valid = True

  # Exactly one of ellipse, linearPolygon, or radialPolygon must be present
  # and valid
  num_location_types = 0

  if item_is_readable(location, 'ellipse', print_to_stdout=False):
    num_location_types += 1
    if not ellipse_is_valid(location['ellipse'], log_file):
      is_valid = False

  if item_is_readable(location, 'linearPolygon', print_to_stdout=False):
    num_location_types += 1
    if not linearPolygon_is_valid(location['linearPolyon'], log_file):
      is_valid = False

  if item_is_readable(location, 'radialPoolygon', print_to_stdout=False):
    num_location_types += 1
    if not radialPolygon_is_valid(location['ellipse'], log_file):
      is_valid = False

  if num_location_types != 1:
    log_message = '\nThe number of location descriptions must be equal to 1. '
    log_message += 'Number found: ' + str(num_location_types) + '\n'
    log(log_message, log_file)
    is_valid = False

  if item_is_readable(location, 'elevation', log_file):
    if not elevation_is_valid(location['elevation'], log_file):
#      print('Elevation not valid') # DEBUG
      is_valid = False
  else:
    is_valid = False

  allowed_indoorDeployments = [0, 1, 2]
  if item_is_readable(location, 'indoorDeployment', log_file):
    if type_is_correct(location['indoorDeployment'], 'indoorDeployment',
                       'int', log_file):
      if location['indoorDeployment'] not in allowed_indoorDeployments:
        is_valid = False
    else:
      is_valid = False
  else:
    is_valid = False
    
  return is_valid


def log(message, log_file='', print_to_stdout=True):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  if log_file != '':
    f = open(log_file, 'a')
    f.write(message)
    f.close()
  if print_to_stdout:
    print(message)
  return


def point_is_valid(point, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  is_valid = True

  if item_is_readable(point, 'longitude', log_file):
    if not type_is_correct(point['longitude'], 'longitude', 'number', log_file):
      is_valid = False
    elif point['longitude'] < -180 or point['longitude'] > 180:
      log_message = '\nlongitude is outside of -180..180: ' + \
                    str(longitude) + '\n'
      log(log_message, log_file)
      is_valid = False
  else:
    is_valid = False

  if item_is_readable(point, 'latitude', log_file):
    if not type_is_correct(point['latitude'], 'latitude', 'number', log_file):
      is_valid = False
    elif point['latitude'] < -90 or point['latitude'] > 90:
      log_message = '\nlatitude is outside of -90..90: ' + \
                    str(latitude) + '\n'
      log(log_message, log_file)
      is_valid = False
  else:
    is_valid = False
  
  return is_valid


def radialPolygon_is_valid(radialPolygon, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  # TODO: Write this
  is_valid = True

  return is_valid


def requestId_is_valid(requestId, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  if not type_is_correct(requestId, 'requestId', 'str', log_file):
    return False
  else:
    return True


def rulesetIds_is_valid(rulesetIds, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  is_valid = True

  valid_rulesetIds = ['US_47_CFR_PART_15_SUBPART_E']
  
  if type_is_correct(rulesetIds, 'rulesetIds', 'list', log_file):
    for rulesetId in rulesetIds:
      if rulesetId not in valid_rulesetIds:
        log_message = '\nInvalid rulesetId: ' + str(rulesetId) + '\n'
        log(log_message, log_file)
        is_valid = False
  else:
    is_valid = False

  return is_valid

  
def serialNumber_is_valid(serialNumber, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  if not type_is_correct(serialNumber, 'serialNumber', 'str', log_file):
    return False
  else:
    return True


def type_is_correct(variable, variable_name, expected_type, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
  
  if expected_type == 'str':
    if type(variable) != str:
      log_message = '\n' + variable_name + ' is not of type string: ' \
                    + str(variable) + '\n'
      log(log_message, log_file)
      return False
    else:
      return True
  elif expected_type == 'int':
    if type(variable) != int:
      log_message = '\n' + variable_name + ' is not of type int: ' \
                    + str(variable) + '\n'
      log(log_message, log_file)
      return False
    else:
      return True
  elif expected_type == 'float':
    if type(variable) != float:
      log_message = '\n' + variable_name + ' is not of type float: ' \
                    + str(variable) + '\n'
      log(log_message, log_file)
      return False
    else:
      return True
  elif expected_type == 'number':
    if type(variable) not in [int, float]:
      log_message = '\n' + variable_name + ' is not of type number (float or int): ' \
                    + str(variable) + '\n'
      log(log_message, log_file)
      return False
    else:
      return True
  elif expected_type == 'list':
    if type(variable) != list:
      log_message = '\n' + variable_name + ' is not of type list: ' \
                    + str(variable) + '\n'
      log(log_message, log_file)
      return False    
    else:
      return True
  else:
    print(expected_type)
    print('Problem in type_is_correct')
    return False


def version_is_valid(version, log_file):

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)
    
  allowed_versions = ['1.1']

  is_valid = True

  if type_is_correct(version, 'version', 'str', log_file):
    if version not in allowed_versions:
      log_message = '\nVersion not supported.\n'
      log_message += '  Version read from file: ' + version + '\n'
      log_message += '  Supported version(s): ' + str(allowed_versions) + '\n'
      log(log_message, log_file)
      is_valid = False
  else:
    is_valid = False
    
  return is_valid

  
def main():

  if DEBUG:
    print(inspect.currentframe().f_code.co_name)

  global requestIds
  requestIds = []

  in_file = 'AFCS.FSP.3.json'
  log_file = in_file + '_log.txt'

  is_valid = True
  
  if not os.path.exists(in_file):
    log_message = '\nFile does not exist: ' + in_file + '\n'
    log(log_message, log_file)
    is_valid = False

  with open(in_file) as f:
    try:
      request = json.load(f)
    except:
      log_message = '\nFile not parsable as JSON: ' + in_file + '\n'
      log(log_message, log_file)
      is_valid = False
    
  if is_valid:
    if availableSpectrumInquiryRequestMessage_is_valid(request, log_file):
      log_message = 'No errors found in ' + in_file
      log(log_message, log_file)
    else:
      print('\n*** Errors found ***\nPlease see log file: ' + log_file)
  else:
    print('\n*** Errors found ***\nPlease see log file: ' + log_file)


#main()
