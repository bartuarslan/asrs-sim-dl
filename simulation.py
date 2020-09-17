import random
import simpy
from math import sqrt
from collections import namedtuple
from statistics import mean

run_time = 1000
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

lift2_location = [3]

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
lift1_avail = [0] * 2
active_transactions = []
flowtime = []
cycletime = []
tier_avail = [0] * tiers
lift1_buffer_control = [0] * tiers
shuttle_buffer_control = [0] * tiers
proc_check = [0] * shuttle_no

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

        if proc_check[0] == 0:
            env.process(shuttle_action1(env, shuttle))

        #if proc_check[1] == 0:
        #    env.process(shuttle_action2(env, shuttle))

        t = random.expovariate(1.0 / interval)
        yield env.timeout(t)


def shuttle_action1(env, shuttle, shuttleID=1):
    while True:
        proc_check[0] = 1
        if len(active_transactions) > 0 and shuttle_avail[shuttleID - 1] == 0:
            name = ""
            for transaction in range(len(active_transactions)):
                transaction_tier = active_transactions[transaction][2] - 1
                if tier_avail[transaction_tier] == 0 or tier_avail[transaction_tier] == shuttleID:
                    name = active_transactions[transaction][0]
                    type = active_transactions[transaction][1]
                    tier = active_transactions[transaction][2]
                    bay = active_transactions[transaction][3]
                    arrive = active_transactions[transaction][4]
                    del active_transactions[transaction]
                    break
            # Process start
            if name != "":

                req1 = yield shuttle.get(lambda shuttleno: shuttleno == shuttleID)
                shuttle_avail[req1 - 1] = name
                tier_avail[tier - 1] = shuttleID
                pickup_time = env.now
                wait = pickup_time - arrive
                print('%7.4f %s: Waited %6.3f, Chosen Shuttle: %s' % (env.now, name, wait, req1))

                if tier != 1:
                    lift1_move = lift1_action(env, name, type, shuttleID, lift1, tier, bay, arrive)
                    env.process(lift1_move)
                elif tier == 1:
                    lift1_buffer_control[0] = name
                if shuttle_locations[shuttleID]["tier"] != tier:
                    temp_tier = shuttle_locations[shuttleID]["tier"]
                    s_travel1 = abs(shuttle_locations[req1]["bay"] - bays) * lengthofbay
                    t_st1 = calctime(a_shuttle, v_shuttle, s_travel1)
                    l2_travel1 = abs(lift2_location[0] - temp_tier) * heightoftier
                    t_l2t = calctime(a_lift, v_lift, l2_travel1)
                    l2_travel2 = abs(tier - temp_tier) * heightoftier
                    t_l2t2 = calctime(a_lift, v_lift, l2_travel2)
                    req_lift2 = lift2.request()
                    yield req_lift2
                    to1 = env.timeout(t_st1)
                    to2 = env.timeout(t_l2t)
                    print('%7.4f %s: Shuttle:%s moving to Lift 2 buffer' % (env.now, name, req1))
                    print('%7.4f %s: Lift 2 moving to %s tier to pick up Shuttle %s' % (
                    env.now, name, temp_tier, shuttleID))
                    yield to1 & to2
                    print('%7.4f %s: Shuttle:%s moved to Lift 2 buffer' % (env.now, name, req1))
                    to3 = env.timeout(t_l2t2)
                    tier_avail[temp_tier - 1] = 0
                    print('%7.4f %s: Lift 2 moving to tier %s' % (env.now, name, tier))
                    yield to3
                    print('%7.4f %s: Lift 2 moved to tier %s' % (env.now, name, tier))
                    shuttle_locations[shuttleID]["tier"] = tier
                    shuttle_locations[shuttleID]["bay"] = bays
                    lift2.release(req_lift2)
                if type == 0:

                    shuttle_travel1 = abs(shuttle_locations[req1]["bay"] - 0) * lengthofbay
                    time_shuttle_travel1 = calctime(a_shuttle, v_shuttle, shuttle_travel1)
                    shuttle_travel2 = bay * lengthofbay
                    time_shuttle_travel2 = calctime(a_shuttle, v_shuttle, shuttle_travel2)
                    t1 = env.timeout(time_shuttle_travel1)
                    print('%7.4f %s: Shuttle:%s moving to buffer' % (env.now, name, req1))
                    yield t1
                    print('%7.4f %s: Shuttle:%s moved to buffer' % (env.now, name, req1))
                    shuttle_buffer_control[tier - 1] = name
                    if lift1_buffer_control[tier - 1] == name:
                        t2 = env.timeout(time_shuttle_travel2)
                        print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, req1, bay))
                        yield t2
                        print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, req1, bay))

                        shuttle_avail[req1 - 1] = 0
                        shuttle.put(req1)
                        shuttle_time = env.now - pickup_time
                        shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
                        shuttle_locations[shuttleID]["bay"] = bay
                        flow_time = env.now - pickup_time
                        cycle_time = env.now - arrive
                        flowtime.append(flow_time)
                        cycletime.append(cycle_time)
                        env.process(shuttle_action1(env, shuttle, shuttleID))
                        print('%7.4f %s: Finished Shuttle:%s, Cycle time: %7.4f' % (env.now, name, req1, cycle_time))
                else:
                    shuttle_travel1 = abs(shuttle_locations[req1]["bay"] - bay) * lengthofbay
                    time_shuttle_travel1 = calctime(a_shuttle, v_shuttle, shuttle_travel1)
                    shuttle_travel2 = bay * lengthofbay
                    time_shuttle_travel2 = calctime(a_shuttle, v_shuttle, shuttle_travel2)
                    ts1 = env.timeout(time_shuttle_travel1)

                    print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, req1, bay))
                    yield ts1
                    print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, req1, bay))

                    ts2 = env.timeout(time_shuttle_travel2)
                    print('%7.4f %s: Shuttle:%s moving to buffer' % (env.now, name, req1))
                    yield ts2
                    print('%7.4f %s: Shuttle:%s moved to buffer' % (env.now, name, req1))

                    shuttle_buffer_control[tier - 1] = name
                    shuttle_avail[req1 - 1] = 0
                    shuttle.put(req1)
                    shuttle_time = env.now - pickup_time
                    shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
                    shuttle_locations[shuttleID]["bay"] = 0
                    if lift1_buffer_control[tier - 1] == name:
                        for no_lift1 in range(2):
                            if lift1_avail[no_lift1] == name:
                                lift1_travel1 = abs(1 - tier) * heightoftier
                                time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
                                tl1 = env.timeout(time_lift1_travel1)

                                print('%7.4f %s: Lift1:%s moving to I/O' % (env.now, name, no_lift1+1))
                                yield tl1
                                print('%7.4f %s: Lift1:%s moved to I/O' % (env.now, name, no_lift1+1))

                                lift1.put(no_lift1+1)
                                lift1_locations[no_lift1+1] = 1
                                lift1_avail[no_lift1] = 0
                                flow_time = env.now - pickup_time
                                cycle_time = env.now - arrive
                                flowtime.append(flow_time)
                                cycletime.append(cycle_time)
                                lift1_util[no_lift1] = lift1_util[no_lift1] + flow_time
                                print('%7.4f %s: Finished Lift1:%s, Cycle time: %7.4f' % (
                                env.now, name, no_lift1+1, cycle_time))
                                if proc_check[0] == 0:
                                    env.process(shuttle_action1(env, shuttle))
                                break
            else:
                proc_check[0] = 0
                break
        else:
            proc_check[0] = 0
            break


