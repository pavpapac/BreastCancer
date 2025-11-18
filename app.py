import streamlit as st
from PatientDataFilterLogic import PatientDataFilterLogic
import pandas as pd
import numpy as np
from PIL import Image

# --- App Configuration ---
st.set_page_config(layout="wide")
st.title("Breast Cancer Patient Data Viewer")

# --- Initialization & Caching ---
@st.cache_resource
def init_logic():
    try:
        return PatientDataFilterLogic("clinical_database.db")
    except Exception as e:
        st.error(f"Fatal Error on startup: Could not initialize the application logic. {e}")
        return None

@st.cache_data
def load_ui_options(_pdfl):
    try:
        return _pdfl.get_ui_selection_options()
    except Exception as e:
        st.error(f"Fatal Error on startup: Could not load UI options. {e}")
        return {}

pdfl = init_logic()
if not pdfl:
    st.stop()

ui_options = load_ui_options(pdfl)
if not all(ui_options.values()):
    st.sidebar.error("Failed to load filter options from the database.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Select Patient Filters")
selected_patient_id = st.sidebar.selectbox("Patient ID", options=ui_options.get('patient_ids', []))
selected_breast_side = st.sidebar.selectbox("Breast Side", options=ui_options.get('breast_sides', []))
selected_image_view = st.sidebar.selectbox("Image View", options=ui_options.get('image_views', []))

# --- Main Content Area ---
if all([selected_patient_id, selected_breast_side, selected_image_view]):
    try:
        filtered_df = pdfl.get_patient_filtered_data(selected_patient_id, selected_breast_side, selected_image_view)
        
        if filtered_df.empty:
            st.warning("No matching clinical data found for the selected filters.")
        else:
            st.header("Filtered Clinical Data")
            st.dataframe(filtered_df)

            st.header("DICOM Image and Metadata")
            dcm_path = pdfl.get_patient_dicom_path(filtered_df)
            
            if not dcm_path.exists():
                st.error(f"DICOM path not found or is invalid: {dcm_path}")
            else:
                pixel_array, image_metadata = pdfl.get_patient_image_data(dcm_path)
                
                col1, col2 = st.columns([3, 1]) 
                with col1:
                    st.subheader("Medical Image")
                    if pixel_array is not None:
                        # Normalize for display contrast
                        pixel_array_float = pixel_array.astype(float)
                        min_val, max_val = pixel_array_float.min(), pixel_array_float.max()
                        if max_val > min_val:
                            normalized_pixels = (pixel_array_float - min_val) * (255.0 / (max_val - min_val))
                        else:
                            normalized_pixels = np.zeros(pixel_array.shape)
                        
                        image = Image.fromarray(normalized_pixels.astype(np.uint8))
                        
                        st.image(image, caption=f"DICOM Image for {selected_patient_id}", use_column_width=True)
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
    st.info("Select patient filters from the sidebar to automatically display data.")
