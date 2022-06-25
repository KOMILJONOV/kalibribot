from django.db import models
from telegram import Bot, Update, User as tgUser
from django.db.models import QuerySet
# Create your models here.


class User(models.Model):
    id: int
    chat_id = models.IntegerField()
    name = models.CharField(null=True, blank=True, max_length=50)
    number = models.CharField(null=True, blank=True, max_length=50)
    is_registered = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    reg_date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get(self, update:Update):
        user: tgUser = update.message.from_user if update.message else update.callback_query.from_user
        db: User = self.objects.filter(chat_id=user.id).first()
        return user, db
    
    def register(self, course:"Course"):
        if not Lead.objects.filter(user=self, course=course).exists():
            Lead.objects.create(user=self, course=course)
        return self
    @classmethod
    def all(self) -> "list[User]":
        return User.objects.all()
    
    def courses(self) -> "list[Lead]":
        return Lead.objects.filter(user=self)
        


class Lead(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    course: "Course" = models.ForeignKey('Course', on_delete=models.CASCADE)



class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    @classmethod
    def all(self) -> "list[Course]":
        return self.objects.all()
    


class Post(models.Model):
    media = models.FileField(null=True, blank=True)
    mediatype = models.IntegerField(choices=[
        (0, 'text'),
        (1, 'image'),
        (2, 'video'),
        (3, 'audio'),
        (4, 'document'),
        (5, 'location'),
    ], default=0)
    image_id = models.IntegerField(null=True, blank=True)
    media_id = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    is_after_register = models.BooleanField(default=False)

    def send_to_user(self, bot:Bot, user:"list[User] | User", reply_markup=None):
        if isinstance(user, QuerySet):
            print('x')
            not_sent_users = []
            res = []
            for u in user:
                try:
                    x = self.send_to_user(bot, u, reply_markup)
                    res.append(x)
                except:
                    not_sent_users.append(u)
            return not_sent_users, res
                    
        else:
            if self.mediatype == 0:
                return bot.send_message(user.chat_id, self.caption, reply_markup=reply_markup)
            elif self.mediatype == 1:
                return bot.send_photo(user.chat_id, open(self.media.path, 'rb'), caption=self.caption, reply_markup=reply_markup)
            elif self.mediatype == 2:
                return bot.send_video(user.chat_id, open(self.media.path, 'rb'), caption=self.caption, reply_markup=reply_markup)
            elif self.mediatype == 3:
                return bot.send_audio(user.chat_id, open(self.media.path, 'rb'), caption=self.caption, reply_markup=reply_markup)
            elif self.mediatype == 4:
                return bot.send_document(user.chat_id, open(self.media.path, 'rb'), caption=self.caption, reply_markup=reply_markup)
            elif self.mediatype == 5:
                # bot.send_location(user.chat_id, self.media, caption=self.caption, reply_markup=reply_markup)
                return bot.send_location(user.chat_id, self.latitude, self.longitude, reply_markup=reply_markup)


    
    
    @classmethod
    def all(self) -> "list[Post]":
        return self.objects.all()

class Button(models.Model):
    text = models.CharField(max_length=100)
    url = models.URLField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE)