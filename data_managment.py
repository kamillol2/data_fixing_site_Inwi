import psycopg2
import tkinter as tk
from quick_report import main
from data_fixing_final import main as data_fixing_main
from full_report import main as full_report_main
import csv
from tkinter import filedialog, messagebox

# Function to export data as CSV
def export_data_as_csv(dbname, user, password, host, port, table_name):
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not file_path:
            return  # User canceled the save dialog

        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        messagebox.showinfo("Success", f"Data exported to {file_path}")
        conn.close()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Function to create the data management GUI
def data_management_gui(dbname, user, password, host, port, selected_table):
    data_window = tk.Tk()
    data_window.title("Data Management")

    # Set the window size
    data_window.geometry("400x300")

    # Create and place the buttons
    button_gathering = tk.Button(data_window, text="Quick Report", command= lambda: main(dbname, user, password, host, port, selected_table), width=20, height=2)
    button_gathering.pack(pady=10)

    button_formatting = tk.Button(data_window, text="Data FIX / TEST", command=lambda: data_fixing_main(dbname, user, password, host, port, selected_table), width=20, height=2)
    button_formatting.pack(pady=10)

    button_fixing = tk.Button(data_window, text="Full Report", command=lambda: full_report_main(dbname, user, password, host, port, selected_table), width=20, height=2)
    button_fixing.pack(pady=10)

    button_export_csv = tk.Button(data_window, text="Export Data as CSV", command=lambda: export_data_as_csv(dbname, user, password, host, port, selected_table), width=20, height=2)
    button_export_csv.pack(pady=10)

    # Function to close the window
    def close_window():
        data_window.destroy()
        exit()

    # Close the window when the X icon is clicked
    data_window.protocol("WM_DELETE_WINDOW", close_window)

    # Run the GUI
    data_window.mainloop()

# Run the data management GUI when this file is executed
if __name__ == "__main__":
    data_management_gui()