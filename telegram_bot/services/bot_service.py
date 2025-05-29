from telegram import Update
from telegram import Poll, PollAnswer
from telegram.ext import PollAnswerHandler, ContextTypes
import logging
from asgiref.sync import sync_to_async
from django.db import transaction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from ..models import TelegramUser
from .api_service import APIService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, TOPIC_SELECTION, QUIZ_SELECTION, QUESTION, ANSWER = range(
    8)

LANGUAGES = {
    "uz": "Узбекский",
    "ru": "Русский",
    "en": "Английский",
    "tr": "Турецкий",
    "ar": "Арабский",
    "ko": "Корейский"
}

QUESTION, ANSWER = range(6, 8)

TEXTS = {
    "ru": {
        "welcome": "Добро пожаловать! Пожалуйста, выберите язык:",
        "phone_request": "Пожалуйста, поделитесь своим номером телефона:",
        "share_phone": "Поделиться номером телефона",
        "name_request": "Введите ваше имя и фамилию:",
        "registration_successful": "Регистрация успешна! Теперь вы можете выбрать предмет:",
        "choose_subject": "Выберите предмет:",
        "choose_lesson": "Выберите урок:",
        "start_quiz": "Начать викторину",
        "quiz_info": "Информация о тесте:\n\nНазвание: {}\nОписание: {}\nКоличество вопросов: {}"
    },

}

for lang in LANGUAGES:
    if lang != "ru":
        TEXTS[lang] = TEXTS["ru"]


