from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from .views import TelegramBotViewSet, CourseLevelViewSet, TelegramSettingsViewSet

from .views import (
    CustomUserViewSet,
    BadPasswordViewSet,
    CourseViewSet,
    TeacherViewSet,
    FAQViewSet,
    ContactViewSet,
    ResultViewSet,
    QuizHistoryViewSet
)
from .views import RequestCreateAPIView, RequestDetailAPIView, recent_requests

from .views import submit_answer

from .views import SubjectViewSet, TopicViewSet, QuestionViewSet, QuizAPIView, SEOViewSet
from .views import RegisterView, LoginView
from .views import PasswordResetView, DevPasswordResetView
from .views import MeView, ProfileView, AdminUserViewSet
from .views import (
    dashboard_stats,
    language_stats,
    proficiency_stats,
    exam_stats,
    activity_data,
    recent_students,
)

router = DefaultRouter()
router.register(r"subjects", SubjectViewSet)
router.register(r"topics", TopicViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r'quiz-history', QuizHistoryViewSet, basename='history')
router.register(r"users", CustomUserViewSet)
router.register(r"bad-passwords", BadPasswordViewSet)
router.register(r"courses", CourseViewSet)
router.register(r"course-levels", CourseLevelViewSet)
router.register(r"teachers", TeacherViewSet)
router.register(r"contacts", ContactViewSet)
router.register(r"bots", TelegramBotViewSet)
router.register(r"exam-results", ResultViewSet, basename="exam-results")
router.register(r"faqs", FAQViewSet, basename="faq")
router.register(
    r"telegram-settings", TelegramSettingsViewSet, basename="telegram-settings"
)
router.register(r"seo", SEOViewSet)
router.register(r"admins", AdminUserViewSet, basename="admins")


urlpatterns = [
    path("", include(router.urls)),
    path("quiz/", QuizAPIView.as_view(), name="quiz-create"),
    path("quiz/<int:quiz_id>/", QuizAPIView.as_view(), name="quiz-detail"),
    path(
        "quiz/<int:quiz_id>/next/", QuizAPIView.next_question, name="quiz-next-question"
    ),
    path("quiz/<int:quiz_id>/answer/", QuizAPIView.answer, name="quiz-answer"),
    path("questions/<int:pk>/submit/", submit_answer, name="submit-answer"),
    path("requests/", RequestCreateAPIView.as_view(), name="request-create"),
    path("requests/<int:pk>/", RequestDetailAPIView.as_view(), name="request-delete"),
    path("requests/recent/", recent_requests, name="recent-requests"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/reset-password/", PasswordResetView.as_view(), name="auth-reset-password"),
    path("auth/get-me/", MeView.as_view(), name="get-me"),
    path("auth/dev/reset-password/<int:user_id>/", DevPasswordResetView.as_view(), name="dev-reset-password"),
    path("auth/profile/", ProfileView.as_view(), name="auth-profile"),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('dashboard/language-stats/', language_stats, name='language-stats'),
    path('dashboard/proficiency-stats/', proficiency_stats, name='proficiency-stats'),
    path('dashboard/exam-stats/', exam_stats, name='exam-stats'),
    path('dashboard/activity/', activity_data, name='activity-data'),
    path('dashboard/recent-students/', recent_students, name='recent-students'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
