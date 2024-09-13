from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.notification import notification_service

notification = APIRouter(prefix="/notifications", tags=["Notifications"])

@notification.get("", status_code=200, response_model=success_response)
async def get_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user),
):
    '''Endpoint to get all user notifications'''

    notifications = notification_service.fetch_all_user_notifications(user)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Notifications retrieved successfully",
        data=jsonable_encoder(notifications),
    )


@notification.get("/{id}", response_model=success_response, status_code=200)
async def get_single_notification(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user),
):
    '''Endpoint to get a single notification'''

    notification = notification_service.fetch(db, user=user, notification_id=id)

    return success_response(
        status_code=200,
        message='Notification fetched successfully',
        data=jsonable_encoder(notification)
    )


@notification.patch('/{id}/mark-as-read', status_code=200)
async def mark_notification_as_read(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user),
):
    '''Endpoint to mark a notiification as read'''

    notification_service.mark_notification_as_read(db, user=user, notification_id=id)

    return success_response(
        status_code=200,
        message='Notification marked as read'
    )


@notification.delete("/{id}", status_code=204)
async def delete_notification(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user),
):
    '''Endpoint to delete a single notification'''

    notification_service.delete(db, user=user, notification_id=id)


@notification.delete("", status_code=204)
async def delete_all_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user),
):
    '''Endpoint to delete a single notification'''

    notification_service.delete_all(db, user=user)
