
class Service(object):
    instance = None

    class __Service:
        def __init__(self):
            self.service = None

    def __new__(cls):
        if not Service.instance:
            Service.instance = Service.__Service()
        return Service.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
