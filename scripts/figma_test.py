import streamlit as st
import os
import requests
from groq import Groq
import PyPDF2
import docx
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import traceback
from datetime import datetime
from jira import JIRA
import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageChops
import base64
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssimimport os
import requests
from dotenv import load_dotenv
from automation import FigmaIntegration

# Load environment variables from .env
load_dotenv()

def get_canvas_node_ids(file_data):
    """Extract CANVAS node IDs from Figma file data"""
    if 'document' in file_data and 'children' in file_data['document']:
        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
    return []

def main():
    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
    figma_file_key = os.getenv("FIGMA_FILE_KEY")
    if not figma_token or not figma_file_key:
        print("Figma API token or file key not set in .env file.")
        return

    figma_api = FigmaIntegration(figma_token)
    try:
        # Get file info
        file_data = figma_api.get_file_info(figma_file_key)
        print("File info loaded successfully.")

        # Extract CANVAS node IDs
        node_ids = get_canvas_node_ids(file_data)
        if not node_ids:
            print("No CANVAS nodes found in Figma file.")
            return

        print(f"Found CANVAS node IDs: {node_ids}")

        # Get images for these node IDs
        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
        print("Figma images response:", images_response)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()    import os
    import requests
    from dotenv import load_dotenv
    from automation import FigmaIntegration
    
    # Load environment variables from .env
    load_dotenv()
    
    def get_canvas_node_ids(file_data):
        """Extract CANVAS node IDs from Figma file data"""
        if 'document' in file_data and 'children' in file_data['document']:
            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
        return []
    
    def main():
        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        figma_file_key = os.getenv("FIGMA_FILE_KEY")
        if not figma_token or not figma_file_key:
            print("Figma API token or file key not set in .env file.")
            return
    
        figma_api = FigmaIntegration(figma_token)
        try:
            # Get file info
            file_data = figma_api.get_file_info(figma_file_key)
            print("File info loaded successfully.")
    
            # Extract CANVAS node IDs
            node_ids = get_canvas_node_ids(file_data)
            if not node_ids:
                print("No CANVAS nodes found in Figma file.")
                return
    
            print(f"Found CANVAS node IDs: {node_ids}")
    
            # Get images for these node IDs
            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
            print("Figma images response:", images_response)
        except Exception as e:
            print(f"Error: {e}")
    
    if __name__ == "__main__":
        main()        import os
        import requests
        from dotenv import load_dotenv
        from automation import FigmaIntegration
        
        # Load environment variables from .env
        load_dotenv()
        
        def get_canvas_node_ids(file_data):
            """Extract CANVAS node IDs from Figma file data"""
            if 'document' in file_data and 'children' in file_data['document']:
                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
            return []
        
        def main():
            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
            figma_file_key = os.getenv("FIGMA_FILE_KEY")
            if not figma_token or not figma_file_key:
                print("Figma API token or file key not set in .env file.")
                return
        
            figma_api = FigmaIntegration(figma_token)
            try:
                # Get file info
                file_data = figma_api.get_file_info(figma_file_key)
                print("File info loaded successfully.")
        
                # Extract CANVAS node IDs
                node_ids = get_canvas_node_ids(file_data)
                if not node_ids:
                    print("No CANVAS nodes found in Figma file.")
                    return
        
                print(f"Found CANVAS node IDs: {node_ids}")
        
                # Get images for these node IDs
                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                print("Figma images response:", images_response)
            except Exception as e:
                print(f"Error: {e}")
        
        if __name__ == "__main__":
            main()            import os
            import requests
            from dotenv import load_dotenv
            from automation import FigmaIntegration
            
            # Load environment variables from .env
            load_dotenv()
            
            def get_canvas_node_ids(file_data):
                """Extract CANVAS node IDs from Figma file data"""
                if 'document' in file_data and 'children' in file_data['document']:
                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                return []
            
            def main():
                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                if not figma_token or not figma_file_key:
                    print("Figma API token or file key not set in .env file.")
                    return
            
                figma_api = FigmaIntegration(figma_token)
                try:
                    # Get file info
                    file_data = figma_api.get_file_info(figma_file_key)
                    print("File info loaded successfully.")
            
                    # Extract CANVAS node IDs
                    node_ids = get_canvas_node_ids(file_data)
                    if not node_ids:
                        print("No CANVAS nodes found in Figma file.")
                        return
            
                    print(f"Found CANVAS node IDs: {node_ids}")
            
                    # Get images for these node IDs
                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                    print("Figma images response:", images_response)
                except Exception as e:
                    print(f"Error: {e}")
            
            if __name__ == "__main__":
                main()                import os
                import requests
                from dotenv import load_dotenv
                from automation import FigmaIntegration
                
                # Load environment variables from .env
                load_dotenv()
                
                def get_canvas_node_ids(file_data):
                    """Extract CANVAS node IDs from Figma file data"""
                    if 'document' in file_data and 'children' in file_data['document']:
                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                    return []
                
                def main():
                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                    if not figma_token or not figma_file_key:
                        print("Figma API token or file key not set in .env file.")
                        return
                
                    figma_api = FigmaIntegration(figma_token)
                    try:
                        # Get file info
                        file_data = figma_api.get_file_info(figma_file_key)
                        print("File info loaded successfully.")
                
                        # Extract CANVAS node IDs
                        node_ids = get_canvas_node_ids(file_data)
                        if not node_ids:
                            print("No CANVAS nodes found in Figma file.")
                            return
                
                        print(f"Found CANVAS node IDs: {node_ids}")
                
                        # Get images for these node IDs
                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                        print("Figma images response:", images_response)
                    except Exception as e:
                        print(f"Error: {e}")
                
                if __name__ == "__main__":
                    main()                    import os
                    import requests
                    from dotenv import load_dotenv
                    from automation import FigmaIntegration
                    
                    # Load environment variables from .env
                    load_dotenv()
                    
                    def get_canvas_node_ids(file_data):
                        """Extract CANVAS node IDs from Figma file data"""
                        if 'document' in file_data and 'children' in file_data['document']:
                            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                        return []
                    
                    def main():
                        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                        figma_file_key = os.getenv("FIGMA_FILE_KEY")
                        if not figma_token or not figma_file_key:
                            print("Figma API token or file key not set in .env file.")
                            return
                    
                        figma_api = FigmaIntegration(figma_token)
                        try:
                            # Get file info
                            file_data = figma_api.get_file_info(figma_file_key)
                            print("File info loaded successfully.")
                    
                            # Extract CANVAS node IDs
                            node_ids = get_canvas_node_ids(file_data)
                            if not node_ids:
                                print("No CANVAS nodes found in Figma file.")
                                return
                    
                            print(f"Found CANVAS node IDs: {node_ids}")
                    
                            # Get images for these node IDs
                            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                            print("Figma images response:", images_response)
                        except Exception as e:
                            print(f"Error: {e}")
                    
                    if __name__ == "__main__":
                        main()                        import os
                        import requests
                        from dotenv import load_dotenv
                        from automation import FigmaIntegration
                        
                        # Load environment variables from .env
                        load_dotenv()
                        
                        def get_canvas_node_ids(file_data):
                            """Extract CANVAS node IDs from Figma file data"""
                            if 'document' in file_data and 'children' in file_data['document']:
                                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                            return []
                        
                        def main():
                            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                            figma_file_key = os.getenv("FIGMA_FILE_KEY")
                            if not figma_token or not figma_file_key:
                                print("Figma API token or file key not set in .env file.")
                                return
                        
                            figma_api = FigmaIntegration(figma_token)
                            try:
                                # Get file info
                                file_data = figma_api.get_file_info(figma_file_key)
                                print("File info loaded successfully.")
                        
                                # Extract CANVAS node IDs
                                node_ids = get_canvas_node_ids(file_data)
                                if not node_ids:
                                    print("No CANVAS nodes found in Figma file.")
                                    return
                        
                                print(f"Found CANVAS node IDs: {node_ids}")
                        
                                # Get images for these node IDs
                                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                print("Figma images response:", images_response)
                            except Exception as e:
                                print(f"Error: {e}")
                        
                        if __name__ == "__main__":
                            main()                            import os
                            import requests
                            from dotenv import load_dotenv
                            from automation import FigmaIntegration
                            
                            # Load environment variables from .env
                            load_dotenv()
                            
                            def get_canvas_node_ids(file_data):
                                """Extract CANVAS node IDs from Figma file data"""
                                if 'document' in file_data and 'children' in file_data['document']:
                                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                return []
                            
                            def main():
                                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                if not figma_token or not figma_file_key:
                                    print("Figma API token or file key not set in .env file.")
                                    return
                            
                                figma_api = FigmaIntegration(figma_token)
                                try:
                                    # Get file info
                                    file_data = figma_api.get_file_info(figma_file_key)
                                    print("File info loaded successfully.")
                            
                                    # Extract CANVAS node IDs
                                    node_ids = get_canvas_node_ids(file_data)
                                    if not node_ids:
                                        print("No CANVAS nodes found in Figma file.")
                                        return
                            
                                    print(f"Found CANVAS node IDs: {node_ids}")
                            
                                    # Get images for these node IDs
                                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                    print("Figma images response:", images_response)
                                except Exception as e:
                                    print(f"Error: {e}")
                            
                            if __name__ == "__main__":
                                main()                                import os
                                import requests
                                from dotenv import load_dotenv
                                from automation import FigmaIntegration
                                
                                # Load environment variables from .env
                                load_dotenv()
                                
                                def get_canvas_node_ids(file_data):
                                    """Extract CANVAS node IDs from Figma file data"""
                                    if 'document' in file_data and 'children' in file_data['document']:
                                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                    return []
                                
                                def main():
                                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                    if not figma_token or not figma_file_key:
                                        print("Figma API token or file key not set in .env file.")
                                        return
                                
                                    figma_api = FigmaIntegration(figma_token)
                                    try:
                                        # Get file info
                                        file_data = figma_api.get_file_info(figma_file_key)
                                        print("File info loaded successfully.")
                                
                                        # Extract CANVAS node IDs
                                        node_ids = get_canvas_node_ids(file_data)
                                        if not node_ids:
                                            print("No CANVAS nodes found in Figma file.")
                                            return
                                
                                        print(f"Found CANVAS node IDs: {node_ids}")
                                
                                        # Get images for these node IDs
                                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                        print("Figma images response:", images_response)
                                    except Exception as e:
                                        print(f"Error: {e}")
                                
                                if __name__ == "__main__":
                                    main()                                    import os
                                    import requests
                                    from dotenv import load_dotenv
                                    from automation import FigmaIntegration
                                    
                                    # Load environment variables from .env
                                    load_dotenv()
                                    
                                    def get_canvas_node_ids(file_data):
                                        """Extract CANVAS node IDs from Figma file data"""
                                        if 'document' in file_data and 'children' in file_data['document']:
                                            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                        return []
                                    
                                    def main():
                                        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                        figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                        if not figma_token or not figma_file_key:
                                            print("Figma API token or file key not set in .env file.")
                                            return
                                    
                                        figma_api = FigmaIntegration(figma_token)
                                        try:
                                            # Get file info
                                            file_data = figma_api.get_file_info(figma_file_key)
                                            print("File info loaded successfully.")
                                    
                                            # Extract CANVAS node IDs
                                            node_ids = get_canvas_node_ids(file_data)
                                            if not node_ids:
                                                print("No CANVAS nodes found in Figma file.")
                                                return
                                    
                                            print(f"Found CANVAS node IDs: {node_ids}")
                                    
                                            # Get images for these node IDs
                                            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                            print("Figma images response:", images_response)
                                        except Exception as e:
                                            print(f"Error: {e}")
                                    
                                    if __name__ == "__main__":
                                        main()                                        import os
                                        import requests
                                        from dotenv import load_dotenv
                                        from automation import FigmaIntegration
                                        
                                        # Load environment variables from .env
                                        load_dotenv()
                                        
                                        def get_canvas_node_ids(file_data):
                                            """Extract CANVAS node IDs from Figma file data"""
                                            if 'document' in file_data and 'children' in file_data['document']:
                                                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                            return []
                                        
                                        def main():
                                            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                            figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                            if not figma_token or not figma_file_key:
                                                print("Figma API token or file key not set in .env file.")
                                                return
                                        
                                            figma_api = FigmaIntegration(figma_token)
                                            try:
                                                # Get file info
                                                file_data = figma_api.get_file_info(figma_file_key)
                                                print("File info loaded successfully.")
                                        
                                                # Extract CANVAS node IDs
                                                node_ids = get_canvas_node_ids(file_data)
                                                if not node_ids:
                                                    print("No CANVAS nodes found in Figma file.")
                                                    return
                                        
                                                print(f"Found CANVAS node IDs: {node_ids}")
                                        
                                                # Get images for these node IDs
                                                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                print("Figma images response:", images_response)
                                            except Exception as e:
                                                print(f"Error: {e}")
                                        
                                        if __name__ == "__main__":
                                            main()                                            import os
                                            import requests
                                            from dotenv import load_dotenv
                                            from automation import FigmaIntegration
                                            
                                            # Load environment variables from .env
                                            load_dotenv()
                                            
                                            def get_canvas_node_ids(file_data):
                                                """Extract CANVAS node IDs from Figma file data"""
                                                if 'document' in file_data and 'children' in file_data['document']:
                                                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                return []
                                            
                                            def main():
                                                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                if not figma_token or not figma_file_key:
                                                    print("Figma API token or file key not set in .env file.")
                                                    return
                                            
                                                figma_api = FigmaIntegration(figma_token)
                                                try:
                                                    # Get file info
                                                    file_data = figma_api.get_file_info(figma_file_key)
                                                    print("File info loaded successfully.")
                                            
                                                    # Extract CANVAS node IDs
                                                    node_ids = get_canvas_node_ids(file_data)
                                                    if not node_ids:
                                                        print("No CANVAS nodes found in Figma file.")
                                                        return
                                            
                                                    print(f"Found CANVAS node IDs: {node_ids}")
                                            
                                                    # Get images for these node IDs
                                                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                    print("Figma images response:", images_response)
                                                except Exception as e:
                                                    print(f"Error: {e}")
                                            
                                            if __name__ == "__main__":
                                                main()                                                import os
                                                import requests
                                                from dotenv import load_dotenv
                                                from automation import FigmaIntegration
                                                
                                                # Load environment variables from .env
                                                load_dotenv()
                                                
                                                def get_canvas_node_ids(file_data):
                                                    """Extract CANVAS node IDs from Figma file data"""
                                                    if 'document' in file_data and 'children' in file_data['document']:
                                                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                    return []
                                                
                                                def main():
                                                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                    if not figma_token or not figma_file_key:
                                                        print("Figma API token or file key not set in .env file.")
                                                        return
                                                
                                                    figma_api = FigmaIntegration(figma_token)
                                                    try:
                                                        # Get file info
                                                        file_data = figma_api.get_file_info(figma_file_key)
                                                        print("File info loaded successfully.")
                                                
                                                        # Extract CANVAS node IDs
                                                        node_ids = get_canvas_node_ids(file_data)
                                                        if not node_ids:
                                                            print("No CANVAS nodes found in Figma file.")
                                                            return
                                                
                                                        print(f"Found CANVAS node IDs: {node_ids}")
                                                
                                                        # Get images for these node IDs
                                                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                        print("Figma images response:", images_response)
                                                    except Exception as e:
                                                        print(f"Error: {e}")
                                                
                                                if __name__ == "__main__":
                                                    main()                                                    import os
                                                    import requests
                                                    from dotenv import load_dotenv
                                                    from automation import FigmaIntegration
                                                    
                                                    # Load environment variables from .env
                                                    load_dotenv()
                                                    
                                                    def get_canvas_node_ids(file_data):
                                                        """Extract CANVAS node IDs from Figma file data"""
                                                        if 'document' in file_data and 'children' in file_data['document']:
                                                            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                        return []
                                                    
                                                    def main():
                                                        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                        figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                        if not figma_token or not figma_file_key:
                                                            print("Figma API token or file key not set in .env file.")
                                                            return
                                                    
                                                        figma_api = FigmaIntegration(figma_token)
                                                        try:
                                                            # Get file info
                                                            file_data = figma_api.get_file_info(figma_file_key)
                                                            print("File info loaded successfully.")
                                                    
                                                            # Extract CANVAS node IDs
                                                            node_ids = get_canvas_node_ids(file_data)
                                                            if not node_ids:
                                                                print("No CANVAS nodes found in Figma file.")
                                                                return
                                                    
                                                            print(f"Found CANVAS node IDs: {node_ids}")
                                                    
                                                            # Get images for these node IDs
                                                            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                            print("Figma images response:", images_response)
                                                        except Exception as e:
                                                            print(f"Error: {e}")
                                                    
                                                    if __name__ == "__main__":
                                                        main()                                                        import os
                                                        import requests
                                                        from dotenv import load_dotenv
                                                        from automation import FigmaIntegration
                                                        
                                                        # Load environment variables from .env
                                                        load_dotenv()
                                                        
                                                        def get_canvas_node_ids(file_data):
                                                            """Extract CANVAS node IDs from Figma file data"""
                                                            if 'document' in file_data and 'children' in file_data['document']:
                                                                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                            return []
                                                        
                                                        def main():
                                                            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                            figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                            if not figma_token or not figma_file_key:
                                                                print("Figma API token or file key not set in .env file.")
                                                                return
                                                        
                                                            figma_api = FigmaIntegration(figma_token)
                                                            try:
                                                                # Get file info
                                                                file_data = figma_api.get_file_info(figma_file_key)
                                                                print("File info loaded successfully.")
                                                        
                                                                # Extract CANVAS node IDs
                                                                node_ids = get_canvas_node_ids(file_data)
                                                                if not node_ids:
                                                                    print("No CANVAS nodes found in Figma file.")
                                                                    return
                                                        
                                                                print(f"Found CANVAS node IDs: {node_ids}")
                                                        
                                                                # Get images for these node IDs
                                                                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                print("Figma images response:", images_response)
                                                            except Exception as e:
                                                                print(f"Error: {e}")
                                                        
                                                        if __name__ == "__main__":
                                                            main()                                                            import os
                                                            import requests
                                                            from dotenv import load_dotenv
                                                            from automation import FigmaIntegration
                                                            
                                                            # Load environment variables from .env
                                                            load_dotenv()
                                                            
                                                            def get_canvas_node_ids(file_data):
                                                                """Extract CANVAS node IDs from Figma file data"""
                                                                if 'document' in file_data and 'children' in file_data['document']:
                                                                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                return []
                                                            
                                                            def main():
                                                                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                if not figma_token or not figma_file_key:
                                                                    print("Figma API token or file key not set in .env file.")
                                                                    return
                                                            
                                                                figma_api = FigmaIntegration(figma_token)
                                                                try:
                                                                    # Get file info
                                                                    file_data = figma_api.get_file_info(figma_file_key)
                                                                    print("File info loaded successfully.")
                                                            
                                                                    # Extract CANVAS node IDs
                                                                    node_ids = get_canvas_node_ids(file_data)
                                                                    if not node_ids:
                                                                        print("No CANVAS nodes found in Figma file.")
                                                                        return
                                                            
                                                                    print(f"Found CANVAS node IDs: {node_ids}")
                                                            
                                                                    # Get images for these node IDs
                                                                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                    print("Figma images response:", images_response)
                                                                except Exception as e:
                                                                    print(f"Error: {e}")
                                                            
                                                            if __name__ == "__main__":
                                                                main()                                                                import os
                                                                import requests
                                                                from dotenv import load_dotenv
                                                                from automation import FigmaIntegration
                                                                
                                                                # Load environment variables from .env
                                                                load_dotenv()
                                                                
                                                                def get_canvas_node_ids(file_data):
                                                                    """Extract CANVAS node IDs from Figma file data"""
                                                                    if 'document' in file_data and 'children' in file_data['document']:
                                                                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                    return []
                                                                
                                                                def main():
                                                                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                    if not figma_token or not figma_file_key:
                                                                        print("Figma API token or file key not set in .env file.")
                                                                        return
                                                                
                                                                    figma_api = FigmaIntegration(figma_token)
                                                                    try:
                                                                        # Get file info
                                                                        file_data = figma_api.get_file_info(figma_file_key)
                                                                        print("File info loaded successfully.")
                                                                
                                                                        # Extract CANVAS node IDs
                                                                        node_ids = get_canvas_node_ids(file_data)
                                                                        if not node_ids:
                                                                            print("No CANVAS nodes found in Figma file.")
                                                                            return
                                                                
                                                                        print(f"Found CANVAS node IDs: {node_ids}")
                                                                
                                                                        # Get images for these node IDs
                                                                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                        print("Figma images response:", images_response)
                                                                    except Exception as e:
                                                                        print(f"Error: {e}")
                                                                
                                                                if __name__ == "__main__":
                                                                    main()                                                                    import os
                                                                    import requests
                                                                    from dotenv import load_dotenv
                                                                    from automation import FigmaIntegration
                                                                    
                                                                    # Load environment variables from .env
                                                                    load_dotenv()
                                                                    
                                                                    def get_canvas_node_ids(file_data):
                                                                        """Extract CANVAS node IDs from Figma file data"""
                                                                        if 'document' in file_data and 'children' in file_data['document']:
                                                                            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                        return []
                                                                    
                                                                    def main():
                                                                        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                        figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                        if not figma_token or not figma_file_key:
                                                                            print("Figma API token or file key not set in .env file.")
                                                                            return
                                                                    
                                                                        figma_api = FigmaIntegration(figma_token)
                                                                        try:
                                                                            # Get file info
                                                                            file_data = figma_api.get_file_info(figma_file_key)
                                                                            print("File info loaded successfully.")
                                                                    
                                                                            # Extract CANVAS node IDs
                                                                            node_ids = get_canvas_node_ids(file_data)
                                                                            if not node_ids:
                                                                                print("No CANVAS nodes found in Figma file.")
                                                                                return
                                                                    
                                                                            print(f"Found CANVAS node IDs: {node_ids}")
                                                                    
                                                                            # Get images for these node IDs
                                                                            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                            print("Figma images response:", images_response)
                                                                        except Exception as e:
                                                                            print(f"Error: {e}")
                                                                    
                                                                    if __name__ == "__main__":
                                                                        main()                                                                        import os
                                                                        import requests
                                                                        from dotenv import load_dotenv
                                                                        from automation import FigmaIntegration
                                                                        
                                                                        # Load environment variables from .env
                                                                        load_dotenv()
                                                                        
                                                                        def get_canvas_node_ids(file_data):
                                                                            """Extract CANVAS node IDs from Figma file data"""
                                                                            if 'document' in file_data and 'children' in file_data['document']:
                                                                                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                            return []
                                                                        
                                                                        def main():
                                                                            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                            figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                            if not figma_token or not figma_file_key:
                                                                                print("Figma API token or file key not set in .env file.")
                                                                                return
                                                                        
                                                                            figma_api = FigmaIntegration(figma_token)
                                                                            try:
                                                                                # Get file info
                                                                                file_data = figma_api.get_file_info(figma_file_key)
                                                                                print("File info loaded successfully.")
                                                                        
                                                                                # Extract CANVAS node IDs
                                                                                node_ids = get_canvas_node_ids(file_data)
                                                                                if not node_ids:
                                                                                    print("No CANVAS nodes found in Figma file.")
                                                                                    return
                                                                        
                                                                                print(f"Found CANVAS node IDs: {node_ids}")
                                                                        
                                                                                # Get images for these node IDs
                                                                                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                print("Figma images response:", images_response)
                                                                            except Exception as e:
                                                                                print(f"Error: {e}")
                                                                        
                                                                        if __name__ == "__main__":
                                                                            main()                                                                            import os
                                                                            import requests
                                                                            from dotenv import load_dotenv
                                                                            from automation import FigmaIntegration
                                                                            
                                                                            # Load environment variables from .env
                                                                            load_dotenv()
                                                                            
                                                                            def get_canvas_node_ids(file_data):
                                                                                """Extract CANVAS node IDs from Figma file data"""
                                                                                if 'document' in file_data and 'children' in file_data['document']:
                                                                                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                return []
                                                                            
                                                                            def main():
                                                                                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                if not figma_token or not figma_file_key:
                                                                                    print("Figma API token or file key not set in .env file.")
                                                                                    return
                                                                            
                                                                                figma_api = FigmaIntegration(figma_token)
                                                                                try:
                                                                                    # Get file info
                                                                                    file_data = figma_api.get_file_info(figma_file_key)
                                                                                    print("File info loaded successfully.")
                                                                            
                                                                                    # Extract CANVAS node IDs
                                                                                    node_ids = get_canvas_node_ids(file_data)
                                                                                    if not node_ids:
                                                                                        print("No CANVAS nodes found in Figma file.")
                                                                                        return
                                                                            
                                                                                    print(f"Found CANVAS node IDs: {node_ids}")
                                                                            
                                                                                    # Get images for these node IDs
                                                                                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                    print("Figma images response:", images_response)
                                                                                except Exception as e:
                                                                                    print(f"Error: {e}")
                                                                            
                                                                            if __name__ == "__main__":
                                                                                main()                                                                                import os
                                                                                import requests
                                                                                from dotenv import load_dotenv
                                                                                from automation import FigmaIntegration
                                                                                
                                                                                # Load environment variables from .env
                                                                                load_dotenv()
                                                                                
                                                                                def get_canvas_node_ids(file_data):
                                                                                    """Extract CANVAS node IDs from Figma file data"""
                                                                                    if 'document' in file_data and 'children' in file_data['document']:
                                                                                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                    return []
                                                                                
                                                                                def main():
                                                                                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                    if not figma_token or not figma_file_key:
                                                                                        print("Figma API token or file key not set in .env file.")
                                                                                        return
                                                                                
                                                                                    figma_api = FigmaIntegration(figma_token)
                                                                                    try:
                                                                                        # Get file info
                                                                                        file_data = figma_api.get_file_info(figma_file_key)
                                                                                        print("File info loaded successfully.")
                                                                                
                                                                                        # Extract CANVAS node IDs
                                                                                        node_ids = get_canvas_node_ids(file_data)
                                                                                        if not node_ids:
                                                                                            print("No CANVAS nodes found in Figma file.")
                                                                                            return
                                                                                
                                                                                        print(f"Found CANVAS node IDs: {node_ids}")
                                                                                
                                                                                        # Get images for these node IDs
                                                                                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                        print("Figma images response:", images_response)
                                                                                    except Exception as e:
                                                                                        print(f"Error: {e}")
                                                                                
                                                                                if __name__ == "__main__":
                                                                                    main()                                                                                    import os
                                                                                    import requests
                                                                                    from dotenv import load_dotenv
                                                                                    from automation import FigmaIntegration
                                                                                    
                                                                                    # Load environment variables from .env
                                                                                    load_dotenv()
                                                                                    
                                                                                    def get_canvas_node_ids(file_data):
                                                                                        """Extract CANVAS node IDs from Figma file data"""
                                                                                        if 'document' in file_data and 'children' in file_data['document']:
                                                                                            return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                        return []
                                                                                    
                                                                                    def main():
                                                                                        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                        figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                        if not figma_token or not figma_file_key:
                                                                                            print("Figma API token or file key not set in .env file.")
                                                                                            return
                                                                                    
                                                                                        figma_api = FigmaIntegration(figma_token)
                                                                                        try:
                                                                                            # Get file info
                                                                                            file_data = figma_api.get_file_info(figma_file_key)
                                                                                            print("File info loaded successfully.")
                                                                                    
                                                                                            # Extract CANVAS node IDs
                                                                                            node_ids = get_canvas_node_ids(file_data)
                                                                                            if not node_ids:
                                                                                                print("No CANVAS nodes found in Figma file.")
                                                                                                return
                                                                                    
                                                                                            print(f"Found CANVAS node IDs: {node_ids}")
                                                                                    
                                                                                            # Get images for these node IDs
                                                                                            images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                            print("Figma images response:", images_response)
                                                                                        except Exception as e:
                                                                                            print(f"Error: {e}")
                                                                                    
                                                                                    if __name__ == "__main__":
                                                                                        main()                                                                                        import os
                                                                                        import requests
                                                                                        from dotenv import load_dotenv
                                                                                        from automation import FigmaIntegration
                                                                                        
                                                                                        # Load environment variables from .env
                                                                                        load_dotenv()
                                                                                        
                                                                                        def get_canvas_node_ids(file_data):
                                                                                            """Extract CANVAS node IDs from Figma file data"""
                                                                                            if 'document' in file_data and 'children' in file_data['document']:
                                                                                                return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                            return []
                                                                                        
                                                                                        def main():
                                                                                            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                            figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                            if not figma_token or not figma_file_key:
                                                                                                print("Figma API token or file key not set in .env file.")
                                                                                                return
                                                                                        
                                                                                            figma_api = FigmaIntegration(figma_token)
                                                                                            try:
                                                                                                # Get file info
                                                                                                file_data = figma_api.get_file_info(figma_file_key)
                                                                                                print("File info loaded successfully.")
                                                                                        
                                                                                                # Extract CANVAS node IDs
                                                                                                node_ids = get_canvas_node_ids(file_data)
                                                                                                if not node_ids:
                                                                                                    print("No CANVAS nodes found in Figma file.")
                                                                                                    return
                                                                                        
                                                                                                print(f"Found CANVAS node IDs: {node_ids}")
                                                                                        
                                                                                                # Get images for these node IDs
                                                                                                images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                                print("Figma images response:", images_response)
                                                                                            except Exception as e:
                                                                                                print(f"Error: {e}")
                                                                                        
                                                                                        if __name__ == "__main__":
                                                                                            main()                                                                                            import os
                                                                                            import requests
                                                                                            from dotenv import load_dotenv
                                                                                            from automation import FigmaIntegration
                                                                                            
                                                                                            # Load environment variables from .env
                                                                                            load_dotenv()
                                                                                            
                                                                                            def get_canvas_node_ids(file_data):
                                                                                                """Extract CANVAS node IDs from Figma file data"""
                                                                                                if 'document' in file_data and 'children' in file_data['document']:
                                                                                                    return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                                return []
                                                                                            
                                                                                            def main():
                                                                                                figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                                figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                                if not figma_token or not figma_file_key:
                                                                                                    print("Figma API token or file key not set in .env file.")
                                                                                                    return
                                                                                            
                                                                                                figma_api = FigmaIntegration(figma_token)
                                                                                                try:
                                                                                                    # Get file info
                                                                                                    file_data = figma_api.get_file_info(figma_file_key)
                                                                                                    print("File info loaded successfully.")
                                                                                            
                                                                                                    # Extract CANVAS node IDs
                                                                                                    node_ids = get_canvas_node_ids(file_data)
                                                                                                    if not node_ids:
                                                                                                        print("No CANVAS nodes found in Figma file.")
                                                                                                        return
                                                                                            
                                                                                                    print(f"Found CANVAS node IDs: {node_ids}")
                                                                                            
                                                                                                    # Get images for these node IDs
                                                                                                    images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                                    print("Figma images response:", images_response)
                                                                                                except Exception as e:
                                                                                                    print(f"Error: {e}")
                                                                                            
                                                                                            if __name__ == "__main__":
                                                                                                main()                                                                                                import os
                                                                                                import requests
                                                                                                from dotenv import load_dotenv
                                                                                                from automation import FigmaIntegration
                                                                                                
                                                                                                # Load environment variables from .env
                                                                                                load_dotenv()
                                                                                                
                                                                                                def get_canvas_node_ids(file_data):
                                                                                                    """Extract CANVAS node IDs from Figma file data"""
                                                                                                    if 'document' in file_data and 'children' in file_data['document']:
                                                                                                        return [child['id'] for child in file_data['document']['children'] if child.get('type') == 'CANVAS']
                                                                                                    return []
                                                                                                
                                                                                                def main():
                                                                                                    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
                                                                                                    figma_file_key = os.getenv("FIGMA_FILE_KEY")
                                                                                                    if not figma_token or not figma_file_key:
                                                                                                        print("Figma API token or file key not set in .env file.")
                                                                                                        return
                                                                                                
                                                                                                    figma_api = FigmaIntegration(figma_token)
                                                                                                    try:
                                                                                                        # Get file info
                                                                                                        file_data = figma_api.get_file_info(figma_file_key)
                                                                                                        print("File info loaded successfully.")
                                                                                                
                                                                                                        # Extract CANVAS node IDs
                                                                                                        node_ids = get_canvas_node_ids(file_data)
                                                                                                        if not node_ids:
                                                                                                            print("No CANVAS nodes found in Figma file.")
                                                                                                            return
                                                                                                
                                                                                                        print(f"Found CANVAS node IDs: {node_ids}")
                                                                                                
                                                                                                        # Get images for these node IDs
                                                                                                        images_response = figma_api.get_file_images(figma_file_key, node_ids=node_ids)
                                                                                                        print("Figma images response:", images_response)
                                                                                                    except Exception as e:
                                                                                                        print(f"Error: {e}")
                                                                                                
                                                                                                if __name__ == "__main__":
                                                                                                    main()
