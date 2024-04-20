Integre uma conversa em multiplos canais
#############################################

Uma conversa EJ pode ser integrada a outras plataformas,
potencializando o engajamento do seu público durante uma coleta
de opinião. A lista a seguir, resume cada uma das ferramentas que temos disponíveis
atualmente e no link de cada ferramenta é possível ter acesso à documentação
completa.

:ref:`Bot de opinião <Bot de Opinião>`: Permite realizar coletas de opinião por meio de uma interface conversacional,
como o Telegram ou um cliente web, chamado de Webchat. O Bot se integra na API da EJ, e
permite ao usuário votar nos comentários de uma conversa previamente selecionada pelo administrador do bot.

.. note::

    Todos os Bots da EJ são oferecidos pela empresa `Pencillabs <https://pencillabs.tec.br/>`_ como serviço.
    Entre em contato pelo email `contato@pencillabs.tec.br <contato@pencillabs.tec.br>`_ para mais informações.

:ref:`Componente de opinião <Componente de opinião>`: Permite realizar coletas de opinião em sites e blogs, sem que o
usuário precise acessar a interface da plataforma. Essa integração simula a tela de uma conversa,
permitindo que o usuário vote, adicione comentários novos e visualize algumas informações sobre
os grupos formados na conversa;

:ref:`Campanha de email <Campanha de email>`: Permite gerar um template html de uma conversa EJ. Este template pode ser
utilizado em ferramentas como Mautic e Mailchimp, para criação de campanhas de coleta, por disparo
de email em massa;

Todas estas ferramentas podem ser acessadas clicando no link *Ferramentas*, dentro da pagina de
uma conversa na EJ. O link só fica disponível para o criador da conversa.



.. _Bot de Opinião:

Telegram e WhatsApp
******************************

A EJ permite realizar coletas de opinião através de uma interface conversacional em que o
participante vota nos comentários e adiciona comentários,  que ficam disponíveis para os demais
participantes votarem. Essa estrutura de chat permite realizar coletas no Telegram, WhatsApp ou página web.
Para instruções técnicas de como rodar o chatbot da EJ em
um ambiente de homologação, acesse https://gitlab.com/pencillabs/ej/ej-bot.


Quando devo utilizar o Bot de Opinião?
======================================

O Bot de Opinião é especialmente útil para usuários que gerenciam grupos no Telegram ou WhatsApp e
desejam que os integrantes participem das coletas sem sair dos applicativos de mensageria.
Também é possível utilizar o bot de opinião em páginas html, por meio da ferramenta :ref:`Webchat`.

Telegram
=========

Para participar de uma coleta no Telegram é necessário gerar o link de participação. Esse link é
uma URL que aponta para o chat da Duda, nosso bot de opinião disponível no plano gratuito da ferramenta.
Para gerar o link de participação acesse a área de **Ferramentas > Bot de Opinião > Telegram**.
A área de ferramentas pode ser encontrada na página interna de uma conversa.

.. figure:: ../images/ej-bot-de-opiniao.png


Nessa tela, você terá duas opções:

1. Iniciar a coleta da conversa em questão no Telegram, por meio do botão **Iniciar Coleta**.
2. Gerar o link da coleta, por meio do botão **Compartilhar Bot**. Esse botão irá copiar para a área
   de transferência o link de participação e um texto de convie, que poderá ser alterado posteriormente.

Ao clicar no link, o participante é direcionado para o chat privado com o Bot.

.. figure:: ../images/coleta-telegram.png
  :align: center


WhatsApp
=========

Para participar de uma coleta no WhatsApp é necessário gerar o link de participação. Esse link é
uma URL que aponta para o chat da Duda, nosso bot de opinião disponível no plano pago da ferramenta.
Para gerar o link de participação acesse a área de **Ferramentas > Bot de Opinião > WhatsApp**.
A área de ferramentas pode ser encontrada na página interna de uma conversa.

.. figure:: ../images/ej-bot-de-opiniao-whatsapp.png

Nessa tela, você terá duas opções:

1. Iniciar a coleta da conversa em questão no WhatsApp, por meio do botão **Iniciar Coleta**.
2. Gerar o link da coleta, por meio do botão **Compartilhar Bot**. Esse botão irá copiar para a área
   de transferência o link de participação e um texto de convie, que poderá ser alterado posteriormente.

Ao clicar no link, o participante é direcionado para o chat privado com o Bot.

.. figure:: ../images/coleta-whatsapp.png


Webchat
======================================

O Webchat é uma das ferramentas de coleta da EJ e permite integrar o bot de opinião em uma página web.
Essa página pode ser desde um post em um blog até uma plataforma de e-commerce.

Como posso utilizar o Webchat?
------------------------------

Exitem duas formas de utilizar o Webchat.

1. Utilizando um link que a própria EJ disponibiliza. Esse link pode ser compartilhado com o seu público,
   que irá conseguir participar de uma coleta sem que você tenha que fazer qualquer outro procedimento.
   Basta ir na área da ferramenta, clicar no botão **Compartilhar Bot** e o link para a coleta será
   copiado para a área de transferência.
   Ao clicar nesse link, o usuário é redirecionado para uma página da EJ com o WebChat integrado.
   A partir dai, basta ele participar da coleta.
   O botão **Iniciar Coleta** é um atalho para que o criador da conversa possa testar a integração com o Webchat.

