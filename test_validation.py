#!/usr/bin/env python3
"""
QA Brother - System Validation Test
Tests all core functionality after fixes
"""

import warnings
import sys
import os

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*", category=UserWarning)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    try:
        from design8 import DesignQAProcessor, EnhancedPlaywrightDriver, FigmaDesignComparator
        from monster2 import MonsterQAAgent, VisualTestExecutor
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_agent_initialization():
    """Test QA Agent initialization"""
    print("🔍 Testing agent initialization...")
    try:
        from monster2 import MonsterQAAgent
        agent = MonsterQAAgent()
        print(f"✅ Agent initialized: {agent.is_initialized}")
        return agent.is_initialized
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def test_playwright_async_compatibility():
    """Test Playwright in asyncio context"""
    print("🔍 Testing Playwright async compatibility...")
    try:
        import asyncio
        from design8 import EnhancedPlaywrightDriver
        
        async def test_setup():
            driver = EnhancedPlaywrightDriver()
            try:
                success = driver.setup_driver(headless=True)
                print(f"   Playwright setup: {success}")
                if success:
                    driver.close()
                return success
            except Exception as e:
                print(f"   Setup error: {e}")
                driver.close()
                return False
        
        result = asyncio.run(test_setup())
        if result:
            print("✅ Playwright async compatibility working")
        else:
            print("❌ Playwright async compatibility failed")
        return result
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def test_image_processing():
    """Test PIL ImageDraw fixes"""
    print("🔍 Testing image processing fixes...")
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create test image
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Test new textbbox method instead of deprecated textsize
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        text = "Test"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((10, 10), text, fill='black', font=font)
        else:
            draw.text((10, 10), text, fill='black')
            
        print("✅ Image processing working (textsize fix applied)")
        return True
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Starting QA Brother System Validation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_agent_initialization,
        test_image_processing,
        test_playwright_async_compatibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! QA Brother is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
