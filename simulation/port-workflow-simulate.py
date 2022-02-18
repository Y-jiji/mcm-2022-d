from matplotlib import container
from simpy import *


class Storage(object):
    def __init__(self, xyz_range, environ):
        self.grid = dict()
        self.rvs_grid = dict()  # reversed query grid
        self.xyz_range = xyz_range
        self.environ = environ
        self.lock = dict()
        for x, y, z in xyz_range:
            # initialize everything empty
            self.grid[(x, y, z)] = None
            # for every (x, y) there should be only one and only one vehicle acting on it
            self.lock[(x, y)] = None

    def suspend_until_free(self, x, y):
        if self.lock[(x, y)] is not None:
            yield self.lock[(x, y)]

    def is_boundary(self, x, y, z):
        return (
            self.grid[(x + 1, y + 1, z)] != None
            or
            self.grid[(x + 1, y - 1, z)] != None
            or
            self.grid[(x - 1, y + 1, z)] != None
            or
            self.grid[(x - 1, y + 1, z)] != None
        )

    def check_unload_container_param(self, unload_time, x, y, z, from_above):
        assert self.grid[(x, y, z + 1)] == None, \
            'trying to unload a container from bottom'
        assert self.grid[(x, y, z)] != None, \
            'trying to unload a container that doesn\'t exist'
        assert (x, y, z) in self.xyz_range, \
            f'(x={x}, y={y}, z={z}): out of range'
        if not from_above:
            assert self.is_boundary(x, y, z), \
                f'(x={x}, y={y}, z={z}): too deep'

    def unload_container(self, unload_time, x, y, z, from_above=False):
        # multiple locks, since many vechicle can work on it
        self.suspend_until_free(x, y)
        self.check_unload_container_param(unload_time, x, y, z, from_above)
        # get a lock
        self.lock[(x, y)] = self.environ.event()
        # container unloading time
        yield self.envrion.timeout(unload_time)
        # remove container
        self.grid[(x, y, z)] = None
        # release a lock
        self.lock[(x, y)].succeed()

    def load_container(self, load_time, x, y, z, container):
        # multiple locks, since many vechicle can work on it
        self.suspend_until_free(x, y)
        # TODO: should have some assertion here
        # get a lock
        self.lock[(x, y)] = self.environ.event()
        # container unloading time
        yield self.envrion.timeout(load_time)
        # add container to grid
        self.grid[(x, y, z)] = container
        # release a lock
        self.lock[(x, y)].succeed()


class Vehicle(object):
    def __init__(self, move_speed, buffer_size, environ):
        self.move_speed = move_speed
        self.buffer = [None] * buffer_size
        self.environ = environ

    def suspend_until_free(self):
        if self.lock is not None:
            yield self.lock

    def get_empty_slot(self):
        # get any empty slot to put container
        for i, slot_content in enumerate(self.buffer):
            if slot_content == None:
                return i

    def move(self, dist):
        self.suspend_until_free()
        # get a lock
        self.lock = self.environ.event()
        # vehicle moving time
        yield self.environ.timeout(dist / self.move_speed)
        # release the lock
        self.lock.succeed()

    def load_container(self, load_time, slot, container, src, **kwargs):
        assert self.buffer[slot] is None, 'Load a container to none empty slot'
        self.suspend_until_free()
        # get a lock
        self.lock = self.environ.event()
        # unload container from source
        src.unload_container(**kwargs)
        # container loading time
        yield self.environ.timeout(load_time)
        # add container to buffer
        self.buffer[slot] = container
        # release the lock
        self.lock.succeed()

    def unload_container(self, unload_time, slot):
        # get a lock
        self.lock = self.environ.event()
        self.suspend_until_free()
        # container unloading time
        yield self.environ.timeout(unload_time)
        # remove container from buffer
        self.buffer[slot] = None
        # release the lock
        self.lock.succeed()


class Container(object):
    def __init__(self, index):
        self.index = index
        pass


class Custom(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    pass
