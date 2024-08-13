class InvalidCredentialsError(Exception):
    """Указывает на то что данные логина неверные. Это может быть как логин, так и пароль"""
    def __init__(self, message="Упс! Видимо вы ошиблись и ввели неправильный логин и пароль"):
        self.message = message
        super().__init__(self.message)


class WebsiteConnectionError(Exception):
    """Указывает на ошибку сайта ГрГУ. Возможно он не отвечает."""
    pass
