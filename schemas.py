import dataclasses

@dataclasses.dataclass
class EchoServerSettings:
    port: int
    port_metrics: int
    timeout_time: int
    host: str

