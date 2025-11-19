import sys
# Add the project root to the Python path to allow importing our modules
sys.path.append('C:/Users/pavpa/PycharmProjects/Apps/BreastCancer')

from DatabaseHandler import DatabaseHandler

def check_abnormality_types():
    """
    Connects to the database and prints all unique values
    from the 'abnormality type' column.
    """
    db_file = "clinical_database.db"
    column_to_check = "abnormality type"
    
    print(f"Checking for unique values in column: '{column_to_check}'...")
    
    try:
        with DatabaseHandler(db_file) as dbh:
            # Use our existing robust function to get the distinct values
            unique_values = dbh.get_distinct_values(column_to_check)
            
            if unique_values:
                print("\nFound the following unique abnormality types:")
                for value in unique_values:
                    print(f"- {value}")
            else:
                print("\nCould not find any unique values for this column.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    check_abnormality_types()
