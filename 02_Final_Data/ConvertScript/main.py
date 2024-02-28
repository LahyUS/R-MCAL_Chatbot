from _converter import CONVERTER
from extern_variables import *

# Convert AUTOSAR document
convert = CONVERTER(type = 'AUTOSAR')
convert.run(module_sub_path = 'MCAL_WPS', 
            output_path = OUTPUT_PATH, 
            save_format = 3, encode = False)

# Convert Hardware Manual document
# convert = CONVERTER(type = 'BASE')
# convert.run(module_sub_path = 'HardwareManual', 
#             output_path = OUTPUT_PATH, 
#             save_format = 3, encode = True)