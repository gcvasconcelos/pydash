# Teleinformática e Redes 2
# Trabalho Final
# Integrantes: Luis Filipe, Alexander e Gabriel

from r2a.ir2a import IR2A
from base.whiteboard import Whiteboard
import math

class R2A_BOLA(IR2A):
    
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.segment_size = []          # S
        self.control_parameter = 0.0    # V
        self.gamma = 0.0                # g

    # Auxiliary methods
    def log_utility_function(self, bitrate_index): # v
        # bitrate_index = m
        return math.log(self.segment_size[bitrate_index]/self.segment_size[1]) 

    def optimal_solution(self,bitrate_index):
        # bitrate_index = m
        # Get Q
        buffer_level = Whiteboard.get_instance().get_amount_video_to_play()

        # Solve optimal solution
        return (self.control_parameter * (self.log_utility_function(bitrate_index) + self.gamma) - buffer_level) / self.segment_size[bitrate_index]

    # def quality_index(self):    # Choose the bitrate 

    # R2A methods
    # def handle_xml_request(self, msg):

    # def handle_xml_response(self, msg):

    # def handle_segment_size_request(self, msg):

    # def handle_segment_size_response(self, msg):

    # Initialization method (initialize the attributes that will be used by the algorithm)
    def initialize(self):
        pass

    # Finalization method (generate final statistics)
    def finalization(self):
        pass