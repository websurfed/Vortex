import random
import time
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

TARGET_REFRESH = 30
FRAME_DURATION = 1.0 / TARGET_REFRESH

class CyEvent(Enum):
    START = auto()

class CyKind(Enum):
    stack = auto()
    hat = auto()
    reporter = auto()

class CyState(Enum):
    IDLE = auto()
    ACTIVE = auto()
    WAITING = auto()
    FINISHED = auto()

class CyOpcode(Enum):
    when_start = auto()
    write = auto()
    wait = auto()
    add = auto()
    sub = auto()
    end = auto()

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
class CyValue:
    Type: CyType
    Value: Any

@dataclass
class CyReference:
    Type: CyType
    Pointer: int

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
    CyOpcode.wait: CySpec(CyKind.stack, None),
    CyOpcode.add: CySpec(CyKind.reporter, None),
    CyOpcode.sub: CySpec(CyKind.reporter, None),
    CyOpcode.end: CySpec(CyKind.stack, None)
}

start_id = generate_id()
write_id = generate_id()
wait_id = generate_id()
start_id2 = generate_id()
write_id2 = generate_id()
sentinel_id = 0

nodes: dict[int, CyNode] = {
    start_id: CyNode(
        start_id,
        None,
        wait_id,
        CyOpcode.when_start
    ),
    wait_id: CyNode(
        wait_id,
        start_id,
        write_id,
        CyOpcode.wait,
        [CyValue(CyType.number, 0)]
    ),
    write_id: CyNode(
        write_id,
        wait_id,
        sentinel_id,
        CyOpcode.write,
        [CyValue(CyType.number, 5)]
    ),
    start_id2: CyNode(
        start_id2,
        None,
        write_id2,
        CyOpcode.when_start
    ),
    write_id2: CyNode(
        write_id2,
        start_id2,
        sentinel_id,
        CyOpcode.write,
        [CyValue(CyType.text, "texttttt")]
    ),
    sentinel_id: CyNode(
        sentinel_id,
        None,
        None,
        CyOpcode.end
    )
}

def get_all_hat_events() -> list[tuple[int, CyEvent]]:
    items: list[tuple[int, CyEvent]] = []
    for identifier, node in nodes.items():
        spec = opcode_specs[node.Opcode]
        if spec.Kind == CyKind.hat and spec.Event is not None:
            items.append((identifier, spec.Event))

    return items

def try_regular_number(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False

def to_number(value) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and try_regular_number(value):
        number = float(value)
    else:
        return 0.0
    if math.isnan(number):
        return 0.0
    return number

def to_string(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return value
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if value == int(value):
        return str(int(value))
    return str(value)

def to_bool(value) -> bool:
    if isinstance(value, str):
        value = value.lower()
    if value == '' or value == '0' or value == "false" or value == 0:
        return False
    return True

def get_time_in_milli() -> int:
    return time.monotonic_ns() // 1_000_000

def execute_report(node: CyNode) -> CyValue:
    if node.Opcode == CyOpcode.add:
        if not node.Inputs:
            raise RuntimeError("Add requires input(s)")
        result = to_number(resolve(node.Inputs[0]).Value) + to_number(resolve(node.Inputs[1]).Value)
        return CyValue(CyType.number, result)

    elif node.Opcode == CyOpcode.sub:
        if not node.Inputs:
            raise RuntimeError("Sub requires input(s)")
        result = to_number(resolve(node.Inputs[0]).Value) - to_number(resolve(node.Inputs[1]).Value)
        return CyValue(CyType.number, result)

    else:
        raise RuntimeError(f"Unknown node : {node.Opcode}")

def resolve(slot) -> CyValue:
    if isinstance(slot, CyValue):
        return slot
    return execute_report(nodes[slot.Pointer])

def execute_node(thread: CyThread):
    pointer = thread.Pointer

    if not nodes.get(pointer):
        raise RuntimeError("That node doesn't exist")
    node = nodes[pointer]

    if node.Opcode == CyOpcode.when_start:
        pass

    elif node.Opcode == CyOpcode.write:
        if not node.Inputs:
            raise RuntimeError("Write requires input(s)")
        value: CyValue = resolve(node.Inputs[0])

        print(to_string(value.Value))

    elif node.Opcode == CyOpcode.wait:
        if not node.Inputs:
            raise RuntimeError("Wait requires input(s)")
        value: CyValue = resolve(node.Inputs[0])

        thread.State = CyState.WAITING
        seconds = max(0, min(to_number(value.Value), 999999))
        thread.Return = get_time_in_milli() + (int(seconds * 1000))

    elif node.Opcode == CyOpcode.end:
        thread.State = CyState.FINISHED

    else:
        raise RuntimeError(f"Unknown node : {node.Opcode}")

    if node.Next is not None:
        thread.Pointer = node.Next

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
            thread.Return = None

def wake_threads(threads):
    now = get_time_in_milli()
    for thread in threads:
        if thread.State == CyState.WAITING and thread.Return is not None and now >= thread.Return:
            thread.State = CyState.ACTIVE
            thread.Return = None

def main():
    threads: list[CyThread] = []
    start_ids: list[tuple[int, CyEvent]] = get_all_hat_events()
    for identifier, event in start_ids:
        thread = CyThread(event, identifier, identifier, CyState.IDLE)
        threads.append(thread)

    trigger_event(CyEvent.START, threads)
    while len(threads) != 0:
        start_time = time.perf_counter()
        wake_threads(threads)

        for thread in threads:
            if thread.State == CyState.ACTIVE:
                execute_thread(thread)

        remaining: list[CyThread] = []
        for thread in threads:
            if thread.State != CyState.FINISHED:
                remaining.append(thread)
        threads = remaining

        elapsed_time = time.perf_counter() - start_time
        sleep_time = FRAME_DURATION - elapsed_time

        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()