class BotService:
    def __init__(self, token):
        self.token = token
        self.application = None

    def start(self):
        self.application = Application.builder().token(self.token).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_handler, pattern=r"^lang_")],
                PHONE_NUMBER: [MessageHandler(filters.CONTACT, self.phone_handler)],
                FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.name_handler)],
                SUBJECT_SELECTION: [
                    CallbackQueryHandler(self.subject_handler, pattern=r"^subject_"),
                    CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$")
                ],
                TOPIC_SELECTION: [CallbackQueryHandler(self.topic_handler, pattern=r"^topic_")],
                QUIZ_SELECTION: [
                    CallbackQueryHandler(self.quiz_handler, pattern=r"^quiz_"),
                    CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_")
                ],
                QUESTION: [
                ],
                ANSWER: [CallbackQueryHandler(self.next_question_handler, pattern=r"^next_question$")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)]
        )

        self.application.add_handler(CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$"))
        self.application.add_handler(CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_"))
        self.application.add_handler(PollAnswerHandler(self.poll_answer_handler))

        self.application.add_handler(conv_handler)
        self.application.run_polling()

    async def restart_subjects_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_subjects_sync():
                return APIService.get_subjects(language_code=lang_code)

            subjects = await get_subjects_sync()

            if not subjects:
                await query.edit_message_text("Не удалось получить список предметов. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for subject in subjects:
                keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)

            return SUBJECT_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в restart_subjects_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def next_question_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            context.user_data["current_question_index"] += 1

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в next_question_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка при переходе к следующему вопросу.")
            return ConversationHandler.END

    @staticmethod
    @transaction.atomic
    def _get_or_create_telegram_user(telegram_id, chat_id, username, first_name, last_name, language_code):
        telegram_user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'chat_id': chat_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code or 'ru'
            }
        )

        if not created:
            telegram_user.chat_id = chat_id
            telegram_user.username = username
            telegram_user.first_name = first_name
            telegram_user.last_name = last_name
            telegram_user.save()

        return telegram_user, created

    @staticmethod
    def _update_telegram_user_language(user_id, lang_code):
        telegram_user = TelegramUser.objects.get(id=user_id)
        telegram_user.language_code = lang_code
        telegram_user.save()

    @staticmethod
    def _update_telegram_user_phone(user_id, phone_number):
        telegram_user = TelegramUser.objects.get(id=user_id)
        telegram_user.phone_number = phone_number
        telegram_user.save()

    @staticmethod
    def _link_telegram_user_with_app_user(telegram_user_id, user_id):
        telegram_user = TelegramUser.objects.get(id=telegram_user_id)
        from zein_app.models import CustomUser
        telegram_user.user = CustomUser.objects.get(id=user_id)
        telegram_user.save()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.effective_user
        context.user_data["chat_id"] = update.effective_chat.id
        context.user_data["telegram_id"] = update.effective_user.id
        context.user_data["username"] = update.effective_user.username or update.effective_user.first_name

        try:
            telegram_user, created = await sync_to_async(self._get_or_create_telegram_user)(
                telegram_id=user.id,
                chat_id=update.effective_chat.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code or 'ru'
            )

            context.user_data["telegram_user_id"] = telegram_user.id

            keyboard = []
            row = []
            for i, (lang_code, lang_name) in enumerate(LANGUAGES.items(), 1):
                button = InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")
                row.append(button)
                if i % 2 == 0:
                    keyboard.append(row)
                    row = []

            if row:
                keyboard.append(row)

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(TEXTS["ru"]["welcome"], reply_markup=reply_markup)
            return LANGUAGE_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка при запуске. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def language_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            lang_code = query.data.split("_")[1]
            context.user_data["language"] = lang_code

            telegram_user_id = context.user_data.get("telegram_user_id")
            if telegram_user_id:
                await sync_to_async(self._update_telegram_user_language)(telegram_user_id, lang_code)

            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton(text=TEXTS[lang_code]["share_phone"], request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await query.edit_message_text(text=TEXTS[lang_code]["phone_request"])
            await query.message.reply_text(
                text=TEXTS[lang_code]["phone_request"],
                reply_markup=keyboard
            )
            return PHONE_NUMBER
        except Exception as e:
            logger.error(f"Ошибка в language_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def phone_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            contact = update.message.contact
            phone_number = contact.phone_number
            context.user_data["phone"] = phone_number

            telegram_user_id = context.user_data.get("telegram_user_id")
            if telegram_user_id:
                await sync_to_async(self._update_telegram_user_phone)(telegram_user_id, phone_number)

            lang_code = context.user_data.get("language", "ru")
            await update.message.reply_text(TEXTS[lang_code]["name_request"])
            return FULL_NAME
        except Exception as e:
            logger.error(f"Ошибка в phone_handler: {e}")
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def name_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            full_name = update.message.text
            context.user_data["full_name"] = full_name

            lang_code = context.user_data.get("language", "ru")
            phone_number = context.user_data.get("phone")

            @sync_to_async
            def register_user_sync():
                return APIService.register_user(
                    phone_number=phone_number,
                    full_name=full_name,
                    language_code=lang_code
                )

            user_data = await register_user_sync()

            if user_data:
                telegram_user_id = context.user_data.get("telegram_user_id")
                if telegram_user_id:
                    await sync_to_async(self._link_telegram_user_with_app_user)(telegram_user_id, user_data["id"])

            @sync_to_async
            def get_subjects_sync():
                return APIService.get_subjects(language_code=lang_code)

            subjects = await get_subjects_sync()

            if not subjects:
                await update.message.reply_text("Не удалось получить список предметов. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for subject in subjects:
                keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(TEXTS[lang_code]["registration_successful"])
            await update.message.reply_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)
            return SUBJECT_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в name_handler: {e}")
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def subject_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            subject_id = int(query.data.split("_")[1])
            context.user_data["subject_id"] = subject_id
            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_topics_sync():
                return APIService.get_topics(subject_id, language_code=lang_code)

            topics = await get_topics_sync()

            if not topics:
                await query.edit_message_text("Не удалось получить список уроков. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for topic in topics:
                keyboard.append([InlineKeyboardButton(topic["title"], callback_data=f"topic_{topic['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(TEXTS[lang_code]["choose_lesson"], reply_markup=reply_markup)
            return TOPIC_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в subject_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END



    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            quiz_data = context.user_data["quiz_data"]
            idx = context.user_data.get("current_question_index", 0)

            if idx >= len(quiz_data["questions"]):
                return await self.show_quiz_results(update, context)

            q = quiz_data["questions"][idx]
            text = f"[{idx + 1}/{len(quiz_data['questions'])}] {q['text']}"
            options = [a["text"] for a in q["answers"]]
            correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))

            explanation = q.get("explanation", "") or ""

            chat_id = None

            if "chat_id" in context.user_data:
                chat_id = context.user_data["chat_id"]
                logger.info(f"Получен chat_id из context.user_data: {chat_id}")

            elif update and update.effective_chat:
                chat_id = update.effective_chat.id
                logger.info(f"Получен chat_id из update.effective_chat: {chat_id}")

            elif update and update.callback_query and update.callback_query.message:
                chat_id = update.callback_query.message.chat_id
                logger.info(f"Получен chat_id из update.callback_query: {chat_id}")

            elif update and hasattr(update, "message") and update.message:
                chat_id = update.message.chat_id
                logger.info(f"Получен chat_id из update.message: {chat_id}")

            elif "telegram_id" in context.user_data:
                @sync_to_async
                def get_chat_id_from_db(telegram_id):
                    try:
                        user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
                        if user and hasattr(user, "chat_id"):
                            return user.chat_id
                        return None
                    except Exception as e:
                        logger.error(f"Ошибка при получении chat_id из БД: {e}")
                        return None

                chat_id = await get_chat_id_from_db(context.user_data["telegram_id"])
                if chat_id:
                    logger.info(f"Получен chat_id из базы данных: {chat_id}")

            if not chat_id and hasattr(context.bot, "active_conversations"):
                for user_id, conv_data in context.bot.active_conversations.items():
                    if user_id == context.user_data.get("telegram_id"):
                        chat_id = conv_data.get("chat_id")
                        if chat_id:
                            logger.info(f"Получен chat_id из active_conversations: {chat_id}")
                            break

            if not chat_id:
                logger.error(
                    f"Не удалось определить chat_id для пользователя: {context.user_data.get('telegram_id', 'Unknown')}")
                return ConversationHandler.END

            context.user_data["chat_id"] = chat_id

            message = await context.bot.send_poll(
                chat_id=chat_id,
                question=text,
                options=options,
                type="quiz",
                correct_option_id=correct_option,
                is_anonymous=False,
                explanation=explanation
            )

            polls = context.user_data.setdefault("polls_mapping", {})
            polls[message.poll.id] = idx

            context.user_data["current_question_index"] = idx + 1

            return QUESTION
        except Exception as e:
            logger.error(f"Ошибка в show_question: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ConversationHandler.END

    # async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     try:
    #         quiz_data = context.user_data["quiz_data"]
    #         idx = context.user_data.get("current_question_index", 0)
    #
    #         if idx >= len(quiz_data["questions"]):
    #             return await self.show_quiz_results(update, context)
    #
    #         q = quiz_data["questions"][idx]
    #         text = f"[{idx + 1}/{len(quiz_data['questions'])}] {q['text']}"
    #         options = [a["text"] for a in q["answers"]]
    #         correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))
    #
    #         chat_id = None
    #
    #         if "chat_id" in context.user_data:
    #             chat_id = context.user_data["chat_id"]
    #             logger.info(f"Получен chat_id из context.user_data: {chat_id}")
    #
    #         elif update and update.effective_chat:
    #             chat_id = update.effective_chat.id
    #             logger.info(f"Получен chat_id из update.effective_chat: {chat_id}")
    #
    #
    #         elif update and update.callback_query and update.callback_query.message:
    #             chat_id = update.callback_query.message.chat_id
    #             logger.info(f"Получен chat_id из update.callback_query: {chat_id}")
    #
    #
    #         elif update and hasattr(update, "message") and update.message:
    #             chat_id = update.message.chat_id
    #             logger.info(f"Получен chat_id из update.message: {chat_id}")
    #
    #
    #         elif "telegram_id" in context.user_data:
    #             @sync_to_async
    #             def get_chat_id_from_db(telegram_id):
    #                 try:
    #                     user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
    #                     if user and hasattr(user, "chat_id"):
    #                         return user.chat_id
    #                     return None
    #                 except Exception as e:
    #                     logger.error(f"Ошибка при получении chat_id из БД: {e}")
    #                     return None
    #
    #             chat_id = await get_chat_id_from_db(context.user_data["telegram_id"])
    #             if chat_id:
    #                 logger.info(f"Получен chat_id из базы данных: {chat_id}")
    #
    #         if not chat_id and hasattr(context.bot, "active_conversations"):
    #             for user_id, conv_data in context.bot.active_conversations.items():
    #                 if user_id == context.user_data.get("telegram_id"):
    #                     chat_id = conv_data.get("chat_id")
    #                     if chat_id:
    #                         logger.info(f"Получен chat_id из active_conversations: {chat_id}")
    #                         break
    #
    #
    #         if not chat_id:
    #             logger.error(
    #                 f"Не удалось определить chat_id для пользователя: {context.user_data.get('telegram_id', 'Unknown')}")
    #             # admin_chat_id = REQUEST_TELEGRAM_ADMIN_CHAT_ID
    #             # await context.bot.send_message(
    #             #     chat_id=admin_chat_id,
    #             #     text=f"Ошибка: Не удалось определить chat_id для пользователя {context.user_data.get('username', 'Unknown')}"
    #             # )
    #             return ConversationHandler.END
    #
    #         context.user_data["chat_id"] = chat_id
    #
    #         message = await context.bot.send_poll(
    #             chat_id=chat_id,
    #             question=text,
    #             options=options,
    #             type="quiz",
    #             correct_option_id=correct_option,
    #             is_anonymous=False,
    #             explanation="Смотри ответ ниже"
    #         )
    #
    #         polls = context.user_data.setdefault("polls_mapping", {})
    #         polls[message.poll.id] = idx
    #
    #         context.user_data["current_question_index"] = idx + 1
    #
    #         return QUESTION
    #     except Exception as e:
    #         logger.error(f"Ошибка в show_question: {e}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         return ConversationHandler.END

    async def topic_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            topic_id = int(query.data.split("_")[1])
            context.user_data["topic_id"] = topic_id
            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_app_user_id():
                tg = TelegramUser.objects.get(id=context.user_data["telegram_user_id"])
                return tg.user.id

            app_user_id = await get_app_user_id()

            @sync_to_async
            def get_or_create_quiz_sync():
                return APIService.get_or_create_quiz(app_user_id, topic_id)

            quiz = await get_or_create_quiz_sync()

            if not quiz:
                await query.edit_message_text("Не удалось запустить викторину. Попробуйте позже.")
                return ConversationHandler.END

            quiz_info = TEXTS[lang_code]["quiz_info"].format(
                getattr(quiz, 'name', ''),
                getattr(quiz, 'description', ''),
                quiz.total_questions
            )
            keyboard = [
                [InlineKeyboardButton(TEXTS[lang_code]["start_quiz"], callback_data=f"quiz_{quiz.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(quiz_info, reply_markup=reply_markup)
            return QUIZ_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в topic_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END

    async def quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            quiz_id = int(query.data.split("_")[1])
            lang_code = context.user_data.get("language", "ru")
            context.user_data["quiz_id"] = quiz_id
            context.user_data["current_question_index"] = 0
            context.user_data["correct_answers"] = 0
            context.user_data["user_answers"] = {}

            @sync_to_async
            def get_quiz_with_questions_sync():
                return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)

            quiz_data = await get_quiz_with_questions_sync()

            if not quiz_data or not quiz_data.get('questions'):
                await query.edit_message_text(f"Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get('questions', []))

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в quiz_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def restart_quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data["chat_id"] = update.effective_chat.id
        context.user_data["telegram_id"] = update.effective_user.id
        try:
            query = update.callback_query
            await query.answer()

            quiz_id = int(query.data.split("_")[2])
            context.user_data["quiz_id"] = quiz_id
            context.user_data["current_question_index"] = 0
            context.user_data["correct_answers"] = 0
            context.user_data["user_answers"] = {}

            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_quiz_with_questions_sync():
                return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)

            quiz_data = await get_quiz_with_questions_sync()

            if not quiz_data or not quiz_data.get('questions'):
                await query.edit_message_text(f"Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get('questions', []))

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в restart_quiz_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def poll_answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            pa: PollAnswer = update.poll_answer
            user_id = pa.user.id
            poll_id = pa.poll_id
            selected_option = pa.option_ids[0]
            polls_map = context.user_data.get("polls_mapping", {})
            question_index = polls_map.get(poll_id)
            if question_index is None:
                return QUESTION

            q = context.user_data["quiz_data"]["questions"][question_index]
            correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))
            is_correct = (selected_option == correct_option)

            ua = context.user_data.setdefault("user_answers", {})
            ua[question_index] = {
                "question_id": q["id"],
                "answer_id": q["answers"][selected_option]["id"],
                "is_correct": is_correct
            }
            if is_correct:
                context.user_data["correct_answers"] = context.user_data.get("correct_answers", 0) + 1

            @sync_to_async
            def save_to_db():
                from zein_app.models import UserAnswer, Quiz, Question, Choice, Topic
                telegram_user = TelegramUser.objects.get(telegram_id=user_id)
                user_instance = telegram_user.user

                question_instance = Question.objects.get(id=q["id"])
                choice_instance = Choice.objects.get(id=q["answers"][selected_option]["id"])

                topic_id = context.user_data.get("selected_topic_id")
                if not topic_id:
                    topic_id = question_instance.topic.id

                try:
                    quiz_instance = Quiz.objects.get(
                        user=user_instance,
                        topic_id=topic_id,
                        status__in=['active', 'in_progress']
                    )
                except Quiz.DoesNotExist:
                    quiz_instance = Quiz.objects.filter(
                        user=user_instance,
                        topic_id=topic_id
                    ).order_by('-created_at').first()

                    if not quiz_instance:
                        logger.error(f"Не найдена викторина для пользователя {user_instance.id} и темы {topic_id}")
                        return
                except Quiz.MultipleObjectsReturned:
                    quiz_instance = Quiz.objects.filter(
                        user=user_instance,
                        topic_id=topic_id,
                        status__in=['active', 'in_progress']
                    ).order_by('-created_at').first()

                print(f"Используется викторина: {quiz_instance.id}")

                UserAnswer.objects.update_or_create(
                    quiz=quiz_instance,
                    question=question_instance,
                    defaults={
                        'selected_choice': choice_instance,
                        'is_correct': is_correct
                    }
                )

            await save_to_db()

            total = context.user_data["total_questions"]
            answered = len(ua)
            if answered < total:
                return await self.show_question(update, context)
            else:
                return await self.show_quiz_results(update, context)

        except Exception as e:
            logger.error(f"Ошибка в poll_answer_handler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # await context.bot.send_message("Произошла ошибка при обработке ответа на опрос.")
            return ConversationHandler.END

    # async def poll_answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     try:
    #         pa: PollAnswer = update.poll_answer
    #         user_id = pa.user.id
    #         poll_id = pa.poll_id
    #         selected_option = pa.option_ids[0]
    #         polls_map = context.user_data.get("polls_mapping", {})
    #         question_index = polls_map.get(poll_id)
    #         if question_index is None:
    #             return QUESTION
    #
    #         q = context.user_data["quiz_data"]["questions"][question_index]
    #         correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))
    #         is_correct = (selected_option == correct_option)
    #
    #         ua = context.user_data.setdefault("user_answers", {})
    #         ua[question_index] = {
    #             "question_id": q["id"],
    #             "answer_id": q["answers"][selected_option]["id"],
    #             "is_correct": is_correct
    #         }
    #         if is_correct:
    #             context.user_data["correct_answers"] = context.user_data.get("correct_answers", 0) + 1
    #
    #         @sync_to_async
    #         def save_to_db():
    #             from zein_app.models import UserAnswer, Quiz, Question, Choice
    #             telegram_user = TelegramUser.objects.get(telegram_id=user_id)
    #             user_instance = telegram_user.user
    #
    #             question_instance = Question.objects.get(id=q["id"])
    #             choice_instance = Choice.objects.get(id=q["answers"][selected_option]["id"])
    #
    #             quiz_instance = Quiz.objects.get(user=user_instance)
    #             print(quiz_instance)
    #
    #             UserAnswer.objects.update_or_create(
    #                 quiz=quiz_instance,
    #                 question=question_instance,
    #                 defaults={
    #                     'selected_choice': choice_instance,
    #                     'is_correct': is_correct
    #                 }
    #             )
    #
    #         await save_to_db()
    #
    #         total = context.user_data["total_questions"]
    #         answered = len(ua)
    #         if answered < total:
    #             return await self.show_question(update, context)
    #         else:
    #             return await self.show_quiz_results(update, context)
    #
    #     except Exception as e:
    #         logger.error(f"Ошибка в poll_answer_handler: {e}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         # await context.bot.send_message("Произошла ошибка при обработке ответа на опрос.")
    #         return ConversationHandler.END

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Операция отменена.")
        return ConversationHandler.END

    async def show_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            quiz_data = context.user_data.get("quiz_data")
            correct_answers = context.user_data.get("correct_answers", 0)
            total_questions = context.user_data.get("total_questions", 0)
            lang_code = context.user_data.get("language", "ru")
            quiz_id = context.user_data.get("quiz_id")

            @sync_to_async
            def save_quiz_results_sync():
                return APIService.save_quiz_results(
                    quiz_id=quiz_id,
                    user_answers=context.user_data.get("user_answers", {}),
                    correct_answers=correct_answers,
                    total_questions=total_questions
                )

            await save_quiz_results_sync()

            percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

            if percentage >= 80:
                message = "Отлично! Вы отлично справились с тестом!"
            elif percentage >= 60:
                message = "Хорошо! Вы успешно прошли тест."
            else:
                message = "Вам стоит повторить материал и попробовать ещё раз."

            result_text = f"Тест завершен!\n\n" \
                          f"Правильных  ответов: {correct_answers} из {total_questions}\n" \
                          f"Процент успеха: {percentage:.1f}%\n\n" \
                          f"{message}"

            keyboard = [
                [InlineKeyboardButton("Выбрать другой предмет", callback_data="restart_subjects")],
                [InlineKeyboardButton("Пройти этот тест снова", callback_data=f"restart_quiz_{quiz_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id

            try:
                if update.callback_query:
                    await update.callback_query.edit_message_text(
                        text=result_text,
                        reply_markup=reply_markup
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_text,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке результата: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Произошла ошибка при отображении результатов."
                )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Ошибка в show_quiz_results: {e}")
            if update.callback_query:
                await update.callback_query.message.reply_text("Произошла ошибка при отображении результатов.")
            else:
                await update.message.reply_text("Произошла ошибка при отображении результатов.")
            return ConversationHandler.END


import requests
from telegram_bot.models import TelegramSettings


def get_telegram_settings():
    settings_obj = TelegramSettings.get_active()

    if settings_obj is None:
        raise Exception("Telegram settings not found in database. Please configure them in admin panel.")

    return {
        'bot_token': settings_obj.bot_token,
        'admin_chat_id': settings_obj.admin_chat_id
    }


def send_telegram_notification(request_instance):
    telegram_settings = get_telegram_settings()
    bot_token = telegram_settings['bot_token']
    chat_id = telegram_settings['admin_chat_id']

    message = f"📱 *Новая заявка*\n\n" \
              f"👤 *Имя:* {request_instance.name}\n" \
              f"☎️ *Телефон:* {request_instance.phone_number}\n" \
              f"🕒 *Дата:* {request_instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to send Telegram notification: {response.text}")
    return response.json()