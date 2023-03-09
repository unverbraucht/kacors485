# -*- coding: utf-8 -*-
import serial
import glob
from .kacoparser import KacoRS485Parser

class KacoRS485(object):
    """
    KacoRS485 can talk to kaco powador rs485 interface

    supports:
        * reading current values
    """

    waitBeforeRead = 0.7

    def port_from_wildcard(self, port):
        port = glob.glob(port)
        if not port:
            raise Exception('could not find a valid rs485 port')
        return port[0]

    def __init__(self,serialPort):
        """
        initalize which serial port we should use

        example
        ``
        kaco = KacoRS485('/dev/ttyUSB0')
        ``
        """
        if '*' in serialPort:
            serialPort = self.port_from_wildcard(serialPort)

        #create and open serial port
        self.ser = serial.Serial(
            port=serialPort,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.5
        )

    def close(self):
        """
        close serial connection
        """
        self.ser.close()

    def readInverter(self,inverterNumber):
        """
        read all available data from inverter inverterNumber

        inverterNumber: can be between 0 and 32
        """

        answers = {}

        sendCommands = [0,3]
        commands = []
        for s in sendCommands:
            commands.append('#{:02d}{:01d}\r\n'.format(inverterNumber,s))

        for cmd in commands:
            answers[cmd] = self.sendCmdAndRead(cmd)

        return answers

    def readInverterAndParse(self,inverterNumber):
        answers = self.readInverter(inverterNumber)

        P = KacoRS485Parser()

        print("answers",answers)

        parsed = []
        for k in answers:
            item = answers[k]
            if len(item) == 0:
                continue
            parsed.append(P.parse(item,k))

        #all answers could be empty, what should we do?
        #we could also silently answer an empty dict
        #but we prefer to raise an exception
        if len(parsed) <= 0:
            raise Exception('Could not get an answer from the inverter number {}; Answer: {:s}'.format(inverterNumber, repr(answers)))

        #important, set input to empty dict
        #otherwise, we will reuse input from last function call
        return P.listDictNameToKey(parsed,{})


    def sendCmdAndRead(self,cmd):
        import time
        """
        send command on rs485 and read answer

        return list of answered lines
        if no answer after waiting time, return empty list
        """

        #can only send bytearrays
        bytearr = cmd.encode()
        self.ser.write(bytearr)

        print("send to rs485",bytearr)

        #wait some time to let device answer
        time.sleep(self.waitBeforeRead)

        #read answer
        #while ser.inWaiting() > 0:
        #    out += ser.read(1)

        #read answer line
        answer = []
        while self.ser.inWaiting() > 0:
            answer.append(self.ser.readline())

        return ''.join(answer)

