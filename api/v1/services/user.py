import random
import string
import pandas as pd
from typing import Any, Optional, Annotated
import datetime as dt
from fastapi import status, Request

from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from api.core.base.services import Service
from api.db.database import get_db
from api.core.settings import settings
from api.utils.db_validators import check_model_existence, get_model_by_params
from api.v1.models.user import User
from api.v1.models.project import Project
from api.v1.models.job import Job
from api.v1.models.data_privacy import DataPrivacySetting
from api.v1.schemas import user
from api.v1.schemas.project import ProjectToolsEnum


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(Service):
    """User service"""

    def fetch_all(
        self,
        db: Session,
        page: int,
        per_page: int,
        search: str,
        **query_params: Optional[Any],
    ):
        """
        Fetch all users
        Args:
            db: database Session object
            page: page number
            per_page: max number of users in a page
            query_params: params to filter by
        """
        per_page = min(per_page, 10)

        if not isinstance(search, str) and search is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid value for search parameter. Must be a non empty string.",
            )

        # Enable filter by query parameter
        filters = []
        if all(query_params):
            # Validate boolean query parameters
            for param, value in query_params.items():
                if value is not None and not isinstance(value, bool):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid value for '{param}'. Must be a boolean.",
                    )
                if value is None:
                    continue
                if hasattr(User, param):
                    filters.append(getattr(User, param) == value)

        # update the active status for each user before filtering
        for user_instance in db.query(User).all():
            user_instance.update_active_status()
        db.commit()

        query = db.query(User)

        if search:
            query = query.filter(
                or_(
                    User.first_name.icontains(search),
                    User.last_name.icontains(search),
                    User.email.icontains(search),
                )
            )

        if filters:
            query = query.filter(*filters)

        total_users = query.count()

        total_pages = int(total_users / per_page) + (total_users % per_page > 0)

        all_users: list[User] = (
            query.order_by(desc(User.created_at))
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )

        return self.all_users_response(
            users=all_users,
            total_users=total_users,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    def all_users_response(
        self, users: list, total_users: int, page: int, per_page: int, total_pages: int
    ):
        """
        Generates a response for all users
        Args:
            users: a list containing user objects
            total_users: total number of users
        """
        if not users or len(users) == 0:
            return user.AllUsersResponse(
                message="No User(s) for this query",
                status="success",
                status_code=200,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                total=0,
                data=[],
            )

        all_users = [
            user.UserData.model_validate(usr, from_attributes=True) for usr in users
        ]
        return user.AllUsersResponse(
            message="Users successfully retrieved",
            status="success",
            status_code=200,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            total=total_users,
            data=all_users,
        )

    def fetch(self, db: Session, id):
        """Fetches a user by their id"""

        user = check_model_existence(db, User, id)
        user.update_active_status()

        # return user if user is not deleted
        if not user.is_deleted:
            return user

    def fetch_by_params(self, db: Session, query_params: dict):
        """Fetches a user by one or more query params"""
        user = get_model_by_params(db, User, query_params)
        return user

    def get_user_by_id(self, db: Session, id: str):
        """Fetches a user by their id"""

        user_instance: User = check_model_existence(db, User, id)
        user_instance.update_active_status()

        data_dict = user_instance.to_dict()
        data_dict["most_used_tool"] = self.fetch_most_used_tool(db, id)

        data = user.UserDetailData(**data_dict)

        return user.UserDetailResponse(
            status="success",
            status_code=status.HTTP_200_OK,
            message="User retrieved successfully",
            data=data,
        )

    def fetch_by_email(self, db: Session, email):
        """Fetches a user by their email"""

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Fetches a user by their email address.

        Args:
            db: The database session.
            email: The email address of the user.

        Returns:
            The user object if found, otherwise None.
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        return user

    def create(self, db: Session, schema: user.UserCreate):
        """Creates a new user"""

        if db.query(User).filter(User.email == schema.email).first():
            raise HTTPException(
                status_code=400,
                detail="User with this email or username already exists",
            )

        # Hash password
        schema.password = self.hash_password(password=schema.password)

        # Create user object with hashed password and other attributes from schema
        user = User(**schema.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)

        # # Create notification settings directly for the user
        # notification_setting_service.create(db=db, user=user)

        # create data privacy setting

        data_privacy = DataPrivacySetting(user_id=user.id)

        db.add(data_privacy)
        db.commit()
        db.refresh(data_privacy)

        return user

    def super_admin_create_user(
        self,
        db: Annotated[Session, Depends(get_db)],
        user_request: user.AdminCreateUser,
    ):
        """
        Creates a user for super admin
        Args:
            db: database Session object
            user_request: The user details to use for creation
        Returns:
            object: the complete details of the newly created user
        """
        try:
            user_exists = (
                db.query(User).filter_by(email=user_request.email).one_or_none()
            )
            if user_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with {user_request.email} already exists",
                )
            if user_request.password:
                user_request.password = self.hash_password(user_request.password)
            new_user = User(**user_request.model_dump())
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_schema = user.UserData.model_validate(new_user, from_attributes=True)
            return user.AdminCreateUserResponse(
                message="User created successfully",
                status_code=201,
                status="success",
                data=user_schema,
            )
        except Exception as exc:
            db.rollback()
            raise Exception(exc) from exc

    def create_admin(self, db: Session, schema: user.UserCreate):
        """Creates a new admin"""

        if hasattr(schema, "admin_secret"):
            del schema.admin_secret

        if db.query(User).filter(User.email == schema.email).first():
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists",
            )

        # Hash password
        schema.password = self.hash_password(password=schema.password)

        # Create user object with hashed password and other attributes from schema
        user = User(**schema.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)

        # Set user to super admin
        user.is_superadmin = True
        db.commit()

        return user

    def update(self, db: Session, current_user: User, schema: user.UserUpdate, id=None):
        """Function to update a User"""
        # Get user from access token if provided, otherwise fetch user by id
        if db.query(User).filter(User.email == schema.email).first():
            raise HTTPException(
                status_code=400,
                detail="User with this email or username already exists",
            )
        if current_user.is_superadmin and id is not None:
            user = self.fetch(db=db, id=id)
        else:
            user = self.fetch(db=db, id=current_user.id)
        update_data = schema.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    def delete(
        self,
        db: Session,
        id=None,
        access_token: str = Depends(oauth2_scheme),
        user: User | None = None,
    ):
        """Function to soft delete a user"""

        if not user:
            # Get user from access token if provided, otherwise fetch user by id
            user = (
                self.get_current_user(access_token, db)
                if id is None
                else check_model_existence(db, User, id)
            )

        user.is_deleted = True
        db.commit()

        return super().delete()

    def restore_deleted(self, db: Session, id=None):
        """Function to restore a deleted user"""

        # Get user from access token if provided, otherwise fetch user by id
        user = check_model_existence(db, User, id)

        user.is_deleted = False
        db.commit()

    def authenticate_user(self, db: Session, email: str, password: str):
        """Function to authenticate a user"""

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid user credentials")

        if not self.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid user credentials")

        user.update_last_login()
        return user

    def hash_password(self, password: str) -> str:
        """Function to hash a password"""

        hashed_password = pwd_context.hash(secret=password)
        return hashed_password

    def verify_password(self, password: str, hash: str) -> bool:
        """Function to verify a hashed password"""

        return pwd_context.verify(secret=password, hash=hash)

    def create_access_token(self, user_id: str) -> str:
        """Function to create access token"""

        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        data = {"user_id": user_id, "exp": expires, "type": "access"}
        encoded_jwt = jwt.encode(data, settings.SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """Function to create access token"""

        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            days=settings.JWT_REFRESH_EXPIRY
        )
        data = {"user_id": user_id, "exp": expires, "type": "refresh"}
        encoded_jwt = jwt.encode(data, settings.SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, access_token: str, credentials_exception):
        """Funtcion to decode and verify access token"""

        try:
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("user_id")
            token_type = payload.get("type")

            if user_id is None:
                raise credentials_exception

            if token_type == "refresh":
                raise HTTPException(detail="Refresh token not allowed", status_code=400)

            token_data = user.TokenData(id=user_id)

        except JWTError as err:
            print(err)
            raise credentials_exception

        return token_data

    def verify_refresh_token(self, refresh_token: str, credentials_exception):
        """Funtcion to decode and verify refresh token"""

        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("user_id")
            token_type = payload.get("type")

            if user_id is None:
                raise credentials_exception

            if token_type == "access":
                raise HTTPException(detail="Access token not allowed", status_code=400)

            token_data = user.TokenData(id=user_id)

        except (JWTError, AttributeError):
            raise credentials_exception

        return token_data

    def refresh_access_token(self, current_refresh_token: str):
        """Function to generate new access token and rotate refresh token"""

        credentials_exception = HTTPException(
            status_code=401, detail="Refresh token expired"
        )

        token = self.verify_refresh_token(current_refresh_token, credentials_exception)

        if token:
            access = self.create_access_token(user_id=token.id)
            refresh = self.create_refresh_token(user_id=token.id)

            return access, refresh

    def get_user_from_refresh_token(self, refresh_token: str, db: Session):
        """Return s thwe id of the user embedded in the refresh token"""

        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = self.verify_refresh_token(refresh_token, credentials_exception)
        user = self.fetch(db, token.id)
        return user

    def get_current_user(
        self, access_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ) -> User:
        """Function to get current logged in user"""

        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = self.verify_access_token(access_token, credentials_exception)
        user = db.query(User).filter(User.id == token.id).first()
        if not user:
            raise credentials_exception
        user.update_last_login()

        return user

    def get_current_user_optional(
        self,
        access_token: Optional[str] = Depends(oauth2_scheme_optional),
        db: Session = Depends(get_db),
    ) -> Optional[User]:
        """Used to optionally check for a user. This will be used for tracking unauthenticated users"""

        if access_token is None:
            return None

        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = self.verify_access_token(access_token, credentials_exception)
        user = db.query(User).filter(User.id == token.id).first()
        if not user:
            raise credentials_exception

        return user

    def change_password(
        self,
        old_password: str,
        new_password: str,
        confirm_new_password: str,
        user: User,
        db: Session,
    ):
        """Endpoint to change the user's password"""

        # Check if the user has an existing password
        if not user.password:
            # user signed up via social authentication (Google/Facebook)
            if old_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You do not have an existing password. Please set up a new password instead.",
                )
            # Allow setting up a new password directly if old password is not provided
            if new_password != confirm_new_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password and confirmation do not match.",
                )
            user.password = self.hash_password(new_password)
            db.commit()

        # If the user has a password, proceed with the normal password change process
        if not self.verify_password(old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password.",
            )

        if new_password != confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match.",
            )

        user.password = self.hash_password(new_password)
        db.commit()

        # Return the passwords in the specified format
        return {
            "oldPassword": old_password,
            "newPassword": user.password,
            "confirmNewPassword": confirm_new_password,
        }

    def get_current_super_admin(
        self, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ):
        """Get the current super admin"""
        user = self.get_current_user(db=db, access_token=token)
        if not user.is_superadmin:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource",
            )
        return user

    def generate_token(self):
        """Generate a 6-digit token"""
        return "".join(
            random.choices(string.digits, k=6)
        ), datetime.utcnow() + timedelta(minutes=10)

    def get_users_statistics(self, db: Session):
        """
        Fetch stats for all users in the database
        Args:
            db: database Session object
        """

        users = db.query(User).all()

        for user in users:
            user.update_active_status()

        total_user_count = len(users)
        active_user_count = sum(1 for user in users if user.is_active)
        inactive_user_count = sum(1 for user in users if not user.is_active)
        deleted_user_count = sum(1 for user in users if user.is_deleted)

        one_hour_ago = datetime.now(timezone(timedelta(hours=1))) - timedelta(hours=1)

        created_in_last_hour = sum(
            1 for user in users if user.created_at >= one_hour_ago
        )

        active_in_last_hour = sum(
            1 for user in users if user.is_active and user.updated_at >= one_hour_ago
        )

        inactive_in_last_hour = sum(
            1
            for user in users
            if not user.is_active and user.updated_at >= one_hour_ago
        )

        deleted_in_last_hour = sum(
            1 for user in users if user.is_deleted and user.updated_at >= one_hour_ago
        )

        return {
            "total_users": total_user_count,
            "active_users": active_user_count,
            "inactive_users": inactive_user_count,
            "deleted_users": deleted_user_count,
            "created_in_last_hour": created_in_last_hour,
            "active_in_last_hour": active_in_last_hour,
            "inactive_in_last_hour": inactive_in_last_hour,
            "deleted_in_last_hour": deleted_in_last_hour,
        }

    def export_to_csv(self, db: Session):
        all_users: list = db.query(User).order_by(desc(User.created_at)).all()

        all_users = [
            [
                user.id,
                user.created_at,
                user.email,
                user.first_name,
                user.last_name,
                user.last_login,
                user.is_active,
                user.is_superadmin,
                user.is_deleted,
            ]
            for user in all_users
        ]

        df = pd.DataFrame(
            all_users,
            columns=[
                "ID",
                "Date Created",
                "Email",
                "First Name",
                "Last Name",
                "Last Login",
                "Is active",
                "Is admin",
                "Is deleted",
            ],
        )
        return StreamingResponse(
            iter([df.to_csv(index=False)]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=all_user_data.csv"},
        )

    def fetch_user_activity_statistics(self, db: Session, user_id: str):
        user_check = check_model_existence(db, User, user_id)
        query = (
            db.query(Project, Job)
            .outerjoin(Job, Project.id == Job.project_id)
            .filter(Project.user_id == user_id)
        )
        stats = {}
        one_hour_ago = datetime.now(timezone(timedelta(hours=1))) - timedelta(hours=1)

        total_tasks = query.count()
        in_progress_tasks = query.filter(
            or_(Job.status.icontains("STARTED"), Job.status.icontains("RUNNING"))
        )
        pending_tasks = query.filter(Job.status.icontains("PENDING"))
        completed_tasks = query.filter(Job.status.icontains("SUCCESS"))

        created_in_last_hour = query.filter(Job.created_at >= one_hour_ago).count()

        in_progress_in_last_hour = in_progress_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        pending_in_last_hour = pending_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        completed_in_last_hour = completed_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        stats = {
            "total_tasks": total_tasks,
            "in_progress_tasks": in_progress_tasks.count(),
            "pending_tasks": pending_tasks.count(),
            "completed_tasks": completed_tasks.count(),
            "created_in_last_hour": created_in_last_hour,
            "in_progress_in_last_hour": in_progress_in_last_hour,
            "pending_in_last_hour": pending_in_last_hour,
            "completed_in_last_hour": completed_in_last_hour,
        }

        return stats

    def fetch_most_used_tool(self, db: Session, user_id: str):
        total_projects = db.query(Project).filter(Project.user_id == user_id).all()

        all_project_count_dict = {}

        # Dict should look like {"podcast_summarizer": 2, ...} once iteration completes
        # Code can further be optimized to use single for-loop to count as well as calculate percentages
        for p in total_projects:
            # Map Enum value stored in db to Enum's name, for use as key in the `all_project_count_dict`
            # Catch errors that would occur when an unknown project_type is encountered
            try:
                project_type_name = ProjectToolsEnum(p.project_type).name
            except ValueError:
                continue

            # Increment count for each tool if already present in all_project_count_dict else intialise it to 1
            prev_count_value = all_project_count_dict.get(project_type_name)
            all_project_count_dict[project_type_name] = (
                1 if prev_count_value is None else prev_count_value + 1
            )

        try:
            max_project_count = max(all_project_count_dict.values())
        except ValueError:
            return "null"

        most_used_tool = "null"

        for project_type, project_count in all_project_count_dict.items():
            if project_count == max_project_count:
                most_used_tool = project_type
                break

        return most_used_tool

    def fetch_user_activity(
        self,
        db: Session,
        user_id: str,
        page: int,
        per_page: int,
        job: str,
        status: str,
    ):
        user_check = check_model_existence(db, User, user_id)
        query = (
            db.query(Project, Job)
            .outerjoin(Job, Project.id == Job.project_id)
            .filter(Project.user_id == user_id)
        )

        if job:
            query = query.filter(Project.project_type.icontains(job))

        if status:
            query = query.filter(Job.status == status)

        total_count = query.count()
        total_pages = int(total_count / per_page) + (total_count % per_page > 0)

        query_result = query.limit(per_page).offset((page - 1) * per_page).all()

        all_tasks = []

        if query_result:
            all_tasks = [
                user.UserActivityData(
                    id=project.id,
                    created_at=project.created_at,
                    status=job.status,
                    tool_used=project.project_type,
                )
                for project, job in query_result
            ]

        if len(all_tasks) == 0:
            return user.UserActivityResponse(
                status="success",
                message="No User activity found for this query",
                page=page,
                per_page=per_page,
                total_jobs_retrieved=total_count,
                total_pages=total_pages,
                data=[],
                status_code=200,
            )

        return user.UserActivityResponse(
            status="success",
            message="User activity data retrieved successfully!",
            page=page,
            per_page=per_page,
            total_jobs_retrieved=total_count,
            total_pages=total_pages,
            data=all_tasks,
            status_code=200,
        )

    def check_superadmin_or_user_in_object(self, user_: User, obj) -> bool:
        """
        Check that user ``is superadmin`` OR has the ID of ``obj.user_id``.
        Raise 401 status code error if false, otherwise return ``True``"""
        if not user_.is_superadmin and not (
            hasattr(obj, "user_id") and obj.user_id == user_.id
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to access this resource",
            )
        return True

    def get_fullname(self, user_):
        return f"{user_.first_name} {user_.last_name}"


user_service = UserService()
