from random import randint
import simpy

on_request_container_list = []
on_ship_container_list = []
at_gate_container_list = []

BERT_NUM = 5
VEHICLE_NUM = 40
STORAGE_NUM = 10
STORAGE_HEIGHT = 10
GATE_CAPACITY = 100000

total_truck_waiting_time = 0
total_truck_cnt = 0


def container_id_gen():
    cnt = 0
    while True:
        cnt += 1
        on_request_container_list.append(cnt)
        yield cnt


environ = simpy.Environment()

container_id_gen = container_id_gen()

container_position = dict()
container_leave_port_event = dict()

gate_cap = simpy.Resource(environ, capacity=GATE_CAPACITY)
which_gate_by_container_id = dict()

vehicle_cap = simpy.Resource(environ, capacity=VEHICLE_NUM)
vehicle_list = [i for i in range(VEHICLE_NUM)]
vehicle_position = [(randint(0, 10), randint(0, 10))
                    for i in range(VEHICLE_NUM)]

port_cap = simpy.Resource(environ, capacity=BERT_NUM)
port_list = [i for i in range(BERT_NUM)]
port_position = [(100 // BERT_NUM, 0)
                 for i in range(BERT_NUM)]

storage_caps = [simpy.Resource(environ, capacity=STORAGE_HEIGHT)
                for i in range(STORAGE_NUM)]
storage_list = [[] for i in range(STORAGE_NUM)]
storage_requests = [[] for i in range(STORAGE_NUM)]
storage_position = [(randint(0, 100), randint(0, 100))
                    for i in range(STORAGE_NUM)]

gate_position = (50, 100)


def select_storage():
    for i, one_list in enumerate(storage_list):
        if len(one_list) < STORAGE_HEIGHT:
            return i
    return randint(0, STORAGE_NUM - 1)


def get_empty_port():
    port_list.remove(port_list[0])
    port_id = port_list[0]
    return port_id


def ship_gen(environ):
    cnt = 0
    while True:
        yield environ.timeout(24 * 60 / 2)
        request = port_cap.request()
        yield request
        port_id = get_empty_port()
        print(f'[ship:{cnt}] >> dock >> [port:{port_id}]')
        this_ship_container_leave_port_event = []
        for i in range(randint(10, 50)):
            container_id = container_id_gen.__next__()
            on_ship_container_list.append(container_id)
            container_position[container_id] = port_position[port_id]
            container_leave_port_event[container_id] = environ.event()
            this_ship_container_leave_port_event.append(
                container_leave_port_event[container_id])
        yield environ.all_of(this_ship_container_leave_port_event)
        cnt += 1
        port_list.append(port_id)
        port_cap.release(request)


environ.process(ship_gen(environ))


def get_empty_vehicle(to_position):
    nearest_vehicle_id = vehicle_list[0]
    dist = abs(vehicle_position[nearest_vehicle_id][0] - to_position[0]) + \
        abs(vehicle_position[nearest_vehicle_id][1] - to_position[1])
    for vehicle_id in vehicle_list:
        deltax = abs(vehicle_position[nearest_vehicle_id][0] - to_position[0])
        deltay = abs(vehicle_position[nearest_vehicle_id][1] - to_position[1])
        if deltax + deltay < dist:
            nearest_vehicle_id = vehicle_id
    vehicle_list.remove(nearest_vehicle_id)
    return nearest_vehicle_id


def storage_work(environ):
    while True:
        while len(on_ship_container_list) == 0:
            yield environ.timeout(1)
        vehicle_request = vehicle_cap.request()
        yield vehicle_request
        container_id = on_ship_container_list.pop()
        cposition = container_position[container_id]
        vehicle_id = get_empty_vehicle(cposition)
        vposition = vehicle_position[vehicle_id]
        yield environ.timeout((abs(vposition[0] - cposition[0]) + abs(vposition[1] - cposition[1])) / 300)
        vehicle_position[vehicle_id] = cposition
        vposition = cposition
        print(f'[vehicle:{vehicle_id}] << load << [container:{container_id}]')
        storage_id = select_storage()
        sposition = storage_position[storage_id]
        yield environ.timeout((abs(sposition[0] - vposition[1]) + abs(sposition[1] - vposition[1])) / 300)
        vposition = sposition
        container_position[container_id] = sposition
        storage_request = storage_caps[storage_id].request()
        print(
            f'[container:{container_id}] >> enstore >> [storage:{storage_id}]')
        yield storage_request
        container_leave_port_event[container_id].succeed()
        container_leave_port_event.pop(container_id)
        storage_list[storage_id].append(container_id)
        storage_requests[storage_id].append(storage_request)
        vehicle_list.append(vehicle_id)
        vehicle_cap.release(vehicle_request)


environ.process(storage_work(environ))


def to_gate_work(environ):
    while True:
        storage_id = randint(0, STORAGE_NUM - 1)
        while len(storage_list[storage_id]) == 0:
            yield environ.timeout(1)
        container_id = storage_list[storage_id].pop()
        cposition = container_position[container_id]
        storage_request = storage_requests[storage_id].pop()
        vehicle_request = vehicle_cap.request()
        yield vehicle_request
        vehicle_id = get_empty_vehicle(cposition)
        vposition = vehicle_position[vehicle_id]
        yield environ.timeout((abs(cposition[0] - vposition[0]) + abs(cposition[1]-vposition[1])) / 300)
        vposition = cposition
        vehicle_position[vehicle_id] = vposition
        vehicle_position[vehicle_id] = gate_position
        print(f'[vehicle:{vehicle_id}] << load << [container:{container_id}]')
        print(f'[container:{container_id}] << leave << [storage:{storage_id}]')
        yield environ.timeout((abs(gate_position[0] - vposition[0]) + abs(gate_position[1] - vposition[1])) / 300)
        print(
            f'[vehicle:{vehicle_id}] >> unload >> [container:{container_id}]')
        print(f'[container:{container_id}] >> enstore >> [gate]')
        container_position.pop(container_id)
        at_gate_container_list.append(container_id)
        storage_caps[storage_id].release(storage_request)
        vehicle_list.append(vehicle_id)
        vehicle_cap.release(vehicle_request)
        gate_req = gate_cap.request()
        which_gate_by_container_id[container_id] = gate_req
        yield gate_req


environ.process(to_gate_work(environ))
environ.process(to_gate_work(environ))
environ.process(to_gate_work(environ))


def truck_gen(environ, cnt_from, cnt_interval):
    cnt = cnt_from
    while True:
        while len(on_request_container_list) == 0:
            yield environ.timeout(10)
        container_id = on_request_container_list.pop()
        global total_truck_cnt
        total_truck_cnt += 1
        print(f'[truck:{cnt}] >> ask for >> [container:{container_id}]')
        start_waiting_time = environ.now
        while container_id not in at_gate_container_list:
            yield environ.timeout(10)
        print(f'[truck:{cnt}] << load << [container:{container_id}]')
        yield environ.timeout(10)
        print(f'[truck:{cnt}] << leave << [container:{container_id}]')
        global total_truck_waiting_time
        total_truck_waiting_time += environ.now - start_waiting_time
        at_gate_container_list.remove(container_id)
        gate_req = which_gate_by_container_id[container_id]
        gate_cap.release(gate_req)
        yield environ.timeout(24 * 60)
        cnt += cnt_interval


for i in range(50):
    environ.process(truck_gen(environ, i, 50))

if __name__ == '__main__':
    environ.run(until=365 * 60 * 24)
    print(f'total truck waiting time : {total_truck_waiting_time}')
    print(f'total truck count : {total_truck_cnt}')
