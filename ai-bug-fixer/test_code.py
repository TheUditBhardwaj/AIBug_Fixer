def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: Division by zero if empty list

def find_max(arr):
    max_val = arr[0]  # Bug: IndexError if empty array
    for i in range(len(arr)):
        if arr[i] > max_val:
            max_val = arr[i]
    return max_val

# Bug: Using == instead of = for assignment
x == 10

# Bug: Potential SQL injection
user_input = "admin'; DROP TABLE users--"
query = "SELECT * FROM users WHERE username = '" + user_input + "'"
