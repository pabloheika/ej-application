=======================
Guia para contribuição
=======================

Para contribuir com o código da Empurrando Juntas, algumas boas práticas de programação
devem ser seguidas. Esse guia apresenta como abrir
bons *merge requests*, além de sugestões de boas práticas de programação adotadas pelo projeto.

Por onde começar
----------------

O ponto de partida para contribuir tecnicamente com o projeto é entrando no grupo aberto
da comunidade no `Telegram <https://t.me/EJComum>`_. Nesse grupo, estão presentes desenvolvedores,
empresas e organizações que contribuem ou já contribuíram com a EJ.
Uma vez no grupo, você pode entrar em contato
com a equipe da `Pencillabs <https://pencillabs.tec.br/>`_ para ser
adicionado ao canal de comunicação de desenvolvimento.

A próxima etapa é subir o ambiente.
O passo a passo está bem documentado no `README.md <https://gitlab.com/pencillabs/ej/ej-application/-/blob/develop/README.md?ref_type=heads>`_
do repositório. Caso você tenha alguma dificuldade ou dúvida que não esteja
documentada, fique à vontade para perguntar nos canais da Pencil. Lembre-se:

1. Seja gentil e educada(o) ao fazer perguntas.
2. Em caso de dúvidas, não deixe de buscar ajuda com a equipe. Evite perguntas sem muitos detalhes. Descreva o que você já tentou e pesquisou e, se possível, forneça logs de erros. Assim, alguém poderá te ajudar de forma mais rápida e direcionada.
3. Seja paciente. As pessoas da equipe irão te responder assim que possível. Caso um tempo já tenha se passado sem resposta, pergunte se alguém da equipe conseguiu verificar ou reproduzir seu problema.
4. Sempre priorize a comunicação nos grupos. Evite contactar pessoas da equipe no privado.

Estudando a aplicação
---------------------

Com o ambiente local configurado, está na hora de estudar a arquitetura
do projeto e suas peculiaridades. Antes de partir para o código, recomendamos que você
leia o :ref:`guia de usuário <Start using>` para exercitar conceitos básicos como:
o que é uma conversa, como funciona a jornada de participação
e como os dados são coletados e processados. Em seguida, recomendamos a leitura do
:ref:`guia de desenvolvimento <Architecture>`. Nele, você terá uma visão geral de como a EJ
funciona internamente, o que irá facilitar o estudo do código-fonte.

Escolhendo uma issue
--------------------

o ponto de partida para começar a contribuir com o código-fonte é o `board de planejamento <https://gitlab.com/pencillabs/ej/ej-application/-/boards/5359092>`_.
Nele, o time prioriza o que será desenvolvido durante a *sprint*. A EJ
utiliza o framework `OKR <https://rockcontent.com/br/blog/okr/>`_ para definir objetivos
e resultados-chave que guiam a priorização do trabalho.
Definido o escopo, o time se dedica durante as próximas
duas semanas para executá-lo. O board, também conhecido como kanban, apresenta o andamento do trabalho ao
longo dessas duas semanas.

Nossa recomendação é que você discuta com o time qual deve ser a sua primeira issue. Nós faremos o
esforço de sempre manter o board atualizado e com as issues devidamente categorizadas, mas
quem realmente sabe o que é prioridade são as pessoas que já estão trabalhando no projeto.
É papel delas te integrar ao fluxo da sprint e dar orientações em relação às boas práticas
de contribuição.

Trabalhando na sua issue
------------------------

A EJ utiliza duas branchs principais.

- **develop**: branch de desenvolvimento que recebe as contribuições do time durante a sprint.
- **prod**: branch de produção, que é atualizada a cada 15 dias com uma nova release do projeto.