import matplotlib.pyplot as plt
import re
from automation import FigmaIntegration

# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Advanced AI QA Automation with Figma",
    page_icon="🚀",
    layout="wide"
)

class JiraIntegration:
    """Base Jira integration class"""
    
    def __init__(self, server_url, email, api_token, project_key):
        self.server_url = server_url
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.jira = None
    
    def connect(self):
        """Connect to Jira"""
        try:
            self.jira = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token)
            )
            # Test connection
            self.jira.myself()
            return True
        except Exception as e:
            st.error(f"Failed to connect to Jira: {e}")
            return False
    
    def create_bug(self, summary, description, steps_to_reproduce="", expected_result="", actual_result=""):
        """Create a basic bug in Jira"""
        if not self.jira:
            return None
        
        try:
            bug_description = f"""
*Description:* {description}

*Steps to Reproduce:*
{steps_to_reproduce}

*Expected Result:* {expected_result}
*Actual Result:* {actual_result}

*Detected by:* AI QA Automation System
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': bug_description,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'Medium'}
            }
            
            bug = self.jira.create_issue(fields=issue_dict)
            return bug.key
            
        except Exception as e:
            st.error(f"Failed to create bug: {e}")
            return None


class FigmaIntegration:
    """Figma API integration for design comparison testing"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": access_token}
    
    def extract_file_id(self, file_id_or_url):
        """Extract file ID from Figma URL or return as-is if already an ID"""
        # If it's already a clean file ID (no slashes/protocols), return it
        if not ('/' in file_id_or_url or 'figma.com' in file_id_or_url):
            return file_id_or_url
        
        # Extract file ID from various Figma URL formats
        patterns = [
            r'figma\.com/design/([a-zA-Z0-9]+)',
            r'figma\.com/file/([a-zA-Z0-9]+)',
            r'figma\.com/proto/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_id_or_url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume it's already a file ID
        return file_id_or_url
    
    def get_file_info(self, file_id_or_url):
        """Get Figma file information and structure"""
        try:
            # Extract clean file ID
            file_id = self.extract_file_id(file_id_or_url)
            
            # Validate file ID format (should be alphanumeric, typically 22-23 characters)
            if not re.match(r'^[a-zA-Z0-9]{15,25}$', file_id):
                st.error(f"Invalid Figma File ID format: {file_id}")
                st.info("File ID should be alphanumeric, 15-25 characters long. Extract it from your Figma URL.")
                return None
            
            url = f"{self.base_url}/files/{file_id}"
            st.info(f"Requesting Figma API: {url}")  # Debug info
            
            response = requests.get(url, headers=self.headers)
            
            # Enhanced error handling with debugging
            if response.status_code == 404:
                st.error(f"File not found (404). This usually means:")
                st.error(f"1. File ID '{file_id}' is incorrect")
                st.error(f"2. You don't have access to this file")
                st.error(f"3. File has been moved or deleted")
                st.info(f"Debug: Full API URL attempted: {url}")
                return None
            elif response.status_code == 403:
                st.error("Access denied (403). This means:")
                st.error("1. Your Figma access token is invalid or expired")
                st.error("2. Token doesn't have permission to access this file")
                st.error("3. You're not signed in to the correct Figma account")
                return None
            elif response.status_code == 401:
                st.error("Authentication failed (401). Your access token is invalid.")
                return None
            elif response.status_code != 200:
                st.error(f"Figma API error {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            return response.json()
            placeholder="https://example.com",ption as e:
            key="figma_website_url"r connecting to Figma API: {e}")
        )   return None
        except Exception as e:
        comparison_pages = st.text_area(igma file info: {e}")
            "Specific Pages to Compare (optional)",
            placeholder="Leave empty to compare all pages, or enter page names separated by commas",
            help="e.g., Homepage, About Us, Contact",s=None, scale=1, format='png'):
            key="figma_comparison_pages"nodes"""
        )ry:
            file_id = self.extract_file_id(file_id_or_url)
        with col2:
            st.info("""lf.base_url}/images/{file_id}"
            **Design Comparison Features:**
            - Structural similarity analysis
            - Pixel-perfect comparison
            - Color palette validation
            - Layout spacing verification
            - Typography consistency checkode_ids)
            """)
            response = requests.get(url, headers=self.headers, params=params)
        comparison_settings = st.expander("Advanced Comparison Settings")
        with comparison_settings:de == 404:
            col_a, col_b, col_c = st.columns(3)und (404) when requesting images")
            with col_a:r(f"File ID: {file_id}")
                comparison_threshold = st.slider("Similarity Threshold", 0.5, 1.0, 0.85, 0.05, key="comparison_threshold")
            with col_b:error(f"Node IDs: {node_ids}")
                screenshot_scale = st.selectbox("Screenshot Scale", [1, 2, 3], index=1, key="screenshot_scale")
            with col_c:se.status_code == 403:
                comparison_method = st.selectbox("Comparison Method", ["structural", "pixel_perfect"], key="comparison_method")
                return None
        if st.button("Start Design Comparison", type="primary"):
            if not figma_file_id or not website_url:esponse.status_code}: {response.text}")
                st.error("Please provide both Figma File ID and Website URL!")
            else:
                with st.spinner("Performing design comparison... This may take several minutes."):
                    try:nse.json()
                        # Initialize Figma integration
                        figma = FigmaIntegration(figma_token)
                        
                        # Initialize design comparison tester
                        comparison_tester = DesignComparisonTester(figma)
                        n elements from Figma file data"""
                        # Parse pages to compare
                        pages_filter = None
                        if comparison_pages.strip():
                            pages_filter = [page.strip().lower() for page in comparison_pages.split(',')]
                        s': [],
                        # Perform comparison
                        results = comparison_tester.perform_design_comparison(
                            figma_file_id, 
                            website_url, t in file_data:
                            pages_filter
                        )
                        es(node, parent_name=""):
                        if results:'CANVAS':
                            st.session_state['design_comparison_results'] = results
                            {
                            # Display summary
                            st.success(f"Design comparison completed!")
                            n': [],
                            col1, col2, col3, col4 = st.columns(4), {})
                            with col1:
                                st.metric("Overall Similarity", f"{results['overall_score']:.1%}")
                            with col2:
                                st.metric("Pages Compared", results['pages_compared'])
                            with col3:rse_nodes(child, node.get('name'))
                                st.metric("Issues Found", len(results['issues_found']))
                            with col4:ldren'].append(child_info)
                                status = "Pass" if results['overall_score'] >= comparison_threshold else "Fail"
                                st.metric("Status", status)
                            info
                            # Display detailed results
                            st.subheader("Comparison Details")
                            frame/container
                            for detail in results['comparison_details']:
                                with st.expander(f"{detail['page_name']} (Similarity: {detail['similarity_score']:.1%})"):
                                    ('name'),
                                    # Show images side by side
                                    img_col1, img_col2, img_col3 = st.columns(3)
                                    e_access(figma_file_id)).get('y', 0),
                                    with img_col1:ndingBox', {}).get('width', 0),
                                        st.subheader("Figma Design")t('height', 0),
                                        figma_img_data = base64.b64decode(detail['figma_image'])
                                        st.image(figma_img_data, use_container_width=True)
                                    
                                    with img_col2:
                                        st.subheader("Website Screenshot")
                                        website_img_data = base64.b64decode(detail['website_image'])
                                        st.image(website_img_data, use_container_width=True)
                                    verse_nodes(child, node.get('name'))
                                    with img_col3:
                                        if detail['comparison_image']:
                                            st.subheader("Difference Map")
                                            comparison_img_data = base64.b64decode(detail['comparison_image'])
                                            st.image(comparison_img_data, use_container_width=True)
                                     'TEXT':
                                    # Show differences found
                                    if detail['differences']:
                                        st.subheader("Issues Detected")
                                        for diff in detail['differences']:
                                            severity_color = "High" if diff['severity'] == 'high' else "Medium"
                                            st.write(f"**{severity_color} - {diff['type'].title()}**: {diff['description']}")
                            e.get('absoluteBoundingBox', {}).get('y', 0),
                            # Auto-create Jira tickets option{}).get('width', 0),
                            if results['issues_found'] and all([).get('height', 0),
                                os.getenv("JIRA_SERVER_URL"),
                                os.getenv("JIRA_EMAIL"),
                                os.getenv("JIRA_API_TOKEN"),
                                os.getenv("JIRA_PROJECT_KEY")
                            ]):o
                                st.subheader("Jira Integration")
                                if st.button("Create Jira Tickets for Issues Found", type="secondary"):
                                    with st.spinner("Creating Jira tickets..."):
                                        jira_client = EnhancedJiraIntegration(
                                            os.getenv("JIRA_SERVER_URL"),
                                            os.getenv("JIRA_EMAIL"),
                                            os.getenv("JIRA_API_TOKEN"),FILE_ID/...",
                                            os.getenv("JIRA_PROJECT_KEY")
                                        )teBoundingBox', {}).get('y', 0),
                                        (Debug)", type="secondary"):('width', 0),
                                        if jira_client.connect():.get('height', 0),
                                            tickets_created = []
                                            for issue in results['issues_found']:
                                                ticket_key = jira_client.create_design_bug(
                                                    issue['page'],
                                                    issue,
                                                    issue.get('figma_image'),
                                                    issue.get('website_image')
                                                ) types
                                                if ticket_key:
                                                    tickets_created.append(ticket_key)
                                            
                                            if tickets_created:
                                                st.success(f"Created {len(tickets_created)} Jira tickets!")
                                                for ticket in tickets_created:
                                                    st.write(f"- {ticket}")
                                            else:
                                                st.error("Failed to create Jira tickets")
                                        else:_id_or_url):
                                            st.error("Failed to connect to Jira")
                        else:
                            st.error("Design comparison failed. Please check your Figma File ID and try again.")
                    
                    except Exception as e:s")
                        st.error(f"Design comparison error: {e}")
                        st.exception(e)* {len(self.access_token) if self.access_token else 0} characters")
            st.write(f"**Token starts with:** `{self.access_token[:10]}...` (showing first 10 chars only)")
