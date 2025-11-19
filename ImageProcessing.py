import numpy as np
from PIL import Image
from typing import Optional

class ImageProcessing:
    """
    A utility class that provides static methods for image processing tasks.
    This class is not meant to be instantiated.
    """

    @staticmethod
    def normalize_to_pil(pixel_array: Optional[np.ndarray]) -> Optional[Image.Image]:
        """
        Normalizes a NumPy pixel array and converts it to a PIL Image.

        This enhances contrast by scaling pixel values to the full 0-255 range.

        Args:
            pixel_array (Optional[np.ndarray]): The raw 2D NumPy array of pixel data.

        Returns:
            Optional[Image.Image]: A display-ready PIL Image, or None if the
                                   input was invalid.
        """
        if pixel_array is None:
            return None

        try:
            pixel_array_float = pixel_array.astype(float)
            min_val = pixel_array_float.min()
            max_val = pixel_array_float.max()

            if max_val > min_val:
                # Normalize to 0-1 range, then scale to 0-255
                normalized_pixels = (pixel_array_float - min_val) / (max_val - min_val) * 255.0
            else:
                # Handle the case of a solid color image
                normalized_pixels = np.zeros(pixel_array.shape)

            # Convert to an 8-bit unsigned integer array and then to a PIL Image
            final_image = Image.fromarray(normalized_pixels.astype(np.uint8))
            return final_image

        except Exception as e:
            print(f"Error during image normalization: {e}")
            return None
