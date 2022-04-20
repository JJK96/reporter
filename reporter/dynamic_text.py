class Generator:
    def __init__(self, content):
        self.content = content

    def generate(self):
        """ Update content object with dynamic content """
        raise NotImplementedError
