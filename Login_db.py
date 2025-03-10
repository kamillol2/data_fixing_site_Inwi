import tkinter as tk
from tkinter import messagebox
import psycopg2
from option_gui import choice_gui  # Import the functions from the selection file

# Function to test the connection
def test_connection():
    dbname = entry_dbname.get()
    user = entry_user.get()
    password = entry_password.get()
    host = entry_host.get()
    port = entry_port.get()

    try:
        # Try connecting to the database with the entered credentials
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        messagebox.showinfo("Success", "Connection successful!")
        root.withdraw()  # Hide the first window
        choice_gui(dbname, user, password, host, port)  # Pass credentials to the next GUI
    except Exception as e:
        messagebox.showerror("Error", f"Connection failed: {e}")

# Create the first window for database login
root = tk.Tk()
root.title("Database Login")

# Create and place the labels and entry fields
label_dbname = tk.Label(root, text="Database Name:")
label_dbname.grid(row=0, column=0, padx=10, pady=10)

entry_dbname = tk.Entry(root)
entry_dbname.grid(row=0, column=1, padx=10, pady=10)

label_user = tk.Label(root, text="Username:")
label_user.grid(row=1, column=0, padx=10, pady=10)

entry_user = tk.Entry(root)
entry_user.grid(row=1, column=1, padx=10, pady=10)

label_password = tk.Label(root, text="Password:")
label_password.grid(row=2, column=0, padx=10, pady=10)

entry_password = tk.Entry(root, show="*")
entry_password.grid(row=2, column=1, padx=10, pady=10)

label_host = tk.Label(root, text="Host:")
label_host.grid(row=3, column=0, padx=10, pady=10)

entry_host = tk.Entry(root)
entry_host.grid(row=3, column=1, padx=10, pady=10)

label_port = tk.Label(root, text="Port:")
label_port.grid(row=4, column=0, padx=10, pady=10)

entry_port = tk.Entry(root)
entry_port.grid(row=4, column=1, padx=10, pady=10)

# Create a button to test the connection
test_button = tk.Button(root, text="Test Connection", command=test_connection)
test_button.grid(row=5, column=0, columnspan=2, pady=20)

# Close the application when the window is closed
root.protocol("WM_DELETE_WINDOW", root.destroy)

# Run the application
root.mainloop()