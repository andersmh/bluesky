""" This plugin manages all the data loggers for my master thesis project. """
# Import the global bluesky objects. Uncomment the ones you need
from genericpath import exists

from numpy import delete
# , settings, navdb, sim, scr, tools
from bluesky import core, traf, stack, scr, sim, navdb
from bluesky.tools import datalog, calculator
from bluesky.traffic import route


# List of the names of all the data loggers
loggers = ['UAV_LOG', 'CONFLICT_LOG',
           'LOSS_OF_SEPARATION_LOG']

# The data loggers
uav_log = None
conflict_log = None
loss_of_separation_log = None
update_interval = 1.0

# Parameters used when logging
uav_log_header = \
    'UAV LOG\n' + \
    'Information about all of the UAVs\n\n' + \
    'Deletion Time [s], UAVX, Distance Traveled'

conflict_log_header = \
    'CONFLICTS LOG\n' + \
    'List of all conflict instances\n\n' + \
    'Simulation Time [s], UAVX, UAVY'

loss_of_separation_log_header = \
    'LOSS OF SEPARATION LOG\n' + \
    'List of all LoS instances\n\n' + \
    'Simulation Time [s], UAVX, UAVY, Distance between'



# Initialisation function of your plugin. Do not change the name of this
# function, as it is the way BlueSky recognises this file as a plugin.


def init_plugin():
    ''' Plugin initialisation function. '''
    # Instantiate the UsepeLogger entity
    loggy = Loggy()

    # Create the loggers
    global uav_log
    global conflict_log
    global loss_of_separation_log

    uav_log = datalog.crelog('UAV_LOG', None, uav_log_header)
    conflict_log = datalog.crelog('CONFLICT_LOG', None, conflict_log_header)
    loss_of_separation_log = datalog.crelog(
        'LOSS_OF_SEPARATION_LOG', None, loss_of_separation_log_header)


    # Configuration parameters
    config = {
        'plugin_name':     'LOGGY',
        'plugin_type':     'sim',
        'update_interval': update_interval,
        'update': loggy.update
    }

    stackfunctions = {
        'LOGGY': [
            'LOGGY LIST/ON',
            'txt',
            loggy.loggy,
            'List/enable all the available data loggers'
        ]
    }

    # init_plugin() should always return a configuration dict.
    return config, stackfunctions


class Loggy(core.Entity):
    ''' Provides the needed funcionality for each log. '''

    def __init__(self):
        super().__init__()

        self.previous_active_uavs = list()
        self.previous_active_uavs_distance_flown = dict()

    def update(self):
        ''' Periodic function calling each logger function. '''
        self.uav_logger()
        self.conflict_logger()
        self.loss_of_separation_logger()

    def conflict_logger(self):
        ''' Sorts current conflicts and logs new and ended events. '''
        if len(traf.cd.confpairs_unique) > 0:
            for pair in traf.cd.confpairs_unique:
                index = 0
                uav_1 = ''
                uav_2 = ''
                for value in pair:
                    if index == 0:
                        uav_1 = value
                        index = index + 1
                    else:
                        uav_2 = value
                        index = index + 1

                conflict_log.log(uav_1, uav_2)

    def loss_of_separation_logger(self):
        ''' Logs every unique LoS '''
        
        if len(traf.cd.lospairs_unique) > 0:
            for pair in traf.cd.lospairs_unique:
                index = 0

                uav_1 = ''
                uav_1_coordinates = (0.0, 0.0)

                uav_2 = ''
                uav_2_coordinates = (0.0, 0.0)

                for value in pair:
                    if index == 0:
                        uav_1 = value
                        idx = traf.id2idx(value)
                        uav_1_coordinates = (traf.lat[idx], traf.lon[idx])
                        index = index + 1

                    else:
                        uav_2 = value
                        idx = traf.id2idx(value)
                        uav_2_coordinates = (traf.lat[idx], traf.lon[idx])
                        index = index + 1

                distance_between_the_two_uavs = calculator.latlondist(float(uav_1_coordinates[0]), float(uav_1_coordinates[1]), float(uav_2_coordinates[0]), float(uav_2_coordinates[1]),)
                loss_of_separation_log.log(uav_1, uav_2, distance_between_the_two_uavs)
        

    def uav_logger(self):
        currently_active_uavs = traf.id
        temp_previous_active_uavs = self.previous_active_uavs

        for uav in currently_active_uavs:
            idx = traf.id2idx(uav)
            self.previous_active_uavs_distance_flown[uav] = traf.distflown[idx]


    
        # Checks if all the active aircrafts are added to the previous_uavs list
        result = all(elem in temp_previous_active_uavs  for elem in currently_active_uavs)

        if not result:
            s = set(temp_previous_active_uavs)
            difference = [x for x in currently_active_uavs if x not in s]
            
            changable_previous_active_uavs = temp_previous_active_uavs
            changable_previous_active_uavs.extend(difference)
            
            self.previous_active_uavs = changable_previous_active_uavs

        s = set(currently_active_uavs)
        deleted_uavs = [x for x in temp_previous_active_uavs if x not in s]
        
        if len(deleted_uavs) > 0:
            sanitized_currently_active_uavs = [x for x in self.previous_active_uavs if x not in deleted_uavs]
            for uav in deleted_uavs:

                uav_log.log(uav, self.previous_active_uavs_distance_flown[uav])
                
                del self.previous_active_uavs_distance_flown[uav]

            self.previous_active_uavs = sanitized_currently_active_uavs
            
           
        

    def loggy(self, cmd):
        ''' LOGGY command for the plugin.
            Options:
            LIST: List all the available data loggers for the project
            ON: Enable all the data loggers '''
        if cmd == 'LIST':
            return True, f'Available data loggers: {str.join(", ", loggers)}'
        elif cmd == 'ON':
            for x in range(len(loggers)):
                stack.stack(f'{loggers[x]} ON')
            return True, f'All data loggers for USEPE enabled.'
        else:
            return False, f'Available commands are: LIST, ON'
