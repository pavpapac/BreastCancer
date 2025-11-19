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
def load_all_patient_ids(_pdfl):
    try:
        return _pdfl.get_all_patient_ids()
    except Exception as e:
        st.error(f"Fatal Error on startup: Could not load patient IDs. {e}")
        return []

pdfl = init_logic()
if not pdfl:
    st.stop()

all_patient_ids = load_all_patient_ids(pdfl)
if not all_patient_ids:
    st.sidebar.error("Failed to load patient IDs from the database.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Select Patient Filters")

selected_patient_id = st.sidebar.selectbox("Patient ID", options=all_patient_ids)

if selected_patient_id:
    patient_options = pdfl.get_dependent_options(selected_patient_id)
    available_breast_sides = patient_options.get('breast_sides', [])
else:
    available_breast_sides = []

if not available_breast_sides:
    st.sidebar.warning("No data available for this patient.")
    selected_breast_side = None
    available_image_views = []
else:
    selected_breast_side = st.sidebar.selectbox("Breast Side", options=available_breast_sides)

if selected_patient_id and selected_breast_side:
    side_options = pdfl.get_dependent_options(selected_patient_id, breast_side=selected_breast_side)
    available_image_views = side_options.get('image_views', [])
else:
    available_image_views = []

if not available_image_views:
    st.sidebar.warning("No image views available for this selection.")
    selected_image_view = None
