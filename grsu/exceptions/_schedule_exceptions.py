class ScheduleNotFound(Exception):
    """
    Указывает на то, что расписание для указанной даты не было найдено
    """
    def __init__(self, message="Мы искали вдоль и поперёк, но не нашли расписание на сайте ( • ᴖ • ｡)"):
        self.message = message
        super().__init__(self.message)
