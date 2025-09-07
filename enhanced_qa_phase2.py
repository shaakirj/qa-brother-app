"""
Enhanced Design QA System - Phase 2: Browser Automation & API Integrations
Fixed version with complete code
"""

import asyncio
import aiohttp
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops
from skimage.metrics import structural_similarity as ssim
import base64
from io import BytesIO
import json
import time
import re
from urllib.parse import urlparse, urljoin
from jira import JIRA
from jira.exceptions import JIRAError
import tempfile
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from groq import Groq

# Import from Phase 1
from enhanced_qa_phase1 import (
    EnhancedDesignIssue, IssuePattern, Priority, IssueCategory, 
    ConfigurationManager, logger
)

class AdvancedChromeDriver:
    """Enhanced Chrome driver with advanced screenshot and analysis capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
        self.current_viewport = None
        self.screenshots_cache = {}
        
    def initialize_driver(self, viewport: Dict[str, Any] = None, headless: bool = True) -> bool:
        """Initialize Chrome driver with optimized settings"""
        try:
            chrome_options = Options()
            
            # Performance optimizations
            if headless:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Speed up initial load
            chrome_options.add_argument("--disable-javascript")  # For static analysis
            
            # Window settings
            if viewport:
                chrome_options.add_argument(f"--window-size={viewport['width']},{viewport['height']}")
                self.current_viewport = viewport
            else:
                chrome_options.add_argument("--window-size=1920,1080")
            
            # Quality settings for screenshots
            chrome_options.add_argument("--force-device-scale-factor=1")
            chrome_options.add_argument("--hide-scrollbars")
            
            # User agent for consistency
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            if viewport:
                self.driver.set_window_size(viewport['width'], viewport['height'])
            
            logger.info(f"Chrome driver initialized for viewport: {self.current_viewport}")
            return True
            
        except Exception as e:
            logger.error(f"Chrome driver initialization failed: {e}")
            return False
    
    async def capture_multi_viewport_screenshots(self, url: str, viewports: List[Dict[str, Any]]) -> Dict[str, Image.Image]:
        """Capture screenshots across multiple viewports"""
        screenshots = {}
        
        for viewport in viewports:
            try:
                # Reinitialize for each viewport
                if self.driver:
                    self.driver.quit()
                
                if not self.initialize_driver(viewport):
                    logger.error(f"Failed to initialize driver for {viewport['name']}")
                    continue
                
                # Navigate and capture
                screenshot = await self._capture_full_page_screenshot(url)
                if screenshot:
                    screenshots[viewport['name']] = screenshot
                    
                logger.info(f"Captured screenshot for {viewport['name']}: {viewport['width']}x{viewport['height']}")
                
            except Exception as e:
                logger.error(f"Screenshot capture failed for {viewport['name']}: {e}")
        
        return screenshots
    
    async def _capture_full_page_screenshot(self, url: str) -> Optional[Image.Image]:
        """Capture full page screenshot with proper waiting"""
        if not self.driver:
            return None
        
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            await asyncio.sleep(3)
            
            # Scroll to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(1)
            
            # Re-enable images for final screenshot
            self.driver.execute_script("""
                document.querySelectorAll('img').forEach(img => {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
            """)
            
            await asyncio.sleep(2)
            
            # Get page dimensions
            total_height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Capture screenshot
            screenshot_data = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot_data))
            
            # Handle long pages with scrolling
            if total_height > viewport_height * 1.2:  # Page is significantly longer
                return await self._capture_scrolling_screenshot(total_height, viewport_height)
            
            return image
            
        except Exception as e:
            logger.error(f"Full page screenshot failed: {e}")
            return None
    
    async def _capture_scrolling_screenshot(self, total_height: int, viewport_height: int) -> Optional[Image.Image]:
        """Capture screenshot of long pages by scrolling"""
        try:
            screenshots = []
            current_position = 0
            
            while current_position < total_height:
                # Scroll to position
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                await asyncio.sleep(0.5)
                
                # Capture screenshot
                screenshot_data = self.driver.get_screenshot_as_png()
                screenshot = Image.open(BytesIO(screenshot_data))
                screenshots.append(screenshot)
                
                current_position += viewport_height
            
            # Stitch screenshots together
            if screenshots:
                total_width = screenshots[0].width
                combined_image = Image.new('RGB', (total_width, total_height), (255, 255, 255))
                
                y_offset = 0
                for screenshot in screenshots:
                    combined_image.paste(screenshot, (0, y_offset))
                    y_offset += viewport_height
                
                # Scroll back to top
                self.driver.execute_script("window.scrollTo(0, 0);")
                
                return combined_image
            
        except Exception as e:
            logger.error(f"Scrolling screenshot failed: {e}")
        
        return None
    
    def analyze_page_elements(self, url: str) -> Dict[str, Any]:
        """Analyze page elements for QA validation"""
        if not self.driver:
            return {}
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            analysis_results = {
                'dom_structure': self._analyze_dom_structure(),
                'accessibility_elements': self._analyze_accessibility_elements(),
                'interactive_elements': self._analyze_interactive_elements(),
                'visual_elements': self._analyze_visual_elements(),
                'performance_indicators': self._analyze_performance_indicators()
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Element analysis failed: {e}")
            return {}
    
    def _analyze_dom_structure(self) -> Dict[str, Any]:
        """Analyze DOM structure for accessibility and semantic markup"""
        try:
            # Get page structure metrics
            total_elements = len(self.driver.find_elements(By.XPATH, "//*"))
            
            # Analyze heading structure
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            heading_structure = {}
            for heading in headings:
                tag = heading.tag_name
                heading_structure[tag] = heading_structure.get(tag, 0) + 1
            
            # Check for semantic elements
            semantic_elements = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
            semantic_usage = {}
            for element in semantic_elements:
                count = len(self.driver.find_elements(By.TAG_NAME, element))
                semantic_usage[element] = count
            
            return {
                'total_elements': total_elements,
                'heading_structure': heading_structure,
                'semantic_elements': semantic_usage,
                'dom_depth': self._calculate_dom_depth()
            }
            
        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            return {}
    
    def _analyze_accessibility_elements(self) -> Dict[str, Any]:
        """Analyze accessibility-related elements"""
        try:
            # Images with/without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            images_with_alt = sum(1 for img in images if img.get_attribute("alt"))
            
            # Form elements with/without labels
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            labeled_inputs = 0
            for input_elem in inputs:
                input_id = input_elem.get_attribute("id")
                if input_id:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        labeled_inputs += 1
                    except NoSuchElementException:
                        pass
            
            # ARIA attributes usage
            aria_elements = len(self.driver.find_elements(By.CSS_SELECTOR, "[aria-label], [aria-labelledby], [aria-describedby]"))
            
            # Interactive elements with proper roles
            interactive_elements = len(self.driver.find_elements(By.CSS_SELECTOR, "button, a, input, select, textarea"))
            
            return {
                'images_total': len(images),
                'images_with_alt': images_with_alt,
                'alt_text_coverage': (images_with_alt / len(images) * 100) if images else 100,
                'inputs_total': len(inputs),
                'labeled_inputs': labeled_inputs,
                'label_coverage': (labeled_inputs / len(inputs) * 100) if inputs else 100,
                'aria_elements': aria_elements,
                'interactive_elements': interactive_elements
            }
            
        except Exception as e:
            logger.error(f"Accessibility analysis failed: {e}")
            return {}
    
    def _analyze_interactive_elements(self) -> Dict[str, Any]:
        """Analyze interactive elements for usability"""
        try:
            # Buttons analysis
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            button_analysis = []
            
            for button in buttons:
                text = button.text or button.get_attribute("value") or button.get_attribute("aria-label")
                size = button.size
                
                button_analysis.append({
                    'text': text,
                    'width': size['width'],
                    'height': size['height'],
                    'meets_touch_target': size['width'] >= 44 and size['height'] >= 44,
                    'has_text': bool(text and len(text.strip()) > 0)
                })
            
            # Links analysis
            links = self.driver.find_elements(By.TAG_NAME, "a")
            external_links = sum(1 for link in links if self._is_external_link(link.get_attribute("href")))
            
            # Form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            form_analysis = []
            
            for form in forms:
                inputs = form.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                required_fields = form.find_elements(By.CSS_SELECTOR, "[required]")
                
                form_analysis.append({
                    'total_fields': len(inputs),
                    'required_fields': len(required_fields),
                    'has_submit_button': len(form.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")) > 0
                })
            
            return {
                'buttons': {
                    'total': len(buttons),
                    'analysis': button_analysis,
                    'touch_target_compliance': sum(1 for b in button_analysis if b['meets_touch_target']) / len(button_analysis) * 100 if button_analysis else 100
                },
                'links': {
                    'total': len(links),
                    'external': external_links,
                    'internal': len(links) - external_links
                },
                'forms': {
                    'total': len(forms),
                    'analysis': form_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Interactive elements analysis failed: {e}")
            return {}
    
    def _analyze_visual_elements(self) -> Dict[str, Any]:
        """Analyze visual elements for design consistency"""
        try:
            # Color analysis
            computed_styles = self.driver.execute_script("""
                const elements = document.querySelectorAll('*');
                const styles = [];
                for (let i = 0; i < Math.min(elements.length, 100); i++) {
                    const el = elements[i];
                    const style = window.getComputedStyle(el);
                    styles.push({
                        tag: el.tagName,
                        color: style.color,
                        backgroundColor: style.backgroundColor,
                        fontSize: style.fontSize,
                        fontFamily: style.fontFamily,
                        fontWeight: style.fontWeight,
                        lineHeight: style.lineHeight
                    });
                }
                return styles;
            """)
            
            # Extract unique values
            colors_used = set()
            font_sizes_used = set()
            font_families_used = set()
            
            for style in computed_styles:
                if style['color'] not in ['rgb(0, 0, 0)', 'rgba(0, 0, 0, 0)']:
                    colors_used.add(style['color'])
                if style['backgroundColor'] not in ['rgb(0, 0, 0)', 'rgba(0, 0, 0, 0)', 'transparent']:
                    colors_used.add(style['backgroundColor'])
                if style['fontSize'] != '16px':  # Default
                    font_sizes_used.add(style['fontSize'])
                font_families_used.add(style['fontFamily'])
            
            return {
                'color_palette': {
                    'unique_colors': len(colors_used),
                    'colors': list(colors_used)[:20]  # Limit for display
                },
                'typography_scale': {
                    'unique_sizes': len(font_sizes_used),
                    'sizes': list(font_sizes_used)
                },
                'font_families': {
                    'unique_families': len(font_families_used),
                    'families': list(font_families_used)
                },
                'computed_styles_sample': computed_styles[:10]
            }
            
        except Exception as e:
            logger.error(f"Visual elements analysis failed: {e}")
            return {}
    
    def _analyze_performance_indicators(self) -> Dict[str, Any]:
        """Analyze basic performance indicators"""
        try:
            # Page metrics
            performance_data = self.driver.execute_script("""
                return {
                    loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                    domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                    firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
                    resourceCount: performance.getEntriesByType('resource').length,
                    documentHeight: document.documentElement.scrollHeight,
                    documentWidth: document.documentElement.scrollWidth
                };
            """)
            
            # Layout stability indicators
            layout_shifts = self.driver.execute_script("""
                return new Promise((resolve) => {
                    let cls = 0;
                    new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (!entry.hadRecentInput) {
                                cls += entry.value;
                            }
                        }
                        resolve(cls);
                    }).observe({type: 'layout-shift', buffered: true});
                    
                    setTimeout(() => resolve(cls), 2000);
                });
            """)
            
            return {
                'load_metrics': performance_data,
                'layout_stability': {
                    'cumulative_layout_shift': layout_shifts
                },
                'viewport_info': {
                    'name': self.current_viewport['name'] if self.current_viewport else 'Unknown',
                    'dimensions': f"{self.current_viewport['width']}x{self.current_viewport['height']}" if self.current_viewport else 'Unknown'
                }
            }
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {}
    
    def _calculate_dom_depth(self) -> int:
        """Calculate maximum DOM depth"""
        try:
            depth = self.driver.execute_script("""
                function getMaxDepth(element) {
                    let maxDepth = 0;
                    function traverse(el, currentDepth) {
                        maxDepth = Math.max(maxDepth, currentDepth);
                        for (let child of el.children) {
                            traverse(child, currentDepth + 1);
                        }
                    }
                    traverse(element, 0);
                    return maxDepth;
                }
                return getMaxDepth(document.body);
            """)
            return depth
        except:
            return 0
    
    def _is_external_link(self, href: str) -> bool:
        """Check if link is external"""
        if not href:
            return False
        
        current_domain = urlparse(self.driver.current_url).netloc
        link_domain = urlparse(href).netloc
        
        return link_domain and link_domain != current_domain
    
    def close(self):
        """Clean up driver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None