else:
    selected_image_view = st.sidebar.selectbox("Image View", options=available_image_views)


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
                st.metric(
                    label="Pathology", 
                    value=str(patient_record.get('pathology', 'N/A')),
                    help="Final diagnosis. Options: BENIGN, BENIGN_WITHOUT_CALLBACK, MALIGNANT."
                )
            with card_col2:
                st.metric(
                    label="BI-RADS Assessment", 
                    value=str(patient_record.get('assessment', 'N/A')),
                    help="0: Incomplete, 1: Negative, 2: Benign, 3: Probably Benign, 4: Suspicious, 5: Highly Suspicious, 6: Known Malignancy."
                )
            with card_col3:
                st.metric(
                    label="Breast Density", 
                    value=str(patient_record.get('breast_density', 'N/A')),
                    help="A score from 1 to 4. 1: Mostly fatty, 2: Scattered density, 3: Heterogeneously dense, 4: Extremely dense."
                )

            st.divider()

            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.metric(
                    label="Mass Shape",
                    value=str(patient_record.get('mass shape', 'N/A')),
                    help="Shape of the mass. Options: ROUND, OVAL, LOBULATED, IRREGULAR, etc."
                )
            with detail_col2:
                st.metric(
                    label="Mass Margins",
                    value=str(patient_record.get('mass margins', 'N/A')),
                    help="Edge characteristics. Options: CIRCUMSCRIBED, OBSCURED, MICROLOBULATED, ILL_DEFINED, SPICULATED."
                )
            with detail_col3:
                st.metric(
                    label="Subtlety Score",
                    value=str(patient_record.get('subtlety', 'N/A')),
                    help="Subjective rating of detection difficulty from 1 (subtle) to 5 (obvious)."
                )

            st.header("DICOM Image")
            dcm_path = pdfl.get_patient_dicom_path(selected_patient_id, selected_breast_side, selected_image_view)
            
            if not dcm_path.exists():
                st.error(f"DICOM path not found or is invalid: {dcm_path}")
            else:
                pixel_array, _ = pdfl.get_patient_image_data(dcm_path)
                
                if pixel_array is not None:
                    display_image = ImageProcessing.normalize_to_pil(pixel_array)
                    if display_image:
                        st.image(display_image, caption=f"DICOM Image for {selected_patient_id}", width='stretch')
                    else:
                        st.error("Could not process the image for display.")
                else:
                    st.error("Could not load pixel data from the DICOM file.")

    except (ValueError, FileNotFoundError) as e:
        st.error(f"Data Retrieval Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
else:
    st.info("Select patient filters from the sidebar to automatically display data.")

# --- NEW: Learn More Section ---
st.divider()
with st.expander("Learn More: Clinical Metrics & Mammography Assessment"):
    st.markdown("""
    This section provides context for the clinical metrics used in breast cancer assessment.

    ### BI-RADS Assessment (Breast Imaging Reporting and Data System)
    A standardized scoring system used by radiologists to categorize mammography, ultrasound, and MRI findings.
    - **0: Incomplete** - Needs additional imaging evaluation (e.g., more views, ultrasound).
    - **1: Negative** - Nothing to report. Breasts are symmetrical, no masses, no suspicious calcifications or distortions.
    - **2: Benign** - Benign (non-cancerous) finding. No malignancy is suspected. Examples: fibroadenoma, simple cysts.
    - **3: Probably Benign** - Short-term follow-up suggested. Finding has a high probability of being benign (>98%), but not 100%.
    - **4: Suspicious Abnormality** - Biopsy should be considered. Finding does not have the classic appearance of cancer but could be. Subdivided into 4A (low suspicion), 4B (intermediate suspicion), 4C (moderate concern).
    - **5: Highly Suggestive of Malignancy** - Action should be taken (biopsy, surgery). Finding has a very high probability of being cancerous (>95%).
    - **6: Known Biopsy-Proven Malignancy** - Used for findings already proven to be cancer by biopsy, but before definitive treatment.

    ### Pathology
    The final diagnosis of tissue obtained from a biopsy.
    - **BENIGN**: Non-cancerous.
    - **BENIGN_WITHOUT_CALLBACK**: Non-cancerous, but may require further review or follow-up.
    - **MALIGNANT**: Cancerous.

    ### Breast Density
    A measure of the amount of fibrous and glandular tissue in the breast compared to fatty tissue. Dense breast tissue can make it harder to detect cancer on mammograms.
    - **1: Almost entirely fatty**
    - **2: Scattered areas of fibroglandular density**
    - **3: Heterogeneously dense** (may obscure small masses)
    - **4: Extremely dense** (may obscure masses)

    ### Mass Shape
    Describes the overall form of a mass.
    - **ROUND**: Circular or spherical.
    - **OVAL**: Elliptical.
    - **LOBULATED**: Undulating or scalloped contours.
    - **IRREGULAR**: Neither round nor oval, often with spiculation.
    - **ARCHITECTURAL_DISTORTION**: Normal architecture is distorted without an obvious mass.
    - **ASYMMETRIC_BREAST_TISSUE**: Asymmetry in breast tissue.
    - **FOCAL_ASYMMETRIC_DENSITY**: Localized area of increased density.

    ### Mass Margins
    Describes the edges of a mass.
    - **CIRCUMSCRIBED**: Well-defined, sharp borders.
    - **OBSCURED**: Margins are hidden by adjacent dense tissue.
    - **MICROLOBULATED**: Short, subtle undulations.
    - **ILL_DEFINED**: Indistinct or vague borders.
    - **SPICULATED**: Straight lines radiating from the mass.

    ### Subtlety Score
    A subjective rating by the radiologist indicating how obvious the abnormality is on the image.
    - **1 (Subtle)**: Very difficult to detect.
    - **2**: Subtle.
    - **3**: Fairly obvious.
    - **4**: Obvious.
    - **5 (Obvious)**: Very easy to detect.

    ### Mammography Assessment Stages
    Mammography is a key tool in breast cancer screening and diagnosis. The assessment process typically involves:
    1.  **Screening Mammogram**: Routine imaging for women without symptoms.
    2.  **Diagnostic Mammogram**: Performed when a screening mammogram shows an abnormality, or when a woman has symptoms (e.g., a lump). It involves more detailed views.
    3.  **Further Imaging**: May include additional mammographic views, ultrasound, or MRI to further characterize a finding.
    4.  **Biopsy**: If a finding remains suspicious after imaging, a tissue sample is taken for pathological examination.
    5.  **Follow-up**: For benign or probably benign findings, short-term follow-up imaging may be recommended.
    """)