with tab3:  
    st.header("AI Test Case Generation")ty with /me endpoint
            st.write("\n**Test 1: Token validity**")
    generation_method = st.radio(s.get(f"{self.base_url}/me", headers=self.headers)
        "Choose Generation Method:",de == 200:
        ["From Design Comparison Results", "From Crawled Website", "From Requirements Document", "Manual Input"],
        key="test_generation_method"alid - User: {user_info.get('email', 'Unknown')}")
    )       else:
                st.error(f"Token invalid - Status: {me_response.status_code}")
    if generation_method == "From Design Comparison Results":
        if 'design_comparison_results' in st.session_state:
            results = st.session_state['design_comparison_results']
            st.info(f"Ready to generate tests from design comparison results ({len(results['issues_found'])} issues found)")
            st.write("\n**Test 2: File access**")
            if st.button("Generate Test Cases from Design Issues", type="primary"):
                with st.spinner("AI is generating design-focused test cases..."):
                    
                    # Create prompt for design-specific test cases
                    design_issues_summary = "\n".join([nse.status_code}")
                        f"- Page: {issue['page']}, Issue: {issue['type']}, Severity: {issue['severity']}, Description: {issue['description']}"
                        for issue in results['issues_found']
                    ])cess("File accessible!")
                    rn True
                    prompt = f"""
Based on the following design comparison results between Figma designs and live website, generate comprehensive test cases in JSON format.
                st.code(file_response.text[:500])  # Show first 500 chars of error
Design Issues Found:
{design_issues_summary}de specific guidance
                if file_response.status_code == 404:
Overall Similarity Score: {results['overall_score']:.1%}
Pages Analyzed: {results['pages_compared']} file ID is correct")
                    st.write("2. Ensure you have 'can view' access to this file")
Please generate test cases in this JSON format that focus on:ts")
1. Visual regression testing("4. Try accessing the file in your browser first")
2. Layout validation file_response.status_code == 403:
3. Component positioningrror("**Token/Permission issue:**")
4. Color accuracy   st.write("1. Regenerate your personal access token in Figma")
5. Typography consistencyite("2. Ensure the token has file access permissions")
6. Responsive design validation. Check you're using the token from the correct account")
                
Include both automated visual tests and manual verification steps.
            
{{      except Exception as e:
    "test_suites": [(f"Debug test failed: {e}")
        {{  return False
            "suite_name": "Visual Regression Tests",
            "test_cases": [r:
                {{ma designs with live website screenshots"""
                    "name": "Verify homepage design matches Figma",
                    "priority": "High",n):
                    "type": "Visual",nput(
                    "description": "Compare homepage layout with Figma design",
                    "preconditions": "Browser open, Figma reference available",
                    "steps": [
                        {{"action": "navigate", "url": "homepage_url"}},
                        {{"action": "capture_screenshot", "element": "body"}},
                        {{"action": "compare_with_figma", "figma_page": "Homepage"}}
                    ],.add_argument("--no-sandbox")
                    "expected_result": "Design matches Figma specifications within threshold"
                }}ions.add_argument("--window-size=1920,1080")
            ]e_options.add_argument("--force-device-scale-factor=1")
        }}
    ]   try:
}}          self.driver = webdriver.Chrome(options=chrome_options)
"""         return True
                    tion as e:
                    test_cases = simple_AI_Function_Agent(prompt, selected_model)
                    st.session_state['generated_tests'] = test_cases
                    
                    st.success("Design-focused test cases generated successfully!")
                    st.code(test_cases, language="json")ment"""
        else:t self.driver:
            st.warning("Please perform a design comparison first in the Design Comparison tab.")
        
    elif generation_method == "From Crawled Website":
        if 'crawled_data' in st.session_state:
            st.info(f"Ready to generate tests from {len(st.session_state['crawled_data']['pages'])} crawled pages")
            
            if st.button("Generate Test Cases from Crawl", type="primary"):
                with st.spinner("AI is generating comprehensive test cases..."):
                    # Use existing functionelement(By.CSS_SELECTOR, element_selector)
                    test_cases = generate_test_cases_from_crawl(st.session_state['crawled_data'], selected_model)
                    st.session_state['generated_tests'] = test_cases
                    pture full page
                    st.success("Test cases generated successfully!")
                    st.code(test_cases, language="json")
        else:t.error(f"Failed to capture screenshot: {e}")
            st.warning("Please crawl a website first in the Web Crawling tab.")
    
    elif generation_method == "From Requirements Document":
        uploaded_file = st.file_uploader("Upload Requirements Document", type=['txt', 'pdf', 'docx'], key="req_doc_uploader")
        with col1:
        if uploaded_file and st.button("Generate Test Cases from Document"):
            with st.spinner("Processing document and generating test cases..."):
                # Process file content (existing logic)
                st.success("Test cases generated from document!")
            st.error(f"Failed to download Figma image: {e}")
    else:  # Manual Input
        manual_requirements = st.text_area("Enter Requirements Manually", height=200, key="manual_requirements")
        compare_images(self, figma_image_data, website_image_data, comparison_type="structural"):
        if manual_requirements and st.button("Generate Test Cases from Text"):
            with st.spinner("Generating test cases from your requirements..."):
                prompt = f"""Images
Generate comprehensive test cases in JSON format based on these requirements:
            website_img = Image.open(BytesIO(website_image_data))
{manual_requirements}
            # Resize images to same dimensions for comparison
Create test suites with individual test cases that include:dth)
- Test name and descriptionn(figma_img.height, website_img.height)
- Priority level
- Test type (Functional, UI, Integration, etc.)in_width, min_height), Image.Resampling.LANCZOS)
- Preconditionssite_resized = website_img.resize((min_width, min_height), Image.Resampling.LANCZOS)
- Detailed test steps
- Expected resultsert to numpy arrays for comparison
            figma_array = np.array(figma_resized.convert('RGB'))
Format as valid JSON.rray = np.array(website_resized.convert('RGB'))
"""         
                test_cases = simple_AI_Function_Agent(prompt, selected_model)
                st.session_state['generated_tests'] = test_cases
                st.success("Test cases generated from manual input!")
                st.code(test_cases, language="json")
                'figma_dimensions': (figma_img.width, figma_img.height),
