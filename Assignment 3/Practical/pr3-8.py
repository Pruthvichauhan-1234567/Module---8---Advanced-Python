# 8. Write a Python program to create a class and access its properties using an object.

class Person:
    def __init__(self, name, age):
        self.name = name  
        self.age = age 
person1 = Person("Alice", 25)
print("Name:", person1.name)
print("Age:", person1.age)