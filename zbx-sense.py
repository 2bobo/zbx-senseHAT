#!/usr/bin/python
import os
import socket
import struct
import json
import ConfigParser

from sense_hat import SenseHat

class ZabbixSender:
    zbx_header = 'ZBXD'
    zbx_version = 1
    zbx_sender_data = {u'request': u'sender data', u'data': []}
    send_data = ''

    def __init__(self, server_host, server_port = 10051):
        self.server_ip = socket.gethostbyname(server_host)
        self.server_port = server_port

    def AddData(self, host, key, value, clock = None):
        add_data = {u'host': host, u'key': key, u'value': value}
        if clock != None:
            add_data[u'clock'] = clock
        self.zbx_sender_data['data'].append(add_data)
        return self.zbx_sender_data

    def ClearData(self):
        self.zbx_sender_data['data'] = []
        return self.zbx_sender_data

    def __MakeSendData(self):
        zbx_sender_json = json.dumps(self.zbx_sender_data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        json_byte = len(zbx_sender_json)
        self.send_data = struct.pack("<4sBq" + str(json_byte) + "s", self.zbx_header, self.zbx_version, json_byte, zbx_sender_json)

    def Send(self):
        self.__MakeSendData()
        so = socket.socket()
        so.connect((self.server_ip, self.server_port))
        wobj = so.makefile(u'wb')
        wobj.write(self.send_data)
        wobj.close()
        robj = so.makefile(u'rb')
        recv_data = robj.read()
        robj.close()
        so.close()
        tmp_data = struct.unpack("<4sBq" + str(len(recv_data) - struct.calcsize("<4sBq")) + "s", recv_data)
        recv_json = json.loads(tmp_data[3])
        return recv_data

def put_zbx_sender(zbxsvip, zbx_key, hostip, sendvalue):
    sender = ZabbixSender(zbxsvip)
    sender.AddData(hostip, zbx_key, sendvalue)
    try:
        sender.Send()
    except:
        print "[ERROR] host: %s  value: %s"%(hostip,sendvalue)
    sender.ClearData()

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.normpath(os.path.join(base, 'config.ini'))

    conf = ConfigParser.SafeConfigParser()
    conf.read(config_file_path)

    sense = SenseHat()
    sense.clear()
    temp = sense.get_temperature()
    temp = round(temp, 1)
    humidity = sense.get_humidity()
    humidity = round(humidity, 1)
    pressure = sense.get_pressure()
    pressure = round(pressure, 1)

    put_zbx_sender(conf.get("zabbix","ip"), "temperature", "myroom", temp)
    put_zbx_sender(conf.get("zabbix","ip"), "humidity", "myroom", humidity)
    put_zbx_sender(conf.get("zabbix","ip"), "pressure", "myroom", pressure)

