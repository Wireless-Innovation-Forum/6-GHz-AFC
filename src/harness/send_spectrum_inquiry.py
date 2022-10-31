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
"""Top main script of the test harness.

If writing your own top level script to run the test harness,
look here how the setup is performed.
It is particularly important to correctly set the geo drivers
and multiprocessing pool for best performance
"""
import afc
import json


print ("running tests")
with open('request_sample.json') as f:
  request_sample = json.loads(f.read())
print ("Request_sample : ", request_sample)
afc_protocol, afc_admin_interface = afc.GetTestingAfc()

received_response = afc_protocol.SpectrumInquiry(request_sample)
print ("\nResponse : ", received_response)
