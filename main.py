import random
import time
from dataclasses import dataclass
from enum import Enum, auto, nonmember
from typing import Any

class CyEvent(Enum):
    START = auto()

class CyKind(Enum):
    stack = auto()
    hat = auto()

class CyState(Enum):
    ACTIVE = auto()
    WAITING = auto()
    FINISHED = auto()

class CyOpcode(Enum):
    when_start = auto()
    write = auto()
    wait = auto()

class CyType(Enum):
    text = auto()
    number = auto()

@dataclass
class CySpec:
    Kind: CyKind
    Event: CyEvent | None

@dataclass
class CyNode:
    Id: int
    Parent: int | None
    Next: int | None
    Opcode: CyOpcode
    Inputs: list | None = None

@dataclass
class CyLiteral:
    Type: CyType
    Value: Any

@dataclass
class CyThread:
    Event: CyEvent
    Lead: int
    Pointer: int
    State: CyState
    Return: int | None = None

def generate_id():
    return random.getrandbits(32)

opcode_specs: dict[CyOpcode, CySpec] = {
    CyOpcode.when_start: CySpec(CyKind.hat, CyEvent.START),
    CyOpcode.write: CySpec(CyKind.stack, None),
    CyOpcode.wait: CySpec(CyKind.stack, None)
}

start_id = generate_id()
wait_id = generate_id()
write_id = generate_id()
nodes: dict[int, CyNode] = {
    start_id: CyNode(
        start_id,
        None,
        wait_id,
        CyOpcode.when_start,
        None
    ),
    wait_id: CyNode(
        wait_id,
        start_id,
        write_id,
        CyOpcode.wait,
        [CyLiteral(CyType.number, 5)]
    ),
    write_id: CyNode(
        write_id,
        wait_id,
        None,
        CyOpcode.write,
        [CyLiteral(CyType.text, "Hello, world!")]
    )
}

def get_all_hat_events() -> list[tuple[int, CyEvent]]:
    items: list[tuple[int, CyEvent]] = []
    for identifier, node in nodes.items():
        spec = opcode_specs[node.Opcode]
        if spec.Kind == CyKind.hat and spec.Event is not None:
            items.append((identifier, spec.Event))

    return items

def get_time_in_milli() -> int:
    return time.time_ns() // 1_000_000

def execute_node(thread: CyThread):
    pointer = thread.Pointer

    if not nodes.get(pointer):
        raise RuntimeError("That node doesn't exist")
    node = nodes[pointer]

    if node.Opcode == CyOpcode.when_start:
        if node.Next is not None:
            thread.Pointer = node.Next

    elif node.Opcode == CyOpcode.write:
        if not node.Inputs:
            raise RuntimeError("Write requires input(s)")
        literal: CyLiteral = node.Inputs[0]

        print(literal.Value)
        if node.Next is not None:
            thread.Pointer = node.Next

    elif node.Opcode == CyOpcode.wait:
        if not node.Inputs:
            raise RuntimeError("Read requires input(s)")
        literal: CyLiteral = node.Inputs[0]

        thread.Return = get_time_in_milli() + (literal.Value * 1000)
        print(thread.Return)
        thread.State = CyState.WAITING
        if node.Next is not None:
            thread.Pointer = node.Next

    else:
        raise RuntimeError("Unknown node")
    return

def execute_thread(thread: CyThread) -> CyState:
    while thread.State == CyState.ACTIVE:
        execute_node(thread)
    return thread.State

def trigger_event(event: CyEvent, threads: list[CyThread]):
    for thread in threads:
        if thread.Event == event:
            thread.Pointer = thread.Lead
            thread.State = CyState.ACTIVE

def wake_threads(threads: list[CyThread]):
    for thread in threads:
        if thread.State == CyState.WAITING and thread.Return is not None and get_time_in_milli() >= thread.Return:
            thread.State = CyState.ACTIVE
            thread.Return = None

def main():
    threads: list[CyThread] = []
    start_ids: list[tuple[int, CyEvent]] = get_all_hat_events()
    for identifier, event in start_ids:
        thread = CyThread(event, identifier, identifier, CyState.WAITING)
        threads.append(thread)

    trigger_event(CyEvent.START, threads)
    while len(threads) != 0:
        wake_threads(threads)

        for thread in threads:
            if thread.State == CyState.ACTIVE:
                state = execute_thread(thread)
                thread.State = state

        remaining: list[CyThread] = []
        for thread in threads:
            if thread.State != CyState.FINISHED:
                remaining.append(thread)
        threads = remaining

    # print(threads)

if __name__ == "__main__":
    main()