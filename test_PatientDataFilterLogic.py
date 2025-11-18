import sqlite3
from PatientDataFilterLogic import PatientDataFilterLogic
from pathlib import Path

def get_test_patient_ids(db_path, count=3):
    """Connects to the database and fetches a few unique patient IDs for testing."""
    try:
        with sqlite3.connect(db_path) as con:
            cursor = con.cursor()
            cursor.execute("SELECT DISTINCT patient_id FROM patients LIMIT ?", (count,))
            # fetchall returns a list of tuples, e.g., [('P_00001',), ('P_00004',)]
            ids = [row[0] for row in cursor.fetchall()]
            return ids
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

def run_test_for_patient(pdfl, patient_id, breast_side, image_view):
    """Runs a single test case for a given patient and filter combination."""
    print(f"--- Testing Patient ID: {patient_id}, Side: {breast_side}, View: {image_view} ---")
    try:
        # 1. Get filtered data rows
        rows = pdfl.get_patient_filtered_data(patient_id, breast_side, image_view)
        if not rows:
            print("Result: FAILED - No data found for the specified filters.\n")
            return False

        print("Result: SUCCESS - Filtered data found.")

        # 2. Get the DICOM path
        dcm_path = pdfl.get_patient_dicom_path(rows)
        if not dcm_path.exists():
            print(f"Result: FAILED - DICOM path does not exist: {dcm_path}\n")
            return False

        print(f"Result: SUCCESS - DICOM path found: {dcm_path}")

        # 3. Get image data
        pixel_array, image_metadata = pdfl.get_patient_image_data(dcm_path)
        if pixel_array is None:
            print("Result: FAILED - Could not extract pixel array from DICOM file.\n")
            return False

        print("Result: SUCCESS - Pixel array and metadata extracted.\n")
        return True

    except Exception as e:
        print(f"Result: FAILED - An unexpected error occurred: {e}\n")
        return False

if __name__ == "__main__":
    db_file = "clinical_database.db"
    
    # Get a list of patient IDs to test
    patient_ids_to_test = get_test_patient_ids(db_file, count=3)
    
    if not patient_ids_to_test:
        print("Could not retrieve patient IDs for testing. Aborting.")
    else:
        print(f"Retrieved Patient IDs for testing: {patient_ids_to_test}\n")
        
        # Initialize the logic class
        pdfl = PatientDataFilterLogic(db_file)
        
        success_count = 0
        total_tests = 0
        
        # Loop through each patient and run tests
        for pid in patient_ids_to_test:
            # Test Case 1: LEFT, CC
            total_tests += 1
            if run_test_for_patient(pdfl, pid, "LEFT", "CC"):
                success_count += 1
            
            # Test Case 2: RIGHT, MLO
            total_tests += 1
            if run_test_for_patient(pdfl, pid, "RIGHT", "MLO"):
                success_count += 1
        
        print(f"\n--- Test Summary ---")
        print(f"{success_count} out of {total_tests} tests passed.")
