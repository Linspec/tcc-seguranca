from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Modulo, Pergunta, Alternativa, RespostaUsuario


class RespostaAdmin(admin.ModelAdmin):
    # ajeita as colunas
    list_display = ('usuario', 'get_modulo', 'pergunta', 'alternativa_escolhida', 'get_acerto', 'data_resposta')

    # filtro para os usuários
    list_filter = ('usuario', 'pergunta__modulo', 'data_resposta')

    search_fields = ('usuario__username', 'pergunta__texto_pergunta')

    def get_modulo(self, obj):
        return obj.pergunta.modulo.titulo

    get_modulo.short_description = 'Módulo'

    def get_acerto(self, obj):
        return "Sim" if obj.alternativa_escolhida.is_correta else "Não"

    get_acerto.short_description = 'Acertou?'


admin.site.register(Usuario, UserAdmin)
admin.site.register(Modulo)
admin.site.register(Pergunta)
admin.site.register(Alternativa)
admin.site.register(RespostaUsuario, RespostaAdmin)