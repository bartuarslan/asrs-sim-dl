import random
import simpy
from math import sqrt
from collections import namedtuple
from statistics import mean

run_time = 20
transaction_interval = 5  # every 5 seconds create transaction
tiers = 5
bays = 25
lengthofbay = 0.5
heightoftier = 0.35
v_lift = 2
a_lift = 2
v_shuttle = 2
a_shuttle = 2
shuttle_no = 2
# shuttleNo = [1, 2, 3, 4, 5]
shuttleNo = []
for x in range(1, shuttle_no + 1):
    shuttleNo.append(x)
lift1No = [1, 2]
"""
shuttle_locations = {
    1: {"tier": 1,
        "bay": 10},
    2: {"tier": 2,
        "bay": 10},
    3: {"tier": 3,
        "bay": 10},
    4: {"tier": 4,
        "bay": 10},
    5: {"tier": 5,
        "bay": 10}
}"""

shuttle_locations = {
    1: {"tier": 5,
        "bay": 10},
    2: {"tier": 4,
        "bay": 10},
}

lift1_locations = {
    1: 1,
    2: 3
}

bay_util = {
    1: {"bay": 0,
        "side": 0},
    2: {"bay": 0,
        "side": 0},
    3: {"bay": 0,
        "side": 0},
    4: {"bay": 0,
        "side": 0},
    5: {"bay": 0,
        "side": 0}
}

shuttle_util = [0] * shuttle_no
lift1_util = [0] * 2
shuttle_avail = [0] * shuttle_no
active_transactions = []
flowtime = []
cycletime = []
tier_avail = [0] * tiers
lift1_buffer_control = [0] * tiers
shuttle_buffer_control = [0] * tiers

for shuttle in shuttleNo:
    tier_avail[shuttle_locations[shuttle]["tier"] - 1] = shuttle

def calctime(A, maxV, d):
    """
    A       constant acceleration, m/s/s
    maxV    maximumum velocity, m/s
    return time in seconds required to travel
    d       distance, m
    """
    ta = float(maxV) / A  # time to accelerate to maxV
    da = A * ta * ta  # distance traveled during acceleration from 0 to maxV and back to 0
    if da > d:  # train never reaches full speed?
        return sqrt(4.0 * d / A)  # time needed to accelerate to half-way point then decelerate to destination
    else:
        return 2 * ta + (d - da) / maxV  # time to accelerate to maxV plus travel at maxV plus decelerate to destination


def source(env, interval):
    t_ID = 0
    while True:
        t_ID += 1
        t_type = bool(random.getrandbits(1))
        t_tier = random.randint(4, tiers)
        t_bay = random.randint(1, bays)
        t_time = env.now
        side = random.randint(1, 2)
        t_info = [t_ID, t_type, t_tier, t_bay, t_time]
        active_transactions.append(t_info)
        if t_type == 0:
            type1 = "Storage"
        else:
            type1 = "Retrieval"
        print('%7.4f %s: Created as %s, Destination tier: %s, bay: %s' % (
            env.now, t_ID, type1, t_tier, t_bay))

        t = random.expovariate(1.0 / interval)
        yield env.timeout(t)
        """
        shuttle_move = shuttle_action(env, shuttle, 1)
        env.process(shuttle_move)
        lift1_move = lift1_action(env, i + 1, type, shuttle, lift1,
                                  t_tier)
        if t_tier != 1:
            env.process(lift1_move)
        """


