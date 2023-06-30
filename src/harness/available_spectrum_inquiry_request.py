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

"""Available Spectrum Inquiry Request Definitions - SDI Protocol v1.4"""

import math
from dataclasses import dataclass
from typing import Union
from contextlib import suppress

# Try to import optional geopy module (used for distance and vector endpoint calculations)
try:
  from geopy.distance import great_circle
except ImportError:
  _geopy_available = False
else:
  _geopy_available = True

from interface_common import FrequencyRange, VendorExtension, init_from_dicts

def _geopy_check():
  """Internal wrapper for handling absence of optional geopy module"""
  if not _geopy_available:
    raise ImportError('The "geopy" module is required for this operation.')

@dataclass
class Channels:
  """Channels List for Inquiry Requests
  
  Specifies a global operating class and (optionally) associated channels over which
  availability is requested
  
  Attributes:
    globalOperatingClass: Defines channel center frequency indices and bandwidths
    channelCfi: List of channel frequency indices over which availability is requested
  """
  globalOperatingClass: Union[float, int]
  channelCfi: list[Union[float, int]] = None

@dataclass
class Point:
  """Location Point (Latitude/Longitude pair)
  
  Specifies a geographic point via latitude and longitude
  
  Attributes:
    longitude: Longitude coordinate in decimal degrees (-180 to +180)
    latitude: Latitude coordinate in decimal degrees (-90 to +90)
  """
  longitude: Union[float, int]
  latitude: Union[float, int]

  def distance_to(self, dest: 'Point'):
    """Determines the distance from this point to another point, in meters
    
    Assumes great circle (Haversine) distance
    
    Parameters:
      dest (Point): Target point to determine distance to
    
    Returns:
      Great circle distance in meters between this point and the destination point
      
    Throws:
      ImportError if geopy module is not available
    """
    _geopy_check()
    return great_circle((self.latitude, self.longitude), (dest.latitude, dest.longitude)).meters

  def as_cart(self):
    """Helper function for converting lat/long coordinates to cartesian coordinates
    
    Used in request validator for edge intersection math
    
    Parameters:
      None
    
    Returns:
      Tuple of (x, y, z) coordinates
    """
    return (math.cos(math.radians(self.latitude))*math.cos(math.radians(self.longitude)),
            math.cos(math.radians(self.latitude))*math.sin(math.radians(self.longitude)),
            math.sin(math.radians(self.latitude)))

@dataclass
class Vector:
  """Location Vector
  
  Defines vectors for use with RadialPolygon definition
  
  Attributes:
    length: length of vector, in meters
    angle: direction of vector in decimal degrees, measured clockwise from True North
  """
  length: Union[float, int]
  angle: Union[float, int]

  def endpoint_from(self, src: Point) -> Point:
    """Helper function for computing the endpoint of a vector, when applied to a start point
    
    Assumes great circle (Haversine) distance

    Parameters:
      src (Point): Start point of vector
      
    Returns:
      New Point reached by traveling along the vector, starting at src
      
    Throws:
      ImportError if geopy module is not available
    """
    _geopy_check()
    geopy_dist = great_circle(meters=self.length)
    geopy_pt = geopy_dist.destination((src.latitude, src.longitude), bearing=self.angle)
    return Point(longitude=geopy_pt.longitude, latitude=geopy_pt.latitude)

@dataclass
class Elevation:
  """Device Elevation Info
  
  Defines a device's height and uncertainty
  
  Attributes:
    height: Height of device, in meters
    heightType: Reference level of height value. Allowed values are:
                "AGL": Above Ground Level
                "AMSL": Above Mean Seal Level
    verticalUncertainty: Uncertainty in height value, in meters (integer only)
    """
  height: Union[float, int]
  heightType: str
  verticalUncertainty: int

@dataclass
class RadialPolygon:
  """Radial Polygon Device Location Info
  
  Defines a device's location and uncertainty area as a radial polygon
  
  Attributes:
    center: Center point of radial polygon
    outerBoundary: List of vectors that, when applied to center, define the location area
  """
  center: Point
  outerBoundary: list[Vector]

  def __post_init__(self):
    with suppress(TypeError):
      self.center = Point(**self.center)
    with suppress(TypeError):
      self.outerBoundary = init_from_dicts(self.outerBoundary, Vector)

@dataclass
class LinearPolygon:
  """Linear Polygon Device Location Info
  
  Defines a device's location and uncertainty area as a linear polygon
  
  Attributes:
    outerBoundary: List of vertices defining the location area
  """
  outerBoundary: list[Point]

  def __post_init__(self):
    with suppress(TypeError):
      self.outerBoundary = init_from_dicts(self.outerBoundary, Point)

  @classmethod
  def from_radial(cls, src: RadialPolygon):
    """Creates a new LinearPolygon object from an existing RadialPolygon object

    Computes outerBoundary vertices from radialPolygon's center + vertex vectors

    Requires:
      geopy module for coordinate math

    Parameters:
      src (RadialPolygon): Source RadialPolygon used to create the new LinearPolygon

    Returns:
      New LinearPolygon with same boundary area as source RadialPolygon

    Throws:
      ImportError if geopy module is not available
    """
    return cls(outerBoundary=[vec.endpoint_from(src.center) for vec in src.outerBoundary])

