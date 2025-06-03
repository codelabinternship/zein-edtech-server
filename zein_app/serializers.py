import re
from rest_framework import serializers
from django.contrib.auth.models import User
import json
from telegram_bot.models import TelegramSettings
from .mixins import ImageDeleteMixin
from .models import (
    BadPassword,
    CustomUser,
    Question,
    Choice,
    Subject,
    Topic,
    Quiz,
    UserAnswer,
    Course,
    CourseLevel,
    Teacher,
    Contact,
    FAQ,
    TelegramBot,
    Request,
    ResultDetail,
    Result,
    SEO,
)


# Start with basic serializers that don't have dependencies
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "full_name", "username")


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "full_name", "username", "password", "date_joined", "role")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class BadPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadPassword
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", "full_name", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            full_name=validated_data["full_name"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


# class HistorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = History
#         fields = "__all__"
#         read_only_fields = ("failed", "score", "percent")


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


# Define base subject and topic serializers first
class SubjectListSerializer(serializers.ModelSerializer):
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "description", "image", "topic_count", "created_at"]

    def get_topic_count(self, obj):
        return obj.topics.count()


class TopicListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "description",
            "question_count",
            "subject",
            "created_at",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


# Now define choice and question serializers
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class AdminChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class QuestionSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    topic_id = serializers.IntegerField(required=True, allow_null=False)
    topic = TopicListSerializer(many=False, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "image",
            "choices",
            "explanation",
            "created_at",
            "topic",
            "topic_id",
        ]

    def validate_correct_choices(self, value):
        allowed_choices = {"A", "B", "C", "D"}
        if not all(choice in allowed_choices for choice in value):
            raise serializers.ValidationError(
                "Each correct choice must be one of 'A', 'B', 'C', or 'D'."
            )
        return value

    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        print(validated_data)
        question = Question.objects.create(**validated_data)

        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            self.delete_old_image(instance, 'image')
        choices_data = validated_data.pop("choices", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if choices_data is not None:
            instance.choices.all().delete()
            for choice_data in choices_data:
                Choice.objects.create(question=instance, **choice_data)

        return instance

from zein_app.models import QuizHistory

class QuizHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizHistory
        fields = '__all__'


class QuestionListSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    topic = TopicListSerializer(many=False, read_only=True)
    topic_id = serializers.IntegerField(required=True, allow_null=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "explanation",
            "image",
            "choices",
            "topic",
            "topic_id",
            "created_at",
            "updated_at",
        ]


class QuestionDetailSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    topic = TopicListSerializer(many=False, read_only=True)
    topic_id = serializers.IntegerField(required=True, allow_null=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "image",
            "choices",
            "topic",
            "topic_id",
            "created_at",
            "updated_at",
        ]


class AdminQuestionSerializer(serializers.ModelSerializer):
    choices = AdminChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "explanation", "image", "choices"]


# Now define the more complex serializers that depend on the ones above
class TopicDetailSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    questions = QuestionListSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "description",
            "questions",
            "subject",
            "subject_id",
            "created_at",
        ]

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            self.delete_old_image(instance, 'image')
        return super().update(instance, validated_data)


class SubjectDetailSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    topics = TopicListSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "name", "description", "image", "topics", "created_at"]

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            self.delete_old_image(instance, 'image')
        return super().update(instance, validated_data)


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ["id", "question", "selected_choice", "is_correct"]


class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ["topic"]


class QuizAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()


class QuizResultSerializer(serializers.ModelSerializer):
    topic_name = serializers.ReadOnlyField(source="topic.name")
    subject_name = serializers.ReadOnlyField(source="topic.subject.name")
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "topic_name",
            "subject_name",
            "score",
            "total_questions",
            "percentage",
            "started_at",
            "completed_at",
        ]

    def get_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        return round((obj.score / obj.total_questions) * 100, 2)


class QuizDetailSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True, read_only=True)
    topic_name = serializers.ReadOnlyField(source="topic.name")
    subject_name = serializers.ReadOnlyField(source="topic.subject.name")
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "topic_name",
            "subject_name",
            "status",
            "score",
            "total_questions",
            "percentage",
            "started_at",
            "completed_at",
            "answers",
        ]

    def get_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        return round((obj.score / obj.total_questions) * 100, 2)


class CourseLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLevel
        fields = [
            "id", "course", "title_uz", "title_ru", "level", "duration_months", "price", "features_uz", "features_ru"
        ]

class CourseSerializer(serializers.ModelSerializer):
    levels = CourseLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "name_uz", "name_ru", "levels"]
class CourseLevelLangSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLevel
        fields = ["id", "title_uz", "title_ru", "level", "duration_months", "price", "features_uz", "features_ru"]


