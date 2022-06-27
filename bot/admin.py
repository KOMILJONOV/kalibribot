from django.contrib import admin

# Register your models here.
from .models import Course, User, Lead, Post



admin.site.register(Course)
# admin.site.register(User)
admin.site.register(Lead)
admin.site.register(Post)


class UserAdmin(admin.ModelAdmin):
    search_fields = ['name', 'number']
admin.site.register(User, UserAdmin)