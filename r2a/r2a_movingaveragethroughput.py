from r2a.ir2a import IR2A
from player.parser import *
import time
from statistics import mean


class R2A_MovingAverageThroughput(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.request_time = 0
        self.window_size = 10
        self.qi = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):

        t = time.perf_counter() - self.request_time
        xml_throughput = (msg.get_bit_length() / t)
        self.throughputs.append(xml_throughput)

        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # get the last window to calculate average throughput
        moving_avg = mean(self.throughputs[-self.window_size:]) / 2

        selected_qi = self.qi[0]
        for i in self.qi:
            if i <= moving_avg:
                selected_qi = i

        msg.add_quality_id(selected_qi)

        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        segment_throughput = (msg.get_bit_length() / t)
        self.throughputs.append(segment_throughput)

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
