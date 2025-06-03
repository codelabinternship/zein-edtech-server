# from telegram import Update
# from telegram import Poll, PollAnswer
# from telegram.ext import PollAnswerHandler, ContextTypes
# import logging
# from asgiref.sync import sync_to_async
# from django.db import transaction
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, \
#     ConversationHandler
#
# from ..models import TelegramUser
# from .api_service import APIService
#
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)
#
# LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, TOPIC_SELECTION, QUIZ_SELECTION, QUESTION, ANSWER = range(
#     8)
#
# LANGUAGES = {
#     "uz": "Узбекский",
#     "ru": "Русский",
# }
#
# QUESTION, ANSWER = range(6, 8)
#
# TEXTS = {
#     "ru": {
#         "welcome": "Добро пожаловать! Пожалуйста, выберите язык:",
#         "phone_request": "Пожалуйста, поделитесь своим номером телефона:",
#         "share_phone": "Поделиться номером телефона",
#         "name_request": "Введите ваше имя и фамилию:",
#         "registration_successful": "Регистрация успешна! Теперь вы можете выбрать предмет:",
#         "choose_subject": "Выберите предмет:",
#         "choose_lesson": "Выберите урок:",
#         "start_quiz": "Начать викторину",
#         "quiz_info": "Информация о тесте:\n\nНазвание: {}\nОписание: {}\nКоличество вопросов: {}"
#     },
#
# }
#
# for lang in LANGUAGES:
#     if lang != "ru":
#         TEXTS[lang] = TEXTS["ru"]
#
#
# class BotService:
#     def __init__(self, token):
#         self.token = token
#         self.application = None
#
#     def start(self):
#         self.application = Application.builder().token(self.token).build()
#
#         conv_handler = ConversationHandler(
#             entry_points=[CommandHandler("start", self.start_command)],
#             states={
#                 LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_handler, pattern=r"^lang_")],
#                 PHONE_NUMBER: [MessageHandler(filters.CONTACT, self.phone_handler)],
#                 FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.name_handler)],
#                 SUBJECT_SELECTION: [
#                     CallbackQueryHandler(self.subject_handler, pattern=r"^subject_"),
#                     CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$")
#                 ],
#                 TOPIC_SELECTION: [CallbackQueryHandler(self.topic_handler, pattern=r"^topic_")],
#                 QUIZ_SELECTION: [
#                     CallbackQueryHandler(self.quiz_handler, pattern=r"^quiz_"),
#                     CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_")
#                 ],
#                 QUESTION: [
#                 ],
#                 ANSWER: [CallbackQueryHandler(self.next_question_handler, pattern=r"^next_question$")]
#             },
#             fallbacks=[CommandHandler("cancel", self.cancel_command)]
#         )
#
#         self.application.add_handler(CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$"))
#         self.application.add_handler(CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_"))
#         self.application.add_handler(PollAnswerHandler(self.poll_answer_handler))
#
#         self.application.add_handler(conv_handler)
#         self.application.run_polling()
#
#     async def restart_subjects_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             lang_code = context.user_data.get("language", "ru")
#
#             @sync_to_async
#             def get_subjects_sync():
#                 return APIService.get_subjects(language_code=lang_code)
#
#             subjects = await get_subjects_sync()
#
#             if not subjects:
#                 await query.edit_message_text("Не удалось получить список предметов. Попробуйте снова позже.")
#                 return ConversationHandler.END
#
#             keyboard = []
#             for subject in subjects:
#                 keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])
#
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await query.edit_message_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)
#
#             return SUBJECT_SELECTION
#
#         except Exception as e:
#             logger.error(f"Ошибка в restart_subjects_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def next_question_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             context.user_data["current_question_index"] += 1
#
#             return await self.show_question(update, context)
#
#         except Exception as e:
#             logger.error(f"Ошибка в next_question_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка при переходе к следующему вопросу.")
#             return ConversationHandler.END
#
#     @staticmethod
#     @transaction.atomic
#     def _get_or_create_telegram_user(telegram_id, chat_id, username, first_name, last_name, language_code):
#         telegram_user, created = TelegramUser.objects.get_or_create(
#             telegram_id=telegram_id,
#             defaults={
#                 'chat_id': chat_id,
#                 'username': username,
#                 'first_name': first_name,
#                 'last_name': last_name,
#                 'language_code': language_code or 'ru'
#             }
#         )
#
#         if not created:
#             telegram_user.chat_id = chat_id
#             telegram_user.username = username
#             telegram_user.first_name = first_name
#             telegram_user.last_name = last_name
#             telegram_user.save()
#
#         return telegram_user, created
#
#     @staticmethod
#     def _update_telegram_user_language(user_id, lang_code):
#         telegram_user = TelegramUser.objects.get(id=user_id)
#         telegram_user.language_code = lang_code
#         telegram_user.save()
#
#     @staticmethod
#     def _update_telegram_user_phone(user_id, phone_number):
#         telegram_user = TelegramUser.objects.get(id=user_id)
#         telegram_user.phone_number = phone_number
#         telegram_user.save()
#
#     @staticmethod
#     def _link_telegram_user_with_app_user(telegram_user_id, user_id):
#         telegram_user = TelegramUser.objects.get(id=telegram_user_id)
#         from zein_app.models import CustomUser
#         telegram_user.user = CustomUser.objects.get(id=user_id)
#         telegram_user.save()
#
#     async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         user = update.effective_user
#         context.user_data["chat_id"] = update.effective_chat.id
#         context.user_data["telegram_id"] = update.effective_user.id
#         context.user_data["username"] = update.effective_user.username or update.effective_user.first_name
#
#         try:
#             telegram_user, created = await sync_to_async(self._get_or_create_telegram_user)(
#                 telegram_id=user.id,
#                 chat_id=update.effective_chat.id,
#                 username=user.username,
#                 first_name=user.first_name,
#                 last_name=user.last_name,
#                 language_code=user.language_code or 'ru'
#             )
#
#             context.user_data["telegram_user_id"] = telegram_user.id
#
#             keyboard = []
#             row = []
#             for i, (lang_code, lang_name) in enumerate(LANGUAGES.items(), 1):
#                 button = InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")
#                 row.append(button)
#                 if i % 2 == 0:
#                     keyboard.append(row)
#                     row = []
#
#             if row:
#                 keyboard.append(row)
#
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await update.message.reply_text(TEXTS["ru"]["welcome"], reply_markup=reply_markup)
#             return LANGUAGE_SELECTION
#         except Exception as e:
#             logger.error(f"Ошибка в start_command: {e}")
#             await update.message.reply_text("Произошла ошибка при запуске. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def language_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             lang_code = query.data.split("_")[1]
#             context.user_data["language"] = lang_code
#
#             telegram_user_id = context.user_data.get("telegram_user_id")
#             if telegram_user_id:
#                 await sync_to_async(self._update_telegram_user_language)(telegram_user_id, lang_code)
#
#             keyboard = ReplyKeyboardMarkup(
#                 [[KeyboardButton(text=TEXTS[lang_code]["share_phone"], request_contact=True)]],
#                 one_time_keyboard=True,
#                 resize_keyboard=True
#             )
#             await query.edit_message_text(text=TEXTS[lang_code]["phone_request"])
#             await query.message.reply_text(
#                 text=TEXTS[lang_code]["phone_request"],
#                 reply_markup=keyboard
#             )
#             return PHONE_NUMBER
#         except Exception as e:
#             logger.error(f"Ошибка в language_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def phone_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             contact = update.message.contact
#             phone_number = contact.phone_number
#             context.user_data["phone"] = phone_number
#
#             telegram_user_id = context.user_data.get("telegram_user_id")
#             if telegram_user_id:
#                 await sync_to_async(self._update_telegram_user_phone)(telegram_user_id, phone_number)
#
#             lang_code = context.user_data.get("language", "ru")
#             await update.message.reply_text(TEXTS[lang_code]["name_request"])
#             return FULL_NAME
#         except Exception as e:
#             logger.error(f"Ошибка в phone_handler: {e}")
#             await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def name_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             full_name = update.message.text
#             context.user_data["full_name"] = full_name
#
#             lang_code = context.user_data.get("language", "ru")
#             phone_number = context.user_data.get("phone")
#
#             @sync_to_async
#             def register_user_sync():
#                 return APIService.register_user(
#                     phone_number=phone_number,
#                     full_name=full_name,
#                     language_code=lang_code
#                 )
#
#             user_data = await register_user_sync()
#
#             if user_data:
#                 telegram_user_id = context.user_data.get("telegram_user_id")
#                 if telegram_user_id:
#                     await sync_to_async(self._link_telegram_user_with_app_user)(telegram_user_id, user_data["id"])
#
#             @sync_to_async
#             def get_subjects_sync():
#                 return APIService.get_subjects(language_code=lang_code)
#
#             subjects = await get_subjects_sync()
#
#             if not subjects:
#                 await update.message.reply_text("Не удалось получить список предметов. Попробуйте снова позже.")
#                 return ConversationHandler.END
#
#             keyboard = []
#             for subject in subjects:
#                 keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])
#
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await update.message.reply_text(TEXTS[lang_code]["registration_successful"])
#             await update.message.reply_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)
#             return SUBJECT_SELECTION
#         except Exception as e:
#             logger.error(f"Ошибка в name_handler: {e}")
#             await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def subject_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             subject_id = int(query.data.split("_")[1])
#             context.user_data["subject_id"] = subject_id
#             lang_code = context.user_data.get("language", "ru")
#
#             @sync_to_async
#             def get_topics_sync():
#                 return APIService.get_topics(subject_id, language_code=lang_code)
#
#             topics = await get_topics_sync()
#
#             if not topics:
#                 await query.edit_message_text("Не удалось получить список уроков. Попробуйте снова позже.")
#                 return ConversationHandler.END
#
#             keyboard = []
#             for topic in topics:
#                 keyboard.append([InlineKeyboardButton(topic["title"], callback_data=f"topic_{topic['id']}")])
#
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await query.edit_message_text(TEXTS[lang_code]["choose_lesson"], reply_markup=reply_markup)
#             return TOPIC_SELECTION
#         except Exception as e:
#             logger.error(f"Ошибка в subject_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#
#
#     async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             quiz_data = context.user_data["quiz_data"]
#             idx = context.user_data.get("current_question_index", 0)
#
#             if idx >= len(quiz_data["questions"]):
#                 return await self.show_quiz_results(update, context)
#
#             q = quiz_data["questions"][idx]
#             text = f"[{idx + 1}/{len(quiz_data['questions'])}] {q['text']}"
#             options = [a["text"] for a in q["answers"]]
#             correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))
#
#             explanation = q.get("explanation", "") or ""
#
#             chat_id = None
#
#             if "chat_id" in context.user_data:
#                 chat_id = context.user_data["chat_id"]
#                 logger.info(f"Получен chat_id из context.user_data: {chat_id}")
#
#             elif update and update.effective_chat:
#                 chat_id = update.effective_chat.id
#                 logger.info(f"Получен chat_id из update.effective_chat: {chat_id}")
#
#             elif update and update.callback_query and update.callback_query.message:
#                 chat_id = update.callback_query.message.chat_id
#                 logger.info(f"Получен chat_id из update.callback_query: {chat_id}")
#
#             elif update and hasattr(update, "message") and update.message:
#                 chat_id = update.message.chat_id
#                 logger.info(f"Получен chat_id из update.message: {chat_id}")
#
#             elif "telegram_id" in context.user_data:
#                 @sync_to_async
#                 def get_chat_id_from_db(telegram_id):
#                     try:
#                         user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
#                         if user and hasattr(user, "chat_id"):
#                             return user.chat_id
#                         return None
#                     except Exception as e:
#                         logger.error(f"Ошибка при получении chat_id из БД: {e}")
#                         return None
#
#                 chat_id = await get_chat_id_from_db(context.user_data["telegram_id"])
#                 if chat_id:
#                     logger.info(f"Получен chat_id из базы данных: {chat_id}")
#
#             if not chat_id and hasattr(context.bot, "active_conversations"):
#                 for user_id, conv_data in context.bot.active_conversations.items():
#                     if user_id == context.user_data.get("telegram_id"):
#                         chat_id = conv_data.get("chat_id")
#                         if chat_id:
#                             logger.info(f"Получен chat_id из active_conversations: {chat_id}")
#                             break
#
#             if not chat_id:
#                 logger.error(
#                     f"Не удалось определить chat_id для пользователя: {context.user_data.get('telegram_id', 'Unknown')}")
#                 return ConversationHandler.END
#
#             context.user_data["chat_id"] = chat_id
#
#             message = await context.bot.send_poll(
#                 chat_id=chat_id,
#                 question=text,
#                 options=options,
#                 type="quiz",
#                 correct_option_id=correct_option,
#                 is_anonymous=False,
#                 explanation=explanation
#             )
#
#             polls = context.user_data.setdefault("polls_mapping", {})
#             polls[message.poll.id] = idx
#
#             context.user_data["current_question_index"] = idx + 1
#
#             return QUESTION
#         except Exception as e:
#             logger.error(f"Ошибка в show_question: {e}")
#             import traceback
#             logger.error(traceback.format_exc())
#             return ConversationHandler.END
#
#
#     async def topic_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             topic_id = int(query.data.split("_")[1])
#             context.user_data["topic_id"] = topic_id
#             lang_code = context.user_data.get("language", "ru")
#
#             @sync_to_async
#             def get_app_user_id():
#                 tg = TelegramUser.objects.get(id=context.user_data["telegram_user_id"])
#                 return tg.user.id
#
#             app_user_id = await get_app_user_id()
#
#             @sync_to_async
#             def get_or_create_quiz_sync():
#                 return APIService.get_or_create_quiz(app_user_id, topic_id)
#
#             quiz = await get_or_create_quiz_sync()
#
#             if not quiz:
#                 await query.edit_message_text("Не удалось запустить викторину. Попробуйте позже.")
#                 return ConversationHandler.END
#
#             quiz_info = TEXTS[lang_code]["quiz_info"].format(
#                 getattr(quiz, 'name', ''),
#                 getattr(quiz, 'description', ''),
#                 quiz.total_questions
#             )
#             keyboard = [
#                 [InlineKeyboardButton(TEXTS[lang_code]["start_quiz"], callback_data=f"quiz_{quiz.id}")]
#             ]
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await query.edit_message_text(quiz_info, reply_markup=reply_markup)
#             return QUIZ_SELECTION
#
#         except Exception as e:
#             logger.error(f"Ошибка в topic_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Попробуйте позже.")
#             return ConversationHandler.END
#
#     async def quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             quiz_id = int(query.data.split("_")[1])
#             lang_code = context.user_data.get("language", "ru")
#             context.user_data["quiz_id"] = quiz_id
#             context.user_data["current_question_index"] = 0
#             context.user_data["correct_answers"] = 0
#             context.user_data["user_answers"] = {}
#
#             @sync_to_async
#             def get_quiz_with_questions_sync():
#                 return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)
#
#             quiz_data = await get_quiz_with_questions_sync()
#
#             if not quiz_data or not quiz_data.get('questions'):
#                 await query.edit_message_text(f"Не удалось получить вопросы для теста.")
#                 return ConversationHandler.END
#
#             context.user_data["quiz_data"] = quiz_data
#             context.user_data["total_questions"] = len(quiz_data.get('questions', []))
#
#             return await self.show_question(update, context)
#
#         except Exception as e:
#             logger.error(f"Ошибка в quiz_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def restart_quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         context.user_data["chat_id"] = update.effective_chat.id
#         context.user_data["telegram_id"] = update.effective_user.id
#         try:
#             query = update.callback_query
#             await query.answer()
#
#             quiz_id = int(query.data.split("_")[2])
#             context.user_data["quiz_id"] = quiz_id
#             context.user_data["current_question_index"] = 0
#             context.user_data["correct_answers"] = 0
#             context.user_data["user_answers"] = {}
#
#             lang_code = context.user_data.get("language", "ru")
#
#             @sync_to_async
#             def get_quiz_with_questions_sync():
#                 return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)
#
#             quiz_data = await get_quiz_with_questions_sync()
#
#             if not quiz_data or not quiz_data.get('questions'):
#                 await query.edit_message_text(f"Не удалось получить вопросы для теста.")
#                 return ConversationHandler.END
#
#             context.user_data["quiz_data"] = quiz_data
#             context.user_data["total_questions"] = len(quiz_data.get('questions', []))
#
#             return await self.show_question(update, context)
#
#         except Exception as e:
#             logger.error(f"Ошибка в restart_quiz_handler: {e}")
#             await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#             return ConversationHandler.END
#
#     async def poll_answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             pa: PollAnswer = update.poll_answer
#             user_id = pa.user.id
#             poll_id = pa.poll_id
#             selected_option = pa.option_ids[0]
#             polls_map = context.user_data.get("polls_mapping", {})
#             question_index = polls_map.get(poll_id)
#             if question_index is None:
#                 return QUESTION
#
#             q = context.user_data["quiz_data"]["questions"][question_index]
#             correct_option = next(i for i, a in enumerate(q["answers"]) if a.get("is_correct"))
#             is_correct = (selected_option == correct_option)
#
#             ua = context.user_data.setdefault("user_answers", {})
#             ua[question_index] = {
#                 "question_id": q["id"],
#                 "answer_id": q["answers"][selected_option]["id"],
#                 "is_correct": is_correct
#             }
#             if is_correct:
#                 context.user_data["correct_answers"] = context.user_data.get("correct_answers", 0) + 1
#
#             @sync_to_async
#             def save_to_db():
#                 from zein_app.models import UserAnswer, Quiz, Question, Choice, Topic
#                 telegram_user = TelegramUser.objects.get(telegram_id=user_id)
#                 user_instance = telegram_user.user
#
#                 question_instance = Question.objects.get(id=q["id"])
#                 choice_instance = Choice.objects.get(id=q["answers"][selected_option]["id"])
#
#                 topic_id = context.user_data.get("selected_topic_id")
#                 if not topic_id:
#                     topic_id = question_instance.topic.id
#
#                 try:
#                     quiz_instance = Quiz.objects.get(
#                         user=user_instance,
#                         topic_id=topic_id,
#                         status__in=['active', 'in_progress']
#                     )
#                 except Quiz.DoesNotExist:
#                     quiz_instance = Quiz.objects.filter(
#                         user=user_instance,
#                         topic_id=topic_id
#                     ).order_by('-started_at').first()
#
#                     if not quiz_instance:
#                         logger.error(f"Не найдена викторина для пользователя {user_instance.id} и темы {topic_id}")
#                         return
#                 except Quiz.MultipleObjectsReturned:
#                     quiz_instance = Quiz.objects.filter(
#                         user=user_instance,
#                         topic_id=topic_id,
#                         status__in=['active', 'in_progress']
#                     ).order_by('-started_at').first()
#
#                 print(f"Используется викторина: {quiz_instance.id}")
#
#                 UserAnswer.objects.update_or_create(
#                     quiz=quiz_instance,
#                     question=question_instance,
#                     defaults={
#                         'selected_choice': choice_instance,
#                         'is_correct': is_correct
#                     }
#                 )
#
#             await save_to_db()
#
#             total = context.user_data["total_questions"]
#             answered = len(ua)
#             if answered < total:
#                 return await self.show_question(update, context)
#             else:
#                 return await self.show_quiz_results(update, context)
#
#         except Exception as e:
#             logger.error(f"Ошибка в poll_answer_handler: {e}")
#             import traceback
#             logger.error(traceback.format_exc())
#             # await context.bot.send_message("Произошла ошибка при обработке ответа на опрос.")
#             return ConversationHandler.END
#
#     async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         await update.message.reply_text("Операция отменена.")
#         return ConversationHandler.END
#
#     async def show_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#         try:
#             quiz_data = context.user_data.get("quiz_data")
#             correct_answers = context.user_data.get("correct_answers", 0)
#             total_questions = context.user_data.get("total_questions", 0)
#             lang_code = context.user_data.get("language", "ru")
#             quiz_id = context.user_data.get("quiz_id")
#
#             @sync_to_async
#             def save_quiz_results_sync():
#                 return APIService.save_quiz_results(
#                     quiz_id=quiz_id,
#                     user_answers=context.user_data.get("user_answers", {}),
#                     correct_answers=correct_answers,
#                     total_questions=total_questions
#                 )
#
#             await save_quiz_results_sync()
#
#             percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
#
#             if percentage >= 80:
#                 message = "Отлично! Вы отлично справились с тестом!"
#             elif percentage >= 60:
#                 message = "Хорошо! Вы успешно прошли тест."
#             else:
#                 message = "Вам стоит повторить материал и попробовать ещё раз."
#
#             result_text = f"Тест завершен!\n\n" \
#                           f"Правильных  ответов: {correct_answers} из {total_questions}\n" \
#                           f"Процент успеха: {percentage:.1f}%\n\n" \
#                           f"{message}"
#
#             keyboard = [
#                 [InlineKeyboardButton("Выбрать другой предмет", callback_data="restart_subjects")],
#                 [InlineKeyboardButton("Пройти этот тест снова", callback_data=f"restart_quiz_{quiz_id}")]
#             ]
#             reply_markup = InlineKeyboardMarkup(keyboard)
#
#             chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
#
#             try:
#                 if update.callback_query:
#                     await update.callback_query.edit_message_text(
#                         text=result_text,
#                         reply_markup=reply_markup
#                     )
#                 else:
#                     await context.bot.send_message(
#                         chat_id=chat_id,
#                         text=result_text,
#                         reply_markup=reply_markup
#                     )
#             except Exception as e:
#                 logger.error(f"Ошибка при отправке результата: {e}")
#                 await context.bot.send_message(
#                     chat_id=chat_id,
#                     text="Произошла ошибка при отображении результатов."
#                 )
#
#             return ConversationHandler.END
#
#         except Exception as e:
#             logger.error(f"Ошибка в show_quiz_results: {e}")
#             if update.callback_query:
#                 await update.callback_query.message.reply_text("Произошла ошибка при отображении результатов.")
#             else:
#                 await update.message.reply_text("Произошла ошибка при отображении результатов.")
#             return ConversationHandler.END
#
#
# import requests
# from telegram_bot.models import TelegramSettings
#
#
# def get_telegram_settings():
#     settings_obj = TelegramSettings.get_active()
#
#     if settings_obj is None:
#         raise Exception("Telegram settings not found in database. Please configure them in admin panel.")
#
#     return {
#         'bot_token': settings_obj.bot_token,
#         'admin_chat_id': settings_obj.admin_chat_id
#     }
#
#
# def send_telegram_notification(request_instance):
#     telegram_settings = get_telegram_settings()
#     bot_token = telegram_settings['bot_token']
#     chat_id = telegram_settings['admin_chat_id']
#
#     message = f"📱 *Новая заявка*\n\n" \
#               f"👤 *Имя:* {request_instance.name}\n" \
#               f"☎️ *Телефон:* {request_instance.phone_number}\n" \
#               f"🕒 *Дата:* {request_instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
#     url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
#     params = {
#         'chat_id': chat_id,
#         'text': message,
#         'parse_mode': 'Markdown'
#     }
#     response = requests.post(url, params=params)
#     if response.status_code != 200:
#         raise Exception(f"Failed to send Telegram notification: {response.text}")
#     return response.json()


































