import os
import logging
from dotenv import load_dotenv

# Configure logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FigmaTest")

# --- Step 1: Load Environment Variables ---
logger.info("Attempting to load .env file...")
if load_dotenv():
    logger.info("✅ .env file loaded successfully.")
else:
    logger.error("❌ Could not find or load .env file. Please ensure it exists in the same directory.")
    exit()

# Check for the specific Figma token
figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
if figma_token:
    logger.info(f"✅ FIGMA_ACCESS_TOKEN found. Token starts with: {figma_token[:8]}...")
else:
    logger.error("❌ FIGMA_ACCESS_TOKEN not found in environment variables.")
    exit()

# --- Step 2: Import the Figma Comparator ---
try:
    from design8 import FigmaDesignComparator
    logger.info("✅ Successfully imported FigmaDesignComparator from design8.py.")
except ImportError as e:
    logger.error(f"❌ Failed to import from design8.py. Error: {e}")
    exit()
except Exception as e:
    logger.error(f"❌ An unexpected error occurred during import. Error: {e}")
    exit()

# --- Step 3: Run the Test ---
def run_test():
    """
    Isolates and tests the Figma URL parsing and image retrieval functionality.
    """
    logger.info("--- Starting Figma Test ---")
    
    # The URL that causes issues
    figma_url_to_test = "https://www.figma.com/design/D0tXCTuRzPjTL1yy0NrPlG/Scans.ai--Dev-?node-id=65-4882&t=0NwZs9UxaGbSHEBM-4"
    logger.info(f"Testing with URL: {figma_url_to_test}")

    try:
        # Instantiate the class
        comparator = FigmaDesignComparator()
    except Exception as e:
        logger.error(f"❌ Failed to instantiate FigmaDesignComparator. Error: {e}")
        return

    # --- Test URL Parsing ---
    logger.info("\n--- Testing URL Parsing ---")
    node_info = comparator.get_specific_node_from_url(figma_url_to_test)

    if node_info and node_info.get("file_id"):
        logger.info("✅ URL Parsing Successful!")
        logger.info(f"   - Extracted File ID: {node_info['file_id']}")
        logger.info(f"   - Extracted Node ID: {node_info['node_id']}")
    else:
        logger.error("❌ URL Parsing FAILED. The `get_specific_node_from_url` method did not return a valid file ID.")
        logger.error("--- Test Aborted ---")
        return

    # --- Test Image Retrieval ---
    logger.info("\n--- Testing Image Retrieval ---")
    file_id = node_info['file_id']
    node_id = node_info['node_id']
    
    figma_image = comparator.get_node_image(file_id, node_id)

    if figma_image:
        logger.info("✅ Image Retrieval Successful!")
        logger.info(f"   - Image object created: {type(figma_image)}")
        logger.info(f"   - Image size: {figma_image.size}")
        
        # Save the image to verify it's correct
        try:
            image_path = "test_figma_output.png"
            figma_image.save(image_path)
            logger.info(f"✅ Image saved to '{image_path}' for verification.")
        except Exception as e:
            logger.error(f"❌ Could not save the downloaded image. Error: {e}")
    else:
        logger.error("❌ Image Retrieval FAILED. The `get_node_image` method did not return an image.")
        logger.error("💡 Common Reasons for Failure:")
        logger.error("   1. Invalid FIGMA_ACCESS_TOKEN.")
        logger.error("   2. The specific frame/node in Figma is not marked for export.")
        logger.error("   3. Network issues or Figma API downtime.")

    logger.info("\n--- Test Complete ---")

if __name__ == "__main__":
    run_test()