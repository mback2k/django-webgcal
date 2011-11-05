from django.contrib import admin
from models import TokenCollection

class TokenCollectionAdmin(admin.ModelAdmin):
    fields = ('user', 'pickled_tokens')
    list_display = ('user',)
    ordering = ('user',)

admin.site.register(TokenCollection, TokenCollectionAdmin)
