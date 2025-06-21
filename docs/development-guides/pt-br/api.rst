.. _API:

====
API
====

Para permitir integrar a jornada de participação com outras plataformas, a EJ possui uma
API REST que pode ser consumida por meio de requisições HTTP. Os endpoints ficam disponíveis
na URL ``/api/v1`` e a documentação em ``/api/v1/docs``. Os tokens são gerados
com a biblioteca `djangorestframework-simplejwt <https://pypi.org/project/djangorestframework-simplejwt/>`_.
É por meio da API que a EJ possibilita realizar consultas em multiplos canais, como
WhatsApp e Telegram.

Autenticação
============

Para autenticação, a API utiliza uma estratégia de token JWT. Existem dois endpoints
que podem ser utilizados para a criação dos tokens:

- ``/api/v1/token``: endpoint responsável por gerar os tokens de acesso (``access_token``) e de renovação (``refresh_token``). Espera um payload contendo o email e senha do usuário.

.. code-block:: json

   {"email": "contato@pencillabs.com.br", "password": "password"}

- ``/api/v1/refresh-token``: endpoint responsável por renovar o token do usuário. Espera um payload contendo o token de renovação gerado a partir do endpoint ``/api/v1/token``.

.. code-block:: json

    {"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxNjMwODkwOSwiaWF0IjoxNzE2MjIyNTA5LCJqdGkiOiI2MDNmYTYzOGRiNjU0ZDc5ODA5NjU3NWUxYjgwY2NiOCIsInVzZXJfaWQiOjc5Nn0.3QZdVL9A_EcAb5LJFWdcSHXRQ8ZWJ2P5RGq8yE9JzRc"}


As seguintes regras são aplicadas ao gerar os tokens de acesso:

1. ``access_token`` tem duração de cinco minutos. Após esse período, é preciso solicitar uma renovação na api ``/api/v1/refresh-token``.
2. ``refresh_token`` tem duração de um dia. Após esse período, é preciso autenticar o usuário novamente.

Os Tokens são assinados utilizando a variável de ambiente ``DJANGO_SECRET_KEY``, que deve
ser mantida privada nos servidores da plataforma.

Nem todos os endpoints exigem autenticação, como por exemplo o endpoint que retorna dados
básicos de uma conversa como título e estatísticas de participação. Para verificar as
permissões exigidas em cada endpoint, procure pelo atributo ``permission_classes`` nos
módulos ``api.py`` da aplicação.

Recuperação de Senha
====================

Para permitir que aplicações externas implementem funcionalidade de recuperação de senha,
a API disponibiliza um endpoint específico para reset de senha com token:

- ``/api/v1/users/recover-password/{token}/``: endpoint responsável por resetar a senha do usuário utilizando um token de recuperação. Espera um payload contendo a nova senha e sua confirmação.

.. code-block:: json

   {"password": "nova_senha_segura", "password_confirm": "nova_senha_segura"}

**Fluxo de Recuperação de Senha:**

1. O usuário solicita recuperação de senha através da interface web da EJ
2. Um token de recuperação é gerado e enviado por email
3. A aplicação externa pode usar o token para resetar a senha via API
4. O token é invalidado após o uso ou expiração (10 minutos)

**Validações Aplicadas:**

- Token deve existir e não estar expirado
- Token não pode ter sido usado anteriormente  
- Senhas devem coincidir (password == password_confirm)
- Token é automaticamente invalidado após uso bem-sucedido

**Códigos de Resposta:**

- ``200``: Senha resetada com sucesso
- ``400``: Token expirado, já usado, ou dados inválidos
- ``404``: Token não encontrado

Este endpoint não requer autenticação JWT, pois utiliza o próprio token de recuperação como mecanismo de segurança.