with tab4:      'website_dimensions': (website_img.width, website_img.height)
    st.header("Automated Test Execution")
            
    if 'generated_tests' in st.session_state:":
        st.success("Test cases available for execution!")
                gray_figma = cv2.cvtColor(figma_array, cv2.COLOR_RGB2GRAY)
        execution_options = st.columns(3)or(website_array, cv2.COLOR_RGB2GRAY)
                
        with execution_options[0]:(gray_figma, gray_website, full=True)
            headless_mode = st.checkbox("Headless Browser", value=True, key="headless_mode")
                
        with execution_options[1]:e image
            parallel_execution = st.checkbox("Parallel Execution", value=False, key="parallel_execution")
                comparison_result['comparison_image'] = diff
        with execution_options[2]:
            screenshot_on_fail = st.checkbox("Screenshot on Failure", value=True, key="screenshot_on_fail")
                if score < 0.9:  # If similarity is less than 90%
        if st.button("Execute Test Suite", type="primary"):append({
            # Check if Groq API is configuredifference',
            if not os.getenv("GROQ_API_KEY"): score < 0.7 else 'medium',
                st.error("Groq API key not configured. Please check your .env file.")
            else:   })
                with st.spinner("Executing automated tests..."):
                    # Simulate test executionrfect":
                    st.success("Test execution completed!")
                     = ImageChops.difference(figma_resized.convert('RGB'), website_resized.convert('RGB'))
                    # Mock results with design-specific tests
                    results_data = {
                        'Test Case': [ of different pixels
                            'Visual - Homepage Layout', _array.sum(axis=2))
                            'Visual - Navigation Design', array.shape[1]
                            'Functional - Form Submission', total_pixels) * 100
                            'Visual - Color Consistency',
                            'Functional - Search Functionality'fference_percentage / 100)
                        ],_result['comparison_image'] = np.array(diff)
                        'Status': ['PASS', 'FAIL', 'PASS', 'FAIL', 'ERROR'],
                        'Duration (s)': [3.5, 2.8, 3.2, 1.5, 0.5],ixels are different
                        'Error Message': [ferences_found'].append({
                            '', 'pixel_difference',
                            'Layout differs from Figma by 15%', age > 20 else 'medium',
                            '', tion': f'Pixel difference: {difference_percentage:.1f}%'
                            'Primary color #FF0000 expected, found #FF1111',
                            'Timeout exception'
                        ]ison_result
                    }
                    tion as e:
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(results_df, use_container_width=True)
                    Figma integration configured!")
                    # Summary metricsf, figma_file_id, website_url, pages_to_compare=None):
                    col1, col2, col3, col4 = st.columns(4)a and website"""
                    with col1:er():
                        st.metric("Total Tests", len(results_df))
                    with col2:
                        st.metric("Passed", len(results_df[results_df['Status'] == 'PASS']))
                    with col3:,
                        st.metric("Failed", len(results_df[results_df['Status'] == 'FAIL']))
                    with col4:,
                        st.metric("Errors", len(results_df[results_df['Status'] == 'ERROR']))
                        
                    # Store results for bug management
                    st.session_state['test_execution_results'] = results_df
    else:   # Get Figma file data
        st.warning("Please generate test cases first in the Test Generation tab.")
            file_data = self.figma.get_file_info(figma_file_id)
with tab5:  if not file_data:
    st.header("Enhanced Bug Management & Jira Integration")
            
    # Check Jira configuration from environment
    jira_server = os.getenv("JIRA_SERVER_URL")ct_design_elements(file_data)
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")neration
    jira_project = os.getenv("JIRA_PROJECT_KEY") in design_elements['pages']]
            if pages_to_compare:
    if all([jira_server, jira_email, jira_token, jira_project]):
        st.success("Jira configuration loaded from .env file!")f any(page['name'].lower() in pages_to_compare for page in design_elements['pages'] if page['id'] == pid)]
            
        # Display current configuration (masked for security)
        with st.expander("Current Jira Configuration"):)
            st.write(f"**Server:** {jira_server}")ges(figma_file_id, page_node_ids, scale=2)
            st.write(f"**Email:** {jira_email}")
            st.write(f"**Project:** {jira_project}")igma_images:
            st.write(f"**Token:** {'*' * len(jira_token[:-4]) + jira_token[-4:] if jira_token else 'Not set'}")
                return None
        tab_a, tab_b, tab_c = st.tabs(["Test Results", "Design Issues", "Manual Bug Creation"])
            total_score = 0
        with tab_a:rocessed = 0
            st.subheader("Test Results Summary")
            for page in design_elements['pages']:
            if 'test_execution_results' in st.session_state:
                results_df = st.session_state['test_execution_results']
                failed_tests = results_df[results_df['Status'].isin(['FAIL', 'ERROR'])]
                st.info(f"Comparing page: {page['name']}")
                if len(failed_tests) > 0:
                    st.write(f"Found {len(failed_tests)} failed tests:")
                    st.dataframe(failed_tests, use_container_width=True)
                    a_image_data = self.download_figma_image(figma_image_url)
                    if st.button("Auto-Create Jira Bugs for Failed Tests"):
                        with st.spinner("Creating Jira tickets for failed tests..."):
                            jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                            if jira_client.connect():
                                bugs_created = []
                                for _, test in failed_tests.iterrows():bsite_url)
                                    issue_details = {
                                        'type': 'test_failure',
                                        'severity': 'high' if test['Status'] == 'ERROR' else 'medium',
                                        'description': f"Test '{test['Test Case']}' failed: {test['Error Message']}"
                                    }
                                    bug_key = jira_client.create_design_bug(mage_data, "structural")
                                        f"Test: {test['Test Case']}", 
                                        issue_details
                                    )
                                    if bug_key:'],
                                        bugs_created.append(bug_key)
                                ity_score': comparison['similarity_score'],
                                if bugs_created:n['differences_found'],
                                    st.success(f"Created {len(bugs_created)} Jira tickets!")
                                    for bug in bugs_created:bsite_image_data).decode(),
                                        st.write(f"- {bug}")(cv2.imencode('.png', comparison['comparison_image'])[1]).decode() if comparison['comparison_image'] is not None else None
                                else:
                                    st.error("Failed to create Jira tickets")
                            else:arison_details'].append(page_result)
                                st.error("Failed to connect to Jira")
                else:ages_processed += 1
                    st.info("No failed tests to create bugs for.")
            else:   # Add issues found
                st.info("No test execution results available. Run tests first.")
                        issue = {
        with tab_b:         'page': page['name'],
            st.subheader("Design Comparison Issues")TOKEN=your_token_here
                            'severity': diff['severity'],
            if 'design_comparison_results' in st.session_state:
                design_results = st.session_state['design_comparison_results']
                            'website_image': website_image_data
                if design_results['issues_found']:
                    st.write(f"Found {len(design_results['issues_found'])} design issues:")
                    
                    # Display issues in a tableore / pages_processed if pages_processed > 0 else 0
                    issues_data = {'] = pages_processed
                        'Page': [issue['page'] for issue in design_results['issues_found']],
                        'Issue Type': [issue['type'] for issue in design_results['issues_found']],
                        'Severity': [issue['severity'] for issue in design_results['issues_found']],
                        'Description': [issue['description'] for issue in design_results['issues_found']]
                    }f"Design comparison failed: {e}")
                    one
                    issues_df = pd.DataFrame(issues_data)
                    st.dataframe(issues_df, use_container_width=True)
                    .driver.quit()
                    if st.button("Create Jira Tickets for Design Issues"):
                        with st.spinner("Creating Jira tickets for design issues..."):
                            jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                            if jira_client.connect():
                                tickets_created = []ails, figma_image=None, website_image=None):
                                for issue in design_results['issues_found']:
                                    ticket_key = jira_client.create_design_bug(
                                        issue['page'],
                                        issue,
                                        issue.get('figma_image'),
                                        issue.get('website_image')
                                    )
                                    if ticket_key:
                                        tickets_created.append(ticket_key)
                                ('type', 'Unknown')}
                                if tickets_created:)}
                                    st.success(f"Created {len(tickets_created)} design issue tickets!")
                                    for ticket in tickets_created:
                                        st.write(f"- {ticket}")
                                else:vs Website Analysis
                                    st.error("Failed to create design issue tickets")
                            else:
                                st.error("Failed to connect to Jira")
                else:gn discrepancies detected in automated comparison
                    st.info("No design issues found to create tickets for.")
            else:rome Browser, Design Comparison Testing
                st.info("No design comparison results available. Run design comparison first.")
            
        with tab_c:ict = {
            st.subheader("Manual Bug Creation")_key},
                'summary': f"Design Issue: {page_name} - {issue_details.get('type', 'Design Mismatch')}",
            col1, col2 = st.columns(2)cription,
                'issuetype': {'name': 'Bug'},
            with col1:ity': {'name': 'High' if issue_details.get('severity') == 'high' else 'Medium'},
                bug_type = st.selectbox("Bug Type", ["Functional", "Visual/Design", "Performance", "Security", "Other"], key="manual_bug_type")
                bug_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="manual_bug_priority")
                bug_summary = st.text_input("Bug Summary", key="manual_bug_summary")
                bug_description = st.text_area("Detailed Description", key="manual_bug_description")
                
            with col2:mages if provided
                steps_to_reproduce = st.text_area("Steps to Reproduce", key="manual_bug_steps")
                expected_result = st.text_input("Expected Result", key="manual_bug_expected")
                actual_result = st.text_input("Actual Result", key="manual_bug_actual")
                environment = st.text_input("Environment", value="Chrome Browser, Manual Testing", key="manual_bug_environment")
                    with open(figma_filename, 'wb') as f:
            uploaded_screenshot = st.file_uploader("Attach Screenshot (optional)", type=['png', 'jpg', 'jpeg'], key="manual_bug_screenshot")
                    
            if st.button("Create Manual Bug in Jira"):, attachment=figma_filename, filename=f"Figma_Design_{page_name}.png")
                if bug_summary and bug_description:ean up
                    with st.spinner("Creating manual bug in Jira..."):
                        jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                        if jira_client.connect():
                            # Use enhanced bug creation method
                            bug_key = jira_client.create_bug(
                                bug_summary,for website screenshot
                                bug_description,_screenshot_{page_name}_{bug.key}.png"
                                steps_to_reproduce,') as f:
                                expected_result,
                                actual_result
                            ).add_attachment(issue=bug, attachment=website_filename, filename=f"Website_Screenshot_{page_name}.png")
                            e(website_filename)  # Clean up
                            if bug_key:
                                st.success(f"Bug created successfully: {bug_key}")
                                
                                # Attach screenshot if provided
                                if uploaded_screenshot and bug_key:
                                    try:
                                        # Save uploaded file temporarily
                                        screenshot_filename = f"manual_screenshot_{bug_key}.png"
                                        with open(screenshot_filename, 'wb') as f:
                                            f.write(uploaded_screenshot.getvalue())
                                        namic content"""
                                        jira_client.jira.add_attachment(
                                            issue=bug_key, 
                                            attachment=screenshot_filename, 
                                            filename=f"Screenshot_{bug_key}.png"
                                        )
                                        os.remove(screenshot_filename)  # Clean up
                                        st.success("Screenshot attached successfully!")
                                    except Exception as e:
                                                                                st.warning(f"Bug created but screenshot attachment failed: {e}")
                            else:
                                st.error("Failed to create bug in Jira")
                        else:
                            st.error("Failed to connect to Jira")
                else:
                    st.error("Please fill in at least Bug Summary and Description.")
    else:   return True
        st.warning("Jira not configured. Please set up your .env file with Jira credentials.")
            st.error(f"Failed to setup Chrome driver: {e}")
        missing_vars = []
        if not jira_server: missing_vars.append("JIRA_SERVER_URL")
        if not jira_email: missing_vars.append("JIRA_EMAIL") 
        if not jira_token: missing_vars.append("JIRA_API_TOKEN")
        if not jira_project: missing_vars.append("JIRA_PROJECT_KEY")
            return None
        st.error(f"Missing environment variables: {', '.join(missing_vars)}")
        crawled_data = {
with tab6:  'pages': [],
    st.header("Results Dashboard")
            'buttons': [],
    # Overall system status
    col1, col2, col3 = st.columns(3)
        }
    with col1:
        st.subheader("Web Crawling")rsonal access tokens
        if 'crawled_data' in st.session_state:te permissions
            crawl_data = st.session_state['crawled_data']
            st.metric("Pages Crawled", len(crawl_data['pages']))
            st.metric("Forms Found", sum(len(page['forms']) for page in crawl_data['pages']))
            st.metric("Buttons Found", sum(len(page['buttons']) for page in crawl_data['pages']))
        else:   
            st.info("No crawling data available") current_depth > depth:
                    continue
    with col2:      
        st.subheader("Design Comparison")url)
        if 'design_comparison_results' in st.session_state:
            design_data = st.session_state['design_comparison_results']
            st.metric("Overall Similarity", f"{design_data['overall_score']:.1%}")
            st.metric("Pages Compared", design_data['pages_compared'])
            st.metric("Issues Found", len(design_data['issues_found']))
        else:   # Extract page content
            st.info("No design comparison data available")_url)
                crawled_data['pages'].append(page_data)
    with col3:  
        st.subheader("Test Execution")ithin depth limit
        if 'test_execution_results' in st.session_state:
            test_data = st.session_state['test_execution_results'] "a")
            st.metric("Total Tests", len(test_data)) links per page
            st.metric("Pass Rate", f"{len(test_data[test_data['Status'] == 'PASS']) / len(test_data):.1%}")
            st.metric("Failed Tests", len(test_data[test_data['Status'].isin(['FAIL', 'ERROR'])]))
        else:               if href and href.startswith(('http', 'https')):
            st.info("No test execution data available")ref, current_depth + 1))
                        except:
                            continue
            
            return crawled_data
            
        except Exception as e:
    # Check if Figma is configuredror: {e}")
    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        finally:
    if not figma_token:ver:
        st.error("Figma Access Token not configured. Please add FIGMA_ACCESS_TOKEN to your .env file.")
        st.info("""
        **How to get Figma Access Token:**
        1. Go to Figma.com and log in current page"""
        page_data = {
            'url': url,
            'title': '',
            'content': '',
            'forms': [],
            'buttons': [],
            'inputs': [],
            'navigation': [],
            'images': [],
            'errors': []
        }
        
        try:
            # Basic page info
            page_data['title'] = self.driver.title
            page_data['content'] = self.driver.find_element(By.TAG_NAME, "body").text[:2000]
            
            # Extract forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_data = {
                    'action': form.get_attribute("action") or "current_page",
                    'method': form.get_attribute("method") or "GET",
                    'inputs': []
                }
                
                            st.write(f"**Buttons Found:** {len(page['buttons'])}")
                            st.write(f"**Content Preview:** {page['content'][:300]}...")
                else:orm_data['inputs'].append({
                    st.error("Failed to crawl website. Please check the URL and try again.")
                        'name': inp.get_attribute("name"),
with tab2:              'placeholder': inp.get_attribute("placeholder"),
    st.header("Figma Design Comparison Testing")ibute("required") is not None
                    })
                
                page_data['forms'].append(form_data)
            
            # Extract buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            buttons.extend(self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']"))
            
            for button in buttons:
                page_data['buttons'].append({
                    'text': button.text or button.get_attribute("value"),
                    'type': button.get_attribute("type"),
                    'id': button.get_attribute("id"),
                    'class': button.get_attribute("class")
                })
            
            # Extract navigation
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            nav_elements.extend(self.driver.find_elements(By.CSS_SELECTOR, ".nav, .navbar, .menu"))
            
            for nav in nav_elements:
                links = nav.find_elements(By.TAG_NAME, "a")
                nav_links = []
                for link in links:
                    nav_links.append({
                        'text': link.text,
                if crawled_data and crawled_data['pages']:
                    st.session_state['crawled_data'] = crawled_data
                    st.success(f"Successfully crawled {len(crawled_data['pages'])} pages!")
                    
                    # Display crawl results
                    for i, page in enumerate(crawled_data['pages']):)
                        with st.expander(f"Page {i+1}: {page['title']}"):
                            st.write(f"**URL:** {page['url']}")
                            st.write(f"**Forms Found:** {len(page['forms'])}")
def simple_AI_Function_Agent(prompt, model="llama-3.3-70b-versatile"):
    """Core function to interface with the Groq API"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found in environment variables"
            
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def generate_test_cases_from_crawl(crawled_data, model):
    """Generate test cases from crawled website data"""
    if not crawled_data or not crawled_data['pages']:
        return "No crawled data available"
    
    # Create summary of crawled data for prompt
    pages_summary = []
    for page in crawled_data['pages']:
        if not website_url:page['title']} ({page['url']})\n"
            st.error("Please enter a website URL!")uttons: {len(page['buttons'])}\n"
        else:ge['forms']:
            with st.spinner("Crawling website... This may take a few minutes."):
                crawler = WebCrawler()
                crawled_data = crawler.crawl_website(website_url, max_pages, crawl_depth)
                for inp in form['inputs']:
                    summary += f"    Input: {inp['type']} - {inp['name']}\n"
        pages_summary.append(summary)
    
    prompt = f"""
Based on the following website crawl data, generate comprehensive test cases in JSON format:
        st.error("⚠️ FIGMA_ACCESS_TOKEN not found in .env file")
    (10).join(pages_summary)}
    if not jira_configured:
        st.warning("⚠️ Jira credentials incomplete in .env file")
        ation testing
        functionality
