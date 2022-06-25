from django.contrib import admin

# Register your models here.
from .models import Course, User, Lead, Post



admin.site.register(Course)
admin.site.register(User)
admin.site.register(Lead)
admin.site.register(Post)