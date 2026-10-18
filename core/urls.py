from django.contrib import admin
from django.urls import path, include
from plataforma import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('promover/<int:user_id>/', views.promover_admin, name='promover_admin'),
    path('usuario/<int:user_id>/', views.detalhe_usuario_admin, name='detalhe_usuario_admin'),
    path('modulo/<int:modulo_id>/', views.detalhe_modulo, name='detalhe_modulo'),
    path('exportar-excel/', views.exportar_relatorio_excel, name='exportar_excel'),
    path('importar-banca/', views.importar_banca_excel, name='importar_banca'),

    # Rotas do SSO Google (allauth)
    path('accounts/', include('allauth.urls')),
]