import openpyxl
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Modulo, Pergunta, Alternativa, RespostaUsuario, Usuario
from .forms import CadastroForm


def login_view(request):
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            auth_login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            return render(request, 'login.html', {'erro': 'Utilizador ou senha incorretos.'})

    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Se for admin, redireciona para tela de admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')

    modulos = Modulo.objects.all()
    progresso_modulos = []

    for m in modulos:
        perguntas_modulo = m.perguntas.all()
        total_p = perguntas_modulo.count()
        respostas_usuario = RespostaUsuario.objects.filter(usuario=request.user, pergunta__in=perguntas_modulo)

        status = "Não Iniciado"
        acertos_modulo = 0

        if total_p > 0 and respostas_usuario.exists():
            for r in respostas_usuario:
                if r.alternativa_escolhida.is_correta:
                    acertos_modulo += 1

            porcentagem = (acertos_modulo / total_p) * 100

            if respostas_usuario.count() >= total_p:
                if porcentagem >= 70:
                    status = "Concluído"
                else:
                    status = "Abaixo de 70% (Refazer)"
            else:
                status = "Em Andamento"

        progresso_modulos.append({
            'modulo': m,
            'status': status,
            'acertos': acertos_modulo,
            'total': total_p
        })

    return render(request, 'index.html', {'modulos': modulos, 'progresso_modulos': progresso_modulos})


def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    modulos = Modulo.objects.all()
    usuarios_comuns = Usuario.objects.filter(is_staff=False, is_superuser=False)
    total_usuarios_comuns = usuarios_comuns.count()

    # 1. media de conclusão  por módulo
    metricas_modulos = []
    for m in modulos:
        perguntas = m.perguntas.all()
        total_p = perguntas.count()
        concluidos_count = 0

        for u in usuarios_comuns:
            respostas_u = RespostaUsuario.objects.filter(usuario=u, pergunta__in=perguntas)
            if total_p > 0 and respostas_u.count() >= total_p:
                acertos = sum(1 for r in respostas_u if r.alternativa_escolhida.is_correta)
                if (acertos / total_p) * 100 >= 70:
                    concluidos_count += 1

        taxa = (concluidos_count / total_usuarios_comuns * 100) if total_usuarios_comuns > 0 else 0
        metricas_modulos.append({
            'modulo': m,
            'concluidos': concluidos_count,
            'taxa_conclusao': round(taxa, 1)
        })

    # 2. media de erro por questão
    metricas_questoes = []
    perguntas_all = Pergunta.objects.all()
    for p in perguntas_all:
        respostas_p = RespostaUsuario.objects.filter(pergunta=p)
        total_resp = respostas_p.count()
        erros = sum(1 for r in respostas_p if not r.alternativa_escolhida.is_correta)
        taxa_erro = (erros / total_resp * 100) if total_resp > 0 else 0
        metricas_questoes.append({
            'pergunta': p,
            'modulo': p.modulo.titulo,
            'total_respostas': total_resp,
            'total_erros': erros,
            'taxa_erro': round(taxa_erro, 1)
        })

    # 3. Lista completa de usuários normal e admin
    todos_usuarios = Usuario.objects.all()

    contexto = {
        'metricas_modulos': metricas_modulos,
        'metricas_questoes': metricas_questoes,
        'todos_usuarios': todos_usuarios,
        'total_usuarios_comuns': total_usuarios_comuns,
    }
    return render(request, 'admin_dashboard.html', contexto)


