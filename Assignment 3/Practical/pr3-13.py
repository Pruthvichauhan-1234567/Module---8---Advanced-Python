# 13. Write a Python program to match a word in a string using re.match().

import re
text = "Python is easy to learn and powerful."
word = input("Enter the word to match: ")
match = re.match(rf'\b{re.escape(word)}\b', text)
if match:
    print(f"'{word}' matches the beginning of the string.")
else:
    print(f"'{word}' does NOT match the beginning of the string.")