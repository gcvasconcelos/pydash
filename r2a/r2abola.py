# Teleinformática e Redes 2
# Trabalho Final
# Integrantes: 
## Luis Filipe Campos Cardoso (19/0100079)
## Gabriel Vasconcelos (16/0120781)
## Alexander Matheus de Melo Lima (12/0108534)

from r2a.ir2a import IR2A
from base.whiteboard import Whiteboard
import math
from player.parser import *
from base.configuration_parser import ConfigurationParser

class R2ABOLA(IR2A):
    
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
        # Get Q = Buffer level
        buffer_level = Whiteboard.get_instance().get_amount_video_to_play()

        # Solve optimal solution
        return (self.control_parameter * (self.log_utility_function(bitrate_index) + self.gamma) - buffer_level) / self.segment_size[bitrate_index]

    def quality_index(self):    # Choose the bitrate that maximize the optimal_solution
        # Initialize variables
        optimal_solution_max = -math.inf
        bitrate_index_selected = None

        # Choose the bitrate that maximize the optimal_solution
        for bitrate_index in range(0, len(self.segment_size) - 1):
            optimal_solution = self.optimal_solution(bitrate_index)

            if optimal_solution_max <= optimal_solution:
                bitrate_index_selected = bitrate_index
                optimal_solution_max = optimal_solution

        return bitrate_index_selected           

    # R2A methods
    def handle_xml_request(self, msg):
        # Send the msg to the bottom layer (ConnectionHandler)
        self.send_down(msg)

    def handle_segment_size_request(self, msg):
        # Get quality of the video (bitrate)
        quality = self.quality_index()

        # Add quality to the video segment
        msg.add_quality_id(self.segment_size[quality])
        
        # Send the msg to the bottom layer (ConnectionHandler)
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # Get the payload of the mpd file
        self.parsed_mpd = parse_mpd(msg.get_payload())
        
        # List qualities
        self.qi = self.parsed_mpd.get_qi()
        self.segment_size = self.qi

        # Get buffer size max
        buffer_size_max = ConfigurationParser.get_instance().get_parameter('max_buffer_size')

        # Calculate the max value of the logarithmic utility function
        log_utility_max = self.log_utility_function(len(self.segment_size) - 1)
        
        # Calculate gamma
        self.gamma = ((buffer_size_max - 1) * (self.log_utility_function(0) * self.segment_size[1] - self.log_utility_function(1) * self.segment_size[0]) - 2 * log_utility_max * (self.segment_size[1] - self.segment_size[0])) / (1 * (self.segment_size[1] - self.segment_size[0]) * (2 - buffer_size_max - 1))

        # Calculate control parameter
        self.control_parameter = (buffer_size_max - 1) / (log_utility_max + self.gamma * 1)

        # Print results
        print('Buffer Size Max', buffer_size_max)
        print('Logarithmic Utility Max', log_utility_max)
        print('Qualities: ', self.qi)
        print('Control Parameter (Performance weight): ', self.control_parameter)
        print('Gamma (Smoothness weight): ', self.gamma)
        
        # Send the mesg to the upper layer (Player)
        self.send_up(msg)

    def handle_segment_size_response(self, msg):
        # Send the response of video segment to the upper layer (Player)
        self.send_up(msg)

    # Initialization method (initialize the attributes that will be used by the algorithm)
    def initialize(self):
        pass

    # Finalization method (generate final statistics)
    def finalization(self):
        pass