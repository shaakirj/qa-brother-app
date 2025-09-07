import os
import requests
import re
import logging
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FigmaDesignComparator:
    """Enhanced Figma API integration with better error handling"""
    
    def __init__(self):
        self.access_token = os.getenv("FIGMA_ACCESS_TOKEN")
        if not self.access_token:
            logger.warning("FIGMA_ACCESS_TOKEN not found in environment variables")
        
        self.headers = {
            "X-Figma-Token": self.access_token,
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.figma.com/v1"
    
    def validate_access_token(self):
        """Validate the Figma access token"""
        try:
            response = requests.get(f"{self.base_url}/me", headers=self.headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Token valid for user: {user_data.get('email', 'Unknown')}")
                return True, user_data
            else:
                logger.error(f"Token validation failed: {response.status_code} - {response.text}")
                return False, response.text
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, str(e)
    
    def extract_file_id(self, figma_url):
        """Extract file ID from Figma URL with enhanced validation"""
        try:
            figma_url = figma_url.strip()
            
            patterns = [
                r'figma\.com/file/([a-zA-Z0-9]{22})',
                r'figma\.com/design/([a-zA-Z0-9]{22})', 
                r'figma\.com/proto/([a-zA-Z0-9]{22})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, figma_url)
                if match:
                    file_id = match.group(1)
                    logger.info(f"Extracted file ID: {file_id}")
                    return file_id
            
            if re.match(r'^[a-zA-Z0-9]{22}$', figma_url):
                logger.info(f"Using direct file ID: {figma_url}")
                return figma_url
            
            logger.error(f"Could not extract file ID from URL: {figma_url}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract file ID: {e}")
            return None
    
    def get_file_info(self, file_id):
        """Get Figma file information with detailed error handling"""
        try:
            if not re.match(r'^[a-zA-Z0-9]{22}$', file_id):
                logger.error(f"Invalid file ID format: {file_id}")
                return {"error": "Invalid file ID format"}
            
            url = f"{self.base_url}/files/{file_id}"
            logger.info(f"Requesting file info from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved file: {data.get('name', 'Unknown')}")
                return data
            else:
                error_msg = f"Figma API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                    
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_image_urls(self, file_id, node_ids=None, scale=1, format="png"):
        """Get image URLs for specific nodes with better error handling"""
        try:
            if not re.match(r'^[a-zA-Z0-9]{22}$', file_id):
                return {"error": "Invalid file ID format"}
            
            if scale not in [1, 2, 4]:
                logger.warning(f"Invalid scale {scale}, using scale=1")
                scale = 1
            
            if format not in ["png", "jpg", "svg", "pdf"]:
                logger.warning(f"Invalid format {format}, using png")
                format = "png"
            
            # If no node IDs provided, get the first page
            if not node_ids:
                file_info = self.get_file_info(file_id)
                if 'error' in file_info:
                    return file_info
                
                # Get first page/canvas
                if 'document' in file_info and 'children' in file_info['document']:
                    first_page = file_info['document']['children'][0]
                    node_ids = [first_page['id']]
                    logger.info(f"Using first page node ID: {first_page['id']}")
                else:
                    return {"error": "No pages found in Figma file"}
            
            if isinstance(node_ids, str):
                node_ids = [node_ids]
            
            url = f"{self.base_url}/images/{file_id}"
            params = {
                "ids": ",".join(node_ids),
                "scale": str(scale),
                "format": format,
                "use_absolute_bounds": "false"
            }
            
            logger.info(f"Requesting images from: {url}")
            logger.info(f"Parameters: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("err"):
                    return {"error": f"Figma API error: {data['err']}"}
                
                if data.get("images"):
                    valid_images = {k: v for k, v in data["images"].items() if v}
                    
                    if valid_images:
                        logger.info(f"Successfully retrieved {len(valid_images)} image URLs")
                        data["images"] = valid_images
                        return data
                    else:
                        return {"error": "All image URLs are null - check node permissions or try different nodes"}
                else:
                    return {"error": "No images field in API response"}
            else:
                error_msg = f"Image API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            logger.error(f"Failed to get image URLs: {e}")
            return {"error": f"Failed to get image URLs: {str(e)}"}

def diagnose_figma_issues():
    """Diagnose common Figma API issues"""
    print("Diagnosing Figma API configuration...")
    
    token = os.getenv("FIGMA_ACCESS_TOKEN")
    if not token:
        print("FIGMA_ACCESS_TOKEN not found in environment variables")
        return False
    
    print(f"Token found: {token[:8]}...{token[-4:]}")
    
    if len(token) < 40:
        print("Token appears too short (should be 40+ characters)")
        return False
    
    comparator = FigmaDesignComparator()
    valid, info = comparator.validate_access_token()
    
    if valid:
        print(f"Token valid for: {info.get('email', 'Unknown user')}")
        return True
    else:
        print(f"Token validation failed: {info}")
        return False

def test_figma_file_access(figma_url):
    """Test specific file access and image generation"""
    print(f"\nTesting Figma file access for: {figma_url}")
    
    comparator = FigmaDesignComparator()
    
    # Step 1: Extract file ID
    file_id = comparator.extract_file_id(figma_url)
    if not file_id:
        print("Could not extract file ID from URL")
        return False
    
    print(f"File ID extracted: {file_id}")
    
    # Step 2: Get file info
    file_info = comparator.get_file_info(file_id)
    if 'error' in file_info:
        print(f"File access failed: {file_info['error']}")
        return False
    
    print(f"File accessed: {file_info.get('name', 'Unknown')}")
    print(f"Pages found: {len(file_info['document']['children'])}")
    
    # Step 3: List available pages/canvases
    for i, page in enumerate(file_info['document']['children']):
        print(f"  Page {i+1}: {page['name']} (ID: {page['id']})")
        
        # Also list frames within the page
        if 'children' in page and page['children']:
            for j, frame in enumerate(page['children'][:3]):  # First 3 frames
                print(f"    Frame {j+1}: {frame.get('name', 'Unnamed')} (ID: {frame['id']})")
    
    # Step 4: Try to get image for first page
    first_page_id = file_info['document']['children'][0]['id']
    print(f"\nTesting image generation for first page: {first_page_id}")
    
    # Try different configurations
    test_configs = [
        {"scale": 1, "format": "png"},
        {"scale": 2, "format": "png"},
    ]
    
    for config in test_configs:
        print(f"\nTrying scale={config['scale']}, format={config['format']}")
        
        image_data = comparator.get_image_urls(file_id, [first_page_id], **config)
        
        if 'error' in image_data:
            print(f"Failed: {image_data['error']}")
        elif image_data.get('images'):
            image_url = image_data['images'].get(first_page_id)
            if image_url:
                print(f"Success: Got image URL")
                print(f"URL: {image_url[:100]}...")
                return True
            else:
                print("No image URL for specified node")
        else:
            print("No images in response")
    
    # Step 5: Try with specific frames instead of page
    if 'children' in file_info['document']['children'][0]:
        frames = file_info['document']['children'][0]['children']
        if frames:
            print(f"\nTrying with first frame instead of page...")
            first_frame_id = frames[0]['id']
            
            image_data = comparator.get_image_urls(file_id, [first_frame_id], scale=1)
            if 'error' not in image_data and image_data.get('images'):
                print(f"Success with frame: {first_frame_id}")
                return True
    
    return False

if __name__ == "__main__":
    # Replace with your actual Figma URL
    figma_url = input("Enter your Figma URL: ")
    
    print("Step 1: Testing API configuration...")
    if diagnose_figma_issues():
        print("\nStep 2: Testing file access...")
        test_figma_file_access(figma_url)
    else:
        print("Fix the token issue before proceeding.")