import psycopg2
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import logging
from datetime import datetime
from full_report import main as full_report_gui

# Setup logging
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
log_filename = os.path.join(log_directory, f"data_fixing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# List of columns to check for data fixing
columns_to_check = ["c_pano_av", "syno", "pht_mas_a", "pht_mas_b", "pht_mas_c", "pht_mas_d", 
                   "ch_fer_apr", "c_ouv_ap2", "c_pano_apr", "pho_fer_av", "c_ouv_av_1"]

# SQL queries for data fixing
SQL_FIXING_QUERIES = [
    r"""
    -- UPDATE column empty text into NULL
    UPDATE {table}
    SET {col} = 'Link Not Found'
    WHERE {col} IS NULL OR {col} = '';
    """,
    r"""
    -- UPDATE column with double extension by deleting BOTH extensions
    UPDATE {table}
    SET {col} = REGEXP_REPLACE({col}, '\.[a-zA-Z0-9]+$', '')
    WHERE {col} ~* '\.(jpg|jpeg|png|gif|heic|tiff|bmp)\.(jpg|jpeg|png|gif|heic|tiff|bmp)$';
    """,
    r"""
    -- UPDATE column with valid extension .jpeg if missing for qfield images
    UPDATE {table}
    SET {col} = {col} ||'.jpeg'
    WHERE {col} NOT ILIKE '%.%' AND {col} ILIKE '%qfield%';
    """,
    r"""
    -- UPDATE column with invalid extension like .heic
    UPDATE {table}
    SET {col} = REGEXP_REPLACE({col}, '\.[a-zA-Z0-9]+$', '.jpg')
    WHERE {col} NOT ILIKE '%.jpg' AND {col} NOT ILIKE '%.jpeg' AND {col} ILIKE '%.%';
    """,
    r"""
    -- UPDATE column with valid extension .jpg if missing
    UPDATE {table}
    SET {col} = {col} ||'.jpg'
    WHERE {col} NOT ILIKE '%.jpg' AND {col} NOT ILIKE '%.%';
    """,
    r"""
    -- UPDATE column missing '/' next to files or next to DCIM
    UPDATE {table}
    SET {col} = CASE
                  WHEN {col} ILIKE 'files%' AND NOT {col} ILIKE 'files/%' THEN REGEXP_REPLACE({col}, 'files', 'files/')
                  WHEN {col} ILIKE 'DCIM%' AND NOT {col} ILIKE 'DCIM/%' THEN REGEXP_REPLACE({col}, 'DCIM', 'DCIM/')
                  ELSE {col}
               END
    WHERE ({col} ILIKE 'files%' AND NOT {col} ILIKE 'files/%') OR ({col} ILIKE 'DCIM%' AND NOT {col} ILIKE 'DCIM/%');
    """,
    r"""
    -- UPDATE column from files/% to DCIM/%
    UPDATE {table}
    SET {col} = REGEXP_REPLACE({col}, 'files/', 'DCIM/')
    WHERE {col} ILIKE 'files/%';
    """
]


def execute_fixing_queries(conn, table_name, progress_callback=None):
    """
    Execute all data fixing queries on the specified table.
    """
    try:
        with conn.cursor() as cursor:
            # Counter for tracking total updates
            total_updates = 0
            total_steps = len(columns_to_check) * len(SQL_FIXING_QUERIES)
            current_step = 0
            
            # Loop through each column
            for column in columns_to_check:
                # Execute each query for this column
                for query_index, query in enumerate(SQL_FIXING_QUERIES):
                    query_name = f"Query {query_index+1} on column {column}"
                    logging.info(f"Executing {query_name}")
                    
                    formatted_query = query.format(col=column, table=table_name)
                    cursor.execute(formatted_query)
                    rows_affected = cursor.rowcount
                    total_updates += rows_affected
                    
                    logging.info(f"Completed {query_name}: {rows_affected} rows affected")
                    
                    # Update progress if callback is provided
                    current_step += 1
                    if progress_callback:
                        progress_percent = (current_step / total_steps) * 100
                        progress_callback(progress_percent, f"Fixing {column}: {rows_affected} updates")
            
            # Commit the changes
            conn.commit()
            logging.info(f"All fixing queries completed successfully. Total updates: {total_updates}")
            
            return total_updates
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logging.error(f"Error executing fixing queries: {str(e)}")
        raise e


def check_file_existence(conn, table_name, folder_path, progress_callback=None):
    """
    Check if files referenced in the database actually exist in the specified folder path.
    Update database records if files don't exist.
    """
    try:
        total_updates = 0
        with conn.cursor() as cursor:
            # First, count total rows to process for progress calculation
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0] * len(columns_to_check)
            processed_rows = 0
            
            # For each column we want to check
            for column in columns_to_check:
                logging.info(f"Checking file existence for column {column}")
                
                # Get the values from this column
                cursor.execute(f"SELECT {column} FROM {table_name}")
                rows = cursor.fetchall()
                
                for row in rows:
                    file_path = row[0]
                    processed_rows += 1
                    
                    # Skip null values or already labeled as not found
                    if file_path.startswith('Link Not Found') or file_path.startswith('File Not Found'):
                        continue
                    
                    # Check if the file exists in the specified folder
                    try:
                        full_path = os.path.join(folder_path, file_path)
                        file_exists = os.path.isfile(full_path)
                        
                        if not file_exists:
                            logging.info(f"File not found: {full_path}")
                            # Update the database if file doesn't exist
                            cursor.execute(
                                f"UPDATE {table_name} SET {column} = %s WHERE {column} = %s",
                                ('File Not Found', file_path)
                            )
                            total_updates += cursor.rowcount
                    except Exception as file_check_error:
                        logging.warning(f"Error checking file {file_path}: {str(file_check_error)}")
                    
                    # Update progress if callback is provided
                    if progress_callback and processed_rows % 10 == 0:  # Update every 10 rows to reduce overhead
                        progress_percent = (processed_rows / total_rows) * 100
                        progress_callback(progress_percent, f"Checking files in {column}: {processed_rows}/{total_rows}")
            
            # Commit the changes
            conn.commit()
            logging.info(f"File existence check completed. Total missing files: {total_updates}")
            
            return total_updates
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logging.error(f"Error checking file existence: {str(e)}")
        raise e


