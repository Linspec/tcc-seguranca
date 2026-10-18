from django import forms
from .models import Usuario


class CadastroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'email', 'cpf', 'idade', 'password']
        labels = {
            'username': 'Nome de Utilizador',
            'first_name': 'Nome Completo',
            'email': 'E-mail',
            'cpf': 'CPF (apenas números ou com pontos/traço)',
            'idade': 'Idade',
        }
        widgets = {
            'password': forms.PasswordInput(),
        }

    # Validação de e-mail estrutural
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise forms.ValidationError("Por favor, insira um endereço de e-mail válido e existente.")
        return email

    # Validação Matemática Real do CPF
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        cpf_limpo = ''.join(filter(str.isdigit, cpf))

        if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11:
            raise forms.ValidationError("CPF inválido. Certifique-se de digitar os 11 números corretos.")

        def calcula_digito(digitos):
            soma = sum(int(digitos[i]) * (len(digitos) + 1 - i) for i in range(len(digitos)))
            resto = 11 - (soma % 11)
            return 0 if resto > 9 else resto

        # Valida 1º dígito
        primeiro_digito = calcula_digito(cpf_limpo[:9])
        if primeiro_digito != int(cpf_limpo[9]):
            raise forms.ValidationError("CPF inválido (dígito verificador incorreto).")

        # Valida 2º dígito
        segundo_digito = calcula_digito(cpf_limpo[:10])
        if segundo_digito != int(cpf_limpo[10]):
            raise forms.ValidationError("CPF inválido (dígito verificador incorreto).")

        return cpf_limpo