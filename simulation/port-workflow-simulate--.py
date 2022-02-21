import simpy

on_request_container_list = []
on_ship_container_list = []
leave_harbor_conatainer_list = []

PORT_NUM = 5
VEHICLE_NUM = 10


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


def harbor_work(environ):
    while True:
        while len(on_ship_container_list) == 0:
            yield environ.timeout(1)
        request = vehicle_cap.request()
        yield request
        vehicle_id = get_empty_vehicle()
        container_id = on_ship_container_list.pop()
        yield environ.timeout(20)
        print(f'[vehicle:{vehicle_id}] << load << [container:{container_id}]')
        yield environ.timeout(20)
        print(
            f'[vehicle:{vehicle_id}] >> unload >> [container:{container_id}]')
        yield environ.timeout(20)
        leave_harbor_conatainer_list.append(container_id)
        vehicle_list.append(vehicle_id)
        vehicle_cap.release(request)


environ.process(harbor_work(environ))


def truck_gen(environ):
    cnt = 0
    while True:
        while len(on_request_container_list) == 0:
            yield environ.timeout(10)
        container_id = on_request_container_list.pop()
        print(f'[truck:{cnt}] >> ask for >> [container:{container_id}]')
        while container_id not in leave_harbor_conatainer_list:
            yield environ.timeout(10)
        print(f'[truck:{cnt}] << load << [container:{container_id}]')
        yield environ.timeout(10)
        print(f'[truck:{cnt}] << leave << [container:{container_id}]')
        yield environ.timeout(24 * 60 / 5)
        cnt += 1


environ.process(truck_gen(environ))


if __name__ == '__main__':
    environ.run(until=365 * 60 * 24)