def shuttle_action2(env, shuttle, shuttleID=2):
    while True:
        proc_check[1] = 1
        if len(active_transactions) > 0 and shuttle_avail[shuttleID - 1] == 0:
            name = ""
            for transaction in range(len(active_transactions)):
                transaction_tier = active_transactions[transaction][2] - 1
                if tier_avail[transaction_tier] == 0 or tier_avail[transaction_tier] == shuttleID:
                    name = active_transactions[transaction][0]
                    type = active_transactions[transaction][1]
                    tier = active_transactions[transaction][2]
                    bay = active_transactions[transaction][3]
                    arrive = active_transactions[transaction][4]
                    del active_transactions[transaction]
                    break
            # Process start
            if name != "":

                req1 = yield shuttle.get(lambda shuttleno: shuttleno == shuttleID)
                shuttle_avail[req1 - 1] = name
                tier_avail[tier - 1] = shuttleID
                pickup_time = env.now
                wait = pickup_time - arrive
                print('%7.4f %s: Waited %6.3f, Chosen Shuttle: %s' % (env.now, name, wait, req1))

                if tier != 1:
                    lift1_move = lift1_action(env, name, type, shuttleID, lift1, tier, bay, arrive)
                    env.process(lift1_move)
                elif tier == 1:
                    lift1_buffer_control[0] = name
                if shuttle_locations[shuttleID]["tier"] != tier:
                    temp_tier = shuttle_locations[shuttleID]["tier"]
                    s_travel1 = abs(shuttle_locations[req1]["bay"] - bays) * lengthofbay
                    t_st1 = calctime(a_shuttle, v_shuttle, s_travel1)
                    l2_travel1 = abs(lift2_location[0] - temp_tier) * heightoftier
                    t_l2t = calctime(a_lift, v_lift, l2_travel1)
                    l2_travel2 = abs(tier - temp_tier) * heightoftier
                    t_l2t2 = calctime(a_lift, v_lift, l2_travel2)
                    req_lift2 = lift2.request()
                    yield req_lift2
                    to1 = env.timeout(t_st1)
                    to2 = env.timeout(t_l2t)
                    print('%7.4f %s: Shuttle:%s moving to Lift 2 buffer' % (env.now, name, req1))
                    print('%7.4f %s: Lift 2 moving to %s tier to pick up Shuttle %s' % (
                    env.now, name, temp_tier, shuttleID))
                    yield to1 & to2
                    print('%7.4f %s: Shuttle:%s moved to Lift 2 buffer' % (env.now, name, req1))
                    to3 = env.timeout(t_l2t2)
                    tier_avail[temp_tier - 1] = 0
                    print('%7.4f %s: Lift 2 moving to tier %s' % (env.now, name, tier))
                    yield to3
                    print('%7.4f %s: Lift 2 moved to tier %s' % (env.now, name, tier))
                    shuttle_locations[shuttleID]["tier"] = tier
                    shuttle_locations[shuttleID]["bay"] = bays
                    lift2.release(req_lift2)
                if type == 0:

                    shuttle_travel1 = abs(shuttle_locations[shuttleID]["bay"] - 0) * lengthofbay
                    time_shuttle_travel1 = calctime(a_shuttle, v_shuttle, shuttle_travel1)
                    shuttle_travel2 = bay * lengthofbay
                    time_shuttle_travel2 = calctime(a_shuttle, v_shuttle, shuttle_travel2)
                    t1 = env.timeout(time_shuttle_travel1)
                    print('%7.4f %s: Shuttle:%s moving to buffer' % (env.now, name, req1))
                    yield t1
                    print('%7.4f %s: Shuttle:%s moved to buffer' % (env.now, name, req1))
                    shuttle_buffer_control[tier - 1] = name
                    if lift1_buffer_control[tier - 1] == name:
                        t2 = env.timeout(time_shuttle_travel2)
                        print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, req1, bay))
                        yield t2
                        print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, req1, bay))

                        shuttle_avail[req1 - 1] = 0
                        shuttle.put(req1)
                        shuttle_time = env.now - pickup_time
                        shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
                        shuttle_locations[shuttleID]["bay"] = bay
                        flow_time = env.now - pickup_time
                        cycle_time = env.now - arrive
                        flowtime.append(flow_time)
                        cycletime.append(cycle_time)
                        env.process(shuttle_action2(env, shuttle, shuttleID))
                        print('%7.4f %s: Finished Shuttle:%s, Cycle time: %7.4f' % (env.now, name, req1, cycle_time))
                    else:
                        proc_check[1] = 0
                else:
                    shuttle_travel1 = abs(shuttle_locations[shuttleID]["bay"] - bay) * lengthofbay
                    time_shuttle_travel1 = calctime(a_shuttle, v_shuttle, shuttle_travel1)
                    shuttle_travel2 = bay * lengthofbay
                    time_shuttle_travel2 = calctime(a_shuttle, v_shuttle, shuttle_travel2)
                    ts1 = env.timeout(time_shuttle_travel1)

                    print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, req1, bay))
                    yield ts1
                    print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, req1, bay))

                    ts2 = env.timeout(time_shuttle_travel2)
                    print('%7.4f %s: Shuttle:%s moving to buffer' % (env.now, name, req1))
                    yield ts2
                    print('%7.4f %s: Shuttle:%s moved to buffer' % (env.now, name, req1))

                    shuttle_buffer_control[tier - 1] = name
                    shuttle_avail[req1 - 1] = 0
                    shuttle.put(req1)
                    shuttle_time = env.now - pickup_time
                    shuttle_util[req1 - 1] = shuttle_util[req1 - 1] + shuttle_time
                    shuttle_locations[shuttleID]["bay"] = 0
                    if lift1_buffer_control[tier - 1] == name:
                        for no_lift1 in range(2):
                            if lift1_avail[no_lift1] == name:
                                lift1_travel1 = abs(1 - tier) * heightoftier
                                time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
                                tl1 = env.timeout(time_lift1_travel1)

                                print('%7.4f %s: Lift1:%s moving to I/O' % (env.now, name, no_lift1+1))
                                yield tl1
                                print('%7.4f %s: Lift1:%s moved to I/O' % (env.now, name, no_lift1+1))

                                lift1.put(no_lift1+1)
                                lift1_locations[no_lift1+1] = 1
                                lift1_avail[no_lift1] = 0
                                flow_time = env.now - pickup_time
                                cycle_time = env.now - arrive
                                flowtime.append(flow_time)
                                cycletime.append(cycle_time)
                                lift1_util[no_lift1] = lift1_util[no_lift1] + flow_time
                                print('%7.4f %s: Finished Lift1:%s, Cycle time: %7.4f' % (
                                env.now, name, no_lift1+1, cycle_time))
                                if proc_check[1] == 0:
                                    env.process(shuttle_action2(env, shuttle))
                                break
            else:
                proc_check[1] = 0
                break
        else:
            proc_check[1] = 0
            break