@dataclass
class Ellipse:
  """Elliptical Device location info
  
  Defines a device's location and uncertainty area as an ellipse
  
  Attributes:
    center: Center point of the ellipse area
    majorAxis: Major axis of the ellipse area, in meters
    minorAxis: Minor axis of the ellipse area, in meters
    orientation: Orientation of the major axis in decimal degrees, measured clockwise from
                 True North
  """
  center: Point
  majorAxis: int
  minorAxis: int
  orientation: Union[float, int]

  def __post_init__(self):
    with suppress(TypeError):
      self.center = Point(**self.center)

@dataclass
class Location:
  """Device Location Info
  
  Specifies the location of a requesting device

  Attributes:
    elevation: Height of the device
    ellipse: Location area of the device, defined as an ellipse
    linearPolygon: Location area of the device, defined as a linear polygon
    radialPolygon: Location area of the device, defined as a radial polygon
    indoorDeployment: Indicates whether a device is indoors or outdoors
                      (0: unknown, 1: indoor, 2: outdoor)
  """
  elevation: Elevation
  ellipse: Ellipse = None
  linearPolygon: LinearPolygon = None
  radialPolygon: RadialPolygon = None
  indoorDeployment: int = None

  def __post_init__(self):
    with suppress(TypeError):
      self.elevation = Elevation(**self.elevation)
    if self.ellipse is not None:
      with suppress(TypeError):
        self.ellipse = Ellipse(**self.ellipse)
    if self.linearPolygon is not None:
      with suppress(TypeError):
        self.linearPolygon = LinearPolygon(**self.linearPolygon)
    if self.radialPolygon is not None:
      with suppress(TypeError):
        self.radialPolygon = RadialPolygon(**self.radialPolygon)

@dataclass
class CertificationId:
  """Device Certification ID
  
  Contains information about a device's certification info
  
  Attributes:
    rulsesetId: Identifier of the regulatory rules corresponding to this cert ID
    id: Certification ID of the device
  """
  rulesetId: str
  id: str

@dataclass
class DeviceDescriptor:
  """Device Descriptor
  
  Contains information about a device requesting spectrum availability
  
  Attributes:
    serialNumber: Device serial number
    certificationId: List of certification IDs and rulesets associated with the device
  """
  serialNumber: str
  certificationId: list[CertificationId]

  def __post_init__(self):
    with suppress(TypeError):
      self.certificationId = init_from_dicts(self.certificationId, CertificationId)

@dataclass
class AvailableSpectrumInquiryRequest:
  """Available Spectrum Inquiry Request

  Contains a request for spectrum availability info

  Attributes:
    requestId: Unique ID for the availability request
    deviceDescriptor: Information about the device requesting spectrum availability
    location: Information about the location of the requesting device
    inquiredFrequencyRange: List of frequency ranges over which availability is requested
    inquiredChannels: List of channels over which availability is requested
    minDesiredPower: Minimum desired power in dBm, below which an AFC shall not return available
                     channels
    vendorExtensions: Optional vendor extensions
  """
  requestId: str
  deviceDescriptor: DeviceDescriptor
  location: Location
  inquiredFrequencyRange: list[FrequencyRange] = None
  inquiredChannels: list[Channels] = None
  minDesiredPower: Union[float, int] = None
  vendorExtensions: list[VendorExtension] = None

  def __post_init__(self):
    if isinstance(self.deviceDescriptor, dict):
      with suppress(TypeError):
        self.deviceDescriptor = DeviceDescriptor(**self.deviceDescriptor)
    if isinstance(self.location, dict):
      with suppress(TypeError):
        self.location = Location(**self.location)
    if self.inquiredFrequencyRange is not None:
      with suppress(TypeError):
        self.inquiredFrequencyRange = init_from_dicts(self.inquiredFrequencyRange,
                                                      FrequencyRange)
    if self.inquiredChannels is not None:
      with suppress(TypeError):
        self.inquiredChannels = init_from_dicts(self.inquiredChannels, Channels)
    if self.vendorExtensions is not None:
      with suppress(TypeError):
        self.vendorExtensions = init_from_dicts(self.vendorExtensions, VendorExtension)

@dataclass
class AvailableSpectrumInquiryRequestMessage:
  """Top-level Spectrum Inquiry Request Message

  Contains one or more spectrum inquiries

  Attributes:
    version: version number of the inquiry request
    availableSpectrumInquiryRequests: list of inquiry requests
    vendorExtensions: Optional vendor extensions
  """
  version: str
  availableSpectrumInquiryRequests: list[AvailableSpectrumInquiryRequest]
  vendorExtensions: list[VendorExtension] = None

  def __post_init__(self):
    with suppress(TypeError):
      self.availableSpectrumInquiryRequests = init_from_dicts(
                                              self.availableSpectrumInquiryRequests,
                                              AvailableSpectrumInquiryRequest)

    if self.vendorExtensions is not None:
      with suppress(TypeError):
        self.vendorExtensions = init_from_dicts(self.vendorExtensions, VendorExtension)

def main():
  """Demonstrates loading and printing inquiry requests"""
  with open(os.path.join(pathlib.Path(__file__).parent.resolve(),
                         "sample_files", "request_sample.json"),
            encoding="UTF-8") as sample_file:
    sample_json = json.load(sample_file)
    sample_conv = AvailableSpectrumInquiryRequestMessage(**sample_json)
    sample_conv2 = AvailableSpectrumInquiryRequestMessage(**sample_json)

    print(f"Messages from same source report equal: {sample_conv == sample_conv2}")
    print(f"Can recreate object from repr: {eval(repr(sample_conv)) == sample_conv}")
    print(sample_conv)

if __name__ == '__main__':
  import json
  import os
  import pathlib
  main()
