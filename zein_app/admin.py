# from django.contrib import admin
# from .models import Subject, Topic, Question, Choice, Quiz, UserAnswer
#
# # Register your models here.
#
#
#
# class ChoiceInline(admin.TabularInline):
#     model = Choice
#     extra = 4
#     min_num = 2
#
#
# @admin.register(Question)
# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ('text', 'topic', 'get_subject')
#     list_filter = ('topic__subject', 'topic')
#     search_fields = ('text', 'topic__name', 'topic__subject__name')
#     inlines = [ChoiceInline]
#
#     def get_subject(self, obj):
#         return obj.topic.subject.name
#
#     get_subject.short_description = 'Предмет'
#
#
# @admin.register(Topic)
# class TopicAdmin(admin.ModelAdmin):
#     list_display = ('name', 'subject', 'get_question_count')
#     list_filter = ('subject',)
#     search_fields = ('name', 'subject__name')
#
#     def get_question_count(self, obj):
#         return obj.questions.count()
#
#     get_question_count.short_description = 'Кол-во вопросов'
#
#
# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('name', 'get_topic_count')
#     search_fields = ('name',)
#
#     def get_topic_count(self, obj):
#         return obj.topics.count()
#
#     get_topic_count.short_description = 'Кол-во тем'
#
#
# class UserAnswerInline(admin.TabularInline):
#     model = UserAnswer
#     extra = 0
#     readonly_fields = ('question', 'selected_choice', 'is_correct', 'answered_at')
#     can_delete = False
#
#
# @admin.register(Quiz)
# class QuizAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'topic', 'get_subject', 'status', 'score', 'total_questions',
#                     'get_percentage', 'started_at', 'completed_at')
#     list_filter = ('status', 'topic__subject', 'topic')
#     search_fields = ('user__username', 'topic__name', 'topic__subject__name')
#     readonly_fields = ('user', 'topic', 'status', 'score', 'total_questions',
#                        'started_at', 'completed_at')
#     inlines = [UserAnswerInline]
#
#     def get_subject(self, obj):
#         return obj.topic.subject.name
#
#     get_subject.short_description = 'Предмет'
#
#     def get_percentage(self, obj):
#         if obj.total_questions == 0:
#             return 0
#         return f"{round((obj.score / obj.total_questions) * 100, 2)}%"
#
#     get_percentage.short_description = 'Процент'





from django.contrib import admin
from .models import Subject, Topic, Question, Choice, Quiz, UserAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    min_num = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'topic', 'get_subject')
    list_filter = ('topic__subject', 'topic')
    search_fields = ('text', 'topic__name_uz', 'topic__name_ru', 'topic__subject__name_uz', 'topic__subject__name_ru')
    inlines = [ChoiceInline]
    fieldsets = (
        ('Question', {
            'fields': ('text', 'topic', 'explanation', 'image'),
        }),
    )

    def get_subject(self, obj):
        if obj.topic and obj.topic.subject:
            return obj.topic.subject.name_ru
        return "-"
    get_subject.short_description = 'Предмет'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'name_uz', 'subject', 'get_question_count')
    list_filter = ('subject',)
    search_fields = ('name_uz', 'name_ru', 'subject__name_uz', 'subject__name_ru')
    fieldsets = (
        ('Uzbek', {
            'fields': ('name_uz',),
        }),
        ('Russian', {
            'fields': ('name_ru',),
        }),
        ('Other', {
            'fields': ('subject', 'description'),
        }),
    )

    def get_question_count(self, obj):
        return obj.questions.count()
    get_question_count.short_description = 'Кол‑во вопросов'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'name_uz', 'get_topic_count')
    search_fields = ('name_uz', 'name_ru')
    fieldsets = (
        ('Uzbek', {
            'fields': ('name_uz',),
        }),
        ('Russian', {
            'fields': ('name_ru',),
        }),
        ('Other', {
            'fields': ('title_ru', 'description', 'image'),
        }),
    )

    def get_topic_count(self, obj):
        return obj.topics.count()
    get_topic_count.short_description = 'Кол‑во тем'


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'is_correct', 'answered_at')
    can_delete = False


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'topic', 'get_subject', 'status',
        'score', 'total_questions', 'get_percentage',
        'started_at', 'completed_at'
    )
    list_filter = ('status', 'topic__subject', 'topic')
    search_fields = ('user__username', 'topic__name', 'topic__subject__name')
    readonly_fields = (
        'user', 'topic', 'status', 'score',
        'total_questions', 'started_at', 'completed_at'
    )
    inlines = [UserAnswerInline]

    def get_subject(self, obj):
        if obj.topic and obj.topic.subject:
            return obj.topic.subject.name
        return "-"
    get_subject.short_description = 'Предмет'

    def get_percentage(self, obj):
        if obj.total_questions == 0:
            return "0%"
        return f"{round((obj.score / obj.total_questions) * 100, 2)}%"
    get_percentage.short_description = 'Процент'





from .models import Request

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone_number')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)



from .models import FAQ


class FAQAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question_en', 'question_ru', 'question_uz')
    fieldsets = (
        (None, {
            'fields': ('order', 'is_active')
        }),
        ('Uzbek', {
            'fields': ('question_uz', 'answer_uz'),
            'classes': ('collapse',),
        }),
        ('Russian', {
            'fields': ('question_ru', 'answer_ru'),
            'classes': ('collapse',),
        }),
        ('English', {
            'fields': ('question_en', 'answer_en'),
        }),
        ('Arabic', {
            'fields': ('question_ar', 'answer_ar'),
            'classes': ('collapse',),
        }),
        ('Korean', {
            'fields': ('question_ko', 'answer_ko'),
            'classes': ('collapse',),
        }),
        ('Turkish', {
            'fields': ('question_tr', 'answer_tr'),
            'classes': ('collapse',),
        }),
    )

    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Question'


admin.site.register(FAQ, FAQAdmin)
