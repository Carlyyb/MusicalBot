from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class UserSubscribe:
    is_subscribe: bool = False
    subscribe_time: Optional[str] = None
    subscribe_tickets: List[Dict] = field(default_factory=list)  # [{id, mode}]
    subscribe_events: List[Dict] = field(default_factory=list)   # [{id, mode}]

@dataclass
class User:
    user_id: str
    activate: bool = True
    create_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    attention_to_hulaquan: int = 0
    chats_count: int = 0
    is_op: bool = False
    subscribe: UserSubscribe = field(default_factory=UserSubscribe)
    contact: Optional[str] = None

    def add_ticket_subscribe(self, ticket_id: str, mode: int):
        self.subscribe.subscribe_tickets.append({'id': ticket_id, 'mode': mode})

    def add_event_subscribe(self, event_id: str, mode: int):
        self.subscribe.subscribe_events.append({'id': event_id, 'mode': mode})

    def remove_ticket_subscribe(self, ticket_id: str):
        self.subscribe.subscribe_tickets = [t for t in self.subscribe.subscribe_tickets if t['id'] != ticket_id]

    def remove_event_subscribe(self, event_id: str):
        self.subscribe.subscribe_events = [e for e in self.subscribe.subscribe_events if e['id'] != event_id]