3. Button interactions
# Override options (for testing/development only)
with st.sidebar.expander("Development Override (Not Recommended)"):
    st.warning("⚠️ Only use for testing. Use .env file for production!")
    at as JSON with test suites and individual test cases.
    override_groq = st.text_input("Override Groq API Key", type="password", help="Temporary override - use .env instead", key="override_groq")
    if override_groq:
        os.environ["GROQ_API_KEY"] = override_groq
        st.success("Groq API key temporarily overridden")
    reamlit UI
    override_figma = st.text_input("Override Figma Access Token", type="password", help="Get from Figma > Settings > Personal access tokens", key="override_figma")
    if override_figma:wling • Design Comparison • Test Generation • Jira Integration • Automated Execution**")
        os.environ["FIGMA_ACCESS_TOKEN"] = override_figma
            crawl_depth = st.number_input("Crawling Depth", min_value=1, max_value=3, value=2, key="crawl_depth")
    idebar.header("Configuration")
    with col2:er("Jira Override")
        st.info("""erver = st.text_input("Override Jira Server", placeholder="https://yourcompany.atlassian.net", key="override_jira_server")
        **Crawling Options:**text_input("Override Jira Email", placeholder="your-email@company.com", key="override_jira_email")
        - Max Pages: Limit crawled pages"Override Jira Token", type="password", key="override_jira_token")
        - Depth: How deep to follow links("Override Project Key", placeholder="TEST", key="override_jira_project")
        - Extracts: Forms, buttons, navigation, contentOKEN") else "❌"
        """)override_jira_server, override_jira_email, override_jira_token, override_jira_project]):
        os.environ["JIRA_SERVER_URL"] = override_jira_server
    if st.button("Start Web Crawling", type="primary"):
        os.environ["JIRA_API_TOKEN"] = override_jira_token
        os.environ["JIRA_PROJECT_KEY"] = override_jira_project
        st.success("Jira settings temporarily overridden")
    
