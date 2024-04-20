==================
Customizando a EJ
==================

Para customizar a EJ, recomendamos não alterar diretamente os :ref:`apps do core <RST Aplicações que compõe o core>`.
Eles implementam a base da jornada de participação e análise de uma conversa e não devem ser
alterados para atender à uma única organização. Qualquer nível de customização na plataforma
deve ser feita adicionando novos ``apps`` ao projeto Django.


Sobrescrevendo o core
======================

A sobrescrita do ``core`` é feita adicionando um novo app Django dentro do diretório ``src``.
Esse app poderá, por exemplo, sobrescrever views e models de qualquer outro app por meio do arquivo ``apps.py``,
gerado pelo comando ``python manage.py startapp newapp``. Esse arquivo é executado pelo python na etapa de inicialização
do `registry <https://docs.djangoproject.com/en/5.0/ref/applications/>`_ do Django. Nesse momento, é possível importar
qualquer objeto Python e sobrescreve-lo com a implementação interna. Um exemplo pode ser encontrado no
app `ej_signatures`, que altera, em tempo execução,
o template utilizado por uma das views do app  `ej_conversations`.

.. code-block:: python

    # ej_signatures/apps.py
    from django.apps import AppConfig
    from django.utils.translation import gettext_lazy as _


    class EjSignaturesConfig(AppConfig):
        name = "ej_signatures"
        verbose_name = _("Signatures")
        rules = None
        api = None
        roles = None

        def ready(self):
            import ej_conversations.views as ej_conversations_views

            ej_conversations_views.BoardConversationsView.template_name = (
                "ej_signatures/board-conversations-list.jinja2"
            )


Carregando apps dinamicamente
-----------------------------

Para seguir a nossa regra de não alterar os apps do core, a EJ é capaz de carregar
apps Django em tempo de execução sem a necessidade de inclui-los na variável ``project_apps``,
definida no arquivo ``src/ej/settings/apps.py``.

Isso é possível porque o método ``get_submodule_apps()`` percorre todos os subdiretórios do
diretório ``src`` procurando, no arquivo ``apps.py``, a variável ``IS_SUBMODULE``.
Quando encontrada, o método injeta o app em questão na lista de apps Django e automaticamente
ele é carregado pela aplicação. Nesse cenário, o desenvolvedor pode manter o desenvolvimento
do seu app em um repositório separado do core, e clona-lo dentro do diretório ``src`` apenas
quando necessário (desenvolvimento local ou deploy).

.. code-block:: python

   from django.apps import AppConfig
   IS_SUBMODULE = True

   class EjPencillabsConfig(AppConfig):
       default_auto_field = "django.db.models.BigAutoField"
       name = "ej_pencillabs"

Adicionando itens ao menu lateral
==================================

Caso o seu app precise ser acessado pelo menu lateral, o `core` possui o método ``apps_custom_menu_links``,
que varre os apps da aplicação procurando pelo método ``customize_menu``. Esse método deve retornar
um dicionário com as informações necessárias para ser inserido no menu lateral. Um exemplo pode
ser encontrado no app ``ej_activation``:

.. code-block:: python

    # ej_activation/apps.py
    def customize_menu(self, conversation):
        """
        injects links in conversation menu template.
        """
        return {
            "title": _("Activation"),
            "links": [
                {
                    "a": reverse(
                        "activation:index",
                        kwargs={
                            "board_slug": conversation.board.slug,
                            "slug": conversation.slug,
                            "conversation_id": conversation.id,
                        },
                    ),
                    "text": _("Public segmentation"),
                    "current_page": "activation",
                }
            ],
        }



Adicionando novas rotas
=======================

É possível adicionar novas rotas à EJ a partir de um app Django sem alterar diretamente
o arquivo ``src/ej/urls.py``. O método ``get_apps_dynamic_urls`` percorre a lista de apps
que foram carregados pelo Django em busca do método ``get_app_urls``. Esse método
precisa ser declarado no arquivo ``apps.py`` do app que deseja adicionar novas rotas na aplicação.
O retorno deve ser um objeto ``path`` do Django, que será incluído na lista de URLs do core.

Isso é particularmente útil em cenários em que o app precisa ter uma subrota dedicada para os
o seu proposito, como é o caso do app ``ej_activation``, que adiciona a rota ``/activation``
e gerencia as requisições que chegam nessa URL.

.. code-block:: python

    class EjActivationConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "ej_activation"

        def get_app_urls(self):
            """
            includes new URLs on ej/urls.py when called by get_apps_dynamic_urls method.
            """
            return path("", include("ej_activation.urls", namespace="activation"))


Customizando o tema
====================

O frontend do EJ é implementado usando a linguagem de modelagem Jinja2 e usa
aprimoramento progressivo para incluir estilos via CSS e comportamentos
personalizados com JavaScript. A seguir apresenta uma breve visão geral
das tecnologias utilizadas em cada uma dessas camadas:

CSS
    O estilo da EJ é implementado utilizando SASS e seguindo o padrão `BEM <http://getbem.com/introduction/>`_.
    A compilação requer o pacote libsass, que é instalado na imagem Docker do servidor.
    Para compilar os estáticos, execute o comando ``inv sass --watch``.

JavaScript/TypeScript
    EJ não adota qualquer estrutura JavaScript tradicional, mas em vez disso,
    depende de aprimoramento progressivo para adicionar funcionalidades opcionais.
    EJ usa Unpoly_ em conjunto com jQuery_ para fornecer a funcionalidade principal.
    Os componentes específicos do EJ são criados usando o TypeScript e aprimoram
    as marcas anotadas com o atributo "is-Component" com comportamentos e
    funcionalidades extras. A compilação do TypeScript é feita com a ferramenta Parcel_.

.. _Mendeleev.css: https://www.npmjs.com/package/mendeleev.css
.. _Unpoly: https://unpoly.com
.. _jQuery: https://jquery.com
.. _Parcel: https://parceljs.org


As tasks de compilação da EJ (``inv sass`` e ``inv ts``) percorrem os apps Django
em busca do diretório ``<nome_do_app>/static/<nome_do_app>/``.
Nele, deverão existir os subdiretórios ``scss`` e ``ts``.
Todos os apps que seguirem essa convenção terão seus arquivos ``.sass`` compilados
para ``.css``, ``.ts`` para ``.js`` e serão incluídos no bundle carregado pela aplicação.
Isso permite que qualquer app implemente suas próprias regras de CSS, podendo sobrescrever
o tema padrão da plataforma. Também é possível reusar partes do tema padrão, via regra ``import`` do sass.

.. note::

    O tema padrão da EJ é versionado no app **ej**, no diretório **ej/static/ej/**.

Apps que tiverem arquivos de estilo próprio, precisam declarar um arquivo index com o mesmo nome
do app. Por exemplo: o `entrypoint` de CSS do app ``ej_activation`` se chama ``ej_activation.scss``.
Uma vez compilado, os templates do app poderão carregar o arquivo css via uma tag de script:


.. code-block:: jinja2

    {% block head %}
        {{ super() }}
        <link rel="stylesheet" href="/static/ej_activation/css/ej_activation.css" />
    {% endblock %}

Por ser um app Django, você será capaz de customizar não só o tema, mas
também os templates jinja2, models e views. Um exemplo de implementação de
tema para a EJ seguindo esta estrutura, pode ser encontrado
`neste repositório <https://gitlab.com/pencillabs/itsrio/ej-application/>`_.

.. note::

    Você pode começar a implementação de um tema customizado, copiando os arquivos do
    tema padrão para o seu app, mas mantendo a estrutura de diretórios estáticos.
