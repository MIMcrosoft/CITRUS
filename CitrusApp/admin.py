from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Saison, Serie, Session, Calendrier, Match, Punition, Equipe, College, Coach, Interprete,Semaine

class CoachCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Coach
        fields = ('nom_coach','prenom_coach','courriel')

class CoachChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Coach
        fields = ('nom_coach','prenom_coach','courriel','admin_flag','equipe_id')

class CoachAdmin(BaseUserAdmin):
    form = CoachChangeForm
    add_form = CoachCreationForm

    fieldsets = (
        (None, {'fields': ('courriel', 'password')}),
        ('Personal info', {'fields': ('nom_coach', 'prenom_coach')}),
        ('Permissions', {'fields': ('admin_flag',)}),
        ('Team info', {'fields': ('equipe_id',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('courriel', 'password1', 'password2'),
        }),
    )

    list_display = ('courriel', 'nom_coach', 'prenom_coach', 'admin_flag')
    search_fields = ('courriel', 'nom_coach', 'prenom_coach')
    ordering = ('courriel',)

admin.site.register(Saison)
admin.site.register(Serie)
admin.site.register(Session)
admin.site.register(Calendrier)
admin.site.register(Match)
admin.site.register(Punition)
admin.site.register(Equipe)
admin.site.register(College)
admin.site.register(Interprete)
admin.site.register(Semaine)
admin.site.register(Coach, CoachAdmin)