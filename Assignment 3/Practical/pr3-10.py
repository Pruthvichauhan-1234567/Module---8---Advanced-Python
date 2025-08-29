# 10. Write Python programs to demonstrate method overloading and method overriding.

class Calculator:
    def add(self, a=0, b=0, c=0):
        return a + b + c
calc = Calculator()
print(calc.add(2, 3))        
print(calc.add(2, 3, 4))     
print(calc.add(10))          
class Animal:
    def sound(self):
        print("Animal makes a sound")
class Dog(Animal):
    def sound(self):
        print("Dog barks")
a = Animal()
d = Dog()
a.sound()   
d.sound()
