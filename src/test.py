from struct import unpack, pack

from src.tools.Node import Node

buffer = b'\x00\x01\x00\x05\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'
primary = unpack(">HHiHHHHi", buffer[0:20])
l = str(len(buffer) - 20) + "s"
body = str(unpack(l, buffer[20:len(buffer)])[0])
body = body[2:len(body) - 1]
packet = str(primary[0]) + str(primary[1])
bl = str(primary[2])
port = str(primary[7])
for i in range(5 - len(bl)):
    packet += "0"
packet += bl
ip = ""
for i in range(3, 7):
    ip += str(primary[i])
    if(i!=6):
        ip += '.'
packet += Node.parse_ip(ip)
for i in range(5 - len(port)):
    packet += "0"
packet += port
packet += body
buf = packet
header = buf[0:27]
body = buf[27:len(buf)]
version = int(buf[0])
type = int(buf[1])
length = int(buf[2:7])
iip = buf[7:22]
port = str(int(buf[22:27]))
address = []
address.append(iip)
address.append(port)
print(header, " ", body, " ", version, " ", type, " ", length, " ", iip, " ", port, " ", address)
print(packet)
print(packet[7:22])
ipb = []
for i in range(4):
    ipb.append(int(header[7 + i * 4:10 + i * 4]))
form = ">HHiHHHHi" + str(len(body)) + "s"
buf = pack(form, version, type, length, ipb[0], ipb[1], ipb[2], ipb[3], int(port), body.encode('utf-8'))
print(buf)
print(buffer)
print(int("00313"))
