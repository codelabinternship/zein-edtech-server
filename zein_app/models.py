# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.db.models.signals import pre_save
from zein_app.storage import CustomS3Storage

def delete_image_if_changed(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            if isinstance(field, models.ImageField):
                old_file = getattr(old_instance, field.name)
                new_file = getattr(instance, field.name)
                if old_file and old_file != new_file:
                    try:
                        default_storage.delete(old_file.path)
                    except Exception:
                        pass
    except sender.DoesNotExist:
        pass

@receiver(pre_save)
def handle_image_updates(sender, instance, **kwargs):
    if hasattr(instance, '_meta') and any(isinstance(f, models.ImageField) for f in instance._meta.fields):
        delete_image_if_changed(sender, instance, **kwargs)
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
        ('dev', 'Developer'),
    )
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)


class BadPassword(models.Model):
    password = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.password




# class History(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="histories"
#     )
#     total_question = models.PositiveIntegerField()
#     correct = models.PositiveIntegerField()
#     failed = models.PositiveIntegerField(editable=False)
#     score = models.FloatField(editable=False)
#     percent = models.FloatField(editable=False)
#
#     def save(self, *args, **kwargs):
#         self.failed = self.total_question - self.correct
#         self.score = float(self.correct)
#         if self.total_question > 0:
#             self.percent = round((self.correct / self.total_question) * 100, 1)
#         else:
#             self.percent = 0.0
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"History of {self.user.username} - Score: {self.score}"


# class Question(models.Model):
#     text = models.TextField()
#     choice_a = models.CharField(max_length=255)
#     choice_b = models.CharField(max_length=255)
#     choice_c = models.CharField(max_length=255, blank=True, null=True)
#     choice_d = models.CharField(max_length=255, blank=True, null=True)
#
#     correct_choices = models.JSONField()
#
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.text


# class Subject(models.Model):
#     name_uz = models.CharField(max_length=255)
#     name_ru = models.CharField(max_length=255)
#     name_en = models.CharField(max_length=255)
#
#     def __str__(self):
#         return self.name_en


from django.contrib.auth.models import AbstractUser


class Subject(models.Model):
    name = models.CharField(max_length=100)
    title_ru = models.TextField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="subjects/", blank=True, null=True,storage=CustomS3Storage)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Topic(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="topics"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

    class Meta:
        ordering = ["subject", "name"]


class Question(models.Model):
    # topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions', default=1)
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="questions", null=True, blank=True
    )
    text = models.TextField()
    explanation = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="questions/", blank=True, null=True,storage=CustomS3Storage)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50]

    class Meta:
        ordering = ["topic", "created_at"]




from django.conf import settings

class QuizHistory(models.Model):
    user = models.ForeignKey("zein_app.CustomUser", on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    # questions = models.ManyToManyField(Question,related_name="questions")
    correct_answers = models.IntegerField()
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.topic} | {self.percentage}%"



class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ["question", "id"]


class Quiz(models.Model):
    STATUS_CHOICES = (
        ("in_progress", "В процессе"),
        ("completed", "Завершено"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="quizzes")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress"
    )
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic.name} ({self.status})"

    class Meta:
        ordering = ["-started_at"]

class UserAnswer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quiz.user.username} - {self.question.text[:30]}"

    class Meta:
        ordering = ['quiz', 'answered_at']
        unique_together = ['quiz', 'question']


# class UserAnswer(models.Model):
#     quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
#     is_correct = models.BooleanField(default=False)
#     answered_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.quiz.user.username} - {self.question.text[:30]}"
#
#     class Meta:
#         ordering = ["quiz", "answered_at"]
#         unique_together = ["quiz", "question"]


# class Topic(models.Model):
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
#     name = models.CharField(max_length=255)
#     lesson_number = models.PositiveIntegerField()
#
#     def __str__(self):
#         return f'{self.subject.name_en} - {self.name}'


# class QuizSession(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_sessions')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
#     topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
#     total_questions = models.PositiveIntegerField()
#     is_active = models.BooleanField(default=True)
#     started_at = models.DateTimeField(auto_now_add=True)
#     finished_at = models.DateTimeField(null=True, blank=True)
#
#     def __str__(self):
#         return f'QuizSession {self.user.username} - {self.subject.name_en}'


# class UserAnswer(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='user_answers')
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     selected_choices = models.JSONField()
#     is_correct = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f'Answer by {self.user.username}'


class Course(models.Model):
    name_uz = models.CharField(max_length=255, default="")
    name_ru = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.name_ru


class CourseLevel(models.Model):
    course = models.ForeignKey(Course, related_name="levels", on_delete=models.CASCADE)
    title_uz = models.CharField(max_length=255, default="")
    title_ru = models.CharField(max_length=255, default="")
    level = models.CharField(max_length=10, default="A1")
    duration_months = models.CharField(max_length=20, default="1")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    features_uz = models.JSONField(default=list, blank=True)
    features_ru = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title_ru} ({self.level})"


class Teacher(models.Model):
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()
    photo = models.ImageField(upload_to="teachers/",storage=CustomS3Storage)

    def __str__(self):
        return self.name


class FAQ(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    question_uz = models.CharField(max_length=255, blank=True)
    question_ru = models.CharField(max_length=255, blank=True)

    answer_uz = models.TextField(blank=True)
    answer_ru = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"


# class FAQ(models.Model):
#     language = models.ForeignKey(on_delete=models.CASCADE, null=True, blank=True)
#     question = models.CharField(max_length=500)
#     answer = models.TextField()
#     order = models.PositiveIntegerField(default=1)
#
#
#     def __str__(self):
#         return self.question


class Contact(models.Model):
    phone = models.CharField(max_length=255, unique=True,default="+998")
    email = models.EmailField(max_length=255, unique=True,default="")
    hero_banner = models.ImageField(upload_to="contact/banner/",null=True,storage=CustomS3Storage)
    telegram = models.CharField(max_length=255,default="t.me/")
    instagram = models.CharField(max_length=255,default="instagram.com/")

    def __str__(self):
        return f"{self.type}: {self.value}"


# models.py
from django.db import models


class TelegramBot(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.username


class Request(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

    class Meta:
        ordering = ["-created_at"]


# class CustomAdmin(models.Model):
#     admin_chat_id = models.CharField(mini_length=300)
#     request_bot_token = models.CharField(max_length=500)


class Result(models.Model):
    user = models.CharField(max_length=100)
    language = models.CharField(max_length=20)
    image = models.ImageField(upload_to="exam-results/", default="/placeholder.svg",storage=CustomS3Storage)
    proficiency_level = models.CharField(max_length=10)
    exam_type = models.CharField(max_length=20)  # IELTS, TOEFL, TOPIK ...
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0
    )  # 9.0  5.5 7.5 ...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ResultDetail(models.Model):
    result = models.ForeignKey(Result, related_name="details", on_delete=models.CASCADE)
    component = models.CharField(max_length=50)  # reading, writing, grammar, ...
    score = models.DecimalField(max_digits=5, decimal_places=2)


class SEO(models.Model):
    metaTitle = models.CharField(max_length=255)
    metaDescription = models.TextField()
    keywords = models.CharField(max_length=512)
    ogImage = models.ImageField(upload_to="seo/og_images/", blank=True, null=True,storage=CustomS3Storage)

    def __str__(self):
        return self.metaTitle