def promover_admin(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    alvo = get_object_or_404(Usuario, id=user_id)
    alvo.is_staff = True
    alvo.save()
    return redirect('admin_dashboard')


def detalhe_usuario_admin(request, user_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    usuario_alvo = get_object_or_404(Usuario, id=user_id)
    respostas = RespostaUsuario.objects.filter(usuario=usuario_alvo)

    return render(request, 'detalhe_usuario_admin.html', {
        'usuario_alvo': usuario_alvo,
        'respostas': respostas
    })


def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = CadastroForm()
    return render(request, 'cadastro.html', {'form': form})


def detalhe_modulo(request, modulo_id):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('admin_dashboard')

    modulo = get_object_or_404(Modulo, id=modulo_id)
    perguntas = modulo.perguntas.all()

    if request.method == 'POST':
        # Recolhe avaliações opcionais do módulo enviadas no final da página
        avaliacao_mod = request.POST.get('avaliacao_modulo', '')
        como_ajudou_mod = request.POST.get('como_ajudou', '')

        RespostaUsuario.objects.filter(usuario=request.user, pergunta__in=perguntas).delete()

        acertos = 0
        total_perguntas = perguntas.count()
        detalhes_respostas = []

        for pergunta in perguntas:
            alternativa_id = request.POST.get(f'pergunta_{pergunta.id}')
            if alternativa_id:
                alternativa = Alternativa.objects.get(id=alternativa_id)
                motivo = request.POST.get(f'motivo_{pergunta.id}', '')
                viveu_parecido = request.POST.get(f'viveu_parecido_{pergunta.id}', 'Nao')
                experiencia = request.POST.get(f'experiencia_{pergunta.id}',
                                               '') if viveu_parecido == 'Sim' else 'Não vivenciado'
                suspeita = request.POST.get(f'suspeita_{pergunta.id}', '')

                if alternativa.is_correta:
                    acertos += 1

                RespostaUsuario.objects.create(
                    usuario=request.user,
                    pergunta=pergunta,
                    alternativa_escolhida=alternativa,
                    motivo_escolha=motivo,
                    viveu_parecido=viveu_parecido,
                    experiencia_passada=experiencia,
                    suspeita_outra=suspeita,
                    avaliacao_modulo=avaliacao_mod,
                    como_ajudou=como_ajudou_mod
                )

                detalhes_respostas.append({
                    'pergunta': pergunta,
                    'escolhida': alternativa,
                    'acertou': alternativa.is_correta,
                    'feedback': alternativa.explicacao_feedback
                })

        contexto = {
            'modulo': modulo,
            'acertos': acertos,
            'total_perguntas': total_perguntas,
            'detalhes_respostas': detalhes_respostas
        }
        return render(request, 'resultado_quiz.html', contexto)

    return render(request, 'detalhe_modulo.html', {'modulo': modulo, 'perguntas': perguntas})


def exportar_relatorio_excel(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatorio Analitico TCC"

    cabecalhos = [
        'Utilizador', 'E-mail', 'CPF', 'Módulo', 'Pergunta',
        'Alternativa Escolhida', 'Acertou?',
        'Motivo da Escolha', 'Já Viveu Parecido?', 'E Como Foi?', 'Suspeita Outra',
        'Avaliação/Melhoria Módulo', 'Como Ajudou', 'Data'
    ]
    ws.append(cabecalhos)

    respostas = RespostaUsuario.objects.all()

    for r in respostas:
        acertou = "Sim" if r.alternativa_escolhida.is_correta else "Não"
        modulo_titulo = r.pergunta.modulo.titulo

        linha = [
            r.usuario.username,
            r.usuario.email,
            getattr(r.usuario, 'cpf', 'N/A'),
            modulo_titulo,
            r.pergunta.texto_pergunta,
            r.alternativa_escolhida.texto_alternativa,
            acertou,
            r.motivo_escolha,
            r.viveu_parecido,
            r.experiencia_passada,
            r.suspeita_outra,
            r.avaliacao_modulo,
            r.como_ajudou,
            r.data_resposta.strftime('%d/%m/%Y %H:%M')
        ]
        ws.append(linha)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=relatorio_analitico_tcc.xlsx'
    wb.save(response)

    return response


import random  # <-- Certifique-se de importar o random no topo do arquivo views.py

import random


def detalhe_modulo(request, modulo_id):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('admin_dashboard')

    modulo = get_object_or_404(Modulo, id=modulo_id)

    # Pega todas as perguntas do módulo e seleciona aleatoriamente até 10 perguntas
    todas_perguntas = list(modulo.perguntas.all())
    random.shuffle(todas_perguntas)
    perguntas = todas_perguntas[:10]  # Limita exatamente a 10 perguntas por tentativa

    # Embaralha as alternativas de cada uma das 10 perguntas
    for p in perguntas:
        alternativas = list(p.alternativas.all())
        random.shuffle(alternativas)  # Embaralha as opções de resposta
        p.alternativas_embaralhadas = alternativas

    if request.method == 'POST':
        avaliacao_mod = request.POST.get('avaliacao_modulo', '')
        como_ajudou_mod = request.POST.get('como_ajudou', '')

        # Remove respostas anteriores deste módulo para recalcular
        RespostaUsuario.objects.filter(usuario=request.user, pergunta__in=todas_perguntas).delete()

        acertos = 0
        total_perguntas = len(perguntas)
        detalhes_respostas = []

        for pergunta in perguntas:
            alternativa_id = request.POST.get(f'pergunta_{pergunta.id}')
            if alternativa_id:
                alternativa = Alternativa.objects.get(id=alternativa_id)
                motivo = request.POST.get(f'motivo_{pergunta.id}', '')
                viveu_parecido = request.POST.get(f'viveu_parecido_{pergunta.id}', 'Nao')
                experiencia = request.POST.get(f'experiencia_{pergunta.id}',
                                               '') if viveu_parecido == 'Sim' else 'Não vivenciado'
                suspeita = request.POST.get(f'suspeita_{pergunta.id}', '')

                if alternativa.is_correta:
                    acertos += 1

                RespostaUsuario.objects.create(
                    usuario=request.user,
                    pergunta=pergunta,
                    alternativa_escolhida=alternativa,
                    motivo_escolha=motivo,
                    viveu_parecido=viveu_parecido,
                    experiencia_passada=experiencia,
                    suspeita_outra=suspeita,
                    avaliacao_modulo=avaliacao_mod,
                    como_ajudou=como_ajudou_mod
                )

                detalhes_respostas.append({
                    'pergunta': pergunta,
                    'escolhida': alternativa,
                    'acertou': alternativa.is_correta,
                    'feedback': alternativa.explicacao_feedback
                })

        contexto = {
            'modulo': modulo,
            'acertos': acertos,
            'total_perguntas': total_perguntas,
            'detalhes_respostas': detalhes_respostas
        }
        return render(request, 'resultado_quiz.html', contexto)

    return render(request, 'detalhe_modulo.html', {'modulo': modulo, 'perguntas': perguntas})

def importar_banca_excel(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    if request.method == 'POST' and request.FILES.get('arquivo_excel'):
        excel_file = request.FILES['arquivo_excel']
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        # Formato esperado nas colunas da planilha:
        # Coluna A: Título do Módulo
        # Coluna B: Descrição do Módulo
        # Coluna C: Texto da Pergunta
        # Coluna D: Alternativa 1 | Coluna E: É Correta? (Sim/Não) | Coluna F: Feedback 1
        # Coluna G: Alternativa 2 | Coluna H: É Correta? (Sim/Não) | Coluna I: Feedback 2
        # Coluna J: Alternativa 3 | Coluna K: É Correta? (Sim/Não) | Coluna L: Feedback 3
        # Coluna M: Alternativa 4 | Coluna N: É Correta? (Sim/Não) | Coluna O: Feedback 4

        for row in sheet.iter_rows(min_row=2, values_only=True):
            titulo_mod = row[0]
            desc_mod = row[1]
            texto_perg = row[2]

            if not titulo_mod or not texto_perg:
                continue

            # Cria ou recupera o módulo
            modulo, _ = Modulo.objects.get_or_create(
                titulo=titulo_mod,
                defaults={'descricao': desc_mod}
            )

            # Cria a pergunta
            pergunta = Pergunta.objects.create(modulo=modulo, texto_pergunta=texto_perg)

            # Processa as alternativas em blocos de 3 colunas (Texto, Correta?, Feedback)
            # Índices iniciais: Alt 1 (3,4,5), Alt 2 (6,7,8), Alt 3 (9,10,11), Alt 4 (12,13,14)
            for i in range(3, 15, 3):
                if i < len(row) and row[i]:
                    txt_alt = row[i]
                    is_corr_str = str(row[i+1]).strip().lower() if row[i+1] else 'nao'
                    is_corr = True if is_corr_str in ['sim', 'true', '1', 's'] else False
                    fb_alt = row[i+2] if (i+2) < len(row) else ''

                    Alternativa.objects.create(
                        pergunta=pergunta,
                        texto_alternativa=txt_alt,
                        is_correta=is_corr,
                        explicacao_feedback=fb_alt
                    )

        return redirect('admin_dashboard')

    return render(request, 'importar_banca.html')