from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import xlsxwriter

from bot.models import Course, Post, User
from tgbot.utils import distribute
from .constants import (
    CHECK_POST,
    NAME,
    NUMBER,
    POST_MEDIA,
    POST_RECEIVERS,
    POST_SOURCE,
    POST_TEXT,
    SELECT_COURSE,
    SELECT_POST,
    TOKEN
)


class ReplyKeyboardMarkup(ReplyKeyboardMarkup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize_keyboard = True

class Bot(Updater):
    def __init__(self):
        super().__init__(TOKEN)

        not_start = ~Filters.regex('^(/start|/post)$')

        self.dispatcher.add_handler(
            ConversationHandler(
                [
                    CommandHandler('start', self.start),
                    CommandHandler('post', self.post)
                ],
                {
                    NAME: [
                        MessageHandler(
                            Filters.text & not_start,
                            self.name
                        )
                    ],
                    NUMBER: [
                        MessageHandler(
                            Filters.contact & not_start,
                            self.number
                        )
                    ],
                    SELECT_COURSE: [
                        MessageHandler(
                            Filters.text & not_start,
                            self.select_course
                        )
                    ],
                    POST_SOURCE: [
                        MessageHandler(
                            Filters.text & not_start,
                            self.post_source
                        )
                    ],
                    POST_RECEIVERS: [
                        MessageHandler(
                            Filters.text & not_start,
                            self.post_receivers
                        )

                    ],
                    POST_MEDIA: [
                        MessageHandler(
                            Filters.photo & not_start,
                            self.post_media_photo
                        ),
                        MessageHandler(
                            Filters.video & not_start,
                            self.post_media_video
                        ),
                        MessageHandler(
                            Filters.document & not_start,
                            self.post_media_document
                        ),
                        MessageHandler(
                            Filters.audio & not_start,
                            self.post_media_audio
                        ),
                        MessageHandler(
                            Filters.location & not_start,
                            self.post_media_location
                        ),
                        CallbackQueryHandler(
                            self.send_only_text,
                            pattern='^send_text_only'
                        )
                    ],
                    POST_TEXT: [
                        MessageHandler(
                            Filters.text & not_start,
                            self.post_text
                        )
                    ],
                    CHECK_POST: [
                        MessageHandler(
                            Filters.text,
                            self.check_post
                        ),
                        CallbackQueryHandler(
                            self.check_post,
                            pattern='^(send_post|re_type)'
                        )
                    ],

                    


                },
                [
                    CommandHandler('start', self.start),
                    CommandHandler('post', self.post)
                ]
            )
        )

        self.dispatcher.add_handler(
            CommandHandler('data', self.data)
        )

        self.start_polling()
        self.idle()

    def start(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        if db:
            if not db.name:
                user.send_message("Iltimos ismingizni yuboring!",
                                  reply_markup=ReplyKeyboardRemove())
                return NAME
            elif not db.number:
                user.send_message("Iltimos raqamingizni yuboring!", reply_markup=ReplyKeyboardMarkup([
                    [
                        KeyboardButton("Raqamni yuborish",
                                       request_contact=True)
                    ]
                ], resize_keyboard=True))
                return NUMBER

            user.send_message("Iltimos quyidagi kurslardan birini tanlang!", reply_markup=ReplyKeyboardMarkup(
                distribute(
                    [
                        course.name for course in Course.all()
                    ]
                ), resize_keyboard=True))
            return SELECT_COURSE
        else:
            new_user = User.objects.create(
                chat_id=user.id
            )
            user.send_message("Iltimos ismingizni yuboring!",
                              reply_markup=ReplyKeyboardRemove())
            return NAME

    def name(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        name = update.message.text
        db.name = name
        db.save()
        user.send_message("Rqamingizni yuboring!", reply_markup=ReplyKeyboardMarkup([
            [
                KeyboardButton("Raqamni yuborish", request_contact=True)
            ]
        ], resize_keyboard=True))
        return NUMBER

    def number(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        number = update.message.contact.phone_number
        db.number = number
        db.save()
        post: Post = Post.objects.filter(is_after_register=True).first()
        if post:
            post.send_to_user(self.bot, db)

        update.message.reply_text("Muvoffaqiyatli ro'yxatdan o'tdingiz!\n\nIltimos ro'yxatdan o'tmoqchi bo'lgan kursingizni tanlang!", reply_markup=ReplyKeyboardMarkup(
            distribute([
                course.name for course in Course.all()
            ]), resize_keyboard=True))
        return SELECT_COURSE

    def select_course(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        course = update.message.text
        course: Course = Course.objects.filter(name=course).first()
        if course:
            db.register(course)
            update.message.reply_text(
                "Tabriklaymiz.\nSiz %s kursiga ro'yxatdan o'tdingiz!\n\nTez orada operatorlarimiz siz bilan bog'lanishadi!\n\nyana boshqa kursga yozilishni hohlasangiz /start komandasini yuboring!" % course.name, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            update.message.reply_text("Kechirasiz kurs topilmadi!\n\nIltimos quyidagi kurslardan birini tanlang!", reply_markup=ReplyKeyboardMarkup(
                distribute([
                    course.name for course in Course.all()
                ]),
                resize_keyboard=True))
            return SELECT_COURSE

    def post(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post'] = {}
        if db.is_admin:
            # user.send_message("Tayyor postlardan yuborasizmi yoki o'zingiz yaratasizmi?", reply_markup=ReplyKeyboardMarkup(
            #     [
            #         [
            #             "Yaratish"
            #         ],
            #         # [
            #         #     "Tayyorlardan tanlash"
            #         # ]
            #     ]
            # ))
            # return POST_SOURCE
            user.send_message("Iltimos postingiz kimlarga yuborilishini tanlang!", reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        "Hammaga"
                    ],
                    [
                        "Start bosganlarga",
                        "Ro'yxatdan o'tganlarga",
                    ]
                ]
            ))
        return POST_RECEIVERS
    
    def post_source(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['src'] = 0 if update.message.text == "Yaratish" else 1
    
        
        user.send_message("Iltimos postingiz kimlarga yuborilishini tanlang!", reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        "Hammaga"
                    ],
                    [
                        "Start bosganlarga",
                        "Ro'yxatdan o'tganlarga",
                    ]
                ]
            ))
        return POST_RECEIVERS
    
    def post_receivers(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        print(update.message.text)
        context.user_data['post']['receivers'] = 0 if update.message.text == "Hammaga" else (
             1 if update.message.text == "Start bosganlarga" else 2)
        print(context.user_data['post']['receivers'])
        user.send_message("Iltimos post uchun rasm, video, document, audio yuboring yoki postni forward qiling!",reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Textning o'zini yuborish", callback_data="send_text_only")
                ]
            ]
        ))
        return POST_MEDIA

    def post_media_photo(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 1
        context.user_data['post']['media'] = update.message.photo[-1]
        user.send_message("Iltimos post uchun matn yuboring!", reply_markup=ReplyKeyboardMarkup(
            [
                [
                    "Textsiz yuborish"
                ]
            ]
        ))
        return POST_TEXT

    def post_media_document(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 4
        context.user_data['post']['media'] = update.message.document
        user.send_message("Iltimos post uchun matn yuboring!", reply_markup=ReplyKeyboardMarkup(
            [
                [
                    "Textsiz yuborish"
                ]
            ]
        ))
        return POST_TEXT

    def post_media_audio(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 3
        context.user_data['post']['media'] = update.message.audio
        user.send_message("Iltimos post uchun matn yuboring!", reply_markup=ReplyKeyboardMarkup(
            [
                [
                    "Textsiz yuborish"
                ]
            ]
        ))
        return POST_TEXT

    def post_media_video(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 2
        context.user_data['post']['media'] = update.message.video
        user.send_message("Iltimos post uchun matn yuboring!", reply_markup=ReplyKeyboardMarkup(
            [
                [
                    "Textsiz yuborish"
                ]
            ]
        ))
        return POST_TEXT
    

    def post_media_location(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 5
        context.user_data['post']['media'] = update.message.location
        user.send_message("Iltimos post uchun matn yuboring!", reply_markup=ReplyKeyboardMarkup(
            [
                [
                    "Textsiz yuborish"
                ]
            ]
        ))
        return POST_TEXT
    
    def send_only_text(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        context.user_data['post']['media_type'] = 0
        context.user_data['post']['media'] = None
        user.send_message("Iltimos post uchun matn yuboring!")
        return POST_TEXT

    
    def post_text(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        post:Post = Post()
        post.mediatype = context.user_data['post']['media_type']
        context.user_data['post']['text'] = update.message.text if update.message.text != "Textsiz yuborish" else None
        context.user_data['post']['ent'] = update.message.entities



        self.send_post_post(update, context, [db])
        user.send_message("Sizning postingiz!\n\nYuborilsinmi?", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Yuborish", callback_data="send_post"),
                        InlineKeyboardButton("Qayta yozish", callback_data="re_type")
                    ]
                ]
            ))
        

        return CHECK_POST
    
    def check_post(self, update: Update, context: CallbackContext):
        user, db = User.get(update)
        if update.callback_query.data == "send_post":
            all_users = User.objects.all() if context.user_data['post']['receivers'] == 0 else (
                    User.objects.filter(is_registered=False) if context.user_data['post']['receivers'] == 1 else User.objects.filter(is_registered=True)
                )
            # not_sent, res = context.user_data['post']['post'].send_to_user(self.bot, all_users)
            res, not_sent = self.send_post_post(
                update,
                context,
                all_users 
            )
            user.send_message(f"""Barcha foydalanuvchilar: {all_users.count()}\nYuborildi {len(res)}\nYuborilmadi: {len(not_sent)}""")
            return ConversationHandler.END
        else:
            user.send_message("Iltimos qayta yozing!")
            return CHECK_POST
    



    def send_post_post(self, update:Update, context:CallbackContext, users:"list[User]"):
        post = context.user_data['post']
        not_sent = []
        res = []
        for user in users:
            try:
                if post['media_type'] == 0:
                        self.bot.send_message(user.chat_id, post['text'], )
                elif post['media_type'] == 1:
                    self.bot.send_photo(user.chat_id, post['media'], caption=post['text'], caption_entities=post['ent'])
                elif post['media_type'] == 2:
                    self.bot.send_video(user.chat_id, post['media'], caption=post['text'], caption_entities=post['ent'])
                elif post['media_type'] == 3:
                    self.bot.send_audio(user.chat_id, post['media'], caption=post['text'], caption_entities=post['ent'] )
                elif post['media_type'] == 4:
                    self.bot.send_document(user.chat_id, post['media'], caption=post['text'], caption_entities=post['ent'] )
                elif post['media_type'] == 5:
                    self.bot.send_location(user.chat_id, self.latitude, self.longitude, caption=post['text'], caption_entities=post['ent'])
                res.append(user)
            except:
                not_sent.append(user)
        return res, not_sent

    
    def data(self, update:Update, context:CallbackContext):
        user, db = User.get(update)
        # user.send_message("Iltimos post uchun matn yuboring!")
        if db.is_admin:
            xlsx = self.make_stats()
            user.send_document(xlsx)

    

    def make_stats(self):
        data = xlsxwriter.Workbook("stats.xlsx")
        worksheet = data.add_worksheet()
        worksheet.write(0, 0, "id")
        worksheet.write(0, 1, "chat_id")
        worksheet.write(0, 2, "name")
        worksheet.write(0, 3, "number")
        worksheet.write(0, 4, "courses")
        worksheet.write(0, 5, "is_registered")
        worksheet.write(0, 6, "is_admin")
        worksheet.write(0, 7, "reg date")

        users = User.all()
        for i in range(len(users)):
            worksheet.write(i+1, 0, users[i].id)
            worksheet.write(i+1, 1, users[i].chat_id)
            worksheet.write(i+1, 2, users[i].name)
            worksheet.write(i+1, 3, users[i].number)
            worksheet.write(i+1, 4, ",".join(
                [
                    course.course.name for course in users[i].courses()
                ]
            ))
            worksheet.write(i+1, 5, users[i].is_registered)
            worksheet.write(i+1, 6, users[i].is_admin)
            worksheet.write(i+1, 7, str(users[i].reg_date))
        data.close()
        return open("stats.xlsx", 'rb')

