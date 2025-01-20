from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Saison, Serie, Session, Calendrier, Match, Punition, Equipe, College, Coach, Interprete,Semaine, Alignements

class CoachCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Coach
        fields = ('nom_coach','prenom_coach','courriel')

class CoachChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Coach
        fields = ('nom_coach','prenom_coach','courriel','admin_flag','equipe')

class CoachAdmin(BaseUserAdmin):
    form = CoachChangeForm
    add_form = CoachCreationForm

    fieldsets = (
        (None, {'fields': ('courriel', 'password')}),
        ('Personal info', {'fields': ('nom_coach', 'prenom_coach','pronom_coach')}),
        ('Permissions', {'fields': ('admin_flag',"validated_flag",)}),
        ('Team info', {'fields': ('equipe',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('courriel', 'password1', 'password2'),
        }),
    )

    list_display = ('courriel', 'nom_coach', 'prenom_coach', 'admin_flag',"validated_flag")
    search_fields = ('courriel', 'nom_coach', 'prenom_coach')
    ordering = ('courriel',)

class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'completed_flag_display', 'url_match_display')

    @admin.display(boolean=True, ordering='completed_flag', description='Completed')
    def completed_flag_display(self, obj):
        return obj.completed_flag

    @admin.display(description='Match URL')
    def url_match_display(self, obj):
        return obj.get_urlMatch

    readonly_fields = ('url_match_display',)


admin.site.register(Saison)
admin.site.register(Serie)
admin.site.register(Session)
admin.site.register(Calendrier)
admin.site.register(Match,MatchAdmin)
admin.site.register(Punition)
admin.site.register(Equipe)
admin.site.register(College)
admin.site.register(Interprete)
admin.site.register(Semaine)
admin.site.register(Coach, CoachAdmin)
admin.site.register(Alignements)
