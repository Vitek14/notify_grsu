class WebsiteNoResponse(Exception):
    """
    Указывает на то, что сайт не отвечает
    """
    def __init__(self, message="Сайт не отвечает ( • ᴖ • ｡)"):
        self.message = message
        super().__init__(self.message)


class WebsiteRemoved(Exception):
    """
    Указывает на то, что на сайте данная информация была удалена
    """
    def __init__(self, message="То что вы искали, больше не существует! <&_&<"):
        self.message = message
        super().__init__(self.message)
