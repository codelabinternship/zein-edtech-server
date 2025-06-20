import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites import requests

from zein_app.models import Subject, Topic, Quiz, Question, UserAnswer, CustomUser, Choice

logger = logging.getLogger(__name__)


class APIService:
    @staticmethod
    def get_subjects(language_code='ru'):
        try:
            subjects = Subject.objects.all()
            return [
                {
                    'id': subject.id,
                    'title': subject.name_uz if language_code == 'ru' else subject.name_ru,
                    'description': subject.description
                }
                for subject in subjects
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении предметов: {e}")
            return []

    @staticmethod
    def get_topics(subject_id, language_code='ru'):
        try:
            topics = Topic.objects.filter(subject_id=subject_id)
            return [
                {
                    'id': topic.id,
                    'title': topic.name_ru if language_code == 'ru' else topic.name_uz,
                    'description': topic.description
                }
                for topic in topics
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении тем для предмета {subject_id}: {e}")
            return []

    @staticmethod
    def get_subject_by_id(subject_id, language_code='ru'):
        try:
            subject = Subject.objects.get(id=subject_id)
            return subject.name_ru if language_code == 'ru' else subject.name_uz
        except Subject.DoesNotExist:
            return 'Неизвестный предмет'

    @staticmethod
    def get_topic_by_id(topic_id, language_code='ru'):
        try:
            topic = Topic.objects.get(id=topic_id)
            return topic.name_ru if language_code == 'ru' else topic.name_uz
        except Topic.DoesNotExist:
            return 'Неизвестная тема'

    @staticmethod
    def get_or_create_quiz(user_id: int, topic_id: int,language_code='ru') -> Quiz:
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            topic = Topic.objects.get(id=topic_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с id={user_id} не найден")
            return None
        except Topic.DoesNotExist:
            logger.error(f"Тема с id={topic_id} не найдена")
            return None

        quiz, created = Quiz.objects.get_or_create(
            user=user,
            topic=topic,
            defaults={
                # 'status': Quiz.Status.IN_PROGRESS,
                # 'total_questions': Question.objects.filter(topic=topic).count()
                'status': 'in_progress',
                'total_questions': Question.objects.filter(topic=topic).count(),
                'name': topic.name_ru if language_code == 'ru' else topic.name_uz,
                'description': topic.description
            }
        )

        if created:
            logger.info(f"Создана новая викторина (id={quiz.id}) для user={user_id}, topic={topic_id}")
        else:
            logger.info(f"Найдена существующая викторина (id={quiz.id}) для user={user_id}, topic={topic_id}")
        return quiz

    @staticmethod
    def get_quizzes(topic_id, language_code='ru'):
        try:
            quizzes = Quiz.objects.filter(topic_id=topic_id, language_code='ru')
            return [
                {
                    'id': quiz.id,
                    # 'title': getattr(quiz, 'title', ''),
                    # 'description': getattr(quiz, 'description', ''),
                    'title': quiz.topic.name_ru if language_code == 'ru' else quiz.topic.name_uz,
                    'description': quiz.topic.description,
                    # 'questions_count': quiz.questions.count()
                    'questions_count': Question.objects.filter(topic=quiz.topic).count()
                }
                for quiz in quizzes
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении тестов для темы {topic_id}: {e}")
            return []

    @staticmethod
    def get_quiz_with_questions(quiz_id, language_code='ru'):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            questions = Question.objects.filter(topic=quiz.topic)

            quiz_data = {
                'id': quiz.id,
                'title': quiz.topic.name_ru if language_code == 'ru' else quiz.topic.name_uz,
                'description': quiz.topic.description,
                'questions': []
            }

            for question in questions:
                choices = Choice.objects.filter(question=question)
                question_data = {
                    'id': question.id,
                    'text': question.text,
                    'explanation': question.explanation or "",
                    'answers': [
                        {
                            'id': choice.id,
                            'text': choice.text,
                            'is_correct': choice.is_correct
                        }
                        for choice in choices
                    ]
                }
                quiz_data['questions'].append(question_data)

            return quiz_data
        except Quiz.DoesNotExist:
            logger.warning(f"Викторина с ID {quiz_id} не найдена")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении викторины с ID {quiz_id}: {e}")
            return None


    # @staticmethod
    # def get_quiz_with_questions(quiz_id, language_code='ru'):
    #     try:
    #         quiz = Quiz.objects.get(id=quiz_id)
    #         # questions = Question.objects.filter(topic=quiz.topic)
    #         questions = Question.objects.filter(topic=quiz.topic)
    #
    #         quiz_data = {
    #             'id': quiz.id,
    #             # 'title': quiz.name,
    #             # 'description': quiz.description,
    #             'title': quiz.topic.name,
    #             'description': quiz.topic.description,
    #             'questions': []
    #         }
    #
    #         for question in questions:
    #             # answers = UserAnswer.objects.filter(question=question)
    #             choices = Choice.objects.filter(question=question)
    #             question_data = {
    #                 'id': question.id,
    #                 'text': question.text,
    #                 'answers': [
    #                     {
    #                     'id': choice.id,
    #                     'text': choice.text,
    #                     'is_correct': choice.is_correct
    #                     }
    #                     for choice in choices
    #                     ]
    #             }
    #             quiz_data['questions'].append(question_data)
    #
    #         return quiz_data
    #     except Quiz.DoesNotExist:
    #         logger.warning(f"Викторина с ID {quiz_id} не найдена")
    #         return None
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении викторины с ID {quiz_id}: {e}")
    #         return None

    @staticmethod
    def register_user(phone_number, full_name, language_code='ru'):
        try:
            names = full_name.split(maxsplit=1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ""

            user, created = CustomUser.objects.get_or_create(
                phone=phone_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': phone_number
                }
            )

            return {
                'id': user.id,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created': created
            }
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя: {e}")
            return None

    @staticmethod
    def save_quiz_results(quiz_id, user_answers, correct_answers, total_questions):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            quiz.status = 'completed'
            quiz.score = correct_answers
            quiz.save()

            for question_index, answer_data in user_answers.items():
                try:
                    question = Question.objects.get(id=answer_data['question_id'])
                    selected_choice = Choice.objects.get(id=answer_data['answer_id'])

                    user_answer, created = UserAnswer.objects.update_or_create(
                        quiz=quiz,
                        question=question,
                        defaults={
                            'selected_choice': selected_choice,
                            'is_correct': answer_data['is_correct']
                        }
                    )

                    if created:
                        logger.info(f"Создан новый ответ для вопроса {question.id}")
                    else:
                        logger.info(f"Обновлен существующий ответ для вопроса {question.id}")

                except Question.DoesNotExist:
                    logger.error(f"Вопрос с ID {answer_data['question_id']} не найден")
                    continue
                except Choice.DoesNotExist:
                    logger.error(f"Вариант ответа с ID {answer_data['answer_id']} не найден")
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при сохранении ответа на вопрос {answer_data['question_id']}: {e}")
                    continue

            logger.info(f"Сохранены результаты для викторины {quiz_id}: {correct_answers}/{total_questions}")
            return True

        except Quiz.DoesNotExist:
            logger.warning(f"Викторина с ID {quiz_id} не найдена при сохранении результатов")
            return False
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов викторины {quiz_id}: {e}")
            return False

    # @staticmethod
    # def save_quiz_results(quiz_id, user_answers, correct_answers, total_questions):
    #     try:
    #         quiz = Quiz.objects.get(id=quiz_id)
    #
    #
    #         quiz.status = 'completed'
    #         quiz.score = correct_answers
    #         quiz.save()
    #
    #
    #         for question_index, answer_data in user_answers.items():
    #             user_answer = UserAnswer(
    #                 quiz=quiz,
    #                 question_id=answer_data['question_id'],
    #                 choice_id=answer_data['answer_id'],
    #                 is_correct=answer_data['is_correct']
    #             )
    #             user_answer.save()
    #
    #         logger.info(f"Сохранены результаты для викторины {quiz_id}: {correct_answers}/{total_questions}")
    #         return True
    #     except Quiz.DoesNotExist:
    #         logger.warning(f"Викторина с ID {quiz_id} не найдена при сохранении результатов")
    #         return False
    #     except Exception as e:
    #         logger.error(f"Ошибка при сохранении результатов викторины {quiz_id}: {e}")
    #         return False