Para começar a trabalhar na sua issue, você criará uma nova branch a partir da **develop**.
A sua branch deve ter no nome o ID da issue que você está desenvolvendo. Todo o desenvolvimento
deve ser feito utilizando o ambiente configurado via Docker, conforme o
`README.md <https://gitlab.com/pencillabs/ej/ej-application/-/blob/develop/README.md?ref_type=heads>`_
do projeto. Seja curioso, explore
o código, estude o que você não souber e se mesmo assim você não conseguir avançar,
faça suas perguntas nos canais do projeto.

O time segue algumas regras que aceleram a revisão e aprovação dos merge request.

*********************************
Testes unitários e de integração
*********************************

Toda alteração no backend que adicione novos comportamentos precisa ser testada de forma
unitária. Alterações em views existentes ou novas, precisam ter testes de integração.
O projeto utiliza a ferramenta `pytest <https://docs.pytest.org/en/8.0.x/>`_ para testes unitários e de integração.

********************
Testes de aceitação
********************

Toda alteração no fluxo de participação (criação/edição de conversa e página de participação),
precisa ter um cenário de testes implementado com a ferramenta `Cypress <https://www.cypress.io/>`_.

********
BEM CSS
********

A EJ utiliza SASS para implementar o estilo das páginas HTML. Para definição das classes,
o time segue a metodologia `BEM <https://getbem.com/>`_.

******
HTMX
******

Algumas telas da EJ precisam realizar requisições de forma assíncrona para o backend. A
EJ utiliza a ferramenta `HTMX <https://htmx.org/>`_ para isso.

***************
Responsividade
***************

Toda issue que envolva frontend precisa garantir responsividade para diferentes tamanhos de tela.
Algumas práticas que adotamos:

- Sempre utilizar a medida ``rem`` para definir a medida de blocos da página.
- Sempre utilizar a medida ``em`` para tamanho de fontes.
- Utilizar como tamanho mínimo de tela, a dimensão de ``360px``.
- Priorizar o uso de ``flexbox`` e ``grid layout`` para posicionar e alinhar elementos na tela.
- Evitar utilizar ``padding`` e ``margin`` para posicionar elementos na tela.
- Nunca definir cores de forma *hardcoded* nos arquivos scss. Sempre reutilizar as variáveis do arquivo ``_config.scss``.
- Priorizar a estruturação de media queries dentro da própria classe do elemento. Este método é conhecido como `Media Query Bubbling <https://www.creativebloq.com/how-to/how-to-structure-media-queries-in-sass>`_.
- Priorizar utilização de métodos do Jquery ao invés de métodos nativos do javascript. Apesar dos métodos nativos apresentarem maior `performance <https://in.indeed.com/career-advice/career-development/javascript-vs-jquery>`_, o Jquery oferece `algumas comodidades <https://learn.jquery.com/using-jquery-core/jquery-object/>`_.
- Caso você tenha alguma dúvida sobre o protótipo de alta fidelidade relacionado à sua issue, pergunte para a pessoa mentora ou a designer.

*****************
Estilo de código
*****************

Toda linguagem tem sua forma de resolver problemas, não é diferente com Python. Sempre
tente implementar a solução da issue da forma mais "pythonica" possível.
A equipe adota a ferramenta `Black <https://github.com/psf/black>`_ como padrão de
formatação de código Python.

*******************
Analisador estático
*******************

A EJ usa o analisador estático `Ruff <https://github.com/astral-sh/ruff>`_ para manter a qualidade do 
código e evitar erros comuns no desenvolvimento de software. Para executar o Ruff, conecte-se ao 
container Django, usando o comando ``inv docker-attach`` e, dentro do container, execute o comando ``ruff check``.


****************************
Boas práticas de programação
****************************

O Django segue a arquitetura MVT (model-view-template). É papel do desenvolvedor refletir
criticamente sobre a responsabilidade de cada uma dessas camadas. De modo geral, temos as
seguintes convenções:

