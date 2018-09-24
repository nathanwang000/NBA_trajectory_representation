from collections import namedtuple, Counter
import sqlite3, copy
from os import path
from legacy.code_mapping import event2code,team2code,code2event,code2team
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from legacy.animate_play import framePlot
import pickle, os
from legacy.data_statistics import STATS

DBFILE = os.environ['BBALLDB']

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
        
        from court import Court
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
        
def loadPossession(game_file_path="cavs_games.txt", gamecodes=None):
    '''
    gamecodes overwrite game file path, for backward compatability
    '''
    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()

    # to discuss: does offensive rebounding count as a new pocession?
    # http://www.insidehoops.com/forum/showthread.php?t=275964
    start_events = (event2code["Possession"],
                    event2code["Pass"],
                    event2code["Dribble"])

    end_events = (event2code["Field Goal Made"], # could follow possession or dribble
                  event2code["Field Goal Missed"], # the ball could go out of bound
                  # todo: handle missed rebound
                  # event2code["Defensive Rebound"], # imediately start a new pocession
                  event2code["Turnover"], # could follow dribble or possession
                  event2code["Foul"] # could follow free throw, pass,dribble,possession
    ) + tuple(range(9,21)) # treat all unknown codes as end events

    # design choice: only use after 2014702 data so that x, y are in shot
    # design choice: only use cavs games
    time_shot_xy = 1404273600000
    sqlpend = '''select * from events where time > %d and event_id in %s''' \
              % (time_shot_xy, str(end_events))

    # use game_file_path to find games to include
    if gamecodes is None and os.path.exists(game_file_path):
        with open(game_file_path) as f:
            codes = tuple(map(lambda gamecode: gamecode.strip(), f.readlines()))
            sqlpend += " and gamecode in (%s)" % ",".join(codes)

    if gamecodes is not None:
        sqlpend += "and gamecode in (%s)" % ",".join(map(str, gamecodes))

    possession_end = c.execute(sqlpend)

    EPSILON = 2 # allow 2 s for determining free throw

    # find the start of a possession
    for i, p_end in enumerate(possession_end):
        innerc = conn.cursor()
        
        pe = EventRow(*p_end)

        # deal with foul: find if freethrow or not in the surrounding 2s
        # if freethrow, this is the end of a possession
        # note that foul could be offensive or defensive
        free_throw_points = 0
        fouled = (pe.event_id == event2code['Foul'])

        if pe.event_id in (event2code["Field Goal Made"],
                           event2code["Foul"],
                           event2code["Field Goal Missed"]):

            # check freethrow
            free_throw = (event2code["Free Throw Made"], event2code["Free Throw Missed"])
            sql_freethrow = '''select * from events where gamecode = %d  and 
            event_id in %s and quarter = %d and game_clock < %f and 
            game_clock > %f''' % (pe.gamecode, str(free_throw), pe.quarter,
                                  pe.game_clock + EPSILON, pe.game_clock - EPSILON)

            freeThrow = innerc.execute(sql_freethrow)
            for item in freeThrow:
                fouled = True
                ft = EventRow(*item)
                free_throw_points += int(ft.event_id == event2code["Free Throw Made"])
                
            
        try:
            sqlprevpe = '''select *, max(time) from events where gamecode = %d and
            pbp_seq_num != '' and event_id in %s and time < %f 
            and quarter = %d''' % (pe.gamecode, str(end_events), pe.time, pe.quarter)

           
            prevpe = innerc.execute(sqlprevpe).fetchone()
        except:
            STATS['bad query'] += 1
            STATS['total possession'] += 1
            continue

        if prevpe[-1] is None:
            # default to begining of a quarter
            sqlqbegin = '''select min(time) from events where gamecode = %d and 
                           quarter = %d''' % (pe.gamecode, pe.quarter)
            prevpetime = innerc.execute(sqlqbegin).fetchone()[0]
            prevpe = EventRow(pe.gamecode, pe.quarter, 720, pe.event_id,
                              prevpetime, pe.local_player_id, pe.player_id,
                              pe.pbp_seq_num, 24)
        else:
            prevpe = EventRow(*prevpe[:-1])
        
        sqlstart = '''select *, min(time) from events where gamecode = %d and 
        event_id in %s and time < %f and time >= %f'''\
            % (pe.gamecode, str(start_events), pe.time,
               prevpe.time)

        ps = EventRow(*innerc.execute(sqlstart).fetchone()[:-1])

        # ps may be empty due to the following reasons
        # add one (3,8) / turn over (7,8) / missed free three
        if ps.gamecode is None: continue

        # ignore too short game play if it is shot followed by foul
        if pe.event_id == event2code['Foul'] and \
           ps.event_id in [event2code['Field Goal Made'],
                           event2code['Field Goal Missed']] and \
           abs(ps.game_clock - pe.game_clock) < EPSILON:
            continue
            
        
        # now we known ps and pe
        # print("ps:", ps, "\npe:", pe)
        
        # pool from shot data tod determine points made
        possession = Possession()

        # collect missed shot in this possession as penalty
        # sqlshots = '''select player_id, x, y, time from shots where gamecode = %s and
        #              quarter = %d and time < %f and time > %f'''\
        #                  % (ps.gamecode, ps.quarter, pe.time+1000, ps.time)
        sqlshots = '''select * from shots where 
                     gamecode = %s and quarter = %d and time <= %f and time > %f'''\
                         % (ps.gamecode, ps.quarter, pe.time, ps.time)


        for item in innerc.execute(sqlshots):
            sr = ShotRow(*item)
            if not sr.x or not sr.y:
                continue # ignore 2013-2014 shots data
            possession.shots.append(sr)
            possession.num_shots += 1
            if sr.made == 1:            
                possession.points += sr.points
            # print(code2event.get(pe.event_id), sr.made, type(sr.made))
            # print(sr.game_clock)

        # fetch the frames in between and visualize
        innerc.execute('''select * from frames where gamecode = %d and 
        time >= %d and time <= %d 
        order by time''' % (ps.gamecode, ps.time, pe.time))

        # use frame reader to grab next frames one by one
        innerc_wrapper = CursorWrapper(innerc)

        possession.gamecode = ps.gamecode
        possession.start_time = ps.game_clock
        possession.end_time = pe.game_clock
        possession.quarter = pe.quarter
        possession.end_event = code2event.get(pe.event_id, "unknown" + str(pe.event_id))
        possession.end_timestamp = pe.time
        
        while not innerc_wrapper.done:
            frame = nextframe(innerc_wrapper)
            possession.add(frame)

        try:
            f = possession.frames[0]

            teams = list(Counter(map(lambda p: p.team, f.players)).keys())
            p = list(filter(lambda p: p.id == ps.player_id, f.players))[0]

            if p.team == teams[1]: teams[0], teams[1] = teams[1], teams[0]
            possession.offensive_team = teams[0]
            possession.defensive_team = teams[1]

            fend = possession.frames[-1]
            p = list(filter(lambda p: p.id == pe.player_id, fend.players))[0]
        except:
            # todo: 2014102824.csv has issue with player, figure out why
            # now just continue
            STATS['bad frame possession'] += 1
            STATS['total possession'] += 1
            continue
        
        possession.endplayer_id = p.id
        possession.endplayer_x = p.x
        possession.endplayer_y = p.y

        # check who make free throw
        if possession.end_event == event2code["Foul"]  and \
           p.team == possession.offensive_team:
            free_throw_points = -free_throw_points # positive for the defense

        possession.points += free_throw_points
        possession.fouled = fouled
        
        # print("pe:", pe)
        # print("prevpe:", prevpe)
        # print("ps:", ps)

        yield possession

if __name__ == '__main__':
    test = 1
    for possession in loadPossession():
        print(possession)
        test -= 1
        if test == 0:
            # possession.animate(save=True)
            pickle.dump(possession, open('tmp_possession.pkl', 'wb'))
            break




