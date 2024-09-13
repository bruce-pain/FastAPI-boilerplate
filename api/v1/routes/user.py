from typing import Annotated, Optional
from fastapi import Depends, APIRouter, Request, status, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import event
from sse_starlette import EventSourceResponse
from fastapi.responses import JSONResponse
import asyncio
import json

from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.models.project import Project
from api.v1.schemas.user import (
    ChangePasswordSchema,
    AllUsersResponse,
    UserUpdate,
    AdminCreateUserResponse,
    AdminCreateUser,
    UserStatResponse,
    UserRestoreResponse,
    UserActivityResponse,
    UserUpdateResponse,
    UserDetailResponse,
    CurrentUserDetailResponse
)
from api.db.database import get_db
from api.v1.services.user import user_service, UserService


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=CurrentUserDetailResponse)
def get_current_user_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to get current user details"""

    return success_response(
        status_code=200,
        message="User details retrieved successfully",
        data=jsonable_encoder(
            current_user,
            exclude=[
                "password",
                "is_deleted",
                "updated_at",
            ],
        ),
    )


@user_router.get("/delete", status_code=200)
async def delete_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to delete a user account"""

    # Delete current user
    user_service.delete(db=db)

    return success_response(
        status_code=200,
        message="User deleted successfully",
    )


@user_router.patch("", status_code=status.HTTP_200_OK)
def update_current_user(
    current_user: Annotated[User, Depends(user_service.get_current_user)],
    schema: UserUpdate,
    db: Session = Depends(get_db),
):
    user = user_service.update(db=db, schema=schema, current_user=current_user)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Updated Successfully",
        data=jsonable_encoder(
            user,
            exclude=[
                "password",
                "is_superadmin",
                "is_deleted",
                "updated_at",
                "created_at",
                "is_active",
            ],
        ),
    )


################ SSE ENDPOINT FOR USER STATISTICS ###################

# total number of connected clients
connections = 0
# {"connection": ["state", "active_status"]}
state_map = {}


def reset_connection_active_status():
    """reset the active status for each open connection tracked by the state_map"""
    if state_map:
        for key, value in state_map.items():
            state_map[key][1] = 0


def remove_inactive_connections():
    """remove all inactive connections from the state_map"""
    connections_to_remove = []
    if state_map:
        for key, value in state_map.items():
            if state_map[key][1] == 0:
                connections_to_remove.append(key)
        for connection in connections_to_remove:
            del state_map[connection]


@event.listens_for(User, "after_insert")
@event.listens_for(User, "after_update")
def orm_event_listener(mapper, connection, target):
    """listen for db updates and update the state_map"""

    # once a change in the db is detected
    # clear all inactive connections from state_map
    # fill each connection in the state_map with [1, 1]
    # [update_state, active_state]

    remove_inactive_connections()

    if state_map:
        for key, value in state_map.items():
            state_map[key] = [1, 1]


async def event_generator(request: Request, db: Session):
    global connections, state_map
    connection_index = connections
    connections += 1
    map_key = f"connection_{connection_index}"

    reset_connection_active_status()

    # initialize current connection state
    state_map[map_key] = [1, 1]

    while True:
        # mark the current connection as active
        try:
            state_map[map_key][1] = 1
        except KeyError:
            ""
            break
        # check if state map is non empty
        if state_map[map_key][0] == 1:
            # send a message if update_state is 1
            data = json.dumps(user_service.get_users_statistics(db))

            # reset current connection update_state to 0
            state_map[map_key][0] = 0

            yield {"event": "statsUpdate", "data": data}
        await asyncio.sleep(1)


