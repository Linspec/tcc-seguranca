import os
import django

# carrega as configurações
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# define os dados de acesso final
usuario = 'admin-nathan'
senha = 'Nathan747@'
email = 'nathan@teste.com'

# se o usuario já existir = atualiza a senha
if User.objects.filter(username=usuario).exists():
    admin = User.objects.get(username=usuario)
    admin.set_password(senha)
    admin.save()
    print(f"Senha do admin '{usuario}' redefinida com sucesso!")
else:
    # Se não existir = cria um novo
    User.objects.create_superuser(usuario, email, senha)
    print(f"Admin '{usuario}' criado com sucesso!")