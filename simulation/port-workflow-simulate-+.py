from random import randint
import simpy

on_request_container_list = []
on_ship_container_list = []
at_gate_container_list = []

PORT_NUM = 5
VEHICLE_NUM = 10
STORAGE_NUM = 10
STORAGE_HEIGHT = 10

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


vehicle_cap = simpy.Resource(environ, capacity=VEHICLE_NUM)
vehicle_list = [i for i in range(VEHICLE_NUM)]

port_cap = simpy.Resource(environ, capacity=PORT_NUM)
port_list = [i for i in range(PORT_NUM)]

storage_caps = [simpy.Resource(environ, capacity=STORAGE_HEIGHT)
                for i in range(STORAGE_NUM)]
storage_list = [[] for i in range(STORAGE_NUM)]
storage_requests = [[] for i in range(STORAGE_NUM)]


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
        request = port_cap.request()
        yield request
        port_id = get_empty_port()
        print(f'[ship:{cnt}] >> dock >> [port:{port_id}]')
        for i in range(10):
            on_ship_container_list.append(container_id_gen.__next__())
        yield environ.timeout(24 * 60 / 5)
        cnt += 1
        port_list.append(port_id)
        port_cap.release(request)


environ.process(ship_gen(environ))


def get_empty_vehicle():
    vehicle_list.remove(vehicle_list[0])
    vehicle_id = vehicle_list[0]
    return vehicle_id


def storage_work(environ):
    while True:
        while len(on_ship_container_list) == 0:
            yield environ.timeout(1)
        vehicle_request = vehicle_cap.request()
        yield vehicle_request
        vehicle_id = get_empty_vehicle()
        container_id = on_ship_container_list.pop()
        yield environ.timeout(20)
        print(f'[vehicle:{vehicle_id}] << load << [container:{container_id}]')
        storage_id = select_storage()
        storage_request = storage_caps[storage_id].request()
        print(f'[container:{container_id}] >> enstore >> [storage:{storage_id}]')
        yield storage_request
        storage_list[storage_id].append(container_id)
        storage_requests[storage_id].append(storage_request)
        vehicle_list.append(vehicle_id)
        vehicle_cap.release(vehicle_request)


environ.process(storage_work(environ))


def outport_work(environ):
    while True:
        storage_id = randint(0, STORAGE_NUM - 1)
        while len(storage_list[storage_id]) == 0:
            yield environ.timeout(1)
        container_id = storage_list[storage_id].pop()
        storage_request = storage_requests[storage_id].pop()
        vehicle_request = vehicle_cap.request()
        yield vehicle_request
        vehicle_id = get_empty_vehicle()
        yield environ.timeout(20)
        print(f'[vehicle:{vehicle_id}] << load << [container:{container_id}]')
        print(f'[container:{container_id}] << leave << [storage:{storage_id}]')
        print(f'[vehicle:{vehicle_id}] >> unload >> [container:{container_id}]')
        print(f'[container:{container_id}] >> enstore >> [outport area]')
        at_gate_container_list.append(container_id)
        storage_caps[storage_id].release(storage_request)
        vehicle_list.append(vehicle_id)
        vehicle_cap.release(vehicle_request)


environ.process(outport_work(environ))


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
        yield environ.timeout(24 * 60)
        cnt += cnt_interval


for i in range(50):
    environ.process(truck_gen(environ, i, 50))

if __name__ == '__main__':
    environ.run(until=365 * 60 * 24)
    print(f'total truck waiting time : {total_truck_waiting_time}')
    print(f'total truck count : {total_truck_cnt}')
