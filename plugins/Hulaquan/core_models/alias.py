from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Alias:
    """
    剧目别名系统的数据结构
    """
    alias_to_event: Dict[str, str] = field(default_factory=dict)
    event_to_names: Dict[str, List[str]] = field(default_factory=dict)
    name_to_alias: Dict[str, str] = field(default_factory=dict)
    no_response: Dict[str, int] = field(default_factory=dict)
