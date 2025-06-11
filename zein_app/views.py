from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import timedelta, datetime
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncMonth

from telegram_bot.models import TelegramSettings
from .pagination import CustomPagination
from rest_framework import filters


# Create your views here.


from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken


from django.contrib.auth import get_user_model

User = get_user_model()


from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    CourseLevelSerializer,
    TelegramSettingsSerializer,
)
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = CustomUser.objects.filter(username=username).first()
        if user and user.check_password(password):
            # Update last_login
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            token = AccessToken.for_user(user)
            return Response(
                {
                    "access": str(token),
                }
            )
        return Response({"detail": "Invalid credentials"}, status=400)

class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_serializer = UserSerializer(user)
        return Response(
            {"message": "Welcome to dashboard!", "user": user_serializer.data}, 200
        )


from .models import (
    CustomUser,
    BadPassword,
    ResultDetail,
    Subject,
    Topic,
    Question,
    UserAnswer,
    Course,
    Teacher,
    Contact,
)
from .serializers import (
    CustomUserSerializer,
    BadPasswordSerializer,
    QuestionSerializer,
    UserAnswerSerializer,
    CourseSerializer,
    TeacherSerializer,
    ContactSerializer,
)


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["username", "created_at"]
    ordering = ["username"]


class BadPasswordViewSet(viewsets.ModelViewSet):
    queryset = BadPassword.objects.all()
    serializer_class = BadPasswordSerializer


# class QuestionViewSet(viewsets.ModelViewSet):
#     queryset = Question.objects.all()
#     serializer_class = QuestionSerializer
#     pagination_class = CustomPagination
#     filter_backends = [filters.OrderingFilter]
#     ordering_fields = ['created_at', 'text']
#     ordering = ['-created_at']


# class HistoryViewSet(viewsets.ModelViewSet):
#     queryset = History.objects.all()
#     serializer_class = HistorySerializer


# class SubjectViewSet(viewsets.ModelViewSet):
#     queryset = Subject.objects.all()
#     serializer_class = SubjectSerializer
#     pagination_class = CustomPagination
#     filter_backends = [filters.OrderingFilter]
#     ordering_fields = ['name_en', 'name_uz']
#     ordering = ['name_en']


# class TopicViewSet(viewsets.ModelViewSet):
#     queryset = Topic.objects.all()
#     serializer_class = TopicSerializer


# class QuizSessionViewSet(viewsets.ModelViewSet):
#     queryset = QuizSession.objects.all()
#     serializer_class = QuizSessionSerializer


# class UserAnswerViewSet(viewsets.ModelViewSet):
#     queryset = UserAnswer.objects.all()
#     serializer_class = UserAnswerSerializer


from rest_framework.decorators import api_view
from .models import Question, Choice
from .serializers import CourseLevelLangSerializer

@api_view(["POST"])
def submit_answer(request, pk):
    try:
        question = Question.objects.get(pk=pk)
        choice_id = request.data.get("choice_id")
        selected_choice = Choice.objects.get(id=choice_id, question=question)

        is_correct = selected_choice.is_correct
        return Response(
            {
                "question": question.text,
                "your_answer": selected_choice.text,
                "correct": is_correct,
            }
        )
    except (Question.DoesNotExist, Choice.DoesNotExist):
        return Response({"error": "Invalid question or choice"}, status=400)


from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response


from .models import Subject, Topic, Question, Choice, Quiz, UserAnswer
from .serializers import (
    SubjectListSerializer,
    SubjectDetailSerializer,
    TopicListSerializer,
    TopicDetailSerializer,
    QuestionListSerializer,
    QuestionDetailSerializer,
    AdminQuestionSerializer,
    QuizCreateSerializer,
    QuizAnswerSerializer,
    QuizResultSerializer,
    QuizDetailSerializer,
)
from .permissions import IsAdminOrReadOnly


