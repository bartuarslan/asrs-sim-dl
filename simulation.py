import random
import simpy
from math import sqrt
from collections import namedtuple
from statistics import mean

run_time = 30
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
#shuttleNo = [1, 2, 3, 4, 5]
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
        t_tier = random.randint(1, tiers)
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
    while len(active_transactions)>0:

        # Process start
        #req1 = yield shuttle.get(lambda shuttleno: shuttleno == tier) Known shuttle
        req1 = yield shuttle.get()
        shuttle_avail[req1-1] = 1
        print(shuttle_avail)
        pickup_time = env.now
        wait = pickup_time - arrive
        print('%7.4f %s: Waited %6.3f, Chosen Shuttle: %s' % (env.now, name, wait, req1))
        if type == 0:
            dist_to_buffer = shuttle_locations[1]["bay"] * lengthofbay
            time_to_buffer = calctime(a_shuttle, v_shuttle, dist_to_buffer)
            t2 = env.timeout(time_to_buffer)
            dist_to_drop = bay * lengthofbay
            time_to_drop = calctime(a_shuttle, v_shuttle, dist_to_drop)
            print('%7.4f %s: Shuttle:%s moving to buffer' % (env.now, name, req1))
            yield t2
            print('%7.4f %s: Shuttle:%s waiting for transaction' % (env.now, name, req1))
            print('%7.4f %s: Shuttle:%s picked up transaction' % (env.now, name, req1))
            yield env.timeout(time_to_drop)
            print('%7.4f %s: Shuttle:%s moved to drop off location' % (env.now, name, req1))
            shuttle_locations[1]["bay"] = bay
            flow_time = env.now - pickup_time
            cycle_time = env.now - arrive
            flowtime.append(flow_time)
            cycletime.append(cycle_time)
            shuttle_avail[req1-1] = 0
            shuttle.put(req1)
            print('%7.4f %s: Finished Shuttle:%s, Cycle time: %7.4f, bay location %s' % (
                    env.now, name, req1, cycle_time, shuttle_locations[1]["bay"]))
            shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + flow_time
        else:
            dist_to_bay = abs(shuttle_locations[1]["bay"] - bay) * lengthofbay
            time_to_bay = calctime(a_shuttle, v_shuttle, dist_to_bay)
            dist_to_buffer = bay * lengthofbay
            time_to_buffer = calctime(a_shuttle, v_shuttle, dist_to_buffer)
            time_total_shuttle = time_to_bay + time_to_buffer
            t1 = env.timeout(time_total_shuttle)
            yield t1
            print('%7.4f %s: Shuttle:%s moved to buffer' % (env.now, name, req1))
            shuttle.put(req1)
            shuttle_time = env.now - pickup_time
            shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
            shuttle_locations[1]["bay"] = 0
            flow_time = env.now - pickup_time
            cycle_time = env.now - arrive
            flowtime.append(flow_time)
            cycletime.append(cycle_time)

def lift1_action(env, name, type, shuttle, lift1, tier):
    arrive = env.now
    req2 = yield lift1.get()
    pickup_time = env.now
    wait = pickup_time - arrive
    if type == 0:
        lift1_travel1 = abs(lift1_locations[req2] - 1) * heightoftier
        time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
        lift1_travel2 = (tier - 1) * heightoftier
        time_lift1_travel2 = calctime(a_lift, v_lift, lift1_travel2)
        time_total_lift1 = time_lift1_travel1 + time_lift1_travel2
        t1 = env.timeout(time_total_lift1)
        print('%7.4f %s: Lift1:%s moving to I/O point and destination tier %s' % (env.now, name, req2, tier))
        yield t1
        lift1.put(req2)
        lift1_locations[req2] = tier
        print('%7.4f %s: Lift1:%s drop transaction at destination tier %s' % (env.now, name, req2, tier))
        lift1_time = env.now - pickup_time
        lift1_util[req2 - 1] = lift1_util[req2 - 1] + lift1_time
        flow_time = env.now - pickup_time
        cycle_time = env.now - arrive
        flowtime.append(flow_time)
        cycletime.append(cycle_time)
    else:
        lift1_travel1 = abs(lift1_locations[req2] - tier) * heightoftier
        time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
        lift1_travel2 = (tier - 1) * heightoftier
        time_lift1_travel2 = calctime(a_lift, v_lift, lift1_travel2)
        t2 = env.timeout(time_lift1_travel1)
        yield t2
        print('%7.4f %s: Lift1:%s waiting for shuttle' % (env.now, name, req2))
        print('%7.4f %s: Lift1:%s picked up transaction from tier %s' % (env.now, name, req2, tier))
        print('%7.4f %s: Lift1:%s moving to I/O point' % (env.now, name, req2))
        yield env.timeout(time_lift1_travel2)
        print('%7.4f %s: Lift1:%s moved to I/O point' % (env.now, name, req2))
        flow_time = env.now - pickup_time
        cycle_time = env.now - arrive
        flowtime.append(flow_time)
        cycletime.append(cycle_time)
        lift1.put(req2)
        lift1_locations[req2] = 1
        lift1_util[req2 - 1] = lift1_util[req2 - 1] + flow_time
        print('%7.4f %s: Finished Lift1:%s, Cycle time: %7.4f' % (env.now, name, req2, cycle_time))


def lift2_action(env, name,picked_shuttle,s_tier, d_tier):
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
    env.process(shuttle_action(env, shuttle, x+1))
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