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

# Top main script of the test harness. Before running:
#
#   - Edit afc.cfg to provide connection info for the SUT
#   - [TODO: Instructions if using certificates]
#   - Edit tests_to_run.py to indicate which spectrum inquiry tests to run,
#     and be sure that the files end in .json
#   - Be sure that a json file for each spectrum inquiry to be tested
#     is in the directory ./inquiries

# Standard python modules
from datetime import datetime
import glob
import json
import os

# Modules specific to the AFC System test harness
import afc
from request_validator import availableSpectrumInquiryRequestMessage_is_valid
from response_validator import validate_response
from tests_to_run import tests_to_run


# If first element of tests_to_run is 'all', run all inquiries in the
# /inquiries directory. Otherwise just run the inquries in the list.
if tests_to_run[0].lower().strip() == 'all':
  tests_to_run = []
  inlist = sorted([os.path.basename(x) for x in glob.glob('inquiries/*')])
  for file in inlist:
    if file[-5:].lower() == '.json':
      tests_to_run.append(file)
else:
  for index in range(len(tests_to_run)):
    if tests_to_run[index][-5:].lower() != '.json':
      tests_to_run[index] += '.json'
      # [TODO: Properly handle .json vs .JSON]

for inquiry in tests_to_run:

  print('*** Processing ' + inquiry)

  dt_string = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
  logfile = 'logs/' + inquiry + '_log_' + dt_string + '.txt'
  responsefile = 'responses/' + inquiry + '_response_' + dt_string + '.json'

  # Read the contents of the spectrum inquiry file in text format
  with open('inquiries/' + inquiry) as fin:
    intext = fin.read()

  # Write inquiry to log file
  flog = open(logfile, 'w')
  flog.write('**** Inquiry:\n')
  flog.write(intext + '\n\n')
  flog.close()

  # Convert inquiry text to JSON
  request_sample = json.loads(intext)

  # Validate the format and required parameters of the request
  passes_validation = availableSpectrumInquiryRequestMessage_is_valid(request_sample, logfile)
  print('  ' + inquiry + ' passes validation: ' + str(passes_validation))

  if passes_validation:
    # Submit the request to the SUT and read the spectrum inquiry response
    afc_protocol, afc_admin_interface = afc.GetTestingAfc()
    print('  Submitting ' + inquiry + ' to SUT')
    response = afc_protocol.SpectrumInquiry(request_sample)
    
    # Write the response to a stand-alone text file
    fresponse = open(responsefile, 'w')
    fresponse.write(json.dumps(response))
    fresponse.close()
    
    # Also append response to the log file
    flog = open(logfile, 'a')
    flog.write('**** Response:\n')
    flog.write(json.dumps(response))
    
    # Analyze/validate the response (format and compliance with mask)
    print('  SUT passes mask test: ' +
          str(validate_response(inquiry, response, flog)))
  else:
    print('  >> Spectrum inquiry did not pass validation test.')
    print('  >> Test was not submitted to SUT')
    print('  >> See log file for errors')

  flog.close()

