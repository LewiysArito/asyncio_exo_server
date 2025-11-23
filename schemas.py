import dataclasses

@dataclasses.dataclass
class EchoServerSettings:
    port: int
    timeout_time: int

