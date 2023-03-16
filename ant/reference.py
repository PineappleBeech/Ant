class FunctionRef:
    def __init__(self, worker, func_name):
        self.worker = worker
        self.func_name = func_name

    def __call__(self, *args, **kwargs):
        return self.worker._call(self.func_name, args)
