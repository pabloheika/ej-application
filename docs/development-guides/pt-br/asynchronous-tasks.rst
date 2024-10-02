*******************
Tarefas assíncronas
*******************

Em alguns momentos, surge a necessidade de alocar implementações para serem executadas de forma
assíncrona, seja pelo alto volume de dados a serem processados ou por uma alta demanda de 
armazenamento, por exemplo. No contexto da EJ, há a oportunidade de distribuir a responsabilidade 
da execução de funções, como, na atualização da clusterização de uma conversa. 
Desta forma, é possível diminuir a carga do servidor e `melhorar a performance <https://medium.com/@fatma_2377/dmastering-asynchronous-tasks-and-event-driven-architectures-in-backend-development-363d657cf1c9/>`_. 

Alguns sistemas são usados para facilitar este processo de administrar tarefas assíncronas, como 
por exemplo, o `Celery <https://docs.celeryq.dev/en/stable/index.html>`_., 
que é a opção utilizada na EJ e é ativada de forma opcional.

De forma complementar, é utilizada a biblioteca `django-celery-beat <https://django-celery-beat.readthedocs.io/en/latest/>`_, 
que permite a criação e manutenção de tarefas assíncronas por meio da interface do Django Admin.

A seguir é descrita a utilização do Celery em implementações do projeto.
 
 
============================
Atualização da clusterização
============================

Localizada no aplicativo `ej_clusters`, a implementação é utilizada em vários locais da aplicação, 
como, no Painel, no Gerenciamento de personas e na aba "Descubra", durante a votação.

Contexto
--------

O local com uma demanda recorrente, é na página de Votação, na aba "Descubra", em que, se realizadas
repetidas requisições à página, com uma conversa com um volume alto de participação, nota-se lentidão 
para renderizar o gráfico de Nuvem de pontos, comprometendo a experiência do usuário.

Solução
-------

Ao invés de executar a atualização da clusterização a cada requisição à página, ela é realizada de 
forma assíncrona com o Celery, a partir da criação de um grupo, sendo repetida dentro de um intervalo 
de tempo de 5 minutos, removendo a dependência da resposta do servidor para que os grupos sejam 
atualizados.
