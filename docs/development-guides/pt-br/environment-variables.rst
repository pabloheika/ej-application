=====================
Variáveis de Ambiente
=====================

EJ usa variáveis de ambiente para personalizar a maioria dos comportamentos e configurações da plataforma.
As variáveis de ambiente podem ser definidas diretamente no ambiente host ou salvo em um arquivo de
ambiente (.env) para que possam ser compartilhados entre diferentes ambientes. Esta seção descreve
as principais variáveis de configuração com seus valores padrão.

Estas variáveis podem ser encontradas no arquivo `docker/variables.env`.


Configuração básica
===================

Esse é o conjunto mínimo de variáveis necessárias, entre parentêses encontra-se o seu valor padrão. **Aviso:** Lembre-se
de ler a seção "Segurança", mais abaixo, antes de concluir sua implantação.

DJANGO_HOSTNAME (localhost):
    Nome do host para o aplicativo EJ. Pode ser algo como "ejplatform.org".
    Este é o endereço no qual sua instância é implantada.

COUNTRY (Brazil):
    O País é utilizado para localização e internacionalização da plataforma. Esta configuração
    controla simultaneamente as variáveis DJANGO_LOCALE_NAME, DJANGO_LANGUAGE_CODE
    e DJANGO_TIME_ZONE usando as configurações padrão para o seu
    país. Os países são especificados pelo nome (por exemplo, USA, Brazil, Argentina,
    Canadá, etc). Você pode usar um PAÍS como base e personalizar qualquer variável
    de forma independente (por exemplo, COUNTRY = "Canadá", LANGUAGE_CODE = "fr-ca")

DJANGO_DEBUG (False):
    A variável DEBUG=True, apresenta o rastreamento quando o Django encontra um erro.
    É bastante útil para ambientes de desenvolvimento, mas deve ser desabilitado em produção.

DB_HOST:
    Nome do container de banco de dados que será utilizado pela aplicação. A EJ utilizada Docker
    para configurar ambientes de desenvolvimento e produção.

CONN_MAX_AGE (0):
    Tempo máximo de cada conexão. Caso o valor seja 0, as conexões são fechadas ao final das
    requisições.

ATOMIC_REQUESTS (False):
    Caso ATOMIC_REQUESTS seja `True`, cada requisição do Django ao banco corresponderá a somente
    uma transação.

DISABLE_SERVER_SIDE_CURSORS (False):
    Os docs do Django especificam que, ao usar um database pooler (como pgbouncer ou pgcat),
    essa variável deve ser configurada como `False`.
    Link: <https://docs.djangoproject.com/en/4.1/ref/databases/#transaction-pooling-server-side-cursors>

TIME_ZONE:
    Configura diretamente o valor da TIME ZONE, por exemplo "America/Sao_Paulo". Por padrão,
    não é especificada. Ao controlar diretamente a variável TIME_ZONE, é mais fácil evitar
    erros e problemas de performance quando o Django tenta rodar statements `SQL SET`.
    Statements `SQL SET` somente funcionam no modo de sessão, e não no modo de transação de
    database poolers (como o pgbouncer).

USE_TZ:
    Quando USE_TZ é `False`, a variável global `TIME_ZONE` é sempre utilizada. Quando é `True`,
    é utilizado o horário 'UTC' por padrão, ou o valor da TIME_ZONE configurado na conexão ao
    Postgres.
    Caso a variável de ambiente TIME_ZONE esteja especificada, USE_TZ será `False` por padrão. Porém,
    pode ser sobrescrita usando a própria variável de ambiente USE_TZ.

SMTP
=====

Para fazer disparos de email, a EJ utiliza a biblioteca `django-anymail <https://github.com/anymail/django-anymail>`_. Ela permite integrar a aplicação com serviços de SMTP, como Mailgun.

MAILGUN_API_KEY:
    Chave de API da conta do Mailgun, que será utilizada para os disparos.

MAILGUN_SENDER_DOMAIN:
    Domínio que será utilizado para enviar os emails.

Segurança
=========


DJANGO_ALLOWED_HOSTS:
    Define a lista de domínios externos que poderão requisitar recursos da EJ.
    Essa variável garante que apenas domínios conhecidos possam interagir com os recursos da aplicação.

DJANGO_SECRET_KEY:
    Uma string randômica utilizada pelo Django para assinaturas criptografadas.
    Essa chave não deve ficar pública, já que é utilizada pelo Django para manter
    recursos como seguros, como o fluxo de recuperação de senha.


Personalização
===============

Essas variáveis customizam o comportamento da EJ de diferentes formas.

Override strings
-----------------

EJ_PAGE_TITLE (Empurrando Juntos):
    Altera o título padrão da página inicial.

EJ_REGISTER_TEXT (Não faz parte da EJ ainda?):
    Texto requisitando o cadastro do usuário.

EJ_LOGIN_TITLE_TEXT (Login in EJ):
    Solicita que o usuário se autentique.

Override paths
--------------

EJ_USER_HOME_PATH (/conversations/):
    Redireciona o usuário logado para essa URL.


Regras e Limites
----------------

EJ_ENABLE_BOARDS (true):
    Habilita a criação de murais no ambiente.

EJ_MAX_COMMENTS_PER_CONVERSATION (2):
    Máximo de comentários válidos por conversa.

EJ_PROFILE_EXCLUDE_FIELDS:
    Lista de campos que não serão mostrados no perfil do usuário.


Modo de execução
----------------

SERVER_MODE (web):
    O valor pode ser "web" ou "api". Caso seja "api", é esperado que somente a API do EJ
    esteja disponível, sem a interface gráfica. Por exemplo, caso o valor seja "api", a
    necessidade de se compilar os arquivos estáticos antes de subir o EJ é eliminada.


Gunicorn
========

Configuração do Gunicorn. Mais sobre cada parâmetro nos docs do Gunicorn:
<https://docs.gunicorn.org/en/stable/settings.html>

GUNICORN_WORKERS:
    Quantidade de workers do Gunicorn.

GUNICORN_THREADS:
    Quantidade de threads de cada worker do Gunicorn.
    Só funciona caso `GUNICORN_WORKER_CLASS` seja `gthread`.

GUNICORN_WORKER_CONNECTIONS:
    Quantidade máxima de conexões por worker. Cada thread pode processar qualquer conexão
    do worker.

GUNICORN_BACKLOG:
    Número máximo de conexões "pending".

GUNICORN_KEEP_ALIVE:
    O número de segundos a esperar por requisições em uma conexão Keep-Alive.

GUNICORN_WORKER_CLASS:
    O tipo de worker a ser utilizado. Por enquanto, os únicos tipos suportados são
    `gthread` e `sync`.

GUNICORN_LOG_LEVEL:
    A granularidade dos logs. Pode ser 'debug', 'info', 'warning', 'error' ou 'critical'.

