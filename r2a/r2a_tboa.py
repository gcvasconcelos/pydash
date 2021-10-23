from r2a.ir2a import IR2A
from player.parser import *
import time
from statistics import mean

import pdb


class R2A_TBOA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.selected_qis = [46980]
        self.qi = []
        self.request_time = 0
        self.playback_step = 1

        # TBOA parameters
        self.smooth_coeffiecient = 0.8
        self.buffer_min = 5
        self.buffer_low = 10
        self.buffer_high = 25

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):

        t = time.perf_counter() - self.request_time
        xml_throughput = (msg.get_bit_length() / t) * self.playback_step
        self.throughputs.append(xml_throughput)

        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        self.send_up(msg)

    def estimate_throughput(self, index):
        '''
            estimation based on last values, using smoothing techniques to
            reduce high frequency throughput fluctuations
        '''
        alpha = self.smooth_coeffiecient
        if index == 1:
            return self.throughputs[index-1]
        else:
            # estimate made 80% of last throughput value and 20% of last
            # throughput estimate
            return (
                alpha * self.throughputs[index-1]
                + (1 - alpha) * self.estimate_throughput(index-1)
            )

    def calculate_buffer_occuppancy(self):
        '''
            checking buffer health, to help to decide bitrate change decision
            and avoid drainage when increasing bitrate
        '''
        # estimating the download time based on last quality selected and the
        # smoothed throughput
        last_qi = self.selected_qis[-1]
        # estimated_throughput = self.throughputs[-1]
        estimated_throughput = self.estimate_throughput(len(self.throughputs))
        download_time = last_qi / estimated_throughput

        # getting current buffer level
        last_buffer_level = self.whiteboard.get_amount_video_to_play()

        # if buffer_level <= 0, pauses may happen because the download time is
        # higher than the buffer level
        buffer_level = last_buffer_level + self.playback_step - download_time
        # pdb.set_trace()

        return estimated_throughput, buffer_level, last_buffer_level

    def max_possible_quality(self, throughput, buffer_level, buffer_treshold):
        '''
            maximizes the possible quality, while being lower than the given
            throughput and with enough buffer level
        '''
        selected_qi = self.qi[0]
        for quality in self.qi:
            if quality <= throughput:
                download_time = quality / throughput

                buffer_pred = buffer_level - (
                    download_time / self.playback_step)
                if buffer_pred > buffer_treshold:
                    selected_qi = quality

        return selected_qi


    def handle_segment_size_request(self, msg):

        estimated_throughput, buffer_level, last_buffer_level = \
            self.calculate_buffer_occuppancy()

        # network conditions are unknown at the beggining, so fill buffer with
        # worst quality until minimum size reached
        if buffer_level <= self.buffer_min:
            selected_qi = self.qi[0]
        # use the quality lesser than the estimated throughput to ensure
        # seamless playback, until low treshold is reached
        elif buffer_level <= self.buffer_low:
            selected_qi = self.max_possible_quality(
                estimated_throughput, buffer_level, self.buffer_min)
        # between low and high treshold, if some conditions related to the
        # buffer health are met, increase bitrate quality
        elif buffer_level <= self.buffer_high:
            last_qi = self.selected_qis[-1]

            if last_qi != self.selected_qis[19]:
                next_qi = self.qi(self.qi.index(last_qi)+1)
                # double checking if next quality will be supported by
                # throughput
                if next_qi <= estimated_throughput:
                    buffer_delta = buffer_level - last_buffer_level
                    if buffer_delta > 0:
                        selected_qi = next_qi
            else:
                selected_qi = last_qi
        # keep maximum possible quality
        elif buffer_level > self.buffer_high:
            # waiting time is calculated to avoid buffer overflow but this is
            # ignored in this implementation, since the pydash algorithm
            # already deals with this issue
            last_qi = self.selected_qis[-1]
            waiting_time = (buffer_level - self.buffer_low -
                (last_qi * self.playback_step)/ self.qi[0])

            if waiting_time > 0:
                # time.sleep(waiting_time)
                selected_qi = self.max_possible_quality(
                    estimated_throughput, buffer_level, self.buffer_low)
            else:
                selected_qi = self.max_possible_quality(
                    estimated_throughput, buffer_level, self.buffer_low)

        self.selected_qis.append(selected_qi)


        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(f'BUFFER LEVEL \t {buffer_level}')
        print(f'SELECTED QI \t {self.human_format(selected_qi)}')
        print(f'EST THROUGHPUT \t {self.human_format(estimated_throughput)}')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        # pdb.set_trace()
        msg.add_quality_id(selected_qi)

        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        segment_throughput = (msg.get_bit_length() / t) * self.playback_step
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