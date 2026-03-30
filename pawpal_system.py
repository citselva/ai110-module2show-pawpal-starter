from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    name: str
    duration: int
    priority: int  # 1-5
    category: str
    is_completed: bool = False


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)


@dataclass
class User:
    name: str
    available_time_mins: int


class CarePlanner:
    def __init__(self, user: User, pet: Pet) -> None:
        self.user = user
        self.pet = pet
        self.reasoning: str = ""

    def generate_schedule(self, tasks: List[Task]) -> List[Task]:
        pass

    def get_reasoning(self) -> str:
        pass
