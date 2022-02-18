from re import L
from typing_extensions import Self
from typing import Optional
import simpy


class Carryer(object):
    def __init__(self,
                 env: simpy.Environment,
                 idx: str,
                 container_list=list()) -> None:
        self.container_list = container_list
        self.idx = idx
        self.env = env

    def remove_container(self):
        pass

    def add_container(self):
        pass


class Container(object):
    def __init__(self,
                 env: simpy.Environment,
                 idx: str,
                 carryer: Carryer,
                 container_above=None):
        self.env = env
        self.idx = idx
        self.container_above = container_above
        self.carryer = carryer

    def add_container_above(self, container: Self):
        # 如果上面已经有箱子, 那么不能再叠
        assert self.container_above is None, 'There is already a container above'
        # 否则设置将箱子叠放在这个箱子上
        self.container_above = container
        # 设置上面一个箱子的拿起事件
        self.container_above.left = self.env.event()

    def get_top(self):
        # 获取最上面的箱子
        if self.container_above is None:
            return self
        return self.container_above.get_top()

    def move(self, carryer: Carryer):
        # 如果上面有一个箱子, 等待上面箱子的拿起事件, 此时上面没有箱子
        if self.container_above is not None:
            yield self.container_above.left
            self.container_above = None
        # 让当前carryer拿出这个箱子
        yield self.carryer.remove_container(self)
        # 让下一个carryer接过这个箱子
        yield self.carryer.add_container(self)
        # 如果下面有箱子, 激活当前箱子的拿起事件
        if self.left is not None:
            self.left.succeed()


class Ship(Carryer):
    def __init__(self,
                 env: simpy.Environment,
                 idx: str,
                 container_list=list()):
        super().__init__(env, idx, container_list)

    def remove_container(self):
        yield self.env.timeout(0.0)

    def add_container(self):
        yield self.env.timeout(0.0)


class GantryCrane(Carryer):
    def __init__(self,
                 env: simpy.Environment,
                 idx: str,
                 container_list=list()) -> None:
        super().__init__(env, idx, container_list)
    
    def remove_container(self):
        return super().remove_container()
