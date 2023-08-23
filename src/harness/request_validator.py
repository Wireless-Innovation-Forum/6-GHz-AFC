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
"""AFC Spectrum Inquiry Request Validation - SDI Protocol v1.4

Validation functions will attempt to exhaustively test all fields (i.e.,
validation does not stop on the first failure, but will report all
observed failures). Multiple failures may be reported for the same
root cause.
"""

import math
import itertools
from dataclasses import dataclass, astuple, field

import available_spectrum_inquiry_request as afc_req
import sdi_validator_common as sdi_validate

@dataclass
class _Edge:
  """Supporting class for edge intersection calculations"""
  vertex1: afc_req.Point
  vertex2: afc_req.Point
  length: float = field(init=False) # Cache edge length to avoid extra distance calcs

  def __post_init__(self):
    # Compute edge length on initialization to reduce number of distance calcs
    self.length = self.vertex1.distance_to(self.vertex2)

  def as_cart(self):
    """Convert a lat/lon edge object to a cartesian edge tuple"""
    return (_CartesianPoint(*self.vertex1.as_cart()), _CartesianPoint(*self.vertex2.as_cart()))

  def contains_point(self, p: afc_req.Point, eps=1e-3):
    """Checks if an edge contains another point
    
    Comparison assumes that, if a point lines on the edge,
    the distance from both vertices to the point will be
    the same as the distance between the vertices
    
    Parameters:
      p (Point): Point used for intersection check
      eps: Allowed tolerance on equality check used to determine intersection (in meters)
    """
    arc_intersect_length = self.vertex1.distance_to(p) + self.vertex2.distance_to(p)
    return math.fabs(self.length - arc_intersect_length) < eps

  def intersects(self, other: '_Edge'):
    """Determines if an edge intersects with another edge
    
    Converts edges to cartesian coordinates, determines planes defining great circles,
    finds intersection points, and checks if intersection points are on both edges
    
    Parameters:
      other (_Edge): Other edge to perform intersection check with
      
    Returns:
      True if the edges intersect, false otherwise
    """
    # Convert arc points to cartesian
    a1_cart = self.as_cart()
    a2_cart = other.as_cart()

    # Get plane normals from arcs
    n1 = a1_cart[0].cross(a1_cart[1]).norm()
    n2 = a2_cart[0].cross(a2_cart[1]).norm()

    # Check for identical normals or connected edges
    if (n1 == n2) or (self.vertex2 == other.vertex1):
      # Handle equal arcs case
      # Check if non-shared endpoints are on the other arc
      for int_point, arc in zip([self.vertex1, other.vertex2], [other, self]):
        does_intersect = arc.contains_point(int_point)
        if does_intersect:
          break

    else:
      # Handle intersecting arcs
      # Find intersection points
      i1 = n1.cross(n2).norm()
      i2 = -i1

      # Convert intersection points back to lat/lon
      i1 = i1.to_sdi_point()
      i2 = i2.to_sdi_point()

      # Check if either intersection point exists on both arcs
      for int_point in [i1, i2]:
        does_intersect = True
        for arc in [self, other]:
          does_intersect &= arc.contains_point(int_point)
        if does_intersect:
          break

    return does_intersect

@dataclass
class _CartesianPoint:
  """Supporting class for cartesian point/vector operations"""
  x: float
  y: float
  z: float

  def cross(self, other: '_CartesianPoint'):
    """Computes vector cross product, treating both points as 3-dimensional vectors
    
    Parameters:
      other (_CartesianPoint): Vector on right-hand side of cross product
    
    Returns:
      A new vector (_CartesianPoint) containing the cross product of the other two vectors
    """
    return _CartesianPoint(self.y*other.z - other.y*self.z,
                           other.x*self.z - self.x*other.z,
                           self.x*other.y - other.x*self.y)

  def norm(self):
    """Computes a version of the vector/point with magnitude/distance from origin of 1
    
    Parameters:
      None
      
    Returns:
      A new _CartesianPoint normalized to magnitude/distance from origin of 1
    """
    tmp = math.sqrt(sum(map(lambda a: a*a, astuple(self))))
    return _CartesianPoint(*map(lambda a: a/tmp, astuple(self)))

  def to_sdi_point(self):
    """Converts a cartesian point back to a lat/lon SDI Point
    
    Assumes cartesian point is normalized (R=1)

    Parameters:
      None
      
    Returns:
      A new SDI Point corresponding to the original cartesian point
    """
    lat = math.degrees(math.asin(self.z))
    lon = math.degrees(math.atan2(self.y, self.x))
    return afc_req.Point(lon, lat)

  def __eq__(self, other):
    return all(map(lambda a: math.fabs(a[0] - a[1]) < 1e-10, zip(astuple(self), astuple(other))))

  def __neg__(self):
    return _CartesianPoint(-self.x, -self.y, -self.z)

