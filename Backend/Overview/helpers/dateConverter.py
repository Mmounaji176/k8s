
import datetime

class DateConverter:
    regex = '\d{2}-\d{2}-\d{4}-\d{2}-\d{2}'
    format = '%d-%m-%Y-%H-%M'

    def to_python(self, value):
        return datetime.datetime.strptime(value, self.format)

    def to_url(self, value):
        return value.strftime(self.format)