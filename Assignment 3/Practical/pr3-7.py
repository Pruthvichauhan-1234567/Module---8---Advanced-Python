# 7. Write a Python program to demonstrate handling multiple exceptions.

def handle_multiple_exceptions():
    try:
        num1 = int(input("Enter a number: "))
        num2 = int(input("Enter another number: "))
        result = num1 / num2
        sample_list = [10, 20, 30]
        index = int(input("Enter an index to access (0-2): "))
        print("Value at index:", sample_list[index])       
        print("Division result:", result)
    except ValueError:
        print("Error: Invalid input! Please enter integers only.")
    except ZeroDivisionError:
        print("Error: Division by zero is not allowed.")
    except IndexError:
        print("Error: Index out of range! Please enter a valid index.")
    except Exception as e:
        print("An unexpected error occurred:", e)
handle_multiple_exceptions()