class CourseLangSerializer(serializers.ModelSerializer):
    levels = CourseLevelLangSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "name_uz", "name_ru", "levels"]

    def to_representation(self, instance):
        lang = self.context.get("request").query_params.get("lang")
        data = super().to_representation(instance)
        if lang == "ru":
            return {
                "id": data["id"],
                "name_ru": data["name_ru"],
                "levels": data["levels"],
            }
        elif lang == "uz":
            return {
                "id": data["id"],
                "name_uz": data["name_uz"],
                "levels": data["levels"],
            }
        return data
class TeacherSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = "__all__"

    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            self.delete_old_image(instance, 'photo')
        return super().update(instance, validated_data)


class FAQSerializer(serializers.ModelSerializer):
    """
    Serializer for the FAQ model.
    Handles serialization and deserialization of FAQ objects.
    """

    class Meta:
        model = FAQ
        fields = [
            "id",
            "question_uz",
            "question_ru",
            "answer_uz",
            "answer_ru",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]


class FAQLanguageSerializer(serializers.Serializer):
    """
    Serializer for displaying FAQs in a specific language.
    Dynamically changes field names based on language.
    """

    id = serializers.IntegerField(read_only=True)
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    order = serializers.IntegerField(read_only=True)

    def __init__(self, *args, **kwargs):
        # Extract language from context if present
        super().__init__(*args, **kwargs)
        self.language = self.context.get("language", "uz")

    def get_question(self, obj):
        return getattr(obj, f"question_{self.language}")

    def get_answer(self, obj):
        return getattr(obj, f"answer_{self.language}")


class LocalizedFAQSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()

    class Meta:
        model = FAQ
        fields = [
            "id",
            "question",
            "answer",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_question(self, obj):
        lang = self.context.get("language", "en")
        return obj.get_question(lang)

    def get_answer(self, obj):
        lang = self.context.get("language", "en")
        return obj.get_answer(lang)


class ContactSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"

    def update(self, instance, validated_data):
        if 'hero_banner' in validated_data:
            self.delete_old_image(instance, 'hero_banner')
        return super().update(instance, validated_data)


class TelegramBotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramBot
        fields = "__all__"


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ["id", "name", "phone_number", "created_at"]
        read_only_fields = ["id", "created_at"]


class ResultDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultDetail
        fields = ["component", "score"]


class ResultSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    details = serializers.JSONField(write_only=True)

    class Meta:
        model = Result
        fields = [
            "id",
            "user",
            "language",
            "image",
            "proficiency_level",
            "exam_type",
            "exam_score",
            "details",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        details_data = validated_data.pop('details', None)
        if isinstance(details_data, str):
            try:
                details_data = json.loads(details_data)
            except json.JSONDecodeError:
                raise serializers.ValidationError({"details": "Invalid JSON format"})

        result = Result.objects.create(**validated_data)

        if details_data:
            for detail in details_data:
                ResultDetail.objects.create(result=result, **detail)

        return result

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            self.delete_old_image(instance, 'image')

        details_data = validated_data.pop('details', None)
        if isinstance(details_data, str):
            try:
                details_data = json.loads(details_data)
            except json.JSONDecodeError:
                raise serializers.ValidationError({"details": "Invalid JSON format"})

        # Update the result instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data is not None:
            # Delete existing details
            instance.details.all().delete()
            # Create new details
            for detail in details_data:
                ResultDetail.objects.create(result=instance, **detail)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['details'] = ResultDetailSerializer(instance.details.all(), many=True).data
        return representation


class TelegramSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramSettings
        fields = [
            "id",
            "bot_token",
            "admin_chat_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SEOSerializer(ImageDeleteMixin, serializers.ModelSerializer):
    ogImage = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = SEO
        fields = ["id", "metaTitle", "metaDescription", "keywords", "ogImage"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        if instance.ogImage:
            if request:
                representation['ogImage'] = request.build_absolute_uri(instance.ogImage.url)
            else:
                representation['ogImage'] = instance.ogImage.url
        return representation

    def update(self, instance, validated_data):
        if 'ogImage' in validated_data:
            # Delete old image if it exists and a new one is being uploaded
            self.delete_old_image(instance, 'ogImage')
        return super().update(instance, validated_data)


class PasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class DevPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)


# Example for a custom login view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import LoginSerializer, CustomUserSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = CustomUser.objects.filter(username=username).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            user_data = CustomUserSerializer(user).data
            return Response(
                {
                    "access": str(refresh.access_token),
                    "user": user_data,  # This includes 'role'
                }
            )
        return Response({"detail": "Invalid credentials"}, status=400)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("full_name", "username")


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "full_name", "username", "last_login", "role")
        read_only_fields = ("id", "last_login", "role")

    def create(self, validated_data):
        validated_data["role"] = "admin"
        password = validated_data.pop("password", None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