class InquiryRequestValidator(sdi_validate.SDIValidatorBase):
  """Provides validation functions for AFC Request-specific types"""

  _enforce_strict_polygon = False # Spec wording does not require many polygon constraints
                                  # (num of vertices, max edge length, no intersecting edges).
                                  # When false, the validator will check these constraints and
                                  # output log messages, but the validator result (true/false)
                                  # will not be impacted. Set this to true for these checks to
                                  # impact the validator result.

  def _validate_polygon_vertex_separation(self, outerBoundary: list[afc_req.Point]):
    """Breakout of max vertex separation check"""
    margin = 25000                     # Spec says 130km, but we allow an extra 25km to account
    allowed_distance = 130000 + margin # for differences in distance calculation methods

    is_valid = True

    # Get number of points to iterate over (wrap in try to gracefully handle non-iterable datatype)
    try:
      num_pts = len(outerBoundary)
    except TypeError as ex:
      self._warning(f'Exception encountered iterating over points in boundary: {ex}')
      return False

    # Check all consecutive vertex pairs, starting with last to first
    for point_idx in range(-1, num_pts-1):
      try:
        if outerBoundary[point_idx].distance_to(outerBoundary[point_idx+1]) > allowed_distance:
          is_valid = False
          self._warning('Distance between polygon endpoints with coordinates '
                        f'(lat: {outerBoundary[point_idx].latitude}, '
                        f'long: {outerBoundary[point_idx].longitude}) and '
                        f'(lat: {outerBoundary[point_idx+1].latitude}, '
                        f'long: {outerBoundary[point_idx+1].longitude}) exceeds the expected '
                        f'separation distance of {allowed_distance - margin})')
      except (TypeError, AttributeError) as ex:
        is_valid = False
        self._warning('Exception encountered getting distance between points '
                     f'({outerBoundary[point_idx]}, {outerBoundary[point_idx+1]}): {ex}')
    return is_valid

  def _validate_polygon_edge_intersection(self, outerBoundary: list[afc_req.Point]):
    """Breakout of polygon edge intersection check"""

    # Define polygon edges from point pairs
    try:
      num_pts = len(outerBoundary)
      edges = []
      for point_idx in range(-1, num_pts-1):
        edges.append(_Edge(outerBoundary[point_idx], outerBoundary[point_idx+1]))
    except (TypeError, AttributeError) as ex:
      self._warning(f'Exception encountered iterating over points in boundary: {ex}')
      return False

    # Check intersections with every pair of edges
    is_valid = True
    for edge_pair in itertools.combinations(edges, 2):
      if edge_pair[0] == edges[0] and edge_pair[1] == edges[-1]:
        edge_pair = edge_pair[1], edge_pair[0]
      if edge_pair[0].intersects(edge_pair[1]):
        self._warning('Found intersection between polygon edges with linear points '
                     f'({edge_pair[0]}) and ({edge_pair[1]})')
        is_valid = False

    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_channels(self, channels: afc_req.Channels):
    """Validates that an Channels object satisfies the SDI spec

    Checks:
      globalOperatingClass must be a valid, finite number
      All values for channelCfi must be valid, finite numbers, if present

    Parameters:
      channels (Channels): Channels to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True

    # globalOperatingClass must be a valid, finite number
    try:
      if not math.isfinite(channels.globalOperatingClass):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'globalOperatingClass ({channels.globalOperatingClass}) '
                     'must be a finite numeric value')

    # All values for channelCfi must be valid, finite numbers, if present
    if channels.channelCfi is not None:
      try:
        if not all(math.isfinite(channel_cfi) for channel_cfi in channels.channelCfi):
          raise TypeError()
      except TypeError:
        is_valid = False
        self._warning(f'channelCfi ({channels.channelCfi}) must be a list of finite numeric values')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_point(self, point: afc_req.Point):
    """Validates that a Point object satisfies the SDI spec

    Checks:
      longitude is a valid number in the range [-180, 180]
      latitude is valid number in the range [-90, 90]

    Parameters:
      point (Point): Point to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True

    # latitude is a valid number in the range [-90, 90]
    try:
      if not (-90 <= point.latitude <= 90):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Latitude {point.latitude} must be a valid number in the range [-90, 90]')

    # longitude is a valid number in the range [-180, 180]
    try:
      if not (-180 <= point.longitude <= 180):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Longitude {point.longitude} must be a valid number in the range [-180, 180]')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_vector(self, vector: afc_req.Vector):
    """Validates that an Vector object satisfies the SDI spec

    Checks:
      length is a valid, finite number
      angle is a valid number in the range [0, 360]

    Parameters:
      vector (Vector): Vector to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True

    # length is a valid, finite number
    try:
      if not math.isfinite(vector.length):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Length ({vector.length}) must be a single finite numeric value')

    # angle is a valid number in the range [-90, 90]
    try:
      if not (0 <= vector.angle <= 360):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Angle ({vector.angle}) must be a valid number in the range [0, 360]')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_elevation(self, elev: afc_req.Elevation):
    """Validates that an Elevation object satisfies the SDI spec

    Checks:
      height is a valid, finite number
      heightType is a supported value
      verticalUncertainty is a valid, positive integer

    Parameters:
      elev (Elevation): Elevation to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True

    # height is a valid, finite number
    try:
      if not math.isfinite(elev.height):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Height ({elev.height}) must be a single finite numeric value')

    # heightType is a supported value
    supported_height_types = ['AGL', 'AMSL']
    if elev.heightType not in supported_height_types:
      is_valid = False
      self._warning(f'HeightType ({elev.heightType}) must be one of: {supported_height_types}')

    # verticalUncertainty is a valid, positive, finite integer
    try:
      if not (0 <= elev.verticalUncertainty):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'VerticalUncertainty ({elev.verticalUncertainty}) must be a valid, positive '
                     'integer')

    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_radial_polygon(self, poly: afc_req.RadialPolygon):
    """Validates that a RadialPolygon object satisfies the SDI spec

    Checks:
      center is valid
      All outerBoundary Vectors are valid
    
    Warns (but does not require, unless _enforce_strict_polygon is enabled):
      At least 3 and no more than 15 unique vertices define the polygon
      Connecting lines between successive vertices may not cross any other connecting lines
        between successive vertices (requires Geopy)
      Distance between successive vertices should not exceed 130km (requires Geopy)

    Parameters:
      poly (RadialPolygon): RadialPolygon to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """

    # center is valid
    is_valid = self.validate_point(poly.center)

    # All outerBoundary points are valid
    try:
      is_valid &= all([self.validate_vector(x) for x in poly.outerBoundary])
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception encountered validating radial polygon vectors: {ex}')

    # At least 3 and no more than 15 vertices define the polygon
    try:
      if not (3 <= len(poly.outerBoundary) <= 15):
        is_valid &= not self._enforce_strict_polygon
        self._warning(f'Radial polygon should contain between 3 and 15 vertices: {poly}')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception encountered validating number of radial polygon vertices: {ex}')

    # All vertices are unique
    try:
      if len(poly.outerBoundary) != len(list(set([astuple(x) for x in poly.outerBoundary]))):
        is_valid &= not self._enforce_strict_polygon
        self._warning(f'Radial polygon contains non-unique vertices: {poly}')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Could not identify unique vertices in radial polygon ({poly}): {ex}')

    try: # Geopy dependent tests
      lin_poly = afc_req.LinearPolygon.from_radial(poly) # Get a temp linear polygon version

      # Distance between successive vertices should not exceed 130km
      if not self._validate_polygon_vertex_separation(lin_poly.outerBoundary):
        is_valid &= not self._enforce_strict_polygon

      # Connecting lines between successive vertices may not cross any other connecting lines
      # between successive vertices
      if not self._validate_polygon_edge_intersection(lin_poly.outerBoundary):
        is_valid &= not self._enforce_strict_polygon
    except ImportError:
      self._warning('Package "geopy" not available; distance and edge intersection validations '
                    'skipped')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception encountered when converting radial to linear polygon: {ex}')

    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_linear_polygon(self, poly: afc_req.LinearPolygon):
    """Validates that a LinearPolygon object satisfies the SDI spec

    Checks:
      All outerBoundary Points are valid
    
    Warns (but does not require, unless _enforce_strict_polygon is enabled):
      At least 3 and no more than 15 unique vertices define the polygon
      Connecting lines between successive vertices may not cross any other connecting lines
        between successive vertices (requires Geopy)
      Distance between successive vertices should not exceed 130km

    Parameters:
      poly (LinearPolygon): LinearPolygon to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """

    is_valid = True

    # All outerBoundary points are valid
    try:
      is_valid &= all([self.validate_point(x) for x in poly.outerBoundary])
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception encountered validating linear polygon points: {ex}')

    # At least 3 and no more than 15 vertices define the polygon
    try:
      if not (3 <= len(poly.outerBoundary) <= 15):
        is_valid &= not self._enforce_strict_polygon
        self._warning(f'Linear polygon should contain between 3 and 15 vertices: {poly}')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception encountered validating number of linear polygon vertices: {ex}')

    # All vertices are unique
    try:
      if len(poly.outerBoundary) != len(list(set([astuple(x) for x in poly.outerBoundary]))):
        is_valid &= not self._enforce_strict_polygon
        self._warning(f'Linear polygon contains non-unique vertices: {poly}')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Could not identify unique vertices in linear polygon ({poly}): {ex}')

    try: # Geopy dependent tests
      # Distance between successive vertices should not exceed 130km
      if not self._validate_polygon_vertex_separation(poly.outerBoundary):
        is_valid &= not self._enforce_strict_polygon

      # Connecting lines between successive vertices may not cross any other connecting lines
      # between successive vertices
      if not self._validate_polygon_edge_intersection(poly.outerBoundary):
        is_valid &= not self._enforce_strict_polygon
    except ImportError:
      self._warning('Package "geopy" not available; distance and edge intersection validation '
                    'skipped')

    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_ellipse(self, ellipse: afc_req.Ellipse):
    """Validates that an Ellipse object satisfies the SDI spec

    Checks:
      center is a valid Point
      majorAxis, minorAxis are valid, positive integer
      majorAxis is greater than or equal to minorAxis
      orientation is a valid number in the range [0, 180]

    Parameters:
      ellipse (Ellipse): Ellipse to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """

    # center is a valid point
    is_valid = self.validate_point(ellipse.center)

    # majorAxis is a valid, positive integer
    try:
      if not (0 <= ellipse.majorAxis):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Major axis ({ellipse.majorAxis}) must be a valid positive integer')

    # minorAxis is a valid, positive integer
    try:
      if not (0 <= ellipse.minorAxis):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Minor axis ({ellipse.minorAxis}) must be a valid positive integer')

    # majorAxis is greater than or equal to minorAxis
    try:
      if not (ellipse.majorAxis >= ellipse.minorAxis):
        is_valid = False
        self._warning(f'Ellipse major axis ({ellipse.majorAxis}) should not be less than '
                      f'minor axis ({ellipse.minorAxis})')
    except TypeError as ex:
      is_valid = False
      self._warning(f'Could not compare ellipse major and minor axis: {ex}')

    # orientation is a valid number in the range [0, 180]
    try:
      if not (0 <= ellipse.orientation <= 180):
        raise TypeError()
    except TypeError:
      is_valid = False
      self._warning(f'Orientation ({ellipse.orientation}) must be a valid number in the '
                     'range [0, 180]')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_location(self, loc: afc_req.Location):
    """Validates that a Location object satisfies the SDI spec

    Checks:
      elevation is valid
      Location outline objects are valid (ellipse, linearPolygon, radialPolygon)
      One and only one of {ellipse, linearPolygon, radialPolygon} is provided
      indoorDeployment is a valid value (0, 1, 2), if present

    Parameters:
      loc (Location): Location to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """

    # elevation is valid
    is_valid = self.validate_elevation(loc.elevation)

    # ellipse is valid, if present
    if loc.ellipse is not None:
      is_valid &= self.validate_ellipse(loc.ellipse)

    # linearPolygon is valid, if present
    if loc.linearPolygon is not None:
      is_valid &= self.validate_linear_polygon(loc.linearPolygon)

    # radialPolygon is valid, if present
    if loc.radialPolygon is not None:
      is_valid &= self.validate_radial_polygon(loc.radialPolygon)

    # One and only one of {ellipse, linearPolygon, radialPolygon} is provided
    exclusive_required_fields = ['ellipse', 'linearPolygon', 'radialPolygon']
    present_flags = []
    for cur_field in exclusive_required_fields:
      present_flags.append(1 if getattr(loc, cur_field) is not None else 0)

    match sum(present_flags):
      case 0:
        is_valid = False
        self._warning('Location must include at least one of these fields: '
                     f'{exclusive_required_fields}')
      case 1:
        pass
      case _:
        is_valid = False
        present_fields = [field for field, present in zip(exclusive_required_fields,
                                                          present_flags) if present]
        self._warning(f'Location includes values for all of {present_fields} but only one is '
                       'permitted')

    # indoorDeployment is a valid value (0, 1, 2)
    if loc.indoorDeployment is not None:
      valid_deployments = [0, 1, 2]
      if not any(loc.indoorDeployment == valid for valid in valid_deployments):
        is_valid = False
        self._warning(f'Indoor deployment value ({loc.indoorDeployment}) is not valid '
                      f'(one of {valid_deployments})')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_certification_id(self, cert_id: afc_req.CertificationId):
    """Validates that a CertificationId object satisfies the SDI spec

    Checks:
      None
    
    Warns (but does not require):
      rulesetId is an acceptable value

    Parameters:
      cert_id (CertificationId): CertificationId to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True
    # rulesetId is an acceptable value
    acceptable_values = ['US_47_CFR_PART_15_SUBPART_E', 'CA_RES_DBS-06']
    if cert_id.rulesetId not in acceptable_values:
      self._warning(f'Ruleset ID ({cert_id.rulesetId}) not one of the SDI accepted values: '
                    f'{acceptable_values}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_device_descriptor(self, dev: afc_req.DeviceDescriptor):
    """Validates that a DeviceDescriptor object satisfies the SDI spec

    Checks:
      Contains at least one CertificationId
      All CertificationIds are valid

    Parameters:
      dev (DeviceDescriptor): DeviceDescriptor to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = True
    try:
      # certificationId contains at least one value
      if len(dev.certificationId) < 1:
        is_valid = False
        self._warning('Device descriptor must have at least one CertificationID')
      else:
        # All CertificationIds are valid
        is_valid &= all([self.validate_certification_id(x) for x in dev.certificationId])
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception caught validating CertificationIds: {ex}')
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_spectrum_inquiry_request(self,
        req: afc_req.AvailableSpectrumInquiryRequest):
    """Validates that an AvailableSpectrumInquiryRequest object satisfies the SDI spec

    Checks:
      deviceDescriptor is valid
      location is valid
      At least one availability type is requested
      Provided availability requests are not empty
      inquiredFrequencyRange is valid, if present
      inquiredChannels is valid, if present
      minDesiredPower is only present for channel inquiry
      minDesiredPower is a valid number
      vendorExtensions are valid

    Parameters:
      req (AvailableSpectrumInquiryRequest): AvailableSpectrumInquiryRequest to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    # deviceDescriptor is valid
    is_valid = self.validate_device_descriptor(req.deviceDescriptor)

    # location is valid
    is_valid &= self.validate_location(req.location)

    # At least one availability type is requested
    if (req.inquiredFrequencyRange is None) and (req.inquiredChannels is None):
      is_valid = False
      self._warning('At least one of inquiredFrequencyRange or inquiredChannels must be present')

    # inquiredFrequencyRange is valid, if present
    if req.inquiredFrequencyRange is not None:
      try:
        if len(req.inquiredFrequencyRange) < 1:
          is_valid = False
          self._warning('Inquired frequency range should not be empty')
        else:
          is_valid &= all(self.validate_frequency_range(x) for x in req.inquiredFrequencyRange)
      except (AttributeError, TypeError) as ex:
        self._warning(f'Exception caught validating frequency range: {ex}')
        is_valid = False

    # inquiredChannels is valid, if present
    if req.inquiredChannels is not None:
      try:
        if len(req.inquiredChannels) < 1:
          is_valid = False
          self._warning('Inquired channels should not be empty')
        else:
          is_valid &= all([self.validate_channels(x) for x in req.inquiredChannels])
      except (AttributeError, TypeError) as ex:
        self._warning(f'Exception caught validating channels: {ex}')
        is_valid = False

    # minDesiredPower is only present for channel inquiry
    if req.minDesiredPower is not None:
      if req.inquiredChannels is None:
        is_valid = False
        self._warning('minDesiredPower is specified, but channel inquiry is not present')

      # minDesiredPower is a valid, finite number
      try:
        if math.isnan(req.minDesiredPower):
          raise TypeError()
      except TypeError:
        is_valid = False
        self._warning(f'minDesiredPower ({req.minDesiredPower}) must be a single valid number')

    # Vendor extensions are valid
    is_valid &= self.validate_vendor_extension_list(req.vendorExtensions)
    return is_valid

  @sdi_validate.common_sdi_validator
  def validate_available_spectrum_inquiry_request_message(self,
        msg: afc_req.AvailableSpectrumInquiryRequestMessage):
    """Validates that an AvailableSpectrumInquiryRequestMessage object satisfies the SDI spec

    Checks:
      version string is valid
      AvailableSpectrumInquiryRequests exist and are all valid
      Each AvailableSpectrumInquiryRequest has a unique requestId
      vendorExtensions are valid

    Warns:
      If request message contains a mixture of valid and invalid requests
        This situation may be handled differently by various AFC implementations,
        making the creation of a mask file difficult. For instance, an AFC might:
          * Process each request individually, returning HTTP code 200 and a mix of
            SDI SUCCESS and error response codes
          * Ignore any valid requests within the message, returning HTTP code 400 and
            the relevant SDI error response codes for each request
        Use of mixed valid and invalid requests is discouraged within a single request message.
        See GitHub PR #41 (https://github.com/Wireless-Innovation-Forum/6-GHz-AFC/pull/41)
        for more details.

    Parameters:
      msg (AvailableSpectrumInquiryRequestMessage): Message to be validated

    Returns:
      True if all checks are satisfied
      False otherwise
    """
    is_valid = self.validate_version(msg.version)
    try:
      if len(msg.availableSpectrumInquiryRequests) < 1:
        is_valid = False
        self._warning(f'Length of availableSpectrumInquiryRequests '
                      f'list must be at least 1: {msg.availableSpectrumInquiryRequests}')
      else:
        # availableSpectrumInquiryRequests exist and are all valid
        valid_request_flags = [self.validate_available_spectrum_inquiry_request(x)
                               for x in msg.availableSpectrumInquiryRequests]
        is_valid &= all(valid_request_flags)

        # Log a special warning for mixtures of valid and invalid requests
        if True in valid_request_flags and False in valid_request_flags:
          self._warning('Request message contains a mixture of valid and invalid requests. The '
                        'expected response for this type of request may be ambiguous '
                        '(see GitHub PR#41). Issues executing this test may occur in some cases.')

        # Each availableSpectrumInquiryRequest has a unique requestID
        resp_ids = [sub_resp.requestId for sub_resp in msg.availableSpectrumInquiryRequests]
        # [list(set(list_val)) gives all unique values in list]
        if len(resp_ids) != len(list(set(resp_ids))):
          is_valid = False
          self._warning('Message should have no more than one occurrence of any given requestId')
    except (TypeError, AttributeError) as ex:
      is_valid = False
      self._warning(f'Exception caught validating requests: {ex}')

    # vendorExtensions are valid
    is_valid &= self.validate_vendor_extension_list(msg.vendorExtensions)
    return is_valid

def main():
  """Demonstrates use of the validator functions"""
  logging.basicConfig()
  logger = logging.getLogger()

  validator = InquiryRequestValidator(logger=logger)

  with open(os.path.join(pathlib.Path(__file__).parent.resolve(),
                         "sample_files", "request_sample.json"),
            encoding="UTF-8") as sample_file:
    sample_json = json.load(sample_file)
    sample_conv = afc_req.AvailableSpectrumInquiryRequestMessage(**sample_json)
    print('Example request is valid: '
         f'{validator.validate_available_spectrum_inquiry_request_message(sample_conv)}')
    print('Can validate sub-fields with JSON dict directly: '
      f'''{validator.validate_available_spectrum_inquiry_request(
           sample_json["availableSpectrumInquiryRequests"][0])}''')
    print('Can validate root message with JSON dict directly: '
         f'{validator.validate_available_spectrum_inquiry_request_message(sample_json)}')
    sample_conv.availableSpectrumInquiryRequests = []
    empty_list_is_valid = validator. \
                          validate_available_spectrum_inquiry_request_message(sample_conv)
    print('^Errors logged to console by default logger config^')
    print(f'Empty response list is not valid: {not empty_list_is_valid}')

if __name__ == '__main__':
  import json
  import logging
  import os
  import pathlib
  main()