def shuttle_action(env, shuttle, shuttleID):
    while len(active_transactions) > 0:  # don't run when there's no transaction
        for transaction in active_transactions:
            transaction_tier = active_transactions[transaction][2] - 1
            if tier_avail[transaction_tier] == 0 or tier_avail[transaction_tier] == shuttleID:
                name = active_transactions[transaction][0]
                type = active_transactions[transaction][1]
                tier = active_transactions[transaction][2]
                bay = active_transactions[transaction][3]
                arrive = active_transactions[transaction][4]
        # Process start
        if shuttle_locations[shuttleID - 1]["tier"] != tier:
            tier_avail[tier] = shuttleID
            # todo move lift 2
        if tier != 1:
            lift1_move = lift1_action(env, name, type, shuttleID, lift1, tier)
            env.process(lift1_move)
        req1 = yield shuttle.get(lambda shuttleno: shuttleno == shuttleID)
        shuttle_avail[req1 - 1] = 1
        pickup_time = env.now
        wait = pickup_time - arrive
        print('%7.4f %s: Waited %6.3f, Chosen Shuttle: %s' % (env.now, name, wait, req1))
        if type == 0:
            move_shuttle(req1, 0, name)
            move_shuttle(req1, bay, name)
            shuttle_buffer_control[tier - 1] = name
            shuttle_avail[req1 - 1] = 0
            shuttle.put(req1)
            shuttle_time = env.now - pickup_time
            shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
            shuttle_locations[1]["bay"] = bay
            flow_time = env.now - pickup_time
            cycle_time = env.now - arrive
            flowtime.append(flow_time)
            cycletime.append(cycle_time)
            env.process(shuttle_action(env, shuttle, shuttleID))
            print('%7.4f %s: Finished Shuttle:%s, Cycle time: %7.4f' % (env.now, name, req1, cycle_time))
        else:
            move_shuttle(req1, bay, name)
            move_shuttle(req1, 0, name)
            shuttle_buffer_control[tier - 1] = name
            shuttle_avail[req1 - 1] = 0
            shuttle.put(req1)
            shuttle_time = env.now - pickup_time
            shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
            shuttle_locations[1]["bay"] = 0
            env.process(shuttle_action(env, shuttle, shuttleID))


def lift1_action(env, name, type, shuttleID, lift1, tier):
    arrive = env.now
    req2 = yield lift1.get()
    pickup_time = env.now
    if type == 0:
        move_lift1(req2, 1, name)
        move_lift1(req2, tier, name)
        lift1.put(req2)
        lift1_locations[req2] = tier
        lift1_time = env.now - pickup_time
        lift1_util[req2 - 1] = lift1_util[req2 - 1] + lift1_time
    else:
        move_lift1(req2, tier, name)
        move_lift1(req2, 1, name)
        lift1.put(req2)
        lift1_locations[req2] = 1
        flow_time = env.now - pickup_time
        cycle_time = env.now - arrive
        flowtime.append(flow_time)
        cycletime.append(cycle_time)
        lift1_util[req2 - 1] = lift1_util[req2 - 1] + flow_time
        print('%7.4f %s: Finished Lift1:%s, Cycle time: %7.4f' % (env.now, name, req2, cycle_time))

def move_lift1(lift1no, tier, name):
    lift1_travel = abs(lift1_locations[lift1no] - tier) * heightoftier
    time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel)
    t1 = env.timeout(time_lift1_travel1)
    print('%7.4f %s: Lift1:%s moving to tier %s' % (env.now, name, lift1no, tier))
    yield t1
    print('%7.4f %s: Lift1:%s moved to tier %s' % (env.now, name, lift1no, tier))

def move_shuttle(shuttleno, bay, name):
    shuttle_travel = abs(shuttle_locations[shuttleno]["bay"] - bay) * lengthofbay
    time_shuttle_travel = calctime(a_shuttle, v_shuttle, shuttle_travel)
    t1 = env.timeout(time_shuttle_travel)
    print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, shuttleno, bay))
    yield t1
    print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, shuttleno, bay))



def lift2_action(env, name, picked_shuttle, s_tier, d_tier):
    # todo make lift 2 pick up shuttle and move to destination tier
    req_lift1 = lift2.request()
    t1 = env.timeout(3)
    print('%7.4f %s: Lift 2 moving to %s tier to pick up Shuttle %s' % (env.now, name, s_tier, picked_shuttle))
    print('%7.4f %s: Lift 2 moving to tier %s' % (env.now, name, d_tier))


env = simpy.Environment()
shuttle = simpy.FilterStore(env, capacity=shuttle_no)
shuttle.items = shuttleNo
lift1 = simpy.FilterStore(env, capacity=2)
lift1.items = lift1No
lift2 = simpy.Resource(env, capacity=1)
env.process(source(env, transaction_interval))
for x in range(0, shuttle_no):
    env.process(shuttle_action(env, shuttle, x + 1))
env.run(until=run_time)
"""
shuttle_utilizations = [x / run_time for x in shuttle_util]
lift1_utilizations = [x / run_time for x in lift1_util]
print("Average cycle time is: %6.3f seconds." % mean(cycletime))
print("Average flow time is: %6.3f seconds." % mean(flowtime))
for a in range(len(shuttle_utilizations)):
    print("Shuttle %s utilization is %4.2f" % (a + 1, shuttle_utilizations[a]))
for a in range(len(lift1_utilizations)):
    print("Lift1 %s utilization is %4.2f" % (a + 1, lift1_utilizations[a]))
"""