def lift1_action(env, name, type, shuttleID, lift1, tier, bay, arrive):
    req2 = yield lift1.get()
    lift1_avail[req2 - 1] = name
    pickup_time = env.now
    if type == 0:

        lift1_travel1 = abs(lift1_locations[req2] - 1) * heightoftier
        time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
        lift1_travel2 = abs(1 - tier) * heightoftier
        time_lift1_travel2 = calctime(a_lift, v_lift, lift1_travel2)
        t1 = env.timeout(time_lift1_travel1)
        print('%7.4f %s: Lift1:%s moving to I/O' % (env.now, name, req2))
        yield t1
        print('%7.4f %s: Lift1:%s moved to I/O' % (env.now, name, req2))

        t2 = env.timeout(time_lift1_travel2)
        print('%7.4f %s: Lift1:%s moving to tier %s' % (env.now, name, req2, tier))
        yield t2
        print('%7.4f %s: Lift1:%s moved to tier %s' % (env.now, name, req2, tier))

        lift1_buffer_control[tier - 1] = name
        lift1.put(req2)
        lift1_locations[req2] = tier
        lift1_time = env.now - pickup_time
        lift1_util[req2 - 1] = lift1_util[req2 - 1] + lift1_time

        if shuttle_buffer_control[tier - 1] == name:
            shuttle_travel2 = bay * lengthofbay
            time_shuttle_travel2 = calctime(a_shuttle, v_shuttle, shuttle_travel2)
            ts2 = env.timeout(time_shuttle_travel2)
            print('%7.4f %s: Shuttle:%s moving to bay %s' % (env.now, name, shuttleID, bay))
            yield ts2
            print('%7.4f %s: Shuttle:%s moved to bay %s' % (env.now, name, shuttleID, bay))

            shuttle_avail[shuttleID - 1] = 0
            shuttle.put(shuttleID)
            shuttle_time = env.now - pickup_time
            shuttle_util[shuttleID - 1] = shuttle_util[shuttleID - 1] + shuttle_time
            shuttle_locations[shuttleID]["bay"] = bay
            flow_time = env.now - pickup_time
            cycle_time = env.now - arrive
            flowtime.append(flow_time)
            cycletime.append(cycle_time)
            print('%7.4f %s: Finished Shuttle:%s, Cycle time: %7.4f' % (env.now, name, shuttleID, cycle_time))
            if shuttleID == 1:
                if proc_check[0] == 0:
                    env.process(shuttle_action1(env, shuttle))
            elif shuttleID == 2:
                if proc_check[1] == 0:
                    env.process(shuttle_action2(env, shuttle))

    else:

        lift1_travel1 = abs(lift1_locations[req2] - tier) * heightoftier
        time_lift1_travel1 = calctime(a_lift, v_lift, lift1_travel1)
        lift1_travel2 = abs(1 - tier) * heightoftier
        time_lift1_travel2 = calctime(a_lift, v_lift, lift1_travel2)
        t1 = env.timeout(time_lift1_travel1)
        print('%7.4f %s: Lift1:%s moving to tier %s' % (env.now, name, req2, tier))
        yield t1
        print('%7.4f %s: Lift1:%s moved to tier %s' % (env.now, name, req2, tier))

        lift1_buffer_control[tier - 1] = name

        if shuttle_buffer_control[tier - 1] == name:
            t2 = env.timeout(time_lift1_travel2)
            print('%7.4f %s: Lift1:%s moving to I/O' % (env.now, name, req2))
            yield t2
            print('%7.4f %s: Lift1:%s moved to I/O' % (env.now, name, req2))

            lift1.put(req2)
            lift1_locations[req2] = 1
            flow_time = env.now - pickup_time
            cycle_time = 0
            flowtime.append(flow_time)
            cycletime.append(cycle_time)
            lift1_util[req2 - 1] = lift1_util[req2 - 1] + flow_time
            print('%7.4f %s: Finished Lift1:%s, Cycle time: %7.4f' % (env.now, name, req2, cycle_time))

