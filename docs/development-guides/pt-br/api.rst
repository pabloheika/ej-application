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

.. _delete-conversation-endpoint:


Deletar uma Conversa
======================

Este endpoint permite a exclusão permanente de uma conversa existente.

Apenas usuários autorizados podem realizar esta operação, garantindo que o conteúdo só seja removido pelos seus respectivos donos ou por administradores do sistema.

.. code-block:: HTML

   DELETE /api/v1/conversations/{id}/

**Permissões**

Para executar esta requisição, o usuário autenticado deve atender a um dos seguintes critérios:

* Ser o **autor** da conversa que está sendo deletada.
* Ser um **superusuário** (``is_superuser=True``).

**Parâmetros da URL**
--------------------

:param id: O ID único da conversa a ser deletada.
:type id: integer
:reqheader Authorization: O token de autenticação do usuário. Ex: ``Bearer <seu_token>``

**Respostas**
-----------

:status 204 No Content: **Sucesso**. A conversa foi deletada com sucesso. A resposta não contém corpo.
:status 401 Unauthorized: **Falha de Autenticação**. O usuário não forneceu credenciais de autenticação válidas.
:status 403 Forbidden: **Falha de Permissão**. O usuário está autenticado, mas não é o autor da conversa nem um superusuário.
:status 404 Not Found: **Não Encontrado**. Nenhuma conversa com o ``id`` fornecido foi encontrada.

**Exemplo de Requisição**
-------------------------

Abaixo, um exemplo de como deletar a conversa com `id=42` usando `curl`.

.. code-block:: bash

   curl -X DELETE \
     http://127.0.0.1:8000/api/v1/conversations/42/ \
     -H "Authorization: Bearer <seu_token_de_acesso>"

**Exemplo de Resposta de Sucesso**
----------------------------------

.. code-block:: HTML

   HTTP/1.1 204 No Content
   Date: Mon, 23 Jun 2025 22:15:00 GMT
   (A resposta não possui corpo)