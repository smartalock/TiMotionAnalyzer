# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting

# High level analyzers must subclass the HighLevelAnalyzer class.
class TiMotionPacket:
    start_time: float
    end_time: float
    datalen: int
    data: bytearray

    def __init__(self, start_time, end_time, data):
        self.start_time = start_time
        self.end_time = end_time
        self.data = bytearray()
        self.data.append(data)
        self.datalen = 1

    def append(self, data, time):
        self.data.append(data)
        self.datalen = self.datalen + 1
        self.end_time = time


class TiMotionController(HighLevelAnalyzer):

    def __init__(self):
        self.current_packet = None
        # Retain 13 bytes of history
        self.history_data = bytearray(13)
        self.history_start = []
        self.history_end = []

    def addbyte(self, data, start_time, end_time):
        self.history_data.append(data)
        del self.history_data[0]
        self.history_start.append(start_time)
        if len(self.history_start) > 13:
            del self.history_start[0]
        self.history_end.append(end_time)
        if len(self.history_end) > 13:
            del self.history_end[0]

    def lcdchar(self, data):
        data = data & 0x7F
        result = "?"
        if data == 0x3F:
            result = "0"
        elif data == 0x06:
            result = "1"
        elif data == 0x5B:
            result = "2"
        elif data == 0x4F:
            result = "3"
        elif data == 0x66:
            result = "4"
        elif data == 0x6D:
            result = "5"
        elif data == 0x7D:
            result = "6"
        elif data == 0x07:
            result = "7"
        elif data == 0x7F:
            result = "8"
        elif data == 0x6F:
            result = "9"
        elif data == 0x79:
            result = "E"
        elif data == 0x73:
            result = "P"
        elif data == 0x40:
            result = "-"
        elif data == 0x00:
            result = " "
        return result

    def formatcmd(self, cmd, data):
        result = "?"
        if cmd == 0x00:
            result = "Stopped"
        elif cmd == 0x03:
            if data != 0xFF:
                result = "Moving"
            else:
                result = "Display"
        elif cmd == 0x07:
            result = "P1"
        elif cmd == 0x0B:
            result = "P2"
        return result


    def decode(self, frame: AnalyzerFrame):
        # AsyncSerial only has 'data' type frames
        if frame.type == 'data':
            data = frame.data['data'][0]

            self.addbyte(data, frame.start_time, frame.end_time)


            if self.current_packet is not None:
                if self.current_packet.datalen == 1:
                    if data == 0x98:
                        self.current_packet.append(data, frame.end_time)
                    else:
                        self.current_packet = None
                elif self.current_packet.datalen >= 2 and self.current_packet.datalen <= 4:
                    self.current_packet.append(data, frame.end_time)
                elif self.current_packet.datalen == 5:
                    self.current_packet.append(data, frame.end_time)
                    if self.current_packet.data[2] == self.current_packet.data[3] and self.current_packet.data[4] == self.current_packet.data[5]:
                        cmd = self.current_packet.data[2]
                        data = self.current_packet.data[4]
                        result = []

                        print("History: ", self.history_data)
                        b1 = self.history_data[5]
                        b2 = self.history_data[3]
                        b3 = self.history_data[1]
                        chk = self.history_data[0]
                        actual = 0
                        for x in range(1, 6):
                            actual += self.history_data[x]
                        while actual >= 256:
                            actual -= 256
                            actual += 1

                        print("chk: ", chk , ", expected: ", actual)

                        if actual == chk:
                            if b1 > 0 or b2 > 0 or b3 > 0:
                                c1 = self.lcdchar(b1)
                                c2 = self.lcdchar(b2)
                                c3 = self.lcdchar(b3)
                                framedata = {
                                    "display": '"' + c1 + c2 + c3 + '"',
                                }
                                if c1 == "E":
                                    framedata["error"] = c2 + c3

                                result.append(AnalyzerFrame('display', self.history_start[0], self.history_end[6], framedata))
                            else:
                                print("zero display - ignore")
                        else:
                            print("checksum incorrect, chk=", chk , ", actual=", actual)

                        # The status frame
                        framedata = {
                            "cmd": cmd,
                            "status": self.formatcmd(cmd, data)
                        }
                        if data != 0xFF:
                            framedata["height"] = data

                        result.append(AnalyzerFrame('status', self.current_packet.start_time, self.current_packet.end_time, framedata))
                        self.current_packet = None
                        return result

                    else:
                        self.current_packet = None
            else:
                if data == 0x98:
                    self.current_packet = TiMotionPacket(frame.start_time, frame.end_time, data)


class TiMotionHandset(HighLevelAnalyzer):
    def __init__(self):
        self.current_packet = None

    def decode(self, frame: AnalyzerFrame):
        # AsyncSerial only has 'data' type frames
        if frame.type == 'data':
            data = frame.data['data'][0]
            if self.current_packet is not None:
                if self.current_packet.datalen == 1:
                    if data == 0xD8:
                        self.current_packet.append(data, frame.end_time)
                    else:
                        self.current_packet = None
                elif self.current_packet.datalen == 2:
                    self.current_packet.append(data, frame.end_time)
                elif self.current_packet.datalen == 3:
                    self.current_packet.append(data, frame.end_time)
                elif self.current_packet.datalen == 4:
                    self.current_packet.append(data, frame.end_time)
                    if self.current_packet.data[3] == self.current_packet.data[4]:
                        # Print out result!
                        actionstr = ''
                        action = self.current_packet.data[3]
                        if action == 0x00:
                            actionstr = "IDLE"
                        elif action == 0x01:
                            actionstr = "DOWN"
                        elif action == 0x02:
                            actionstr = "UP"
                        else:
                            if action & 0x40 > 0:
                                actionstr += "M|"
                            if action & 0x20 > 0:
                                actionstr += "4|"
                            if action & 0x10 > 0:
                                actionstr += "3|"
                            if action & 0x08 > 0:
                                actionstr += "2|"
                            if action & 0x04 > 0:
                                actionstr += "1|"
                            if action & 0x02 > 0:
                                actionstr += "UP|"
                            if action & 0x01 > 0:
                                actionstr += "DN|"

                        frame_data = {
                            'id': hex(self.current_packet.data[2]),
                            'action': actionstr

                        }
                        result = AnalyzerFrame('handset', self.current_packet.start_time, self.current_packet.end_time, frame_data)
                        self.current_packet = None
                        return result
                    else:
                        self.current_packet = None
            else:
                if data == 0xD8:
                    self.current_packet = TiMotionPacket(frame.start_time, frame.end_time, data)

