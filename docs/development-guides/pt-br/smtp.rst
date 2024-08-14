==========
SMTP
==========

A EJ depende de um servidor SMTP para realizar algumas operações como recuperação de senha.
Para isso é preciso indicar qual o servidor será utilizado. 

Como padrão, utilizamos a biblioteca `anymail <https://anymail.dev/en/stable/>`_ para simplificar
a integração com servidores SMTP. Nesse caso, estamos utilizando a API do Mailgun para realizar os disparos.
Acesse a documentação da biblioteca para verificar quais outros serviços são suportados por padrão.

A configuração do Mailgun é realizada por meio das seguintes variáveis de ambiente:

- MAILGUN_API_KEY
- MAILGUN_SENDER_DOMAIN

No entanto, o Anymail não tem suporte à conexão SMTP direta com um servidor privado. Nesse caso é possível
utilizar a `biblioteca padrão do django <https://docs.djangoproject.com/en/5.0/topics/email/>`_ para o envio 
de emails. Para isso será necessário configurar as seguintes variáveis de ambiente:

- EMAIL_HOST
- EMAIL_PORT
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD

Ou seja, se as variáveis EMAIL_HOST e EMAIL_PORT estiverem preenchidas, será usado o EMAIL_BACKEND 
`django.core.mail.backends.smtp.EmailBackend`, caso contrário, será usado o `anymail.backends.mailgun.EmailBackend`.