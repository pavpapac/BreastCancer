import sqlite3
from PatientDataFilterLogic import PatientDataFilterLogic
from pathlib import Path
import pandas as pd

def get_test_patient_ids(db_path, count=3):
    """Connects to the database and fetches a few unique patient IDs for testing."""
    try:
        with sqlite3.connect(db_path) as con:
            cursor = con.cursor()
            cursor.execute("SELECT DISTINCT patient_id FROM patients LIMIT ?", (count,))
            ids = [row[0] for row in cursor.fetchall()]
            return ids
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

def run_test_for_patient(pdfl, patient_id, breast_side, image_view):
    """Runs a single test case for a given patient and filter combination."""
    print(f"--- Testing Patient ID: {patient_id}, Side: {breast_side}, View: {image_view} ---")
    try:
        # 1. Get filtered data as a DataFrame
        filtered_df = pdfl.get_patient_filtered_data(patient_id, breast_side, image_view)
        if filtered_df.empty:
            print("Result: SKIPPED - No data found for the specified filters.\n")
            return True  # Not a failure, just no data to test

        print("Result: SUCCESS - Filtered data found.")

        # 2. Get the DICOM path
        dcm_path = pdfl.get_patient_dicom_path(filtered_df)
        if not dcm_path.exists():
            print(f"Result: FAILED - DICOM path does not exist: {dcm_path}\n")
            return False

        print(f"Result: SUCCESS - DICOM path found: {dcm_path}")

        # 3. Get image data and the new pixel_spacing value
        image_data_tuple = pdfl.get_patient_image_data(dcm_path)
        
        # --- NEW: Verify the return tuple and pixel_spacing ---
        if len(image_data_tuple) != 3:
            print(f"Result: FAILED - Expected 3 return values from get_patient_image_data, but got {len(image_data_tuple)}.\n")
            return False
        
        pixel_array, image_metadata, pixel_spacing = image_data_tuple
        
        if pixel_array is None:
            print("Result: FAILED - Could not extract pixel array from DICOM file.\n")
            return False
            
        if not isinstance(pixel_spacing, list) or len(pixel_spacing) != 2 or not all(isinstance(x, float) for x in pixel_spacing):
            print(f"Result: FAILED - Pixel spacing is not a list of two floats. Got: {pixel_spacing}\n")
            return False

        print(f"Result: SUCCESS - Pixel spacing extracted successfully: {pixel_spacing}\n")
        return True

    except Exception as e:
        print(f"Result: FAILED - An unexpected error occurred: {e}\n")
        return False

if __name__ == "__main__":
    db_file = "clinical_database.db"
    
    patient_ids_to_test = get_test_patient_ids(db_file, count=3)
    
    if not patient_ids_to_test:
        print("Could not retrieve patient IDs for testing. Aborting.")
    else:
        print(f"Retrieved Patient IDs for testing: {patient_ids_to_test}\n")
        
        pdfl = PatientDataFilterLogic(db_file)
        
        success_count = 0
        total_tests = 0
        
        for pid in patient_ids_to_test:
            # Test a couple of common combinations
            for side, view in [("LEFT", "CC"), ("RIGHT", "MLO")]:
                total_tests += 1
                if run_test_for_patient(pdfl, pid, side, view):
                    success_count += 1
        
        print(f"\n--- Test Summary ---")
        print(f"{success_count} out of {total_tests} tests passed.")
