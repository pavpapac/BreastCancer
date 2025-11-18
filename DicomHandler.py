import pydicom
import numpy as np
import pandas as pd
import os
from pathlib import Path
import matplotlib.pyplot as plt


class DicomHandler:
    """
    This class includes all methods needed to access, read and extract data from DICOM files. It serves as a handler
    to requests from the business logic layer, that require input from DICOM files. What should not happen here is
    operations on clinical database and/or user interactions with the business logic. Clinical database should have the
    patient related path to the DICOM files and provide them to this class"""

    def __init__(self, folder_path):
        """
        Initializes the handler by finding and reading the first DICOM file in a folder.

        Args:
            folder_path (str or Path): The path to the folder containing DICOM files.
        """
        self.folder_path = Path(folder_path)
        self.dicom_path = self._find_first_dicom_file()
        self.dataset = None

        if self.dicom_path:
            try:
                self.dataset = pydicom.dcmread(self.dicom_path)
                print(f"DicomHandler initialized for: {self.dicom_path.name}")
            except Exception as e:
                print(f"Error reading DICOM file at {self.dicom_path}: {e}")
        else:
            print(f"No valid DICOM files found in '{self.folder_path}'.")

    def _find_first_dicom_file(self):
        """
        Finds the first valid DICOM file in the specified folder path.

        Returns:
            Path object or None: The path to the first DICOM file, or None if not found.
        """
        if not self.folder_path.is_dir():
            print(f"Error: Provided path '{self.folder_path}' is not a directory.")
            return None

        for file_path in self.folder_path.iterdir():
            if file_path.is_file():
                try:
                    # Try to read the file header to confirm it's a DICOM file
                    pydicom.dcmread(file_path, stop_before_pixels=True)
                    print(f"Found DICOM file: {file_path.name}")
                    return file_path  # Return the path of the first valid file
                except pydicom.errors.InvalidDicomError:
                    continue  # Not a DICOM file, ignore

        return None  # No DICOM files were found

    # ----------------------------------------------------------------------
    # 1. Function to return the pixel data as a numpy array
    # ----------------------------------------------------------------------
    def get_pixel_array(self):
        """
        Returns the raw image pixel data as a NumPy array from the loaded DICOM file.
        """
        if self.dataset is None:
            print("Cannot get pixel array: No DICOM dataset loaded.")
            return None

        try:
            pixel_data = self.dataset.pixel_array
            print(f"Pixel data extracted successfully. Shape: {pixel_data.shape}")
            return pixel_data
        except Exception as e:
            print(f"Error extracting pixel data: {e}")
            return None

    # ----------------------------------------------------------------------
    # 2. Function to return patient metadata
    # ----------------------------------------------------------------------
    def get_metadata(self):
        """
        Returns a dictionary of key patient and series metadata from the loaded DICOM file.
        """
        if self.dataset is None:
            print("Cannot get metadata: No DICOM dataset loaded.")
            return {}

        metadata = {}
        tags_to_extract = [
            'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex', 'PatientAge',
            'StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID', 'StudyID',
            'SeriesNumber', 'AcquisitionDate', 'StudyDescription', 'SeriesDescription',
            'Modality', 'Manufacturer', 'Rows', 'Columns', 'PixelSpacing'
        ]

        for tag in tags_to_extract:
            try:
                data_element = self.dataset[tag]
                metadata[tag] = str(data_element.value)
            except (KeyError, AttributeError):
                metadata[tag] = 'N/A'

        print("Metadata extracted successfully.")
        return metadata


if __name__ == '__main__':
    # This path now points to the FOLDER containing the DICOM file(s)
    dicom_folder_path = Path('C:/Users/pavpa/PycharmProjects/Apps/BreastCancer/Data/manifest-ZkhPvrLo5216730872708713142/CBIS-DDSM/Mass-Training_P_00001_LEFT_MLO/07-20-2016-DDSM-NA-90988/1.000000-full mammogram images-80834')
    
    if dicom_folder_path.exists():
        dh = DicomHandler(dicom_folder_path)

        if dh.dataset:
            pixel_array = dh.get_pixel_array()
            if pixel_array is not None:
                plt.imshow(pixel_array, cmap=plt.cm.gray)
                plt.title("DICOM Image")
                plt.show()

            dicom_metadata = dh.get_metadata()
            print("\n--- DICOM Metadata ---")
            for key, value in dicom_metadata.items():
                print(f"{key}: {value}")
    else:
        print(f"Test folder not found: {dicom_folder_path}")
