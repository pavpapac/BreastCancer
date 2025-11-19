import streamlit as st
from PatientDataFilterLogic import PatientDataFilterLogic
from ImageProcessing import ImageProcessing
import pandas as pd

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
        presentation_df = pdfl.get_patient_filtered_data(selected_patient_id, selected_breast_side, selected_image_view)
        
        if presentation_df.empty:
            st.warning("No matching clinical data found for the selected filters.")
        else:
            st.header("Clinical Findings")
            
            patient_record = presentation_df.iloc[0]

            card_col1, card_col2, card_col3 = st.columns(3)
            with card_col1:
                st.metric(label="Pathology", value=str(patient_record.get('pathology', 'N/A')))
            with card_col2:
                st.metric(label="BI-RADS Assessment", value=str(patient_record.get('assessment', 'N/A')))
            with card_col3:
                st.metric(label="Abnormality Type", value=str(patient_record.get('abnormality type', 'N/A')))

            st.divider()

            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.info(f"**Mass Shape:** {patient_record.get('mass shape', 'N/A')}")
            with detail_col2:
                st.info(f"**Mass Margins:** {patient_record.get('mass margins', 'N/A')}")
            with detail_col3:
                st.info(f"**Subtlety Score:** {patient_record.get('subtlety', 'N/A')}")

            # --- FIXED: Use pandas Styler to hide the index ---
            #with st.expander("Show Full Data Table"):
                # Use the Styler object to hide the index before rendering
            #    st.dataframe(presentation_df.style.hide(axis="index"))


            st.header("DICOM Image and Metadata")
            dcm_path = pdfl.get_patient_dicom_path(selected_patient_id, selected_breast_side, selected_image_view)
            
            if not dcm_path.exists():
                st.error(f"DICOM path not found or is invalid: {dcm_path}")
            else:
                pixel_array, image_metadata = pdfl.get_patient_image_data(dcm_path)
                
                img_col, meta_col = st.columns([3, 1]) 
                with img_col:
                    st.subheader("Medical Image")
                    if pixel_array is not None:
                        display_image = ImageProcessing.normalize_to_pil(pixel_array)
                        if display_image:
                            st.image(display_image, caption=f"DICOM Image for {selected_patient_id}", use_column_width=True)
                        else:
                            st.error("Could not process the image for display.")
                    else:
                        st.error("Could not load pixel data from the DICOM file.")
                
                with meta_col:
                    st.subheader("Image Metadata")
                    st.json(image_metadata)

    except (ValueError, FileNotFoundError) as e:
        st.error(f"Data Retrieval Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
else:
    st.info("Select patient filters from the sidebar to automatically display data.")