"""
def lift2_action(env, name, picked_shuttle, s_tier, d_tier):
    # todo make lift 2 pick up shuttle and move to destination tier
    yield lift2.request()
    l2_travel1 = abs(lift2_location[0] - s_tier) * heightoftier
    t_l2t = calctime(a_lift, v_lift, l2_travel1)
    l2_travel2 = abs(d_tier - s_tier) * heightoftier
    t_l2t2 = calctime(a_lift, v_lift, l2_travel2)
    t1 = env.timeout(t_l2t)
    print('%7.4f %s: Lift 2 moving to %s tier to pick up Shuttle %s' % (env.now, name, s_tier, picked_shuttle))
    yield t1
    print('%7.4f %s: Lift 2 moving to tier %s' % (env.now, name, d_tier))
    t2 = env.timeout(t_l2t2)
    yield t2
    print('%7.4f %s: Lift 2 moved to tier %s' % (env.now, name, d_tier))
"""

env = simpy.Environment()
shuttle = simpy.FilterStore(env, capacity=shuttle_no)
shuttle.items = shuttleNo
lift1 = simpy.FilterStore(env, capacity=2)
lift1.items = lift1No
lift2 = simpy.Resource(env, capacity=1)
env.process(source(env, transaction_interval))
#env.process(shuttle_action1(env, shuttle))
#env.process(shuttle_action2(env, shuttle))
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
