import sys
sys.path.append("../..")
import csvpeg as csv

csv.csvreader("1")
csv.csvreader("1\r\n")
csv.csvreader("1,2,3")
csv.csvreader("1,2,3\r\n")
csv.csvreader("1\r\n2\r\n3")
csv.csvreader("1\r\n2\r\n3\r\n")
#csv.csvpegParser("-3")
#csv.csvpegParser("0")
#csv.csvpegParser("null")
#csv.csvpegParser("true")
#csv.csvpegParser("false")
#csv.csvpegParser("\"fast\"")
#csv.csvpegParser("3.1")
#csv.csvpegParser("-3.1")
#csv.csvpegParser("3.1e4")
#csv.csvpegParser("3.1e-4")
#csv.csvpegParser("[true, false, true, true]")
#csv.csvpegParser("[-1, 0, 1, 2]")
#csv.csvpegParser("[-1.2, 0.1, 1.2, 2.3]")
#csv.csvpegParser("[true, -1, 2.3, \"fast\"]")
#csv.csvpegParser("[true, -1, {\"fast\" : 2.3}]")
#csv.csvpegParser("[]")
#csv.csvpegParser("{}")
#csv.csvpegParser("{\"key\": \"value\"}")
#csv.csvpegParser("{\"key\": true}")
#csv.csvpegParser("{\"key\": false}")
#csv.csvpegParser("{\"key\": null}")
#csv.csvpegParser("{\"key\": 1}")
#csv.csvpegParser("{\"key\": -1.2}")
#csv.csvpegParser("{\"key\": [1, -1.2]}")
#csv.csvpegParser("{\"key\": {1, -1.2}}") # this fails correctly
#csv.csvpegParser("{\"key\": {\"value\": -1.2}}")
#csv.csvpegParser("{\"key\": {\"value\": -1.2}}{\"key2\": {\"value2\": -2.4}}")