class IsAuthenticatedOrReadOnlyCustom(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return super().has_permission(request, view)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyCustom]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on lang parameter.
        """
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            return SubjectLanguageSerializer
        if self.action == "list":
            return SubjectListSerializer
        return SubjectDetailSerializer

    def get_serializer_context(self):
        """
        Add language to serializer context.
        """
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            context["language"] = lang
        return context


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyCustom]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on lang parameter.
        """
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            return TopicLanguageSerializer
        if self.action == "list":
            return TopicListSerializer
        return TopicDetailSerializer

    def get_serializer_context(self):
        """
        Add language to serializer context.
        """
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            context["language"] = lang
        return context

    def get_queryset(self):
        queryset = Topic.objects.all()
        subject_id = self.request.query_params.get("subject_id", None)
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyCustom]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return QuestionSerializer
        if self.action == "list":
            return QuestionListSerializer
        return QuestionDetailSerializer

    def get_queryset(self):
        queryset = Question.objects.all()
        topic_id = self.request.query_params.get("topic_id")
        if topic_id is not None:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset

from zein_app.models import QuizHistory
from zein_app.serializers import QuizHistorySerializer

class QuizHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuizHistory.objects.all().order_by("-created_at")
    serializer_class = QuizHistorySerializer

class QuizAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        if serializer.is_valid():
            topic_id = serializer.validated_data["topic"].id

            questions = Question.objects.filter(topic_id=topic_id)

            if not questions.exists():
                return Response(
                    {"error": "В данной теме нет вопросов"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            quiz = Quiz.objects.create(
                user=request.user, topic_id=topic_id, total_questions=questions.count()
            )

            first_question = questions.first()
            question_serializer = QuestionDetailSerializer(first_question)

            return Response(
                {"quiz_id": quiz.id, "question": question_serializer.data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def next_question(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)

        if quiz.status == "completed":
            return Response(
                {"error": "Эта викторина уже завершена", "quiz_id": quiz.id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        all_questions = Question.objects.filter(topic=quiz.topic)

        answered_question_ids = UserAnswer.objects.filter(quiz=quiz).values_list(
            "question_id", flat=True
        )

        next_question = all_questions.exclude(id__in=answered_question_ids).first()

        if next_question:
            question_serializer = QuestionDetailSerializer(next_question)
            return Response({"quiz_id": quiz.id, "question": question_serializer.data})
        else:
            quiz.status = "completed"
            quiz.completed_at = timezone.now()
            quiz.save()

            result_serializer = QuizResultSerializer(quiz)
            return Response(
                {"message": "Викторина завершена", "results": result_serializer.data}
            )

    @action(detail=True, methods=["post"])
    def answer(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)

        if quiz.status == "completed":
            return Response(
                {"error": "Эта викторина уже завершена"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = QuizAnswerSerializer(data=request.data)
        if serializer.is_valid():
            question_id = serializer.validated_data["question_id"]
            choice_id = serializer.validated_data["choice_id"]

            question = get_object_or_404(Question, id=question_id, topic=quiz.topic)

            choice = get_object_or_404(Choice, id=choice_id, question=question)

            if UserAnswer.objects.filter(quiz=quiz, question=question).exists():
                return Response(
                    {"error": "Вы уже ответили на этот вопрос"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            is_correct = choice.is_correct
            UserAnswer.objects.create(
                quiz=quiz,
                question=question,
                selected_choice=choice,
                is_correct=is_correct,
            )

            if is_correct:
                quiz.score += 1
                quiz.save()

            all_questions = Question.objects.filter(topic=quiz.topic)

            answered_question_ids = UserAnswer.objects.filter(quiz=quiz).values_list(
                "question_id", flat=True
            )

            if all_questions.count() == len(answered_question_ids):
                quiz.status = "completed"
                quiz.completed_at = timezone.now()
                quiz.save()

                result_serializer = QuizResultSerializer(quiz)
                return Response(
                    {
                        "message": "Викторина завершена",
                        "is_correct": is_correct,
                        "results": result_serializer.data,
                    }
                )
            else:
                next_question = all_questions.exclude(
                    id__in=answered_question_ids
                ).first()
                question_serializer = QuestionDetailSerializer(next_question)

                return Response(
                    {
                        "is_correct": is_correct,
                        "next_question": question_serializer.data,
                    }
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, quiz_id=None):
        user = request.user

        if quiz_id:
            quiz = get_object_or_404(Quiz, id=quiz_id, user=user)
            serializer = QuizDetailSerializer(quiz)
            return Response(serializer.data)
        else:
            quizzes = Quiz.objects.filter(user=user)
            serializer = QuizResultSerializer(quizzes, many=True)
            return Response(serializer.data)


from .models import Course, CourseLevel


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_serializer_class(self):
        lang = self.request.query_params.get("lang")
        if lang == "ru":
            return CourseLangSerializer
        elif lang == "uz":
            return CourseLangSerializer
        return CourseSerializer

    # Separate update for course name
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        if "name_uz" in data:
            instance.name_uz = data["name_uz"]
        if "name_ru" in data:
            instance.name_ru = data["name_ru"]
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class CourseLevelViewSet(viewsets.ModelViewSet):
    queryset = CourseLevel.objects.all()
    serializer_class = CourseLevelSerializer

    # Separate update for course level
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        for field in ["title_uz", "title_ru", "level", "duration_months", "price", "features_uz", "features_ru"]:
            if field in data:
                setattr(instance, field, data[field])
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer


from rest_framework import viewsets
from rest_framework.decorators import action
from django.utils.translation import activate
from .models import FAQ
from .serializers import FAQSerializer, FAQLanguageSerializer


class FAQViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing FAQ instances.

    Provides `list`, `create`, `retrieve`, `update`, and `destroy` actions.
    Additionally includes an `active` action to get only active FAQs.

    For client requests:
    - Use ?lang=ru for Russian content
    - Use ?lang=uz for Uzbek content
    - No parameter returns full content (admin view)
    """

    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["question_uz", "question_ru", "answer_uz", "answer_ru"]
    ordering_fields = ["order", "created_at", "updated_at"]
    ordering = ["order"]  # default ordering

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on lang parameter.
        """
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            return FAQLanguageSerializer
        return FAQSerializer

    def get_serializer_context(self):
        """
        Add language to serializer context.
        """
        context = super().get_serializer_context()
        lang = self.request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            context["language"] = lang
        return context

    def list(self, request, *args, **kwargs):
        """
        Override list to filter by language if requested.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # If not for admin, only show active FAQs
        lang = request.query_params.get("lang")
        if lang in ["uz", "ru"]:
            queryset = queryset.filter(is_active=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Return only active FAQs."""
        active_faqs = FAQ.objects.filter(is_active=True).order_by("order")
        serializer = self.get_serializer(active_faqs, many=True)
        return Response(serializer.data)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get_queryset(self):
        first_contact = Contact.objects.first()
        if first_contact:
            return Contact.objects.filter(pk=first_contact.pk)
        return Contact.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)
        return Response({}, status=200)


from rest_framework import status
from rest_framework.response import Response
from .models import Request
from .serializers import RequestSerializer
from telegram_bot.services.bot_service import send_telegram_notification

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class RequestCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        requests = Request.objects.all().order_by("created_at")
        serializer = RequestSerializer(requests, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RequestSerializer(data=request.data)
        if serializer.is_valid():
            request_instance = serializer.save()
            try:
                send_telegram_notification(request_instance)
            except Exception as e:
                print(f"Error sending Telegram notification: {e}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_requests(request):
    """Get 6 most recent requests"""
    recent = Request.objects.order_by('-created_at')[:6]
    serializer = RequestSerializer(recent, many=True)
    return Response(serializer.data)


class RequestDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        request_instance = get_object_or_404(Request, pk=pk)
        serializer = RequestSerializer(request_instance)
        return Response(serializer.data)

    def delete(self, request, pk):
        request_instance = get_object_or_404(Request, pk=pk)
        request_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# views.py
from rest_framework import viewsets
from .models import TelegramBot
from .serializers import TelegramBotSerializer


class TelegramBotViewSet(viewsets.ModelViewSet):
    queryset = TelegramBot.objects.all()
    serializer_class = TelegramBotSerializer


class TelegramSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = TelegramSettingsSerializer
    queryset = TelegramSettings.objects.all()

    def get_queryset(self):
        return TelegramSettings.objects.filter(is_active=True)

    @action(detail=False, methods=["get"])
    def active(self, request):
        active_setting = TelegramSettings.get_active()
        if active_setting:
            serializer = self.get_serializer(active_setting)
            return Response(serializer.data)
        return Response({"detail": "No active Telegram settings found."}, status=404)


# from rest_framework.decorators import action
# from rest_framework.response import Response
# from .models import CustomUser, Results, Language
# from .serializers import UserSerializer, ResultsSerializer
#
# class ResultsViewSet(viewsets.ModelViewSet):
#     queryset = Results.objects.all()
#     serializer_class = ResultsSerializer
#     filter_backends = [filters.SearchFilter]
#     search_fields = ['full_name', 'language']
#
#     def get_queryset(self):
#         queryset = Results.objects.all()
#         language = self.request.query_params.get('language', None)
#
#         if language is not None:
#             queryset = queryset.filter(language=language)
#
#         return queryset
#
#     @action(detail=False, methods=['get'])
#     def languages(self, request):
#         languages = [
#             {'code': code, 'name': name}
#             for code, name in Language.choices
#         ]
#         return Response(languages)
#
#     @action(detail=False, methods=['get'])
#     def top_students(self, request):
#         top_results = Results.objects.filter(is_top_student=True)
#         serializer = self.get_serializer(top_results, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=['get'])
#     def by_language_group(self, request):
#         grouped_results = {}
#
#         for code, name in Language.choices:
#             results = Results.objects.filter(language=code)
#             serializer = ResultsSerializer(results, many=True)
#             grouped_results[code] = {
#                 'name': name,
#                 'results': serializer.data
#             }
#
#         return Response(grouped_results)


# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django_filters.rest_framework import DjangoFilterBackend
# from .models import CustomUser, Results, Language
# from .serializers import CustomUserSerializer, ResultsSerializer
# from .pagination import CustomPagination
#
#
#
#
#
# class ResultsViewSet(viewsets.ModelViewSet):
#     queryset = Results.objects.all()
#     serializer_class = ResultsSerializer
#     pagination_class = CustomPagination
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
#     filterset_fields = ['language', 'proficiency_level', 'exam_type', 'user']
#     ordering_fields = ['created_at', 'exam_score', 'user__full_name']
#     ordering = ['-created_at']
#     search_fields = ['user__full_name', 'exam_type']
#
#     @action(detail=False, methods=['get'])
#     def languages(self, request):
#         languages = [
#             {'code': code, 'name': name}
#             for code, name in Language.choices
#         ]
#         return Response(languages)
#
#     @action(detail=False, methods=['get'])
#     def by_language(self, request):
#         language = request.query_params.get('language')
#         if not language:
#             return Response({"error": "Language parameter is required."}, status=400)
#
#         results = self.get_queryset().filter(language=language)
#         serializer = self.get_serializer(results, many=True)
#         return Response(serializer.data)


from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

# from django_filters.rest_framework import DjangoFilterBackend
from .models import CustomUser
from .serializers import CustomUserSerializer, ResultSerializer
from .pagination import CustomPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
# from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Result


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [AllowAny]

# class ResultsViewSet(viewsets.ModelViewSet):
#     queryset = Results.objects.all()
#     serializer_class = ResultsSerializer
#     filter_backends = [filters.OrderingFilter, filters.SearchFilter]
#     ordering_fields = ['created_at', 'exam_score']
#     ordering = ['-created_at']
#     search_fields = ['user', 'exam_type']
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         params = self.request.query_params
#
#         filter_fields = ['language', 'proficiency_level', 'exam_type', 'user']
#         filters_dict = {field: params.get(field) for field in filter_fields if params.get(field)}
#         return queryset.filter(**filters_dict)
#
#     @action(detail=False, methods=['get'])
#     def languages(self, request):
#         return Response([
#             {'code': code, 'name': name}
#             for code, name in Language.choices
#         ])
#
#     @action(detail=False, methods=['get'])
#     def by_language(self, request):
#         language = request.query_params.get('language')
#         if not language:
#             return Response({"error": "Language parameter is required."}, status=400)
#
#         results = self.get_queryset().filter(language=language)
#         serializer = self.get_serializer(results, many=True)
#         return Response(serializer.data)

from rest_framework import viewsets
from .models import SEO
from .serializers import SEOSerializer

class SEOViewSet(viewsets.ModelViewSet):
    queryset = SEO.objects.all()
    serializer_class = SEOSerializer

    def list(self, request):
        first_seo = SEO.objects.first()
        if first_seo:
            serializer = SEOSerializer(first_seo, context={'request': request})
            return Response(serializer.data)
        return Response({}, status=200)


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import (
    PasswordResetSerializer,
    DevPasswordResetSerializer,
    ProfileSerializer,
    CustomUserSerializer,
)

User = get_user_model()

class PasswordResetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        new_password = serializer.validated_data["new_password"]

        # If user is dev, allow reset without old password
        if user.role == "dev":
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password reset successfully."})

        # For others, require old password
        old_password = serializer.validated_data.get("old_password")
        if not old_password or not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successfully."})

class DevPasswordResetView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, user_id):
        serializer = DevPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'}, status=404)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Password reset successfully.'})
        return Response(serializer.errors, status=400)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

from rest_framework import viewsets
from .models import CustomUser
from .serializers import AdminUserSerializer
from .permissions import IsSuperAdminOrDev

class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperAdminOrDev]
    def get_queryset(self):
        # Only show admins (not super_admins)
        user = self.request.user
        if user.role == "dev":
            return CustomUser.objects.filter(role__in=["admin", "super_admin"])
        return CustomUser.objects.filter(role="admin")

    def perform_create(self, serializer):
        # Only dev can create super_admin, otherwise always admin
        role = self.request.data.get("role", "admin")
        if role == "super_admin":
            if self.request.user.role == "dev":
                serializer.save(role="super_admin")
            else:
                serializer.save(role="admin")
        else:
            serializer.save(role="admin")

    def perform_update(self, serializer):
        # Only dev can update role to super_admin
        role = self.request.data.get("role")
        if role == "super_admin" and self.request.user.role == "dev":
            serializer.save(role="super_admin")
        else:
            serializer.save(role="admin")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    # Get the first day of current month
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    # Current totals
    total_courses = Course.objects.count()
    total_questions = Question.objects.count()
    total_students = CustomUser.objects.filter(role='admin').count()
    total_clients = Request.objects.values('name').count()

    # Monthly growth - Course doesn't have created_at
    new_courses = 0  # Course model doesn't have created_at field
    new_questions = Question.objects.filter(created_at__gte=current_month_start).count()
    new_students = CustomUser.objects.filter(
        role='admin',
        date_joined__gte=current_month_start
    ).count()
    new_clients = Request.objects.filter(
        created_at__gte=current_month_start
    ).values('name').distinct().count()

    return Response({
        "totalCourses": total_courses,
        "totalQuestions": total_questions,
        "totalStudents": total_students,
        "totalClients": total_clients,
        "monthlyGrowth": {
            "courses": new_courses,
            "questions": new_questions,
            "students": new_students,
            "clients": new_clients
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def language_stats(request):
    language_data = Result.objects.values('language')\
        .annotate(
            students=Count('user', distinct=True),
            avgScore=Avg('exam_score')
        )

    return Response([{
        "name": item['language'],
        "students": item['students'],
        "avgScore": round(item['avgScore'], 2) if item['avgScore'] else 0
    } for item in language_data])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def proficiency_stats(request):
    proficiency_data = Result.objects.values('proficiency_level')\
        .annotate(value=Count('id'))

    return Response([{
        "name": item['proficiency_level'],
        "value": item['value']
    } for item in proficiency_data])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_stats(request):
    component_data = ResultDetail.objects.values('component')\
        .annotate(score=Avg('score'))

    return Response([{
        "name": item['component'],
        "score": round(item['score'], 2) if item['score'] else 0
    } for item in component_data])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_data(request):
    # Get the last 12 months of activity
    months_data = Result.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('-month')[:12]

    return Response([{
        "name": item['month'].strftime("%B"),
        "total": item['total']
    } for item in months_data])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_students(request):
    recent = Result.objects.select_related('details')\
        .order_by('-created_at')[:5]\
        .values(
            'user',
            'language',
            'exam_type',
            'exam_score',
            'created_at'
        )

    return Response(list(recent))
