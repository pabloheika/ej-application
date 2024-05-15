import environ

from boogie.configurations import Conf

env = environ.Env(
    DEFAULT_FROM_EMAIL=(str, "cd@cidadedemocratica.org.br"),
    DEFAULT_FROM_NAME=(str, "Empurrando Juntas"),
    MAILGUN_API_KEY=(str, ""),
    MAILGUN_SENDER_DOMAIN=(str, ""),
)


class EmailConf(Conf):

    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
    DEFAULT_FROM_NAME = env("DEFAULT_FROM_NAME")
    ANYMAIL = {
        "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
        "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
    }

    def get_email_backend(self):
        return "anymail.backends.mailgun.EmailBackend"