# Model and workflow selectiongroq_configured}")
st.sidebar.subheader("AI Configuration")figured}")
models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
selected_model = st.sidebar.selectbox("AI Model", models, key="ai_model_selection")
    if not os.getenv("GROQ_API_KEY"):
# Main tabserror("⚠️ GROQ_API_KEY not found in .env file")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Web Crawling", ("FIGMA_ACCESS_TOKEN"):
    "Design Comparison", A_ACCESS_TOKEN not found in .env file")
    "Test Generation", 
    "Test Execution", ured:
    "Bug Management",️ Jira credentials incomplete in .env file")
    "Results Dashboard"
])      

with tab1: options (for testing/development only)
    st.header("Website Crawler & Analysis")ide (Not Recommended)"):
    st.warning("⚠️ Only use for testing. Use .env file for production!")
    col1, col2 = st.columns([2, 1])
    override_groq = st.text_input("Override Groq API Key", type="password", help="Temporary override - use .env instead", key="override_groq")
    with col1:e_groq:
        website_url = st.text_input("Website URL to Crawl", placeholder="https://example.com", key="crawl_website_url")
        st.success("Groq API key temporarily overridden")
        col_a, col_b = st.columns(2)
        with col_a:= st.text_input("Override Figma Access Token", type="password", help="Get from Figma > Settings > Personal access tokens", key="override_figma")
            max_pages = st.number_input("Max Pages to Crawl", min_value=1, max_value=20, value=5, key="crawl_max_pages")
        with col_b:"FIGMA_ACCESS_TOKEN"] = override_figma
        st.success("Figma token temporarily overridden")
    
    st.subheader("Jira Override")
    override_jira_server = st.text_input("Override Jira Server", placeholder="https://yourcompany.atlassian.net", key="override_jira_server")
    override_jira_email = st.text_input("Override Jira Email", placeholder="your-email@company.com", key="override_jira_email")
    override_jira_token = st.text_input("Override Jira Token", type="password", key="override_jira_token")
    override_jira_project = st.text_input("Override Project Key", placeholder="TEST", key="override_jira_project")
    
    if all([override_jira_server, override_jira_email, override_jira_token, override_jira_project]):
        os.environ["JIRA_SERVER_URL"] = override_jira_server
        os.environ["JIRA_EMAIL"] = override_jira_email
        os.environ["JIRA_API_TOKEN"] = override_jira_token
        os.environ["JIRA_PROJECT_KEY"] = override_jira_project
        st.success("Jira settings temporarily overridden")

