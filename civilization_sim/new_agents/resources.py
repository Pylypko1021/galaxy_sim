from mesa import Agent

class Resource(Agent):
    """Base class for all resources."""
    def __init__(self, model):
        super().__init__(model)

class Food(Resource):
    def __init__(self, model):
        super().__init__(model)

class Tree(Resource):
    def __init__(self, model):
        super().__init__(model)

class Stone(Resource):
    def __init__(self, model):
        super().__init__(model)

class IronOre(Resource):
    def __init__(self, model):
        super().__init__(model)

class Mountain(Resource):
    def __init__(self, model):
        super().__init__(model)

class River(Resource):
    def __init__(self, model):
        super().__init__(model)
