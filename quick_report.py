import psycopg2
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from docx import Document


#columns list 
columns_to_check = ["c_pano_av", "syno", "pht_mas_a", "pht_mas_b", "pht_mas_c", "pht_mas_d", "ch_fer_apr", "c_ouv_ap2", "c_pano_apr", "pho_fer_av", "c_ouv_av_1"]

#full names for the columns
column_full_names = {
    "c_pano_av": "Chambre Panoramique Avant",
    "syno": "Photo Feuille Manuel",
    "pht_mas_a": "Photo Masque A",
    "pht_mas_b":"Photo Masque B",
    "pht_mas_c":"Photo Masque C",
    "pht_mas_d":"Photo Masque D",
    "ch_fer_apr":"Chambre Fermeture Apres",
    "ch_ouv_ap2":"Chambre Ouverte Après Photo",
    "c_pano_apr":"Chambre Panoramique Apres",
    "pho_fer_av":"Photo Fermeture Avant",
    "c_ouv_av_1":"Chambre Ouverte Avant",
    

}
# Full SQL Queries Dictionary
SQL_QUERIES = {
    "no_slash_and_not_empty": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} NOT LIKE '%/%' AND {col} != '' AND {col} IS NOT NULL;
    """,
    "empty_or_null_count": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} = '' OR {col} IS NULL;
    """,
    "jpg_count": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} ILIKE '%.jpg';
    """,
    "jpeg_count": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} ILIKE '%.jpeg';
    """,
    "other_extension_count": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} NOT ILIKE '%.jpg'
          AND {col} NOT ILIKE '%.jpeg'
          AND {col} ILIKE '%.%';
    """,
    "missing_extension_rows": """
        SELECT count({col})
        FROM {table}
        WHERE {col} NOT ILIKE '%.%' AND {col} != '';
    """,
    "double_extension_rows": """
        SELECT count({col})
        FROM {table}
        WHERE {col} ~* '\\.(jpg|jpeg|png|gif|heic|tiff|bmp)\\.(jpg|jpeg|png|gif|heic|tiff|bmp)$';
    """,
    "wrong_path_count": """
        SELECT COUNT({col})
        FROM {table}
        WHERE {col} ILIKE 'files/%';
    """
}

def gather_column_info(cursor, table_name, column_name):
    column_info = {}
    for check_name, query in SQL_QUERIES.items():
        cursor.execute(query.format(col=column_name, table=table_name))
        column_info[check_name] = cursor.fetchone()[0]  # Always fetch a single value
    return column_info

def generate_report(conn, table_name):
    report = {}
    with conn.cursor() as cursor:
        for col in columns_to_check:
            report[col] = gather_column_info(cursor, table_name, col)
    return report

def display_report_gui(report):
    window = tk.Tk()
    window.title("Column Status Report")
    window.geometry("700x500")

    # Create a scrolled text area
    text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=90, height=25, font=("Arial", 10))
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Define tags for formatting
    text_area.tag_configure("bold", font=("Arial", 10, "bold"))
    text_area.tag_configure("center", justify="center")
    text_area.tag_configure("spacing", spacing1=10, spacing3=10)  # Add spacing before and after lines

    report_text = ""
    for column, data in report.items():
        # Add column name (centered and bold)
        full_name = column_full_names.get(column, column)  # Get the full name, or use the abbreviation if not found
        text_area.insert(tk.END, f"Column: {column} ({full_name})\n", ("bold", "center", "spacing"))
        
        # Add column data
        text_area.insert(tk.END, f"  Row count missing slash & not empty: {data['no_slash_and_not_empty']}\n", "spacing")
        text_area.insert(tk.END, f"  Row count Empty or NULL: {data['empty_or_null_count']}\n", "spacing")
        text_area.insert(tk.END, f"  .jpg count: {data['jpg_count']}\n", "spacing")
        text_area.insert(tk.END, f"  .jpeg count: {data['jpeg_count']}\n", "spacing")
        text_area.insert(tk.END, f"  Other extension count: {data['other_extension_count']}\n", "spacing")
        text_area.insert(tk.END, f"  Missing extension row count: {data['missing_extension_rows']}\n", "spacing")
        text_area.insert(tk.END, f"  Double extension count: {data['double_extension_rows']}\n", "spacing")
        text_area.insert(tk.END, f"  Wrong path (files/%) count: {data['wrong_path_count']}\n\n", "spacing")

    # Disable editing
    text_area.config(state=tk.DISABLED)

    # Add a save button
    save_button = tk.Button(window, text="Save Report", command=lambda: save_report(report))
    save_button.pack(side=tk.LEFT, padx=10, pady=10)
    def close_window():
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", close_window)  # Handle window close event
    window.mainloop()

def save_report(report):
    # Ask the user for the file path and type
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx")]
    )

    if not file_path:
        return  # User canceled the save dialog

    # Generate the report text
    report_text = ""
    for column, data in report.items():
        full_name = column_full_names.get(column, column)  # Get the full name, or use the abbreviation if not found
        report_text += f"Column: {column} ({full_name})\n"
        report_text += f"  Row count missing slash & not empty: {data['no_slash_and_not_empty']}\n"
        report_text += f"  Row count Empty or NULL: {data['empty_or_null_count']}\n"
        report_text += f"  .jpg count: {data['jpg_count']}\n"
        report_text += f"  .jpeg count: {data['jpeg_count']}\n"
        report_text += f"  Other extension count: {data['other_extension_count']}\n"
        report_text += f"  Missing extension row count: {data['missing_extension_rows']}\n"
        report_text += f"  Double extension count: {data['double_extension_rows']}\n"
        report_text += f"  Wrong path (files/%) count: {data['wrong_path_count']}\n\n"

    # Save the report
    if file_path.endswith(".txt"):
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(report_text)
    elif file_path.endswith(".docx"):
        doc = Document()
        doc.add_paragraph(report_text)
        doc.save(file_path)

    messagebox.showinfo("Success", f"Report saved to {file_path}")

def main(dbname, user, password, host, port, table_name):
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        # Generate the report
        report = generate_report(conn, table_name)
        # Display the report in a GUI
        display_report_gui(report)
        conn.close()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        return

if __name__ == "__main__":
    main()