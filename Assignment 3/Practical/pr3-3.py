# 3. Write a Python program to open a file in write mode, write some text, and then close it.

file = open("1st.txt", "w")
file.write("Hello, this is a test.\n")
file.write("This is the second line.\n")
file.close()
print("Text has been written to '1st.txt'.")