.. figure:: ../images/ej-webchat-integrado.png

2. Integrando o script do Webchat em uma página html qualquer. Essa opção permite que você integre o Webchat no seu site, o que facilita a jornada do usuário, já que ele não será redirecionado para uma página da EJ. O script de integração permite que o Webchat, mesmo rodando fora da EJ, apresente a conversa que você criou.
Caso opte por integrar o Webchat no seu site, o seguinte script pode ser utilizado como ponto de partida da integração. Note que você estará sujeito aos limites de uso do plano gratutito, caso seja o seu caso.

.. code-block:: html

   <html>
      <head></head>
      <body></body>
      <script>!(function () {
         localStorage.removeItem("chat_session");
      let e = document.createElement("script"),
         t = document.head || document.getElementsByTagName("head")[0];
      (e.src =
            "https://cdn.jsdelivr.net/npm/rasa-webchat@1.0.1/lib/index.js"),
            (e.async = !0),
            (e.onload = () => {
            window.WebChat.default(
               {
                  initPayload: window.location.href,
                  title: "Duda",
                  socketUrl: https://rasadefault.pencillabs.com.br?token=thisismysecret,
                  profileAvatar: "/static/img/icons/duda.png",
                  embedded: true
               },
            null
      );
      }),
      t.insertBefore(e, t.firstChild);
      })();
      </script>
      <style>
   #rasaWebchatPro {
   height: 100vh;
   width: 80vw;
   margin: auto;
   }

   .rw-avatar {
      width: 3rem !important;
      height: 3rem !important;
      border-radius: 100%;
      margin-right: 6px;
      position: relative;
      bottom: 5px;
   }

   #main-content {
   display: none;
   }

   #instance-error-webchat {
   margin: 30px;
   }
      </style>
   </html>


Uma vez configurado o script na página, será necessário registrar na EJ a URL em que o webchat está integrado. Dessa forma, o bot saberá qual conversa da EJ ele deve apresentar para o visitante.

Para realizar esse registro, basta acessar a área de **ferramentas** da conversa, clicar em **Bots de Opinião** e selecionar a ferramenta **WebChat**. Cadastre então a URL em que o script foi configurado.
Essa URL tem que ser exatamente igual à url em que o script do Webchat será configurado.
Feito isso, o webchat irá apresentar para os visitantes a conversa integrada.

.. figure:: ../images/ej-docs-webchat.png


Quando devo utilizar o WebChat?
-------------------------------

Recomendamos utilizar o Webchat para situações em que utilizar o Telegram não é uma opção.
O usuário irá participar votando nos comentários e poderá adicionar um novo comentário, que será solicitado pelo bot.
Uma das vantagens do Webchat em relação ao Telegram é que ele pode ser integrado ao seu site ou plataforma web.

.. _Componente de opinião:

Sites e plataformas de terceiros
********************************

O componente de opinião é um projeto desenvolvido separadamente do código principal da EJ.
Seu objetivo integrar a jornada de participação em sites e plataformas de terceiros. O componente funciona da seguinte forma:

1. Usuário da EJ cria uma nova conversa (ou seleciona uma já existente).
2. Usuário da EJ integra o componente de opinião em uma página externa, como um site ou blog.
3. Visitante acessa o site ou blog, vota e comenta na conversa criada anteriormente.
4. Votos e comentários dados no componente são enviados para a EJ via API.

.. figure:: ../images/opinion-component-preview.png
   :align: center

   Exemplo de uso do Componente de Opinião.


O Componente permite um fluxo de participação mais fluido, já que o usuário não precisa ser redirecionado
para a EJ. Ao utilizar o componente de opinião, o administrador da conversa é capaz
reaproveitar acessos ao seu site ou plataforma para realizar uma pesquisa de opinião,
sem exigir que o visitante tenha que ser redirecionado para a EJ para participar.

.. note::

    O componente de opinião é desenvolvido utilizando o
    framework `Stencil <https://stenciljs.com/>`_.
    Ele permite criar componentes web reusáveis, que uma vez
    carregados em páginas HTML, adicionam novos comportamentos e funcionalidades ao site.


Quando devo utilizar o Componente de Opinião?
==============================================

O Componente de Opinião é especialmente útil para usuários que possuem sites, blogs ou plataformas
web e querem que seu público participe de coletas nestes ambientes.

Como posso utilizar a ferramenta?
==================================

Exitem duas formas de utilizar o Componente de Opinião.

1. Utilizando a página integrada da EJ. Com ela, você não precisa ter um site ou sistema web para
   realizar coletas com o Componente de Opinião. Basta acessar **Ferramentas > Componente de Opinião**
   e clicar no botão **Iniciar Coleta**. A vantagem dessa opção é que você pode enviar a URL dessa página
   para seus contatos e redes. Quem clicar no link, irá
   ser redirecionado para a página da EJ e conseguirá particiar da coleta. Essa forma democratiza
   o acesso à ferramenta, já que mesmo que você não tenha um site, ainda assim conseguirá fazer a coleta.