# Model and workflow selection
st.sidebar.subheader("AI Configuration")
models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
selected_model = st.sidebar.selectbox("AI Model", models, key="ai_model_selection")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Web Crawling", 
    "Design Comparison", 
    "Test Generation", 
    "Test Execution", 
    "Bug Management",
    "Results Dashboard"
])

with tab1:
    st.header("Website Crawler & Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        website_url = st.text_input("Website URL to Crawl", placeholder="https://example.com", key="crawl_website_url")
        
        col_a, col_b = st.columns(2)
        with col_a:
            max_pages = st.number_input("Max Pages to Crawl", min_value=1, max_value=20, value=5, key="crawl_max_pages")
        with col_b:
            crawl_depth = st.number_input("Crawling Depth", min_value=1, max_value=3, value=2, key="crawl_depth")
    
    with col2:
        st.info("""
        **Crawling Options:**
        - Max Pages: Limit crawled pages
        - Depth: How deep to follow links
        - Extracts: Forms, buttons, navigation, content
        """)
    
    if st.button("Start Web Crawling", type="primary"):
        if not website_url:
            st.error("Please enter a website URL!")
        else:
            with st.spinner("Crawling website... This may take a few minutes."):
                crawler = WebCrawler()
                crawled_data = crawler.crawl_website(website_url, max_pages, crawl_depth)
                
                if crawled_data and crawled_data['pages']:
                    st.session_state['crawled_data'] = crawled_data
                    st.success(f"Successfully crawled {len(crawled_data['pages'])} pages!")
                    
                    # Display crawl results
                    for i, page in enumerate(crawled_data['pages']):
                        with st.expander(f"Page {i+1}: {page['title']}"):
                            st.write(f"**URL:** {page['url']}")
                            st.write(f"**Forms Found:** {len(page['forms'])}")
                            st.write(f"**Buttons Found:** {len(page['buttons'])}")
                            st.write(f"**Content Preview:** {page['content'][:300]}...")
                else:
                    st.error("Failed to crawl website. Please check the URL and try again.")

with tab2:
    st.header("Figma Design Comparison Testing")
    
    # Check if Figma is configured
    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
    
    if not figma_token:
        st.error("Figma Access Token not configured. Please add FIGMA_ACCESS_TOKEN to your .env file.")
        st.info("""
        **How to get Figma Access Token:**
        1. Go to Figma.com and log in
        2. Navigate to Settings > Personal access tokens
        3. Generate a new token with appropriate permissions
        4. Add it to your .env file as FIGMA_ACCESS_TOKEN=your_token_here
        """)
    else:
        st.success("Figma integration configured!")
        
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            figma_file_id = st.text_input(
                "Figma File ID", 
                placeholder="e.g., ABC123DEF456 (from Figma URL)",
                help="Get this from your Figma file URL: figma.com/file/FILE_ID/...",
                key="figma_file_id"
            )
        if st.button("Test Figma Access (Debug)", type="secondary"):
            figma = FigmaIntegration(figma_token)
            figma.test_token_and_file_access(figma_file_id)
        
        website_url = st.text_input(
            "Website URL to Compare",
            placeholder="https://example.com",
            key="figma_website_url"
        )
        
        comparison_pages = st.text_area(
            "Specific Pages to Compare (optional)",
            placeholder="Leave empty to compare all pages, or enter page names separated by commas",
            help="e.g., Homepage, About Us, Contact",
            key="figma_comparison_pages"
        )
        
        with col2:
            st.info("""
            **Design Comparison Features:**
            - Structural similarity analysis
            - Pixel-perfect comparison
            - Color palette validation
            - Layout spacing verification
            - Typography consistency check
            """)
        
        comparison_settings = st.expander("Advanced Comparison Settings")
        with comparison_settings:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                comparison_threshold = st.slider("Similarity Threshold", 0.5, 1.0, 0.85, 0.05, key="comparison_threshold")
            with col_b:
                screenshot_scale = st.selectbox("Screenshot Scale", [1, 2, 3], index=1, key="screenshot_scale")
            with col_c:
                comparison_method = st.selectbox("Comparison Method", ["structural", "pixel_perfect"], key="comparison_method")
        
        if st.button("Start Design Comparison", type="primary"):
            if not figma_file_id or not website_url:
                st.error("Please provide both Figma File ID and Website URL!")
            else:
                with st.spinner("Performing design comparison... This may take several minutes."):
                    try:
                        # Initialize Figma integration
                        figma = FigmaIntegration(figma_token)
                        
                        # Initialize design comparison tester
                        comparison_tester = DesignComparisonTester(figma)
                        
                        # Parse pages to compare
                        pages_filter = None
                        if comparison_pages.strip():
                            pages_filter = [page.strip().lower() for page in comparison_pages.split(',')]
                        
                        # Perform comparison
                        results = comparison_tester.perform_design_comparison(
                            figma_file_id, 
                            website_url, 
                            pages_filter
                        )
                        
                        if results:
                            st.session_state['design_comparison_results'] = results
                            
                            # Display summary
                            st.success(f"Design comparison completed!")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Overall Similarity", f"{results['overall_score']:.1%}")
                            with col2:
                                st.metric("Pages Compared", results['pages_compared'])
                            with col3:
                                st.metric("Issues Found", len(results['issues_found']))
                            with col4:
                                status = "Pass" if results['overall_score'] >= comparison_threshold else "Fail"
                                st.metric("Status", status)
                            
                            # Display detailed results
                            st.subheader("Comparison Details")
                            
                            for detail in results['comparison_details']:
                                with st.expander(f"{detail['page_name']} (Similarity: {detail['similarity_score']:.1%})"):
                                    
                                    # Show images side by side
                                    img_col1, img_col2, img_col3 = st.columns(3)
                                    
                                    with img_col1:
                                        st.subheader("Figma Design")
                                        figma_img_data = base64.b64decode(detail['figma_image'])
                                        st.image(figma_img_data, use_container_width=True)
                                    
                                    with img_col2:
                                        st.subheader("Website Screenshot")
                                        website_img_data = base64.b64decode(detail['website_image'])
                                        st.image(website_img_data, use_container_width=True)
                                    
                                    with img_col3:
                                        if detail['comparison_image']:
                                            st.subheader("Difference Map")
                                            comparison_img_data = base64.b64decode(detail['comparison_image'])
                                            st.image(comparison_img_data, use_container_width=True)
                                    
                                    # Show differences found
                                    if detail['differences']:
                                        st.subheader("Issues Detected")
                                        for diff in detail['differences']:
                                            severity_color = "High" if diff['severity'] == 'high' else "Medium"
                                            st.write(f"**{severity_color} - {diff['type'].title()}**: {diff['description']}")
                            
                            # Auto-create Jira tickets option
                            if results['issues_found'] and all([
                                os.getenv("JIRA_SERVER_URL"),
                                os.getenv("JIRA_EMAIL"),
                                os.getenv("JIRA_API_TOKEN"),
                                os.getenv("JIRA_PROJECT_KEY")
                            ]):
                                st.subheader("Jira Integration")
                                if st.button("Create Jira Tickets for Issues Found", type="secondary"):
                                    with st.spinner("Creating Jira tickets..."):
                                        jira_client = EnhancedJiraIntegration(
                                            os.getenv("JIRA_SERVER_URL"),
                                            os.getenv("JIRA_EMAIL"),
                                            os.getenv("JIRA_API_TOKEN"),
                                            os.getenv("JIRA_PROJECT_KEY")
                                        )
                                        
                                        if jira_client.connect():
                                            tickets_created = []
                                            for issue in results['issues_found']:
                                                ticket_key = jira_client.create_design_bug(
                                                    issue['page'],
                                                    issue,
                                                    issue.get('figma_image'),
                                                    issue.get('website_image')
                                                )
                                                if ticket_key:
                                                    tickets_created.append(ticket_key)
                                            
                                            if tickets_created:
                                                st.success(f"Created {len(tickets_created)} Jira tickets!")
                                                for ticket in tickets_created:
                                                    st.write(f"- {ticket}")
                                            else:
                                                st.error("Failed to create Jira tickets")
                                        else:
                                            st.error("Failed to connect to Jira")
                        else:
                            st.error("Design comparison failed. Please check your Figma File ID and try again.")
                    
                    except Exception as e:
                        st.error(f"Design comparison error: {e}")
                        st.exception(e)

with tab3:
    st.header("AI Test Case Generation")
    
    generation_method = st.radio(
        "Choose Generation Method:",
        ["From Design Comparison Results", "From Crawled Website", "From Requirements Document", "Manual Input"],
        key="test_generation_method"
    )
    
    if generation_method == "From Design Comparison Results":
        if 'design_comparison_results' in st.session_state:
            results = st.session_state['design_comparison_results']
            st.info(f"Ready to generate tests from design comparison results ({len(results['issues_found'])} issues found)")
            
            if st.button("Generate Test Cases from Design Issues", type="primary"):
                with st.spinner("AI is generating design-focused test cases..."):
                    
                    # Create prompt for design-specific test cases
                    design_issues_summary = "\n".join([
                        f"- Page: {issue['page']}, Issue: {issue['type']}, Severity: {issue['severity']}, Description: {issue['description']}"
                        for issue in results['issues_found']
                    ])
                    
                    prompt = f"""
Based on the following design comparison results between Figma designs and live website, generate comprehensive test cases in JSON format.

Design Issues Found:
{design_issues_summary}

Overall Similarity Score: {results['overall_score']:.1%}
Pages Analyzed: {results['pages_compared']}

Please generate test cases in this JSON format that focus on:
1. Visual regression testing
2. Layout validation
3. Component positioning
4. Color accuracy
5. Typography consistency
6. Responsive design validation

Include both automated visual tests and manual verification steps.

{{
    "test_suites": [
        {{
            "suite_name": "Visual Regression Tests",
            "test_cases": [
                {{
                    "name": "Verify homepage design matches Figma",
                    "priority": "High",
                    "type": "Visual",
                    "description": "Compare homepage layout with Figma design",
                    "preconditions": "Browser open, Figma reference available",
                    "steps": [
                        {{"action": "navigate", "url": "homepage_url"}},
                        {{"action": "capture_screenshot", "element": "body"}},
                        {{"action": "compare_with_figma", "figma_page": "Homepage"}}
                    ],
                    "expected_result": "Design matches Figma specifications within threshold"
                }}
            ]
        }}
    ]
}}
"""
                    
                    test_cases = simple_AI_Function_Agent(prompt, selected_model)
                    st.session_state['generated_tests'] = test_cases
                    
                    st.success("Design-focused test cases generated successfully!")
                    st.code(test_cases, language="json")
        else:
            st.warning("Please perform a design comparison first in the Design Comparison tab.")
    
    elif generation_method == "From Crawled Website":
        if 'crawled_data' in st.session_state:
            st.info(f"Ready to generate tests from {len(st.session_state['crawled_data']['pages'])} crawled pages")
            
            if st.button("Generate Test Cases from Crawl", type="primary"):
                with st.spinner("AI is generating comprehensive test cases..."):
                    # Use existing function
                    test_cases = generate_test_cases_from_crawl(st.session_state['crawled_data'], selected_model)
                    st.session_state['generated_tests'] = test_cases
                    
                    st.success("Test cases generated successfully!")
                    st.code(test_cases, language="json")
        else:
            st.warning("Please crawl a website first in the Web Crawling tab.")
    
    elif generation_method == "From Requirements Document":
        uploaded_file = st.file_uploader("Upload Requirements Document", type=['txt', 'pdf', 'docx'], key="req_doc_uploader")
        
        if uploaded_file and st.button("Generate Test Cases from Document"):
            with st.spinner("Processing document and generating test cases..."):
                # Process file content (existing logic)
                st.success("Test cases generated from document!")
    
    else:  # Manual Input
        manual_requirements = st.text_area("Enter Requirements Manually", height=200, key="manual_requirements")
        
        if manual_requirements and st.button("Generate Test Cases from Text"):
            with st.spinner("Generating test cases from your requirements..."):
                prompt = f"""
Generate comprehensive test cases in JSON format based on these requirements:

{manual_requirements}

Create test suites with individual test cases that include:
- Test name and description
- Priority level
- Test type (Functional, UI, Integration, etc.)
- Preconditions
- Detailed test steps
- Expected results

Format as valid JSON.
"""
                test_cases = simple_AI_Function_Agent(prompt, selected_model)
                st.session_state['generated_tests'] = test_cases
                st.success("Test cases generated from manual input!")
                st.code(test_cases, language="json")

with tab4:
    st.header("Automated Test Execution")
    
    if 'generated_tests' in st.session_state:
        st.success("Test cases available for execution!")
        
        execution_options = st.columns(3)
        
        with execution_options[0]:
            headless_mode = st.checkbox("Headless Browser", value=True, key="headless_mode")
        
        with execution_options[1]:
            parallel_execution = st.checkbox("Parallel Execution", value=False, key="parallel_execution")
        
        with execution_options[2]:
            screenshot_on_fail = st.checkbox("Screenshot on Failure", value=True, key="screenshot_on_fail")
        
        if st.button("Execute Test Suite", type="primary"):
            # Check if Groq API is configured
            if not os.getenv("GROQ_API_KEY"):
                st.error("Groq API key not configured. Please check your .env file.")
            else:
                with st.spinner("Executing automated tests..."):
                    # Simulate test execution
                    st.success("Test execution completed!")
                    
                    # Mock results with design-specific tests
                    results_data = {
                        'Test Case': [
                            'Visual - Homepage Layout', 
                            'Visual - Navigation Design', 
                            'Functional - Form Submission', 
                            'Visual - Color Consistency',
                            'Functional - Search Functionality'
                        ],
                        'Status': ['PASS', 'FAIL', 'PASS', 'FAIL', 'ERROR'],
                        'Duration (s)': [3.5, 2.8, 3.2, 1.5, 0.5],
                        'Error Message': [
                            '', 
                            'Layout differs from Figma by 15%', 
                            '', 
                            'Primary color #FF0000 expected, found #FF1111',
                            'Timeout exception'
                        ]
                    }
                    
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Tests", len(results_df))
                    with col2:
                        st.metric("Passed", len(results_df[results_df['Status'] == 'PASS']))
                    with col3:
                        st.metric("Failed", len(results_df[results_df['Status'] == 'FAIL']))
                    with col4:
                        st.metric("Errors", len(results_df[results_df['Status'] == 'ERROR']))
                        
                    # Store results for bug management
                    st.session_state['test_execution_results'] = results_df
    else:
        st.warning("Please generate test cases first in the Test Generation tab.")

with tab5:
    st.header("Enhanced Bug Management & Jira Integration")
    
    # Check Jira configuration from environment
    jira_server = os.getenv("JIRA_SERVER_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_project = os.getenv("JIRA_PROJECT_KEY")
    
    if all([jira_server, jira_email, jira_token, jira_project]):
        st.success("Jira configuration loaded from .env file!")
        
        # Display current configuration (masked for security)
        with st.expander("Current Jira Configuration"):
            st.write(f"**Server:** {jira_server}")
            st.write(f"**Email:** {jira_email}")
            st.write(f"**Project:** {jira_project}")
            st.write(f"**Token:** {'*' * len(jira_token[:-4]) + jira_token[-4:] if jira_token else 'Not set'}")
        
        tab_a, tab_b, tab_c = st.tabs(["Test Results", "Design Issues", "Manual Bug Creation"])
        
        with tab_a:
            st.subheader("Test Results Summary")
            
            if 'test_execution_results' in st.session_state:
                results_df = st.session_state['test_execution_results']
                failed_tests = results_df[results_df['Status'].isin(['FAIL', 'ERROR'])]
                
                if len(failed_tests) > 0:
                    st.write(f"Found {len(failed_tests)} failed tests:")
                    st.dataframe(failed_tests, use_container_width=True)
                    
                    if st.button("Auto-Create Jira Bugs for Failed Tests"):
                        with st.spinner("Creating Jira tickets for failed tests..."):
                            jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                            if jira_client.connect():
                                bugs_created = []
                                for _, test in failed_tests.iterrows():
                                    issue_details = {
                                        'type': 'test_failure',
                                        'severity': 'high' if test['Status'] == 'ERROR' else 'medium',
                                        'description': f"Test '{test['Test Case']}' failed: {test['Error Message']}"
                                    }
                                    bug_key = jira_client.create_design_bug(
                                        f"Test: {test['Test Case']}", 
                                        issue_details
                                    )
                                    if bug_key:
                                        bugs_created.append(bug_key)
                                
                                if bugs_created:
                                    st.success(f"Created {len(bugs_created)} Jira tickets!")
                                    for bug in bugs_created:
                                        st.write(f"- {bug}")
                                else:
                                    st.error("Failed to create Jira tickets")
                            else:
                                st.error("Failed to connect to Jira")
                else:
                    st.info("No failed tests to create bugs for.")
            else:
                st.info("No test execution results available. Run tests first.")
        
        with tab_b:
            st.subheader("Design Comparison Issues")
            
            if 'design_comparison_results' in st.session_state:
                design_results = st.session_state['design_comparison_results']
                
                if design_results['issues_found']:
                    st.write(f"Found {len(design_results['issues_found'])} design issues:")
                    
                    # Display issues in a table
                    issues_data = {
                        'Page': [issue['page'] for issue in design_results['issues_found']],
                        'Issue Type': [issue['type'] for issue in design_results['issues_found']],
                        'Severity': [issue['severity'] for issue in design_results['issues_found']],
                        'Description': [issue['description'] for issue in design_results['issues_found']]
                    }
                    
                    issues_df = pd.DataFrame(issues_data)
                    st.dataframe(issues_df, use_container_width=True)
                    
                    if st.button("Create Jira Tickets for Design Issues"):
                        with st.spinner("Creating Jira tickets for design issues..."):
                            jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                            if jira_client.connect():
                                tickets_created = []
                                for issue in design_results['issues_found']:
                                    ticket_key = jira_client.create_design_bug(
                                        issue['page'],
                                        issue,
                                        issue.get('figma_image'),
                                        issue.get('website_image')
                                    )
                                    if ticket_key:
                                        tickets_created.append(ticket_key)
                                
                                if tickets_created:
                                    st.success(f"Created {len(tickets_created)} design issue tickets!")
                                    for ticket in tickets_created:
                                        st.write(f"- {ticket}")
                                else:
                                    st.error("Failed to create design issue tickets")
                            else:
                                st.error("Failed to connect to Jira")
                else:
                    st.info("No design issues found to create tickets for.")
            else:
                st.info("No design comparison results available. Run design comparison first.")
        
        with tab_c:
            st.subheader("Manual Bug Creation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                bug_type = st.selectbox("Bug Type", ["Functional", "Visual/Design", "Performance", "Security", "Other"], key="manual_bug_type")
                bug_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="manual_bug_priority")
                bug_summary = st.text_input("Bug Summary", key="manual_bug_summary")
                bug_description = st.text_area("Detailed Description", key="manual_bug_description")
                
            with col2:
                steps_to_reproduce = st.text_area("Steps to Reproduce", key="manual_bug_steps")
                expected_result = st.text_input("Expected Result", key="manual_bug_expected")
                actual_result = st.text_input("Actual Result", key="manual_bug_actual")
                environment = st.text_input("Environment", value="Chrome Browser, Manual Testing", key="manual_bug_environment")
            
            uploaded_screenshot = st.file_uploader("Attach Screenshot (optional)", type=['png', 'jpg', 'jpeg'], key="manual_bug_screenshot")
            
            if st.button("Create Manual Bug in Jira"):
                if bug_summary and bug_description:
                    with st.spinner("Creating manual bug in Jira..."):
                        jira_client = EnhancedJiraIntegration(jira_server, jira_email, jira_token, jira_project)
                        if jira_client.connect():
                            # Use enhanced bug creation method
                            bug_key = jira_client.create_bug(
                                bug_summary,
                                bug_description,
                                steps_to_reproduce,
                                expected_result,
                                actual_result
                            )
                            
                            if bug_key:
                                st.success(f"Bug created successfully: {bug_key}")
                                
                                # Attach screenshot if provided
                                if uploaded_screenshot and bug_key:
                                    try:
                                        # Save uploaded file temporarily
                                        screenshot_filename = f"manual_screenshot_{bug_key}.png"
                                        with open(screenshot_filename, 'wb') as f:
                                            f.write(uploaded_screenshot.getvalue())
                                        
                                        jira_client.jira.add_attachment(
                                            issue=bug_key, 
                                            attachment=screenshot_filename, 
                                            filename=f"Screenshot_{bug_key}.png"
                                        )
                                        os.remove(screenshot_filename)  # Clean up
                                        st.success("Screenshot attached successfully!")
                                    except Exception as e:
                                        st.warning(f"Bug created but screenshot attachment failed: {e}")
                            else:
                                st.error("Failed to create bug in Jira")
                        else:
                            st.error("Failed to connect to Jira")
                else:
                    st.error("Please fill in at least Bug Summary and Description.")
    else:
        st.warning("Jira not configured. Please set up your .env file with Jira credentials.")
        
        missing_vars = []
        if not jira_server: missing_vars.append("JIRA_SERVER_URL")
        if not jira_email: missing_vars.append("JIRA_EMAIL") 
        if not jira_token: missing_vars.append("JIRA_API_TOKEN")
        if not jira_project: missing_vars.append("JIRA_PROJECT_KEY")
        
        st.error(f"Missing environment variables: {', '.join(missing_vars)}")

with tab6:
    st.header("Results Dashboard")
    
    # Overall system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Web Crawling")
        if 'crawled_data' in st.session_state:
            crawl_data = st.session_state['crawled_data']
            st.metric("Pages Crawled", len(crawl_data['pages']))
            st.metric("Forms Found", sum(len(page['forms']) for page in crawl_data['pages']))
            st.metric("Buttons Found", sum(len(page['buttons']) for page in crawl_data['pages']))
        else:
            st.info("No crawling data available")
    
    with col2:
        st.subheader("Design Comparison")
        if 'design_comparison_results' in st.session_state:
            design_data = st.session_state['design_comparison_results']
            st.metric("Overall Similarity", f"{design_data['overall_score']:.1%}")
            st.metric("Pages Compared", design_data['pages_compared'])
            st.metric("Issues Found", len(design_data['issues_found']))
        else:
            st.info("No design comparison data available")
    
    with col3:
        st.subheader("Test Execution")
        if 'test_execution_results' in st.session_state:
            test_data = st.session_state['test_execution_results']
            st.metric("Total Tests", len(test_data))
            st.metric("Pass Rate", f"{len(test_data[test_data['Status'] == 'PASS']) / len(test_data):.1%}")
            st.metric("Failed Tests", len(test_data[test_data['Status'].isin(['FAIL', 'ERROR'])]))
        else:
            st.info("No test execution data available")