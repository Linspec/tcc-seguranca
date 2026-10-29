import os
import django

# Carrega as configurações do seu projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Defina aqui os seus dados de acesso finais
usuario = 'admin-nathan'
senha = 'Nathan747@'
email = 'nathan@teste.com'

# Se o utilizador já existir, ele apenas atualiza a senha (corrige o seu erro atual)
if User.objects.filter(username=usuario).exists():
    admin = User.objects.get(username=usuario)
    admin.set_password(senha)
    admin.save()
    print(f"Senha do admin '{usuario}' redefinida com sucesso!")
else:
    # Se não existir, ele cria um novo
    User.objects.create_superuser(usuario, email, senha)
    print(f"Admin '{usuario}' criado com sucesso!")