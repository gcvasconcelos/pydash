from r2a.ir2a import IR2A
from player.parser import *
import time
from statistics import mean

import pdb


class R2A_MovingAverageThroughput(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.buffer = []
        self.request_time = 0
        self.window_size = 5
        self.qi = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):

        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        xml_throughput = msg.get_bit_length() / t
        self.throughputs.append(xml_throughput)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.buffer.append(
            self.whiteboard.get_amount_video_to_play())

        self.request_time = time.perf_counter()

        # get the last window to calculate average throughput
        moving_avg = mean(self.throughputs[-self.window_size:]) / 2

        selected_index = 0
        for index, quality in enumerate(self.qi):
            if moving_avg > quality:
                selected_index = index

        selected_qi = self.qi[selected_index]

        msg.add_quality_id(selected_qi)

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        segment_throughput = msg.get_bit_length() / t
        self.throughputs.append(segment_throughput)

        self.send_up(msg)

    def human_format(self, num):
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        # add more suffixes if you need them
        return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

    def initialize(self):
        pass

    def finalization(self):
        pass