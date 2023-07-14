This directory contains the Expected Spectrum Inquiry Response Messages (i.e., response masks) corresponding to defined tests that are to be conducted on AFC Systems.

These response masks are from the Wi-Fi Alliance AFC System (SUT) Compliance Test Vectors (v1.2), available from the [Wi-Fi Alliance website](https://www.wi-fi.org/discover-wi-fi/specifications) under "AFC Specification and Test Plans."

Implementation notes:
  * The mask file for AFCS.SRS.1 has been created to allow the maximum allowed power for the requested frequency ranges and all channel indices in the requested global operating classes (according to the channel index list in Table E-4 of [IEEE 802.11ax-2021](https://ieeexplore.ieee.org/document/9442429)).
  * The URS test cases also permit -1 (GENERAL_FAILURE), in addition to the more specific (but optional) codes listed in the test vectors document.
  * AFCS.URS.1 has been fixed to expect a response code of 102 (MISSING_PARAM) in addition to 103 (INVALID_VALUE) to better align with the current request definition (which, rather tha including an invalid device ID, instead does not include a value for the device ID).
