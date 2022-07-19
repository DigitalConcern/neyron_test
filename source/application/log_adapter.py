import logging


class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        my_context = kwargs.pop('route', self.extra['route'])
        return '[%s] %s' % (my_context, msg), kwargs