- Regras de negócio devem ser implementadas na camada de models. Em caso de dúvidas, discuta com o time qual parte da sua issue é regra de negócio.
- A camada de templates precisa executar o mínimo de lógica possível. É papel da view alimentar o template com as variáveis necessárias para a correta renderização.
- O papel da camada de visualização é conectar templates com models. Ela deve receber uma requisição HTTP e responder o template apropriado. Tenha cuidado com a coesão ao implementar código na camada de visualização. Dê preferência para `class-based views <https://docs.djangoproject.com/en/5.0/topics/class-based-views/>`_ ao implementar fluxos complexos de requisição.
- Evite definir arquivos com nome ``utils`` ou ``helpers`` se o código vai ser utilizado em uma única classe. Melhor manter o código dentro da classe que vai utilizá-lo.
- Evite *overengineering*. Busque sempre a implementação mais simples possível, que respeite a arquitetura do Django e os princípios `SOLID <https://en.wikipedia.org/wiki/SOLID>`_. Deixe para resolver um problema futuro quando ele acontecer.
- Signals, middlewares, decorators e outros recursos intermediários e avançados do Django e do Python devem ser utilizados com cautela. Quanto mais genérica a implementação, mais complexa a manutenção.

*************
Documentação
*************

A EJ utiliza o projeto `Sphinx <https://www.sphinx-doc.org/en/master/>`_ para construir
tanto o guia de usuário quanto de desenvolvimento. Fique atento se a sua issue exige
atualizar a documentação. Caso sim, você precisará atualizar os arquivos ``.rst``
da documentação com as mudanças propostas. A documentação está disponível
no diretório ``docs`` do repositório.

***********
Traduções
***********

A EJ utiliza o suporte nativo do Django para internacionalização. Todas as strings precisam estar
em inglês e utilizarem o suporte de tradução do Django.
No arquivo ``locale/pt_BR/LC_MESSAGES/django.po`` ficam as traduções do inglês para o
português. Leia mais em :ref:`Internalização e tradução <Translations>`.

Abrindo um merge request
------------------------

Para que a sua contribuição seja disponibilizada no ambiente de homologação e depois em
produção, é preciso passar pela etapa de revisão. Essa etapa consiste em abrir um merge
request no Gitlab, da branch que você criou para desenvolver a issue para a **develop**.
O revisor do seu merge request será alguém mais experiente do time e você pode solicitar
a revisão no canal de comunicação para desenvolvimento.

O time segue algumas convenções para abertura de merge rquests.

***************************
Revise o seu merge request
***************************

A primeira convenção (que é praticamente uma regra) é que você revise o seu merge request
antes de solicitar um revisor. Isso é importante para que você corrija problemas e
erros de falta de atenção que ocorreram durante o desenvolvimento. Aproveite esse momento
e releia o guia de contribuição para verificar se alguma das boas práticas não foi seguida.
Uma forma prática de fazer essa "auto revisão" é abrir o MR como `draft <https://docs.gitlab.com/ee/user/project/merge_requests/drafts.html>`_.
Com o MR em draft, os revisores sabem que ele não está pronto para revisão, mas você poderá
utilizar o painel do Gitlab para verificar quais mudanças serão adicionadas ou removidas.
Quando você julgar que o MR está pronto, remova o draft e solicite um revisor no canal.

**************************
Teste o seu merge request
**************************

Um merge request que quebra os testes não será revisado, a não ser que a branch **develop**
também esteja quebrada. Um merge request que altera o backend e não adiciona novos testes, não será revisado.
Um merge request que altera a jornada de participação e não adiciona novos testes, não será revisado.
Você pode acompanhar a execução do *pipeline* de integração contínua na página do seu MR.
O Gitlab irá informar se alguma etapa da esteira de integração e deploy falhou.

*****************************
Aprovando o seu merge request
*****************************

Quando o seu merge request for aprovado, nossa esteira de deploy contínuo será ativada e
o `ambiente de homologação <ejplatform.pencillabs.tec.br/>`_ será atualizado com a sua contribuição 🎉🎉.
