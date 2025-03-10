import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
from data_managment import data_management_gui

# Function to fetch existing tables from the database
def fetch_existing_tables(dbname, user, password, host, port):
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()

        # Query to fetch all table names
        cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
        """)
        tables = cur.fetchall()

        # Close the connection
        cur.close()
        conn.close()

        # Extract table names from the result
        return [table[0] for table in tables]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch tables: {e}")
        return []

# Function to handle the selection of an existing table
def select_existing_table(dbname, user, password, host, port):
    # Create a new window for table selection
    table_select_window = tk.Tk()
    table_select_window.title("Select Existing Table")
    table_select_window.geometry("400x250")
    # Fetch existing tables
    tables = fetch_existing_tables(dbname, user, password, host, port)

    if not tables:
        messagebox.showinfo("Info", "No tables found in the database.")
        table_select_window.destroy()
        return

    # Create and place the dropdown for table selection
    label_table = tk.Label(table_select_window, text="Select Table:")
    label_table.pack(pady=10)

    table_var = tk.StringVar()
    table_var.set(tables[0])  # Set the default value to the first table
    dropdown_tables = ttk.Combobox(table_select_window, textvariable = table_var, state="readonly")
    def on_selection(event):
        table_var.set(dropdown_tables.get())

    dropdown_tables.bind("<<ComboboxSelected>>", on_selection)
    
    dropdown_tables['values'] = tables
    dropdown_tables.current(0) # Set the default value to the first table
    dropdown_tables.pack(pady=10)

    # Function to handle the selection and proceed to data management
    def proceed_to_data_management():
        selected_table = table_var.get()
        if not selected_table:
            messagebox.showerror("Error", "Please select a table.")
        else:
            table_select_window.destroy()
            data_management_gui(dbname, user, password, host, port, selected_table)
            return

    # Create the submit button
    button_submit = tk.Button(table_select_window, text="Submit", command=proceed_to_data_management)
    button_submit.pack(pady=20)
    
    def close_window():
        table_select_window.destroy()
        exit()
    
    table_select_window.protocol("WM_DELETE_WINDOW", close_window)
    # Run the table selection window
    table_select_window.mainloop()  # Run the window