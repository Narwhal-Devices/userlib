class animal():
    fur = 'brown'
    def __init__(self, a):
        self.a = a

class dog(animal):
    fur = 'gray'
    def __init__(self, a):
        super().__init__(a)
        print(self.fur)

if __name__ == '__main__':
    murray = dog('cute')
    print(murray.a)
    print(murray.fur)