class FunctionWrapper:
    def __init__(self, func):
        raise Exception("I'm not using this class")
        self.func = func
        self.targets = []

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def add_target(self, target):
        self.targets.append(target)

    def is_target(self, target):
        return target in self.targets

    def __getattr__(self, item):
        return getattr(self.func, item)