.. figure:: ../images/register-opinion-component.png
   :align: center

   Etapa de cadastro do Componente de Opinião.

.. warning::

    Para participar pela página integrada, você precisa estar deslogado da sua conta na plataforma.


2. A segunda forma é integrando o componente ao seu site ou plataforma web. Apresenteremos o passo a passo a seguir.


.. _Configurando o componente no seu site ou página html:

Configurando o componente no seu site ou página html
====================================================

Para integrar o componente de opinião em uma página HTML, acesse a aba "Gerar código", na página da Ferramenta.

.. figure:: ../images/opinion-component-snippet.png
   :align: center

   Código de integração para páginas HTML.

Copie o código gerado pela EJ e inclua no HTML da página que deseja fazer a integração. O browser irá
carregar o Componente de Opinião e apresentá-lo ao usuário. Desse ponto em diante, toda a comunicação com a EJ
será feita via API.

Configurando a aparência do componente de opinião
====================================================

Na página da ferramenta, é possível customizar três aspectos do Componente de Opinião:

1. A imagem de fundo que aparece junto com o card de participação.
2. A logomarca que irá aparecer ao lado da logo da EJ.
3. A mensagem de encerramento da coleta, apresentada depois que o participante vota em todos os comentários.

Para customizar a imagem de fundo e a logomarca, basta fazer upload dos arquivos nos respectivos campos da página
de configuração.

.. figure:: ../images/uploads-opinion-component.png
   :align: center

   Campos de upload de imagem para customização.

Para customizar a mensagem de encerramento da coleta, basta escrever o texto desejado no editor disponível na
página de configuração.

.. figure:: ../images/editor-opinion-component.png
   :align: center

   Editor de texto para customização da mensagem de encerramento.

Uma vez feita as configurações, o Componente irá carregar para o participante utilizando a imagens de fundo,
logomarca e mensagem de encerramento configuradas na página da ferramenta.

.. note::

    Caso não seja feita nenhuma customização, o componente irá carregar com uma imagem de fundo,
    logomarca da EJ e mensagem de encerramento padrão.


Configuração de CORS
======================

Para que o componente possa fazer requisições na API da EJ a partir de um domínio externo, é preciso adicioná-lo
na variável **CORS_ALLOWED_ORIGINS**, definida no arquivo :code:`docker/variables.env`, em uma lista separada por vírgulas.
Do contrário, o componente irá acusar erro de `Cross-Origin Resource Sharing <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`_,
sempre que tentar requisitar informações na API da EJ a partir do domínio que estiver integrado.

Correções de css na pagina do componente
=========================================

O componente fará o melhor possível para carregar bem enquadrado e responsivo, mas é possível que, dependendo de como a pagina foi construída, sejam necessários alguns ajustes no css para que o componente seja apresentado corretamente. Ferramentas como o Divi, muito utilizado no Wordpress para construção de sites, normalmente exigem algumas customizações para não quebrar o componente. Para corrigir as imagens anteriores, por exemplo, o seguinte css foi alterado no tema da página:

.. code-block:: css

  .et_pb_row {
    max-width: unset !important;
    width: unset !important;
    padding: unset !important;
  }
  .et_pb_section {
    padding: unset !important;
  }

  .. _Divi: https://www.elegantthemes.com/gallery/divi/

Para mais informações técnicas sobre o componente de opinião, acesse o `repositório do projeto <https://gitlab.com/pencillabs/ej/conversation-component>`_.

.. _Campanha de email:

Listas de email
****************


A ferramenta Campanha de email, permite realizar coletas de opinião a partir emails enviados
em massa ou para usuários específicos, a partir de plataformas de *mailmarketing* como Mailchimp e Mautic.
O usuário recebe um email o convidando a participar de uma conversa da EJ. Ao clicar em um dos
botões de voto, ele pode ser redirecionado para uma página em que o
:ref:`componente de opinião <Componente de opinião>` esteja integrado.


.. figure:: ../images/mail-campaign-preview.png

O template de email gerado na EJ irá simular a tela de participação do Componente de opinião,
para quando o usuário for redirecionado, ele esteja com um ambiente visualmente compatível.

Criando um template de email
============================

1. Para iniciar, primeiramente é necessário acessar a página de Campanha de e-mail a partir de uma conversa selecionada;
2. Em seguida, no "Gerador de template", selecione a opção "Mailchimp" e escolha o tema para o template;
3. Na opção de "Componente de opinião, clique e insira um endereço em que um Componente de Opinião esteja sendo executado;
4. A partir deste momento, clique na opção de "Download" e o template está e pronto para ser importado no Mailchimp.

.. figure:: ../images/ej-docs-mail-template.png

Enviando um template de email
==============================

O envio do template irá variar de acordo com a ferramenta de criação disparos que você
utiliza. Plataformas como Mautic e Mailchimp possuem áreas de construção de campanhas
que permitem o upload de arquivos HTML.
