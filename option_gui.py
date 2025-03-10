import tkinter as tk
from table_creation import create_table_gui
from selection_gui import select_existing_table
# Function to create the main GUI after login
def choice_gui(dbname, user, password, host, port):
    # Create the main window
    main_window = tk.Tk()
    main_window.title("Table Selection")
    main_window.geometry("300x250")

    # Create and place the buttons
    button_create_table = tk.Button(main_window, text="Create New Table", command=lambda: create_table_gui(dbname, user, password, host, port), width=20, height=2)
    button_create_table.pack(pady=10)

    button_select_table = tk.Button(main_window, text="Select Existing Table", command=lambda: select_existing_table(dbname, user, password, host, port), width=20, height=2)
    button_select_table.pack(pady=10)

    def close_window():
        main_window.destroy()
        exit()
    
    main_window.protocol("WM_DELETE_WINDOW", close_window)
    # Run the main window
    main_window.mainloop()