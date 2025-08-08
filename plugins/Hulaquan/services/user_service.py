
from ..data.user_data_manager import UserDataManager
from ..models.user import User


class UserService:
    def __init__(self, user_data_manager: UserDataManager):
        self.user_data_manager = user_data_manager

    def register_user(self, user_id: str, contact: str = None) -> User:
        user = User(user_id=user_id, contact=contact)
        self.user_data_manager.add_user(user)
        return user

    def get_user(self, user_id: str) -> User:
        return self.user_data_manager.get_user(user_id)

    def subscribe_ticket(self, user_id: str, ticket_id: str, mode: int):
        user = self.get_user(user_id)
        if user:
            user.add_ticket_subscribe(ticket_id, mode)
            self.user_data_manager.update_user(user)

    def subscribe_event(self, user_id: str, event_id: str, mode: int):
        user = self.get_user(user_id)
        if user:
            user.add_event_subscribe(event_id, mode)
            self.user_data_manager.update_user(user)

    def unsubscribe_ticket(self, user_id: str, ticket_id: str):
        user = self.get_user(user_id)
        if user:
            user.remove_ticket_subscribe(ticket_id)
            self.user_data_manager.update_user(user)

    def unsubscribe_event(self, user_id: str, event_id: str):
        user = self.get_user(user_id)
        if user:
            user.remove_event_subscribe(event_id)
            self.user_data_manager.update_user(user)