class EnhancedDataFixingDialog:
    def __init__(self, parent, dbname, user, password, host, port, table_name):
        self.parent = parent
        self.db_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.table_name = table_name
        self.folder_path = None
        
        # Create a new top-level window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Enhanced Data Fixing Tool")
        self.dialog.geometry("800x600")
        
        # Make the dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create widgets
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=50, pady=50)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Database Image Path Fixing Tool", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Folder selection frame
        folder_frame = tk.LabelFrame(main_frame, text="Image Folder Selection", padx=10, pady=10)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Folder path display
        path_frame = tk.Frame(folder_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        self.path_var = tk.StringVar()
        self.path_var.set("No folder selected")
        path_entry = tk.Entry(path_frame, textvariable=self.path_var, width=40, state='readonly')
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_button = tk.Button(path_frame, text="Browse...", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT)
        
        # Options frame
        options_frame = tk.LabelFrame(main_frame, text="Operation Options", padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Checkboxes for operations
        self.fix_paths_var = tk.BooleanVar(value=True)
        fix_paths_cb = tk.Checkbutton(options_frame, text="Fix path formatting issues", 
                                      variable=self.fix_paths_var)
        fix_paths_cb.pack(anchor=tk.W, pady=2)
        
        self.check_existence_var = tk.BooleanVar(value=True)
        check_existence_cb = tk.Checkbutton(options_frame, text="Check file existence", 
                                           variable=self.check_existence_var)
        check_existence_cb.pack(anchor=tk.W, pady=2)
        
        self.launch_report_var = tk.BooleanVar(value=True)
        launch_report_cb = tk.Checkbutton(options_frame, text="Launch full report after completion", 
                                         variable=self.launch_report_var)
        launch_report_cb.pack(anchor=tk.W, pady=2)
        
        # Status and progress frame
        status_frame = tk.LabelFrame(main_frame, text="Status", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to start")
        status_label = tk.Label(status_frame, textvariable=self.status_var, anchor="w")
        status_label.pack(fill=tk.X)
        
        # Log text widget with scrollbar
        log_frame = tk.Frame(status_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=5, width=50, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 0))
        
        self.start_button = tk.Button(button_frame, text="Start", command=self.run_data_fixing, 
                                     width=10)
        self.start_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy, 
                                 width=10)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Create a custom logger handler to display logs in the text widget
        self.setup_log_handler()
    
    def setup_log_handler(self):
        """Set up a custom handler to display logs in the text widget"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.configure(state='disabled')
                    self.text_widget.see(tk.END)
                # Schedule to be executed in the main thread
                self.text_widget.after(0, append)
        
        # Configure the handler
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Add the handler to the logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)
    
    def browse_folder(self):
        """Open a file dialog to select the DCIM folder"""
        folder_selected = filedialog.askdirectory(title="Select Folder Containing Image Files")
        if folder_selected:
            self.folder_path = folder_selected
            self.path_var.set(folder_selected)
            logging.info(f"Selected folder: {folder_selected}")
    
    def update_progress(self, value, message):
        """Update the progress bar and status message"""
        self.progress_var.set(value)
        self.status_var.set(message)
        self.dialog.update_idletasks()
    
    def run_data_fixing(self):
        """Execute the selected data fixing operations"""
        # Check if folder is required and selected
        if self.check_existence_var.get() and not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder for file existence check.")
            return
        
        # Disable the start button to prevent multiple executions
        self.start_button.config(state=tk.DISABLED)
        
        try:
            # Log the start of operations
            logging.info(f"Starting data fixing operations on table: {self.table_name}")
            self.update_progress(0, "Starting operations...")
            
            # Initialize counters
            fixing_updates = 0
            existence_updates = 0
            
            # Connect to the database
            try:
                logging.info("Connecting to database...")
                conn = psycopg2.connect(**self.db_params)
                logging.info("Database connection established.")
            except Exception as db_error:
                raise Exception(f"Failed to connect to database: {str(db_error)}")
            
            # Execute path fixing if selected
            if self.fix_paths_var.get():
                logging.info("Starting path format fixing...")
                self.update_progress(10, "Fixing path formats...")
                
                fixing_updates = execute_fixing_queries(
                    conn, 
                    self.table_name, 
                    lambda percent, msg: self.update_progress(10 + percent * 0.4, msg)
                )
                
                logging.info(f"Path fixing completed: {fixing_updates} updates made")
                self.update_progress(50, f"Path fixing completed: {fixing_updates} updates")
            
            # Check file existence if selected
            if self.check_existence_var.get():
                logging.info("Starting file existence check...")
                self.update_progress(50, "Checking file existence...")
                
                existence_updates = check_file_existence(
                    conn, 
                    self.table_name, 
                    self.folder_path,
                    lambda percent, msg: self.update_progress(50 + percent * 0.4, msg)
                )
                
                logging.info(f"File existence check completed: {existence_updates} files not found")
                self.update_progress(90, f"File check completed: {existence_updates} missing files")
            
            # Close the database connection
            conn.close()
            logging.info("Database connection closed.")
            
            # Complete the progress bar
            self.update_progress(100, "All operations completed successfully!")
            
            # Show success message
            messagebox.showinfo(
                "Operation Complete", 
                f"Data fixing operations completed successfully!\n\n"
                f"- Format fixing updates: {fixing_updates}\n"
                f"- Missing file updates: {existence_updates}\n"
                f"- Total updates: {fixing_updates + existence_updates}\n\n"
                f"Detailed log saved to: {log_filename}"
            )
            
            # Launch the full report GUI if selected
            if self.launch_report_var.get():
                logging.info("Launching full report...")
                self.dialog.destroy()
                
                full_report_gui(
                    self.db_params['dbname'], 
                    self.db_params['user'], 
                    self.db_params['password'], 
                    self.db_params['host'], 
                    self.db_params['port'], 
                    self.table_name
                )
            
        except Exception as e:
            # Log the error
            logging.error(f"Error: {str(e)}")
            
            # Show error message
            messagebox.showerror(
                "Error", 
                f"An error occurred during the operation:\n\n{str(e)}\n\n"
                f"Please check the log file for details:\n{log_filename}"
            )
            
            # Update status
            self.update_progress(0, f"Operation failed: {str(e)}")
        
        finally:
            # Re-enable the start button
            self.start_button.config(state=tk.NORMAL)

def main(dbname, user, password, host, port, table_name):
    """
    Main function to connect to the database and open the enhanced data fixing GUI.
    """
    try:
        # Log the start of the application
        logging.info(f"Starting Enhanced Data Fixing Tool for table: {table_name}")
        
        # Create the root window
        root = tk.Tk()
        # Show the enhanced data fixing dialog
        dialog = EnhancedDataFixingDialog(root, dbname, user, password, host, port, table_name)
        
        # Start the Tkinter main loop
        root.mainloop()
        
        logging.info("Application closed.")
        
    except Exception as e:
        # Log any uncaught exceptions
        logging.critical(f"Uncaught exception: {str(e)}")
        
        # Show error message
        if 'root' in locals():
            messagebox.showerror("Critical Error", f"An unexpected error occurred:\n\n{str(e)}")
            root.destroy()

if __name__ == "__main__":
    main("test_csv", "kamil", "123456", "localhost", "5432", "flop_flop")