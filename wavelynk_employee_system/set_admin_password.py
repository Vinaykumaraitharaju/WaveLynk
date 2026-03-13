from database import execute
from utils import hash_password

new_password = input("Enter new admin password: ").strip()

execute(
    "UPDATE users SET password_hash = ? WHERE username = ?",
    (hash_password(new_password), "admin"),
)

print("Admin password updated successfully.")
