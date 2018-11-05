from legacy.court import Court
from legacy.possession import ShotRow
from collections import defaultdict
import sqlite3, os

DBFILE = os.environ['BBALLDB']

def reward(location, average, player_id=None, time=None, mix=True):
    sql_parts = []
    if player_id is not None:
        sql_parts.append("player_id = %s" % str(player_id))
    if time is not None:
        sql_parts.append("time < %s" % str(time))

    sql = "select * from shots"
    if len(sql_parts) != 0:
        sql += " where " + " and ".join(sql_parts)
    
    return reward_(sql, location, average, mix)

# mix is whether mix average or not with actual
def reward_(sql, location, average, mix=True):
    made2, made3, missed = actual_shots_(sql)
    # calculate statistics
    totalshots = made2[location] + missed[location] + made3[location]    
    if made2[location] == 0:
        actual2 = 0
    else:
        actual2 = made2[location] / totalshots * 2

    if made3[location] == 0:
        actual3 = 0
    else:
        actual3 = made3[location] / totalshots * 3

    if totalshots == 0:
        mixing = 1
    else:
        mixing = 1 / totalshots

    if not mix: mixing = 0

    actual = actual2 + actual3

    if __name__ == '__main__':
        print("location: %d, mixing: %.4f, actual: %.4f, average: %.4f" % \
              (location, mixing, actual, average))
    return (1-mixing) * actual + mixing * average
    
def actual_shots_(sql):
    made2 = defaultdict(int)
    made3 = defaultdict(int)
    missed = defaultdict(int)
    
    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()

    court = Court()
    shots = c.execute(sql)
    for i, item in enumerate(shots):
        shot = ShotRow(*item)

        if not shot.x or not shot.y:
            # inner_c = conn.cursor()
            # # get from frame data the location based on player_id, gamecode,
            # # quarter, and game_clock
            # sqlxy = '''select x, y from frames where time > % d and time < %d 
            #             and player_id = %d'''\
            #             % (shot.time-50, shot.time+50, shot.player_id)
            # resxy = inner_c.execute(sqlxy).fetchone()
            # if resxy is None:
            #     continue
            # else: shot_x, shot_y = resxy
            continue
        else: shot_x, shot_y = shot.x, shot.y
            
        if i % 1000 == 0 and i != 0 and __name__ == '__main__':
            print("shot number %d" % i)
        region = court.region([(shot_x, shot_y)])[0]

        # todo: could use fractional weight to denote recent vs. historical
        weight = 1
        if shot.made == 1:
            if shot.points == 2:
                made2[region] += weight
            else:
                made3[region] += weight
        else:
            missed[region] += weight

    conn.close()
    return made2, made3, missed

def reward_locations(locations, player_id=None, time=None):
    sql_parts = []
    if player_id is not None:
        sql_parts.append("player_id = %s" % str(player_id))
    if time is not None:
        sql_parts.append("time < %s" % str(time))

    sql = "select * from shots"
    if len(sql_parts) != 0:
        sql += " where " + " and ".join(sql_parts)

    made2, made3, missed = actual_shots_(sql)

    twos = sum([made2[l] for l in locations])
    threes = sum([made3[l] for l in locations])
    zeros = sum([missed[l] for l in locations])

    return twos / (twos + threes + zeros) * 2  + threes / (twos + threes + zeros) * 3 


if __name__ == '__main__':
    player_id = '329525' # kd
    time = '1596885488761' # game 3 of 2017 finals
    locations = [12,13,14,15,16,17,18]#range(18)

    # print(reward_locations(locations, player_id, time))
    # print(reward_locations(locations))    

    average = reward(12, average=0, time=time, mix=False)
    
    # rewards = []
    # for location in locations:
    #     average = 1
    #     rewards.append(reward(location, average, player_id, time, mix=True))
    # print(rewards)
