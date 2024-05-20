import re
import glob


class Father():
    def __init__(self, name, age, height):
        self.name = name
        self.age = age
        self.height = height


class Son(Father):
    def __init__(self, name, age, height, weight):
        super().__init__(name, age, height)
        self.weight = weight
    pass


the_sun = Son("sun", 18, 180, 60)

print(the_sun.name)
print(the_sun.age)
print(the_sun.height)
print(the_sun.weight)
