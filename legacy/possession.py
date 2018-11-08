from collections import namedtuple, Counter
import sqlite3, copy
from os import path
from legacy.code_mapping import event2code,team2code,code2event,code2team
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from legacy.animate_play import framePlot
import pickle, os
from legacy.data_statistics import STATS

<<<<<<< HEAD
=======
# DBFILE = os.environ['BBALLDB']

>>>>>>> f5b5a3c72f8401a3156ed75be79b875ee8eac847
Player = namedtuple('Player', ['x', 'y', 'id', 'team'])
Ball = namedtuple('Ball', ['x', 'y', 'z'])
Ref = namedtuple('Ref', ['x', 'y', 'id'])
EventRow = namedtuple('EventRow', ['gamecode', 'quarter', 'game_clock',
                                   'event_id', 'time', 
                                   'local_player_id', # not used
                                   'player_id', 'pbp_seq_num', 'shot_clock'])
FrameRow = namedtuple('FrameRow', ['gamecode', 'quarter', 'game_clock',
                                   'time', 'team_id', 'player_id',
                                   'x', 'y', 'z', 'shot_clock'])
ShotRow = namedtuple('ShotRow', ['gamecode', 'player_id', 'defender_id',
                                 'defender_dist', 'quarter', 'game_clock',
                                 'time', 'points', 'touch_time', 'dribbles',
                                 'shot_distance', 'made', 'right', 'x', 'y'])

class Possession(object):
    def __init__(self):
        self.end_timestamp = None
        self.frames = []
        self.gamecode = None
        self.points = 0
        self.start_time = None
        self.end_time = None
        self.quarter = None
        self.end_event = None
        self.fouled = False

        self.endplayer_id = None
        self.endplayer_x = None
        self.endplayer_y = None
        self.attack_right = None        
        self.expected_outcome = None

        self.shots = []
        self.num_shots = 0
        
        self.offensive_team = None
        self.defensive_team = None

    def add(self, frame):
        self.frames.append(frame)

    def set(self, frames):
        self.frames = frames
        
    def __repr__(self):
        if not self.start_time: return "Possession()"
        return "Possession(%d, %dv%d, %.1f-%.1f, q%d, %s, p%d)" % \
            (self.gamecode, self.offensive_team, self.defensive_team, self.start_time,
             self.end_time, self.quarter, self.end_event, self.points)


    def animate(self, save=True, name=None, ret=False, match=None):
        
        title = name or ("tmp_" + self.__repr__())
        fig = plt.figure()

        plt.axis('off')
        ax = plt.axes()
        plt.title(title)
        
        from legacy.court import Court
        c = Court()
        court_tuple = c.plot(ax)
        region_tuple = c.plotRegion()
        setFrameTuple, frame_tuple = framePlot(ax)
        
        def update_frame(i):
            setFrameTuple(self.frames[i], match)
            return court_tuple + frame_tuple + region_tuple
        
        self.ani = animation.FuncAnimation(fig, update_frame,
                                           frames=len(self.frames),
                                           interval=25, blit=False)
        if save:
            self.ani.save("%s.mp4" % title)
        else:
            if ret:
                return self.ani
            plt.show()
        return self.ani

class FrameInfo(namedtuple('FrameInfo', ['gamecode', 'game_clock',
                                         'quarter', 'shot_clock'])):
    def __eq__(self, other):
        return (self.gamecode == other.gamecode and
                self.game_clock == other.game_clock and
                self.quarter == other.quarter and
                self.shot_clock == other.shot_clock)
    
    def  __ne__(self, other):
        return not self.__eq__(other)
    
class Frame(object):
    def __init__(self):
        # each frame is x, y coords of 10 players, marked by player id, team id
        self.players = []
        self.ball = None
        self.refs = []
        self.frameInfo = None
        
    def __repr__(self):
        # players = str(self.players)
        # refs = str(self.refs)
        # ball = str(self.ball)
        # return '\n'.join([players, refs, ball])
        return str(self.frameInfo)
        
    def add(self, fr):
        frameInfo = FrameInfo(fr.gamecode, fr.game_clock, fr.quarter, fr.shot_clock)
        if self.frameInfo is None:
            self.frameInfo = frameInfo
        else:
            assert self.frameInfo == frameInfo, "neq frame info"
        
        if fr.team_id == -1:
            self.add_ball(fr.x, fr.y, fr.z)
        elif fr.team_id == -2:
            self.add_ref(fr.x, fr.y, fr.player_id)
        else:
            self.add_player(fr.x, fr.y, fr.team_id, fr.player_id)
        
    def add_player(self, x, y, team_id, player_id):
        assert len(self.players) < 10, "more than 10 players"
        assert len(list(filter(lambda p: p.team == team_id, self.players))) < 5,\
            "team full"
        assert len(list(filter(lambda p: p.id == player_id, self.players))) < 1,\
            "player duplicate"       
        self.players.append(Player(x, y, player_id, team_id))

    def add_ball(self, x, y, z):
        assert self.ball == None, "ball duplicate"
        self.ball = Ball(x, y, z)

    def add_ref(self, x, y, ref_id):
        assert len(self.refs) < 3, "ref more than 3"
        self.refs.append(Ref(x, y, ref_id))

class CursorWrapper:
    def __init__(self, cursor):
        self.results = []
        self.cursor = cursor
        self.done = False

    def fetchone(self):
        if len(self.results) == 0:
            self.results.append(self.cursor.fetchone())
        res = self.results[0]
        del self.results[0]
        if res is None: self.done = True
        return res

    def cache(self, result):
        self.results.append(result)

def nextframe(c): # c is a cursorWrapper, helper for load possession
    frame = Frame()
    # read until invalid frame
    line = c.fetchone()
    while line is not None:
        fr = FrameRow(*line)
        try:
            frame.add(fr)
        except Exception as e:
            # print(e.args[0])
            c.cache(fr)
            return frame
        line = c.fetchone()
    return frame

