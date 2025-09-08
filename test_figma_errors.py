#!/usr/bin/env python3
"""
Figma API Error Testing Script
Tests the enhanced error reporting for Figma API issues
"""

import os
import sys
sys.path.append('.')

from design8 import FigmaDesignComparator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_figma_error_reporting():
    """Test various Figma error scenarios"""
    
    print("🧪 Figma API Error Testing")
    print("=" * 50)
    
    # Initialize the comparator
    comparator = FigmaDesignComparator()
    
    # Test 1: Check token availability
    print("\n1. Testing Token Configuration:")
    if comparator.figma_token:
        print(f"✅ Token configured (length: {len(comparator.figma_token)})")
        # Mask token for security
        masked_token = comparator.figma_token[:8] + "*" * (len(comparator.figma_token) - 12) + comparator.figma_token[-4:]
        print(f"   Token: {masked_token}")
    else:
        print("❌ No token configured")
        return
    
    # Test 2: Test with the configured URL
    figma_test_url = os.getenv("FIGMA_TEST_URL")
    if figma_test_url:
        print(f"\n2. Testing with configured URL:")
        print(f"   URL: {figma_test_url}")
        
        # Parse URL
        node_info = comparator.get_specific_node_from_url(figma_test_url)
        if node_info:
            print(f"✅ URL parsed successfully:")
            print(f"   File ID: {node_info['file_id']}")
            print(f"   Node ID: {node_info['node_id']}")
            
            # Test image retrieval
            print(f"\n3. Testing Image Retrieval:")
            image = comparator.get_node_image(node_info['file_id'], node_info['node_id'])
            if image:
                print(f"✅ Image retrieved successfully (size: {image.size})")
            else:
                print("❌ Image retrieval failed - check logs for details")
            
            # Test properties retrieval
            print(f"\n4. Testing Properties Retrieval:")
            properties = comparator.get_node_properties(node_info['file_id'], node_info['node_id'])
            if properties and not properties.startswith("Error"):
                print(f"✅ Properties retrieved successfully ({len(properties)} characters)")
            else:
                print("❌ Properties retrieval failed:")
                print(f"   Error: {properties}")
        else:
            print("❌ Failed to parse URL")
    else:
        print("\n2. No FIGMA_TEST_URL configured")
    
    # Test 3: Test with a different organization's URL (should fail)
    print(f"\n5. Testing with Different Organization URL:")
    different_org_url = "https://www.figma.com/design/abc123def456/Test-Design?node-id=123-456"
    print(f"   URL: {different_org_url}")
    
    node_info = comparator.get_specific_node_from_url(different_org_url)
    if node_info:
        print(f"✅ URL parsed: File ID: {node_info['file_id']}, Node ID: {node_info['node_id']}")
        
        # This should fail with detailed error message
        image = comparator.get_node_image(node_info['file_id'], node_info['node_id'])
        if image:
            print("✅ Image retrieved (unexpected - this should have failed)")
        else:
            print("❌ Image retrieval failed as expected - check logs for detailed error message")
    
    # Test 4: Test with invalid file ID
    print(f"\n6. Testing with Invalid File ID:")
    image = comparator.get_node_image("invalid_file_id", "123:456")
    if image:
        print("✅ Image retrieved (unexpected)")
    else:
        print("❌ Image retrieval failed as expected - check logs for detailed error message")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")
    print("\nNote: Check the terminal output above for detailed error messages")
    print("The enhanced error handling should now provide specific HTTP status codes")
    print("and explanations for different types of failures.")

if __name__ == "__main__":
    test_figma_error_reporting()