from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Poll, PollAnswer
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    PollAnswerHandler,
    ContextTypes,
)
import logging
from asgiref.sync import sync_to_async
from django.db import transaction

from ..models import TelegramUser
from .api_service import APIService

from zein_app.models import QuizHistory

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, TOPIC_SELECTION, QUIZ_SELECTION, QUESTION, ANSWER = range(8)

LANGUAGES = {
    "uz": "Узбекский",
    "ru": "Русский",
}

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
        "quiz_info": "Информация о тесте:\n\nНазвание: {}\nОписание: {}\nКоличество вопросов: {}",
        "profile_info": "👤 Профиль:\nИмя: {}\nUsername: @{}\nТелефон: {}\n\n📊 Результаты:\n{}"
    },
}

for lang in LANGUAGES:
    if lang != "ru":
        TEXTS[lang] = TEXTS["ru"]

TEXTS["uz"] = {
    "welcome": "Xush kelibsiz! Iltimos, tilni tanlang:",
    "phone_request": "Iltimos, telefon raqamingizni yuboring:",
    "share_phone": "Telefon raqamni yuborish",
    "name_request": "Ism va familiyangizni kiriting:",
    "registration_successful": "Ro'yxatdan o'tish muvaffaqiyatli! Endi fan tanlashingiz mumkin:",
    "choose_subject": "Fan tanlang:",
    "choose_lesson": "Mavzuni tanlang:",
    "start_quiz": "Testni boshlash",
    "quiz_info": "Test haqida:\n\nNomi: {}\nTavsifi: {}\nSavollar soni: {}",
    "profile_info": "👤 Profil:\nIsm: {}\nUsername: @{}\nTelefon: {}\n\n📊 Natijalar:\n{}"
}


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
                QUESTION: [],
                ANSWER: [CallbackQueryHandler(self.next_question_handler, pattern=r"^next_question$")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$"))
        self.application.add_handler(CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_"))
        self.application.add_handler(PollAnswerHandler(self.poll_answer_handler))

        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("stop_test", self.stop_test_command))
        self.application.add_handler(CommandHandler("continue_test", self.continue_test_command))
        self.application.add_handler(CommandHandler("myprofil", self.profile_command))

        self.application.run_polling()

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

            @sync_to_async
            def is_user_linked(tu_id):
                return TelegramUser.objects.filter(id=tu_id, user__isnull=False).exists()

            linked = await is_user_linked(telegram_user.id)
            if linked:
                @sync_to_async
                def get_app_user_id(tu_id):
                    tu = TelegramUser.objects.get(id=tu_id)
                    return tu.user.id

                app_user_id = await get_app_user_id(telegram_user.id)

                @sync_to_async
                def get_in_progress_quiz(user_id):
                    from zein_app.models import Quiz
                    return Quiz.objects.filter(user_id=user_id, status="in_progress").order_by('-started_at').first()

                quiz = await get_in_progress_quiz(app_user_id)
                if quiz:
                    context.user_data["quiz_id"] = quiz.id
                    context.user_data["current_question_index"] = 0

                    @sync_to_async
                    def get_language_code(tu_id):
                        return TelegramUser.objects.get(id=tu_id).language_code or "ru"

                    lang_code = await get_language_code(telegram_user.id)
                    context.user_data["language"] = lang_code

                    @sync_to_async
                    def load_quiz_data(q_id, lang):
                        return APIService.get_quiz_with_questions(q_id, language_code=lang)

                    context.user_data["quiz_data"] = await load_quiz_data(quiz.id, lang_code)
                    await update.message.delete()
                    return await self.show_question(update, context)

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

                @sync_to_async
                def phone_exists(tu_id):
                    return TelegramUser.objects.filter(id=tu_id, phone_number__isnull=False).exists()

                if await phone_exists(telegram_user_id):
                    await query.message.delete() if query.message else None
                    await query.message.chat.send_message(
                        text=TEXTS[lang_code]["name_request"]
                    )
                    return FULL_NAME

            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton(text=TEXTS[lang_code]["share_phone"], request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )

            if query.message:
                await query.edit_message_text(text=TEXTS[lang_code]["phone_request"])
                await query.message.reply_text(text=TEXTS[lang_code]["phone_request"], reply_markup=keyboard)
            else:
                await update.effective_chat.send_message(text=TEXTS[lang_code]["phone_request"], reply_markup=keyboard)

            return PHONE_NUMBER

        except Exception as e:
            logger.error(f"Ошибка в language_handler: {e}")
            try:
                if update.effective_chat:
                    await update.effective_chat.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.")
            except:
                pass
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
            if not update.message or not update.message.text:
                logger.error("update.message или update.message.text отсутствует в name_handler")
                if update.effective_chat:
                    await update.effective_chat.send_message("Произошла ошибка. Повторите ввод имени.")
                return ConversationHandler.END

            full_name = update.message.text.strip()
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
                await update.message.reply_text("Не удалось получить список предметов. Попробуйте позже.")
                return ConversationHandler.END

            keyboard = [
                [InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")]
                for subject in subjects
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(TEXTS[lang_code]["registration_successful"])
            await update.message.reply_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)

            return SUBJECT_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в name_handler: {e}")
            try:
                if update.effective_chat:
                    await update.effective_chat.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.")
            except:
                pass
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
                await query.edit_message_text("Не удалось получить список уроков. Попробуйте позже.")
                return ConversationHandler.END

            keyboard = []
            for topic in topics:
                keyboard.append([InlineKeyboardButton(topic["title"], callback_data=f"topic_{topic['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(TEXTS[lang_code]["choose_lesson"], reply_markup=reply_markup)
            return TOPIC_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в subject_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END




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
            def get_or_create_quiz():
                return APIService.get_or_create_quiz(app_user_id, topic_id)

            quiz = await get_or_create_quiz()
            if not quiz:
                await query.edit_message_text("Не удалось запустить викторину. Попробуйте позже.")
                return ConversationHandler.END

            @sync_to_async
            def get_titles(subj_id, top_id, lang):
                return (
                    APIService.get_subject_by_id(subj_id, lang),
                    APIService.get_topic_by_id(top_id, lang)
                )

            subj_title, top_title = await get_titles(context.user_data["subject_id"], topic_id, lang_code)
            context.user_data["quiz_subject"] = subj_title
            context.user_data["quiz_topic"] = top_title

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
            if not quiz_data or not quiz_data.get("questions"):
                await query.edit_message_text("Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get("questions", []))

            from zein_app.models import Quiz as QuizModel
            @sync_to_async
            def set_quiz_in_progress():
                quiz_obj = QuizModel.objects.get(id=quiz_id)
                quiz_obj.status = "in_progress"
                quiz_obj.save()

            await set_quiz_in_progress()
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
            if not quiz_data or not quiz_data.get("questions"):
                await query.edit_message_text("Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get("questions", []))

            from zein_app.models import Quiz as QuizModel
            @sync_to_async
            def set_quiz_in_progress():
                quiz_obj = QuizModel.objects.get(id=quiz_id)
                quiz_obj.status = "in_progress"
                quiz_obj.save()

            await set_quiz_in_progress()
            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в restart_quiz_handler: {e}")
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
            elif update and update.effective_chat:
                chat_id = update.effective_chat.id
            elif update and update.callback_query and update.callback_query.message:
                chat_id = update.callback_query.message.chat_id
            elif update and hasattr(update, "message") and update.message:
                chat_id = update.message.chat_id
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

            if not chat_id and hasattr(context.bot, "active_conversations"):
                for user_id, conv_data in context.bot.active_conversations.items():
                    if user_id == context.user_data.get("telegram_id"):
                        chat_id = conv_data.get("chat_id")
                        if chat_id:
                            break

            if not chat_id:
                logger.error(f"Не удалось определить chat_id для пользователя: {context.user_data.get('telegram_id', 'Unknown')}")
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
    #             from zein_app.models import UserAnswer, Quiz as QuizModel, Question as QuestionModel, Choice as ChoiceModel
    #             telegram_user = TelegramUser.objects.get(telegram_id=user_id)
    #             user_instance = telegram_user.user
    #
    #             question_instance = QuestionModel.objects.get(id=q["id"])
    #             choice_instance = ChoiceModel.objects.get(id=q["answers"][selected_option]["id"])
    #
    #             topic_id = context.user_data.get("topic_id") or question_instance.topic.id
    #
    #             try:
    #                 quiz_instance = QuizModel.objects.get(
    #                     user=user_instance,
    #                     topic_id=topic_id,
    #                     status__in=["active", "in_progress"]
    #                 )
    #             except QuizModel.DoesNotExist:
    #                 quiz_instance = QuizModel.objects.filter(
    #                     user=user_instance,
    #                     topic_id=topic_id
    #                 ).order_by("-started_at").first()
    #                 if not quiz_instance:
    #                     logger.error(f"Не найдена викторина для пользователя {user_instance.id} и темы {topic_id}")
    #                     return
    #             except QuizModel.MultipleObjectsReturned:
    #                 quiz_instance = QuizModel.objects.filter(
    #                     user=user_instance,
    #                     topic_id=topic_id,
    #                     status__in=["active", "in_progress"]
    #                 ).order_by("-started_at").first()
    #
    #             UserAnswer.objects.update_or_create(
    #                 quiz=quiz_instance,
    #                 question=question_instance,
    #                 defaults={
    #                     "selected_choice": choice_instance,
    #                     "is_correct": is_correct
    #                 }
    #             )
    #
    #         await save_to_db()
    #
    #         total = context.user_data["total_questions"]
    #         answered = len(context.user_data["user_answers"])
    #         if answered < total:
    #             return await self.show_question(update, context)
    #         else:
    #             return await self.show_quiz_results(update, context)
    #
    #     except Exception as e:
    #         logger.error(f"Ошибка в poll_answer_handler: {e}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         return ConversationHandler.END

    async def poll_answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            pa: PollAnswer = update.poll_answer
            user_id = pa.user.id
            poll_id = pa.poll_id
            selected_option = pa.option_ids[0] if pa.option_ids else None

            if selected_option is None:
                logger.warning(f"Не выбран вариант ответа для опроса {poll_id}")
                return QUESTION

            if not context.user_data.get('chat_id') and update.effective_chat:
                context.user_data['chat_id'] = update.effective_chat.id
            elif not context.user_data.get('chat_id') and update.effective_user:
                context.user_data['chat_id'] = update.effective_user.id

            polls_map = context.user_data.get("polls_mapping", {})
            question_index = polls_map.get(poll_id)
            if question_index is None:
                logger.warning(f"Не найден индекс вопроса для опроса {poll_id}")
                return QUESTION

            quiz_data = context.user_data.get("quiz_data", {})
            questions = quiz_data.get("questions", [])

            if question_index >= len(questions):
                logger.error(f"Индекс вопроса {question_index} превышает количество вопросов {len(questions)}")
                return QUESTION

            q = questions[question_index]
            answers = q.get("answers", [])

            if selected_option >= len(answers):
                logger.error(f"Выбранный вариант {selected_option} превышает количество ответов {len(answers)}")
                return QUESTION

            try:
                correct_option = next(i for i, a in enumerate(answers) if a.get("is_correct"))
            except StopIteration:
                logger.error(f"Не найден правильный ответ для вопроса {question_index}")
                correct_option = 0

            is_correct = (selected_option == correct_option)

            ua = context.user_data.setdefault("user_answers", {})
            ua[question_index] = {
                "question_id": q.get("id"),
                "answer_id": answers[selected_option].get("id") if selected_option < len(answers) else None,
                "is_correct": is_correct
            }

            if is_correct:
                context.user_data["correct_answers"] = context.user_data.get("correct_answers", 0) + 1

            @sync_to_async
            def save_to_db():
                try:
                    from zein_app.models import UserAnswer, Quiz as QuizModel, Question as QuestionModel, \
                        Choice as ChoiceModel

                    try:
                        telegram_user = TelegramUser.objects.get(telegram_id=user_id)
                        user_instance = telegram_user.user
                        if not user_instance:
                            logger.error(f"У Telegram пользователя {user_id} нет связанного основного пользователя")
                            return
                    except TelegramUser.DoesNotExist:
                        logger.error(f"Telegram пользователь с ID {user_id} не найден")
                        return

                    try:
                        question_instance = QuestionModel.objects.get(id=q["id"])
                        choice_instance = ChoiceModel.objects.get(id=answers[selected_option]["id"])
                    except (QuestionModel.DoesNotExist, ChoiceModel.DoesNotExist, KeyError) as e:
                        logger.error(f"Ошибка при получении вопроса или выбора: {e}")
                        return

                    topic_id = context.user_data.get("topic_id") or question_instance.topic.id

                    try:
                        quiz_instance = QuizModel.objects.get(
                            user=user_instance,
                            topic_id=topic_id,
                            status__in=["active", "in_progress"]
                        )
                    except QuizModel.DoesNotExist:
                        quiz_instance = QuizModel.objects.filter(
                            user=user_instance,
                            topic_id=topic_id
                        ).order_by("-started_at").first()
                        if not quiz_instance:
                            logger.error(f"Не найдена викторина для пользователя {user_instance.id} и темы {topic_id}")
                            return
                    except QuizModel.MultipleObjectsReturned:
                        quiz_instance = QuizModel.objects.filter(
                            user=user_instance,
                            topic_id=topic_id,
                            status__in=["active", "in_progress"]
                        ).order_by("-started_at").first()

                    UserAnswer.objects.update_or_create(
                        quiz=quiz_instance,
                        question=question_instance,
                        defaults={
                            "selected_choice": choice_instance,
                            "is_correct": is_correct
                        }
                    )
                    logger.info(f"Сохранен ответ пользователя для вопроса {question_instance.id}")

                except Exception as e:
                    logger.error(f"Ошибка при сохранении ответа в БД: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            await save_to_db()

            total = context.user_data.get("total_questions", 0)
            answered = len(context.user_data.get("user_answers", {}))

            logger.info(f"Отвечено на {answered} из {total} вопросов")

            if answered < total:
                return await self.show_question(update, context)
            else:
                return await self.show_quiz_results(update, context)

        except Exception as e:
            logger.error(f"Ошибка в poll_answer_handler: {e}")
            import traceback
            logger.error(traceback.format_exc())

            try:
                chat_id = context.user_data.get('chat_id')
                if chat_id:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Произошла ошибка при обработке ответа. Попробуйте еще раз."
                    )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

            return ConversationHandler.END

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Операция отменена.")
        return ConversationHandler.END

    # async def show_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     try:
    #         quiz_data = context.user_data.get("quiz_data", {})
    #         correct_answers = context.user_data.get("correct_answers", 0)
    #         total_questions = context.user_data.get("total_questions", 0)
    #         lang_code = context.user_data.get("language", "ru")
    #         quiz_id = context.user_data.get("quiz_id")
    #
    #         @sync_to_async
    #         def save_quiz_results_sync():
    #             return APIService.save_quiz_results(
    #                 quiz_id=quiz_id,
    #                 user_answers=context.user_data.get("user_answers", {}),
    #                 correct_answers=correct_answers,
    #                 total_questions=total_questions
    #             )
    #
    #         await save_quiz_results_sync()
    #
    #         from zein_app.models import Quiz as QuizModel
    #         @sync_to_async
    #         def set_quiz_completed():
    #             quiz_obj = QuizModel.objects.get(id=quiz_id)
    #             quiz_obj.status = "completed"
    #             quiz_obj.save()
    #
    #         await set_quiz_completed()
    #
    #         percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    #
    #         if percentage >= 80:
    #             message = "Отлично! Вы отлично справились с тестом!"
    #         elif percentage >= 60:
    #             message = "Хорошо! Вы успешно прошли тест."
    #         else:
    #             message = "Вам стоит повторить материал и попробовать ещё раз."
    #
    #         result_text = (
    #             f"Тест завершен!\n\n"
    #             f"Правильных ответов: {correct_answers} из {total_questions}\n"
    #             f"Процент успеха: {percentage:.1f}%\n\n"
    #             f"{message}"
    #         )
    #
    #         keyboard = [
    #             [InlineKeyboardButton("Выбрать другой предмет", callback_data="restart_subjects")],
    #             [InlineKeyboardButton("Пройти этот тест снова", callback_data=f"restart_quiz_{quiz_id}")]
    #         ]
    #         reply_markup = InlineKeyboardMarkup(keyboard)
    #
    #         chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
    #
    #         try:
    #             if update.callback_query:
    #                 await update.callback_query.edit_message_text(text=result_text, reply_markup=reply_markup)
    #             else:
    #                 await context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=reply_markup)
    #         except Exception as e:
    #             logger.error(f"Ошибка при отправке результата: {e}")
    #             await context.bot.send_message(chat_id=chat_id, text="Произошла ошибка при отображении результатов.")
    #
    #         @sync_to_async
    #         def save_history():
    #             from telegram_bot.models import QuizHistory
    #             TelegramUserObj = TelegramUser.objects.get(id=context.user_data["telegram_user_id"])
    #             if not TelegramUserObj.user:
    #                 return
    #             user = TelegramUserObj.user
    #             subject = context.user_data.get("quiz_subject", "Неизвестно")
    #             topic = context.user_data.get("quiz_topic", "Неизвестно")
    #
    #             QuizHistory.objects.create(
    #                 user=user,
    #                 subject=subject,
    #                 topic=topic,
    #                 correct_answers=correct_answers,
    #                 total_questions=total_questions,
    #                 percentage=percentage
    #             )
    #
    #         await save_history()
    #
    #         return ConversationHandler.END
    #
    #     except Exception as e:
    #         logger.error(f"Ошибка в show_quiz_results: {e}")
    #         if update.callback_query:
    #             await update.callback_query.message.reply_text("Произошла ошибка при отображении результатов.")
    #         else:
    #             await update.message.reply_text("Произошла ошибка при отображении результатов.")
    #         return ConversationHandler.END

    async def show_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            quiz_data = context.user_data.get("quiz_data", {})
            correct_answers = context.user_data.get("correct_answers", 0)
            total_questions = context.user_data.get("total_questions", 0)
            lang_code = context.user_data.get("language", "ru")
            quiz_id = context.user_data.get("quiz_id")

            @sync_to_async
            def save_quiz_results_sync():
                try:
                    return APIService.save_quiz_results(
                        quiz_id=quiz_id,
                        user_answers=context.user_data.get("user_answers", {}),
                        correct_answers=correct_answers,
                        total_questions=total_questions
                    )
                except Exception as e:
                    logger.error(f"Ошибка при сохранении результатов викторины: {e}")
                    return None

            await save_quiz_results_sync()

            @sync_to_async
            def set_quiz_completed():
                try:
                    from zein_app.models import Quiz as QuizModel
                    if quiz_id:
                        quiz_obj = QuizModel.objects.get(id=quiz_id)
                        quiz_obj.status = "completed"
                        quiz_obj.save()
                        logger.info(f"Викторина {quiz_id} помечена как завершенная")
                except QuizModel.DoesNotExist:
                    logger.error(f"Викторина с ID {quiz_id} не найдена")
                except Exception as e:
                    logger.error(f"Ошибка при обновлении статуса викторины: {e}")

            await set_quiz_completed()

            percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

            if percentage >= 80:
                message = "Отлично! Вы отлично справились с тестом!"
            elif percentage >= 60:
                message = "Хорошо! Вы успешно прошли тест."
            else:
                message = "Вам стоит повторить материал и попробовать ещё раз."

            result_text = (
                f"Тест завершен!\n\n"
                f"Правильных ответов: {correct_answers} из {total_questions}\n"
                f"Процент успеха: {percentage:.1f}%\n\n"
                f"{message}"
            )

            keyboard = [
                [InlineKeyboardButton("Выбрать другой предмет", callback_data="restart_subjects")],
                [InlineKeyboardButton("Пройти этот тест снова", callback_data=f"restart_quiz_{quiz_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            chat_id = None
            if update.effective_chat:
                chat_id = update.effective_chat.id
            elif update.effective_user:
                chat_id = update.effective_user.id
            elif context.user_data.get('chat_id'):
                chat_id = context.user_data['chat_id']

            if not chat_id:
                logger.error("Не удалось определить chat_id для отправки результатов")
                return ConversationHandler.END

            try:
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.edit_message_text(text=result_text, reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Ошибка при отправке результата: {e}")
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Произошла ошибка при отображении результатов, но тест завершен успешно."
                    )
                except Exception as send_error:
                    logger.error(f"Критическая ошибка: не удалось отправить сообщение: {send_error}")

            @sync_to_async
            def save_history():
                try:
                    try:
                        from zein_app.models import QuizHistory
                    except ImportError:
                        logger.warning("Модель QuizHistory не найдена, пропускаем сохранение истории")
                        return

                    telegram_user_id = context.user_data.get("telegram_user_id")
                    if not telegram_user_id:
                        logger.warning("telegram_user_id не найден в user_data")
                        return

                    try:
                        telegram_user_obj = TelegramUser.objects.get(id=telegram_user_id)
                        if not telegram_user_obj.user:
                            logger.warning(f"У TelegramUser {telegram_user_id} нет связанного пользователя")
                            return

                        user = telegram_user_obj.user
                        subject = context.user_data.get("quiz_subject", "Неизвестно")
                        topic = context.user_data.get("quiz_topic", "Неизвестно")

                        QuizHistory.objects.create(
                            user=user,
                            subject=subject,
                            topic=topic,
                            correct_answers=correct_answers,
                            total_questions=total_questions,
                            percentage=percentage
                        )
                        logger.info(f"История викторины сохранена для пользователя {user.id}")

                    except TelegramUser.DoesNotExist:
                        logger.error(f"TelegramUser с ID {telegram_user_id} не найден")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении истории: {e}")

                except Exception as e:
                    logger.error(f"Общая ошибка в save_history: {e}")

            await save_history()

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Ошибка в show_quiz_results: {e}")
            import traceback
            logger.error(traceback.format_exc())

            try:
                chat_id = None
                if update and update.effective_chat:
                    chat_id = update.effective_chat.id
                elif update and update.effective_user:
                    chat_id = update.effective_user.id
                elif context.user_data.get('chat_id'):
                    chat_id = context.user_data['chat_id']

                if chat_id:
                    if update and update.callback_query and update.callback_query.message:
                        await update.callback_query.message.reply_text("Произошла ошибка при отображении результатов.")
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="Произошла ошибка при отображении результатов."
                        )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

            return ConversationHandler.END


    async def stop_test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            quiz_id = context.user_data.get("quiz_id")
            if quiz_id:
                from zein_app.models import Quiz as QuizModel
                quiz = await sync_to_async(QuizModel.objects.get)(id=quiz_id)
                quiz.status = "stopped"
                await sync_to_async(quiz.save)()
                await update.message.reply_text("Тест приостановлен.")
            else:
                await update.message.reply_text("Нет активного теста.")
        except Exception as e:
            logger.error(f"Ошибка в stop_test_command: {e}")
            await update.message.reply_text("Ошибка при остановке теста.")

    async def continue_test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            quiz_id = context.user_data.get("quiz_id")
            if quiz_id:
                from zein_app.models import Quiz as QuizModel
                quiz = await sync_to_async(QuizModel.objects.get)(id=quiz_id)
                quiz.status = "in_progress"
                await sync_to_async(quiz.save)()
                return await self.show_question(update, context)
            else:
                await update.message.reply_text("Нет приостановленного теста.")
        except Exception as e:
            logger.error(f"Ошибка в continue_test_command: {e}")
            await update.message.reply_text("Ошибка при продолжении теста.")

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            tg_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
            user = tg_user.user
            from zein_app.models import QuizHistory

            results = await sync_to_async(list)(QuizHistory.objects.filter(user=user).order_by("-created_at"))
            result_lines = []
            for r in results:
                result_lines.append(f"{r.subject} / {r.topic} — {r.correct_answers}/{r.total_questions} ({r.percentage:.1f}%)")

            lang_code = context.user_data.get("language", "ru")
            text = TEXTS[lang_code]["profile_info"].format(
                user.first_name + " " + user.last_name,
                tg_user.username,
                tg_user.phone_number or "—",
                "\n".join(result_lines) or "Нет результатов"
            )
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"Ошибка в profile_command: {e}")
            await update.message.reply_text("Ошибка при получении профиля.")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.profile_command(update, context)



import requests
from telegram_bot.models import TelegramSettings

def get_telegram_settings():
    settings_obj = TelegramSettings.get_active()
    if settings_obj is None:
        raise Exception("Telegram settings not found in database. Please configure them in admin panel.")
    return {
        "bot_token": settings_obj.bot_token,
        "admin_chat_id": settings_obj.admin_chat_id
    }

def send_telegram_notification(request_instance):
    telegram_settings = get_telegram_settings()
    bot_token = telegram_settings["bot_token"]
    chat_id = telegram_settings["admin_chat_id"]

    message = (
        f"📱 *Новая заявка*\n\n"
        f"👤 *Имя:* {request_instance.name}\n"
        f"☎️ *Телефон:* {request_instance.phone_number}\n"
        f"🕒 *Дата:* {request_instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to send Telegram notification: {response.text}")
    return response.json()
