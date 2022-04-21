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

# This file contains python instantiation of the objects that are defined in
# the WFA AFC System to AFC Device interface.
#
# All parameters that are required per the spec do not have default values,
# whereas parameters that are optional have a default value of None. Values
# that are conditionally required have default values of None.

class Channels:
  def __init__(self, globalOperatingClass, channelCfi=None):
    self.globalOperatingClass = globalOperatingClass
    self.channelCfi = channelCfi
      
class FrequencyRange:
  def __init__(self, lowFrequency, highFrequency):
    self.lowFrequency = lowFrequency
    self.highFrequency = highFrequency
    
class Vector:
  def __init__(self, length, angle):
    self.length = length
    self.angle = angle

class Point:
  def __init__(self, longitude, latitude):
    self.longitude = longitude
    self.latitude = latitude
    
class Elevation:
  def __init__(self, height, heightType, verticalUncertainty):
    self.height = height
    self.heightType = heightType
    self.verticalUncertainty = verticalUncertainty

class RadialPolygon:
  def __init__(self, center, outerBoundary):
    self.center = center
    self.outerBoundary = outerBoundary

class LinearPolygon:
  def __init__(self, outerBoundary):
    self.outerBoundary = outerBoundary

class Ellipse:
  def __init__(self, center, majorAxis, minorAxis, orientation):
    self.center = center
    self.majorAxis = majorAxis
    self.minorAxis = minorAxis
    self.orientation = orientation

class Location:
  def __init__(self, elevation, ellipse=None, linearPolygon=None,
               radialPolygon=None, indoorDeployment=None):
    self.elevation = elevation
    self.ellipse = ellipse
    self.linearPolygon = linearPolygon
    self.radialPolygon = radialPolygon
    self.indoorDeployment = indoorDeployment

class CertificationId:
  def __init__(self, nra, _id):
    self.nra = nra
    self.id = _id

class DeviceDescriptor:
  def __init__(self, serialNumber, certificationId, rulesetIds):
    self.serialNumber = serialNumber
    self.certificationId = certificationId
    self.rulesetIds = rulesetIds

class AvailableSpectrumInquiryRequest:
  def __init__(self, requestId, deviceDescriptor, location,
               inquiredFrequencyRange=None, inquiredChannels=None,
               minDesiredPower=None, vendorExtensions=None):
    self.requestId = requestId
    self.deviceDescriptor = deviceDescriptor
    self.location = location
    self.inquiredFrequencyRange = inquiredFrequencyRange
    self.inquiredChannels = inquiredChannels
    self.minDesiredPower = minDesiredPower
    self.vendorExtensions = vendorExtensions

class AvailableSpectrumInquiryRequestMessage:
  def __init__(self, version, availableSpectrumInquiryRequests,
               vendorExtensions=None):
    self.version = version
    self.availableSpectrumInquiryRequests = \
         availableSpectrumInquiryRequests
    self.vendorExtensions = vendorExtensions
