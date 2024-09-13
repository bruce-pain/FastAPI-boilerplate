from fastapi import APIRouter
from api.v1.routes.ai_tools.youtube_summarizer import video_summary
from api.v1.routes.api_status import api_status
from api.v1.routes.auth import auth
from api.v1.routes.help_topics import help_topics
from api.v1.routes.user import user_router
from api.v1.routes.payment import payments
from api.v1.routes.billing_plan import billing_plan
from api.v1.routes.ai_tools.summary import summary
from api.v1.routes.ai_tools.save_summary import save_summary
from api.v1.routes.ai_tools.yt_summary import yt_summary, download
from api.v1.routes.notification_settings import notification_setting
from api.v1.routes.faq import faq
from api.v1.routes.resource import resource
from api.v1.routes.presets import preset_router
from api.v1.routes.google_auth import google_auth
from api.v1.routes.lang_region_settings import regions
from api.v1.routes.data_privacy import privacy
from tests.run_all_test import test_rout
from api.v1.routes.request_password import pwd_reset
from api.v1.routes.profile import profile
from api.v1.routes.notification import notification
from api.v1.routes.user_subscription import user_subs

from api.v1.routes.ai_tools.talking_avatar import video_router
from api.v1.routes.ai_tools.background_task import background_router
from api.v1.routes.testimonial import testimonial
from api.v1.routes.project import project_router
from api.v1.routes.job import job
from api.v1.routes.ai_tools.audio_transcriber import audio
from api.v1.routes.dashboard import dashboard
from api.v1.routes.ai_tools.thumbnail import thumbnail_router
from api.v1.routes.ai_tools.video_subtitles import video_subtitles_router
from api.v1.routes.ai_tools.text_to_video import ttv_router
from api.v1.routes.file_downloader import downloader


api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(api_status)
api_version_one.include_router(auth)
api_version_one.include_router(help_topics)
api_version_one.include_router(google_auth)
api_version_one.include_router(user_router)
api_version_one.include_router(summary)
api_version_one.include_router(video_router)
api_version_one.include_router(yt_summary)
api_version_one.include_router(video_summary)
api_version_one.include_router(ttv_router)
api_version_one.include_router(audio)
api_version_one.include_router(profile)
api_version_one.include_router(payments)
api_version_one.include_router(billing_plan)
api_version_one.include_router(notification_setting)
api_version_one.include_router(faq)
api_version_one.include_router(resource)
api_version_one.include_router(testimonial)
api_version_one.include_router(project_router)
api_version_one.include_router(google_auth)
api_version_one.include_router(pwd_reset)
api_version_one.include_router(job)
api_version_one.include_router(notification)
api_version_one.include_router(preset_router)
api_version_one.include_router(regions)
api_version_one.include_router(privacy)
api_version_one.include_router(background_router)
api_version_one.include_router(save_summary)
api_version_one.include_router(job)
api_version_one.include_router(video_summary)
api_version_one.include_router(audio)
api_version_one.include_router(dashboard)
api_version_one.include_router(thumbnail_router)
api_version_one.include_router(video_subtitles_router)
api_version_one.include_router(download)
api_version_one.include_router(user_subs)
api_version_one.include_router(downloader)
api_version_one.include_router(test_rout)