@user_router.get(
    "/statistics",
    status_code=status.HTTP_200_OK,
    response_model=UserStatResponse,
    summary="Get user statistics data via SSE",
)
def get_user_statistics(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Endpoint to fetch all user statistics via SSE"""
    return EventSourceResponse(event_generator(request, db))


#########################################

################ SSE ENDPOINT FOR USER ACTIVITY STATISTICS ###################


@event.listens_for(Project, "after_insert")
@event.listens_for(Project, "after_update")
def orm_event_listener_for_project(mapper, connection, target):
    """listen for db updates and update the state_map"""

    # once a change in the db is detected
    # clear all inactive connections from state_map
    # fill each connection in the state_map with [1, 1]
    # [update_state, active_state]

    remove_inactive_connections()

    if state_map:
        for key, value in state_map.items():
            state_map[key] = [1, 1]


async def activity_event_generator(db: Session, user_id: str):
    global connections, state_map
    connection_index = connections
    connections += 1
    map_key = f"connection_{connection_index}"

    reset_connection_active_status()

    # initialize current connection state
    state_map[map_key] = [1, 1]

    while True:
        # mark the current connection as active
        try:
            state_map[map_key][1] = 1
        except KeyError:
            # if connection is already deleted
            break
        # check if state map is non empty
        if state_map[map_key][0] == 1:
            # send a message if update_state is 1
            data = json.dumps(user_service.fetch_user_activity_statistics(db, user_id))

            # reset current connection update_state to 0
            state_map[map_key][0] = 0

            yield {"event": "acticityStatsUpdate", "data": data}
        await asyncio.sleep(1)


#########################################


@user_router.get("/export/csv", status_code=status.HTTP_200_OK)
def export_csv(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    return user_service.export_to_csv(db)


@user_router.get(
    "/{user_id}/activity/statistics",
    status_code=status.HTTP_200_OK,
    response_model=UserStatResponse,
)
def get_user_activity_statistics(
    db: Annotated[Session, Depends(get_db)],
    user_id: str,
):
    """Endpoint to fetch all user activity statistics"""
    return EventSourceResponse(activity_event_generator(db, user_id))


@user_router.get(
    "/{user_id}/activity",
    status_code=status.HTTP_200_OK,
    response_model=UserActivityResponse,
)
def get_user_activity(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Annotated[Session, Depends(get_db)],
    user_id: str,
    job: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = 1,
    per_page: int = 10,
):
    """Endpoint to fetch user activity"""
    return user_service.fetch_user_activity(
        db=db,
        user_id=user_id,
        page=page,
        per_page=per_page,
        job=job,
        status=status,
    )


@user_router.patch(
    "/{user_id}", status_code=status.HTTP_200_OK, response_model=UserUpdateResponse
)
def update_user(
    user_id: str,
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    schema: UserUpdate,
    db: Session = Depends(get_db),
):
    user = user_service.update(
        db=db, schema=schema, id=user_id, current_user=current_user
    )

    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Updated Successfully",
        data=jsonable_encoder(
            user,
            exclude=[
                "password",
                "is_superadmin",
                "is_deleted",
                "updated_at",
                "created_at",
                "is_active",
            ],
        ),
    )


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Session = Depends(get_db),
):
    """Endpoint for user deletion (soft-delete)"""

    """

    Args:
        user_id (str): User ID
        current_user (User): Current logged in user
        db (Session, optional): Database Session. Defaults to Depends(get_db).

    Raises:
        HTTPException: 403 FORBIDDEN (Current user is not a super admin)
        HTTPException: 404 NOT FOUND (User to be deleted cannot be found)
    """

    # soft-delete the user
    user_service.delete(db=db, id=user_id)


@user_router.put(
    "/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    response_model=UserRestoreResponse,
)
def restore_deleted_user(
    user_id: str,
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Session = Depends(get_db),
):
    """Endpoint for user restoration"""

    """

    Args:
        user_id (str): User ID
        current_user (User): Current logged in user
        db (Session, optional): Database Session. Defaults to Depends(get_db).

    Raises:
        HTTPException: 403 FORBIDDEN (Current user is not a super admin)
        HTTPException: 404 NOT FOUND (User to be restored cannot be found)
    """

    # restore the deleted user
    user_service.restore_deleted(db=db, id=user_id)

    return success_response(
        status_code=status.HTTP_200_OK, message="User restored successfully!"
    )


@user_router.get("", status_code=status.HTTP_200_OK, response_model=AllUsersResponse)
async def get_users(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_deleted: Optional[bool] = Query(None),
    is_superadmin: Optional[bool] = Query(None),
):
    """
    Retrieves all users.
    Args:
        current_user: The current user(admin) making the request
        db: database Session object
        page: the page number
        per_page: the maximum size of users for each page
        is_active: boolean to filter active users
        is_deleted: boolean to filter deleted users
        is_superadmin: boolean to filter users that are super admin
    Returns:
        UserData
    """
    query_params = {
        "is_active": is_active,
        "is_deleted": is_deleted,
        "is_superadmin": is_superadmin,
    }
    return user_service.fetch_all(db, page, per_page, search, **query_params)


@user_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=AdminCreateUserResponse
)
def admin_registers_user(
    user_request: AdminCreateUser,
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Session = Depends(get_db),
):
    """
    Endpoint for an admin to register a user.
    Args:
        user_request: the body containing the user details to register
        current_user: The superadmin registering the user
        db: database Session object
    Returns:
        AdminCreateUserResponse: The full details of the newly created user
    """
    return user_service.super_admin_create_user(db, user_request)


@user_router.get(
    "/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailResponse
)
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    return user_service.get_user_by_id(db=db, id=user_id)


@user_router.put(
    "/update/password", status_code=status.HTTP_200_OK, response_model=success_response
)
def change_password(
    request: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Route to change the user's password"""

    user_service = UserService()

    # Call the service method directly
    user_service.change_password(
        old_password=request.old_password,
        new_password=request.new_password,
        confirm_new_password=request.confirm_new_password,
        user=current_user,
        db=db,
    )

    return success_response(
        status_code=status.HTTP_200_OK, message="Password changed successfully!!"
    )
