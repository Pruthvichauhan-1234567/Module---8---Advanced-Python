# 5. Write a Python program to write multiple strings into a file.

lines = [
    "Hello, this is line one.\n",
    "This is line two.\n",
    "And here is line three.\n"
]
with open("myfile.txt", "w") as file:
    file.writelines(lines)
print("Strings have been written to 'myfile.txt'")
