# 12. Write a Python program to search for a word in a string using re.search().

import re
text = "Python is a powerful and easy-to-learn programming language."
word = input("Enter the word to search: ")
match = re.search(rf'\b{re.escape(word)}\b', text)
if match:
    print(f"'{word}' found in the string.")
else:
    print(f"'{word}' not found in the string.")