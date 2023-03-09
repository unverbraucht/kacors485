import socket
import select
from .kacoparser import KacoRS485Parser

class KacoTCP(object):
    """
    KacoTCP can talk to kaco powador rs485 interface via a TCP connection, for example through a Terminal converter

    supports:
        * reading current values
    """

    waitBeforeRead = 0.7
    parser = KacoRS485Parser()

    def __init__(self, host, port):
        """
        initalize and determine which host and port to connect to

        example
        ``
        kaco = KacoTCP('192.168.1.1', 23)
        ``
        """

        #create and open serial port
        self.socket = socket.create_connection([host, port])
        self.socket.setblocking(True)

    def close(self):
        """
        close serial connection
        """
        self.socket.close()

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

        print("answers", answers)

        parsed = []
        for k in answers:
            lines = answers[k]
            for line in lines:
              if len(line) == 0:
                  continue
              parsed.append(self.parser.parse(line, k))

        #all answers could be empty, what should we do?
        #we could also silently answer an empty dict
        #but we prefer to raise an exception
        if len(parsed) <= 0:
            raise Exception('Could not get an answer from the inverter number {}; Answer: {:s}'.format(inverterNumber, repr(answers)))

        #important, set input to empty dict
        #otherwise, we will reuse input from last function call
        return self.parser.listDictNameToKey(parsed,{})


    def sendCmdAndRead(self,cmd):
        import time
        """
        send command on rs485 and read answer

        return list of answered lines
        if no answer after waiting time, return empty list
        """

        #can only send bytearrays
        bytearr = cmd.encode()
        self.socket.send(bytearr)

        print("send to rs485", bytearr)

        # read answer
        answer = []
        while True:
          ready = select.select([self.socket], [], [], self.waitBeforeRead)
          if ready[0]:
            #read answer line
            answer.extend(self.socket.recv(4096).decode('iso8859-15'))
          else:
              break

        return ''.join(answer).split('\n')

if __name__ == '__main__':
    tcp_reader = KacoTCP('192.168.32.146', 23)
    print(tcp_reader.readInverterAndParse(1))
    tcp_reader.close()