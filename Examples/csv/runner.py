import sys
sys.path.append("../..")
import csvpeg as csv

print(csv.loads("1"))
print(csv.loads("1\r\n"))
print(csv.loads("1,2,3"))
print(csv.loads("1,2,3\r\n"))
print(csv.loads("1\r\n2\r\n3"))
print(csv.loads("1\r\n2\r\n3\r\n"))
print(csv.loads("data:\r\n1\r\n2\r\n3\r\n", has_headers=True))
print(csv.loads("data:\r\n1\r\n2\r\n3\r\n", has_headers=False))