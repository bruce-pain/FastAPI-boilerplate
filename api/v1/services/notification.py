from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.utils.db_validators import check_model_existence
from api.v1.models.notifications import Notification
from api.v1.models.user import User


class NotificationService:
    """Notification service functionality"""
    
    def send_notification(self, db: Session, title: str, message: str, user: User, type: str='success'):
        """Create a new notification"""
        
        notification = Notification(
            title=title,
            message=message,
            receiver_id=user.id,
            status='unread',
            notification_type=type
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification
    

    def check_notification_permission(self, notification: Notification, user: User):
        '''Function to check if a user has access to a notification'''

        if notification not in user.notifications:
            raise HTTPException(status_code=403, detail='You do not have access to this notification')
    

    def fetch(self, db: Session, user: User, notification_id: str):
        """Fetches a notification by id"""

        notification = check_model_existence(db, Notification, notification_id)
        self.check_notification_permission(notification, user)
        return notification
    
    
    def fetch_all_user_notifications(self, user: User):
        """Fetch all notifications"""

        return user.notifications


    def update(self):
        pass


    def mark_notification_as_read(self, db: Session, user: User, notification_id: str):
        '''Mark the notification as read'''

        notification = check_model_existence(db, Notification, notification_id)

        self.check_notification_permission(notification, user)
        
        notification.status ='read'
        db.commit()
        db.refresh(notification)


    def delete(self, db: Session, user: User, notification_id: str):
        '''Delete a single notification'''

        notification = check_model_existence(db, Notification, notification_id)
        self.check_notification_permission(notification, user)
        db.delete(notification)

    
    def delete_all(self, db:Session, user: User):
        '''Delete all user notifications'''

        for notification in user.notifications:
            db.delete(notification)
        
        db.commit()
        
        
notification_service = NotificationService()
