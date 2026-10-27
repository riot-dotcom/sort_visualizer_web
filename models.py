from dataclasses import dataclass, field


@dataclass
class SortEvent:
    type: str
    indices: list[int] = field(default_factory=list)


@dataclass
class Statistics:
    comparisons: int = 0
    swaps: int = 0
    writes: int = 0
    events: int = 0

    def add_event(self, event):
        self.events += 1
        if event.type == "compare":
            self.comparisons += 1
        elif event.type == "swap":
            self.swaps += 1
            self.writes += 2
        elif event.type == "write":
            self.writes += 1