class EnhancedFigmaIntegration:
    """Advanced Figma API integration with design token extraction"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"X-Figma-Token": access_token}
        self.base_url = "https://api.figma.com/v1"
        
    async def analyze_figma_design(self, figma_url: str) -> Dict[str, Any]:
        """Comprehensive Figma design analysis"""
        
        # Extract file ID
        file_id = self._extract_file_id(figma_url)
        if not file_id:
            raise ValueError("Invalid Figma URL or file ID")
        
        try:
            # Get file information
            file_data = await self._get_file_data(file_id)
            
            # Extract design tokens
            design_tokens = await self._extract_design_tokens(file_data)
            
            # Get component specifications
            component_specs = await self._extract_component_specs(file_data)
            
            # Generate design screenshots
            screenshots = await self._generate_design_screenshots(file_id)
            
            return {
                'file_id': file_id,
                'file_info': file_data,
                'design_tokens': design_tokens,
                'component_specs': component_specs,
                'screenshots': screenshots,
                'analysis_metadata': {
                    'extraction_time': time.time(),
                    'components_found': len(component_specs),
                    'tokens_extracted': sum(len(tokens) for tokens in design_tokens.values())
                }
            }
            
        except Exception as e:
            logger.error(f"Figma analysis failed: {e}")
            raise
    
    def _extract_file_id(self, figma_url: str) -> Optional[str]:
        """Extract file ID from various Figma URL formats"""
        try:
            if "figma.com/file/" in figma_url:
                return figma_url.split("/file/")[1].split("/")[0]
            elif "figma.com/design/" in figma_url:
                return figma_url.split("/design/")[1].split("/")[0]
            elif re.match(r'^[a-zA-Z0-9]{15,25}$', figma_url):
                return figma_url
            return None
        except:
            return None
    
    async def _get_file_data(self, file_id: str) -> Dict[str, Any]:
        """Get comprehensive file data from Figma API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/files/{file_id}"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Figma API error: {response.status}")
    
    async def _extract_design_tokens(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract design tokens from Figma file data"""
        try:
            document = file_data.get('document', {})
            
            # Extract colors from styles
            styles = file_data.get('styles', {})
            color_tokens = {}
            typography_tokens = {}
            
            for style_id, style_data in styles.items():
                style_type = style_data.get('styleType')
                name = style_data.get('name', f'unnamed_{style_id}')
                
                if style_type == 'FILL':
                    color_tokens[name] = {
                        'id': style_id,
                        'type': 'color',
                        'description': style_data.get('description', '')
                    }
                elif style_type == 'TEXT':
                    typography_tokens[name] = {
                        'id': style_id,
                        'type': 'typography',
                        'description': style_data.get('description', '')
                    }
            
            # Extract spacing patterns from components
            spacing_tokens = await self._extract_spacing_patterns(document)
            
            return {
                'colors': color_tokens,
                'typography': typography_tokens,
                'spacing': spacing_tokens,
                'extraction_metadata': {
                    'total_styles': len(styles),
                    'color_styles': len(color_tokens),
                    'typography_styles': len(typography_tokens)
                }
            }
            
        except Exception as e:
            logger.error(f"Design token extraction failed: {e}")
            return {'colors': {}, 'typography': {}, 'spacing': {}}
    
    async def _extract_spacing_patterns(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract spacing patterns from Figma components"""
        spacing_values = []
        
        def traverse_node(node):
            # Extract padding/margin-like spacing
            if 'paddingLeft' in node:
                spacing_values.extend([
                    node.get('paddingLeft', 0),
                    node.get('paddingRight', 0), 
                    node.get('paddingTop', 0),
                    node.get('paddingBottom', 0)
                ])
            
            # Extract gap values from auto-layout
            if node.get('layoutMode') == 'HORIZONTAL' or node.get('layoutMode') == 'VERTICAL':
                if 'itemSpacing' in node:
                    spacing_values.append(node['itemSpacing'])
            
            # Recurse through children
            for child in node.get('children', []):
                traverse_node(child)
        
        traverse_node(document)
        
        # Analyze spacing patterns
        unique_values = list(set(spacing_values))
        
        return {
            'detected_values': unique_values,
            'most_common': max(set(spacing_values), key=spacing_values.count) if spacing_values else 0,
            'spacing_scale_suggestion': self._suggest_spacing_scale(unique_values)
        }
    
    def _suggest_spacing_scale(self, values: List[float]) -> List[int]:
        """Suggest a consistent spacing scale based on detected values"""
        if not values:
            return [4, 8, 12, 16, 24, 32, 48, 64]
        
        # Round values to nearest 4px and create scale
        rounded_values = [round(v / 4) * 4 for v in values if v > 0]
        unique_rounded = sorted(set(rounded_values))
        
        # Extend scale logically
        base_scale = [4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96]
        suggested_scale = sorted(set(unique_rounded + base_scale))
        
        return suggested_scale[:12]  # Return reasonable number of values
    
    async def _extract_component_specs(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component specifications from Figma"""
        try:
            components = file_data.get('components', {})
            component_sets = file_data.get('componentSets', {})
            
            specs = {}
            
            # Process individual components
            for comp_id, comp_data in components.items():
                name = comp_data.get('name', f'Component_{comp_id}')
                specs[name] = {
                    'id': comp_id,
                    'description': comp_data.get('description', ''),
                    'type': 'component',
                    'properties': self._extract_component_properties(comp_data)
                }
            
            # Process component sets (variants)
            for set_id, set_data in component_sets.items():
                name = set_data.get('name', f'ComponentSet_{set_id}')
                specs[name] = {
                    'id': set_id,
                    'description': set_data.get('description', ''),
                    'type': 'component_set',
                    'properties': self._extract_component_set_properties(set_data)
                }
            
            return specs
            
        except Exception as e:
            logger.error(f"Component extraction failed: {e}")
            return {}
    
    def _extract_component_properties(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from individual component"""
        return {
            'size': {
                'width': component_data.get('absoluteBoundingBox', {}).get('width'),
                'height': component_data.get('absoluteBoundingBox', {}).get('height')
            },
            'constraints': component_data.get('constraints', {}),
            'fills': component_data.get('fills', []),
            'strokes': component_data.get('strokes', [])
        }
    
    def _extract_component_set_properties(self, set_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from component set (variants)"""
        return {
            'variant_count': len(set_data.get('children', [])),
            'variant_properties': set_data.get('componentPropertyDefinitions', {})
        }
    
    async def _generate_design_screenshots(self, file_id: str) -> Dict[str, str]:
        """Generate screenshots of Figma designs"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get image URLs
                url = f"{self.base_url}/images/{file_id}?format=png&scale=2"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        image_data = await response.json()
                        return image_data.get('images', {})
                    else:
                        logger.error(f"Screenshot generation failed: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Figma screenshot generation failed: {e}")
            return {}
from typing import List, Optional
import os
import json

# Try to import Groq client; it's okay if it's not installed
try:
    from groq import Groq
except ImportError:
    Groq = None

class AIAnalysisEngine:
    """
    AI wrapper to generate test cases and user stories.
    Uses Groq API if available, otherwise provides fallback responses.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "llama3-70b-8192"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.client = None
        if Groq and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.client = None

    def _call_ai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Private method to call the AI model."""
        if not self.client:
            return None
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Warning: AI API call failed: {e}")
            return None

    def generate_test_cases(self, requirements_text: str) -> List[str]:
        """Generates a list of test cases from requirements text."""
        if not requirements_text:
            return ["No requirements provided"]

        system_prompt = "You are a QA engineer. Generate a list of detailed test cases based on the user's requirements. Each test case should be a single, complete sentence."
        ai_result = self._call_ai(system_prompt, requirements_text)

        if ai_result:
            # Split by newline and filter out empty lines
            test_cases = [line.strip() for line in ai_result.split('\n') if line.strip()]
            return test_cases if test_cases else ["AI generated empty response"]

        # Fallback to a simple heuristic if AI call fails
        sentences = [sentence.strip() for sentence in requirements_text.split('.') if sentence.strip()]
        return [f"Test Case: Verify that the system correctly implements - {sentence}" for sentence in sentences[:5]]

    def generate_user_stories(self, requirements_text: str) -> List[str]:
        """Generates a list of user stories from requirements text."""
        if not requirements_text:
            return ["No requirements provided"]

        system_prompt = "You are a Product Owner. Convert the following requirements into user stories in the format 'As a <role>, I want <goal> so that <benefit>'."
        ai_result = self._call_ai(system_prompt, requirements_text)

        if ai_result:
            user_stories = [line.strip() for line in ai_result.split('\n') if "As a" in line]
            return user_stories if user_stories else ["As a user, I want the system to work as specified so that I can complete my tasks"]

        # Fallback to a simple heuristic
        sentences = [sentence.strip() for sentence in requirements_text.split('.') if sentence.strip()]
        return [f"As a user, I want to {sentence.lower()} so that I can achieve my goal" for sentence in sentences[:3]]

class AdvancedChromeDriver:
    """Basic Chrome driver implementation"""
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        return True
    
    def close(self):
        if self.driver:
            self.driver.quit()

class EnhancedFigmaIntegration:
    """Basic Figma integration implementation"""
    def __init__(self, access_token):
        self.access_token = access_token
