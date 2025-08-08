
from ..services.user_service import UserService
from ..data.user_data_manager import UserDataManager

user_data_manager = UserDataManager()
user_service = UserService(user_data_manager)

def register_user(user_id: str, contact: str = None):
    return user_service.register_user(user_id, contact)

def get_user(user_id: str):
    return user_service.get_user(user_id)

def subscribe_ticket(user_id: str, ticket_id: str, mode: int):
    user_service.subscribe_ticket(user_id, ticket_id, mode)

def subscribe_event(user_id: str, event_id: str, mode: int):
    user_service.subscribe_event(user_id, event_id, mode)

def unsubscribe_ticket(user_id: str, ticket_id: str):
    user_service.unsubscribe_ticket(user_id, ticket_id)

def unsubscribe_event(user_id: str, event_id: str):
    user_service.unsubscribe_event(user_id, event_id)
