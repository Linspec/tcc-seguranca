from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    idade = models.IntegerField(null=True, blank=True)


class Modulo(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    explicacao_pratica = models.TextField(blank=True, null=True)
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link incorporado do vídeo (ex: https://www.youtube.com/embed/...)"
    )

    def __str__(self):
        return self.titulo


class Pergunta(models.Model):
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='perguntas')
    texto_pergunta = models.TextField()

    def __str__(self):
        return self.texto_pergunta


class Alternativa(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE, related_name='alternativas')
    texto_alternativa = models.TextField()
    is_correta = models.BooleanField(default=False)
    explicacao_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.texto_alternativa} ({'Correta' if self.is_correta else 'Incorreta'})"


class RespostaUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    alternativa_escolhida = models.ForeignKey(Alternativa, on_delete=models.CASCADE)

    motivo_escolha = models.TextField(blank=True, null=True)
    viveu_parecido = models.CharField(max_length=3, choices=[('Sim', 'Sim'), ('Nao', 'Não')], blank=True, null=True)
    experiencia_passada = models.TextField(blank=True, null=True)
    suspeita_outra = models.TextField(blank=True, null=True)

    avaliacao_modulo = models.TextField(blank=True, null=True)
    como_ajudou = models.TextField(blank=True, null=True)

    data_resposta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resposta de {self.usuario.username} - {self.pergunta.modulo.titulo}"