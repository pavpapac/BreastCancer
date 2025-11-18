import streamlit as st
from PatientDataFilterLogic import PatientDataFilterLogic
import pandas as pd
import numpy as np

# --- App Configuration ---
st.set_page_config(layout="wide")
st.title("Breast Cancer Patient Data Viewer")

# --- Initialization ---
try:
    pdfl = PatientDataFilterLogic("clinical_database.db")
    ui_options = pdfl.get_ui_selection_options()
except Exception as e:
    st.error(f"Fatal Error on startup: Could not initialize the application logic. {e}")
    st.stop()

# --- Sidebar for User Selections ---
st.sidebar.header("Select Patient Filters")

if not ui_options.get('patient_ids') or not ui_options.get('breast_sides') or not ui_options.get('image_views'):
    st.sidebar.error("Failed to load filter options from the database.")
    st.stop()

selected_patient_id = st.sidebar.selectbox("Patient ID", options=ui_options.get('patient_ids', []))
selected_breast_side = st.sidebar.selectbox("Breast Side", options=ui_options.get('breast_sides', []))
selected_image_view = st.sidebar.selectbox("Image View", options=ui_options.get('image_views', []))

# --- Main Content Area ---
if st.sidebar.button("Get Patient Data"):
    if not all([selected_patient_id, selected_breast_side, selected_image_view]):
        st.warning("Please make a selection for all fields.")
    else:
        st.info(f"Fetching data for Patient: {selected_patient_id}, Side: {selected_breast_side}, View: {selected_image_view}")
        
        try:
            # 1. Get filtered clinical data
            filtered_rows = pdfl.get_patient_filtered_data(
                selected_patient_id,
                selected_breast_side,
                selected_image_view
            )
            
            if not filtered_rows:
                st.warning("No matching clinical data found for the selected filters.")
            else:
                st.header("Filtered Clinical Data")
                columns = pdfl.get_column_names()
                if columns:
                    df = pd.DataFrame(filtered_rows, columns=columns)
                    st.dataframe(df)
                else:
                    st.error("Could not retrieve column headers for the data.")

                # 2. Get DICOM image and metadata
                st.header("DICOM Image and Metadata")
                dcm_path = pdfl.get_patient_dicom_path(filtered_rows)
                
                if not dcm_path.exists():
                    st.error(f"DICOM path not found or is invalid: {dcm_path}")
                else:
                    pixel_array, image_metadata = pdfl.get_patient_image_data(dcm_path)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Medical Image")
                        if pixel_array is not None:
                            # --- IMPROVED: Normalize pixel data for better contrast ---
                            # Convert to float for normalization
                            pixel_array_float = pixel_array.astype(float)
                            # Scale pixel values to the 0-255 range
                            min_val = pixel_array_float.min()
                            max_val = pixel_array_float.max()
                            if max_val > min_val:
                                normalized_pixels = (pixel_array_float - min_val) * (255.0 / (max_val - min_val))
                            else:
                                normalized_pixels = np.zeros(pixel_array.shape) # Avoid division by zero
                            
                            # Convert to uint8, which is the standard for image display
                            final_image = normalized_pixels.astype(np.uint8)
                            
                            st.image(final_image, caption=f"DICOM Image for {selected_patient_id}", use_column_width=True)
                        else:
                            st.error("Could not load pixel data from the DICOM file.")
                    
                    with col2:
                        st.subheader("Image Metadata")
                        st.json(image_metadata)

        except (ValueError, FileNotFoundError) as e:
            st.error(f"Data Retrieval Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
else:
    st.info("Select patient filters from the sidebar and click 'Get Patient Data' to begin.")
