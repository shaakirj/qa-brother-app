import os
import requests
import warnings
import sys
import platform
import time  # Added missing import

# Suppress urllib3 SSL warnings for macOS LibreSSL compatibility
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

from io import BytesIO
from datetime import datetime
from jira import JIRA, JIRAError
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageChops
import numpy as np
import cv2  # Import OpenCV
from datetime import datetime as _dt
from scipy import ndimage
from skimage.metrics import structural_similarity as ssim  # Added missing import
import re
try:
    import logging
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional
import tempfile
import base64
from openai import OpenAI
import httpx
import json
import imageio
import shutil
import html
import threading
import concurrent.futures

# Load environment variables
load_dotenv()

# Configure logging FIRST - with maximum cloud environment compatibility
logger = None
if LOGGING_AVAILABLE:
    try:
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"), 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # Force reconfiguration for cloud environments
        )
        logger = logging.getLogger(__name__)
        logger.info("Logger initialized successfully")
    except Exception as e:
        LOGGING_AVAILABLE = False

if not LOGGING_AVAILABLE or logger is None:
    # Ultimate fallback for any cloud environment issues
    class SimpleLogger:
        def info(self, msg): print(f"INFO: {msg}", file=sys.stderr, flush=True)
        def warning(self, msg): print(f"WARNING: {msg}", file=sys.stderr, flush=True) 
        def error(self, msg): print(f"ERROR: {msg}", file=sys.stderr, flush=True)
        def debug(self, msg): print(f"DEBUG: {msg}", file=sys.stderr, flush=True)
    logger = SimpleLogger()
    logger.warning("Using fallback logger - logging module unavailable or failed")

# Cloud environment detection
IS_CLOUD_DEPLOYMENT = (
    os.getenv("STREAMLIT_SHARING_MODE") is not None or
    os.getenv("HOSTNAME", "").startswith("streamlit") or
    "streamlit.app" in os.getenv("HOSTNAME", "") or
    platform.system() == "Linux" and not os.path.exists("/usr/bin/google-chrome")
)

# Conditionally import browser automation based on environment
BROWSER_AUTOMATION_AVAILABLE = False
try:
    if not IS_CLOUD_DEPLOYMENT:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from playwright.sync_api import sync_playwright, ViewportSize, Playwright, Browser, Page, Error as PlaywrightError
        BROWSER_AUTOMATION_AVAILABLE = True
    else:
        # For cloud deployment, provide mock classes
        class MockPlaywright:
            def __init__(self):
                pass
            def chromium(self):
                return self
            def launch(self, **kwargs):
                return MockBrowser()
            def close(self):
                pass
        
        class MockBrowser:
            def new_page(self):
                return MockPage()
            def close(self):
                pass
        
        class MockPage:
            def goto(self, url):
                pass
            def screenshot(self, **kwargs):
                return b""
            def set_viewport_size(self, viewport):
                pass
            def close(self):
                pass
        
        sync_playwright = lambda: MockPlaywright()
        BROWSER_AUTOMATION_AVAILABLE = False
        logger.warning("Browser automation disabled for cloud deployment")
        
except ImportError as e:
    BROWSER_AUTOMATION_AVAILABLE = False
    logger.warning(f"Browser automation not available: {e}")

class EnhancedPlaywrightDriver:
    def __init__(self):
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None
        self.video_dir = None
        self.live_preview_enabled = False
        self.live_preview_callback = None
        self.live_preview_thread = None
        self.recording_enabled = False
        self.cloud_mode = IS_CLOUD_DEPLOYMENT

    def _device_preset(self, pw, name: Optional[str]):
        if not name:
            return None
        try:
            devices = pw.devices
            # Try exact, else fallback simple map
            if name in devices:
                return devices[name]
            mapping = {
                "iphone 12 pro": "iPhone 12 Pro",
                "pixel 5": "Pixel 5",
                "samsung galaxy s21": "Galaxy S21",
                "ipad pro": "iPad Pro 11",
                "ipad air": "iPad Air",
            }
            key = name.strip().lower()
            mapped = mapping.get(key)
            return devices.get(mapped) if mapped else None
        except Exception:
            return None

    def setup_driver(self, headless=True, window_size="1920,1080", mobile_device_name: Optional[str] = None, browser_type="Chromium", enable_video_recording=False, enable_live_preview=False, live_preview_callback=None):
        try:
            if self.browser and self.context and self.page:
                return True
            
            logger.info(f"Setting up Playwright browser (headless={headless}, device={mobile_device_name})")
            
            # Configure recording & live preview flags
            self.recording_enabled = bool(enable_video_recording)
            self.live_preview_enabled = bool(enable_live_preview and live_preview_callback is not None)
            self.live_preview_callback = live_preview_callback
            
            # Check if we're in an asyncio event loop (like Streamlit)
            import asyncio
            in_async_loop = False
            try:
                asyncio.get_running_loop()
                in_async_loop = True
                logger.warning("Running in asyncio context - setting up Playwright in separate thread")
            except RuntimeError:
                # No event loop running, safe to proceed normally
                pass
            
            if in_async_loop:
                # Run Playwright setup in a separate thread to avoid asyncio conflicts
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._setup_playwright_sync, headless, window_size, mobile_device_name, browser_type)
                    return future.result(timeout=30)
            else:
                return self._setup_playwright_sync(headless, window_size, mobile_device_name, browser_type)
            
        except Exception as e:
            logger.error(f"Playwright setup failed: {e}")
            self.close()
            return False
    
    def _setup_playwright_sync(self, headless=True, window_size="1920,1080", mobile_device_name: Optional[str] = None, browser_type="Chromium"):
        """Internal method to setup Playwright synchronously - always runs outside asyncio loop"""
        if self.cloud_mode:
            logger.warning("Browser automation disabled in cloud deployment mode")
            return False
            
        if not BROWSER_AUTOMATION_AVAILABLE:
            logger.warning("Browser automation libraries not available")
            return False
            
        try:
            self._pw = sync_playwright().start()
            
            # Select browser engine based on browser_type
            browser_engine = self._pw.chromium  # default
            if browser_type == "Firefox":
                browser_engine = self._pw.firefox
            elif browser_type == "Safari (WebKit)":
                browser_engine = self._pw.webkit
            elif browser_type == "Chromium":
                browser_engine = self._pw.chromium
            
            # Use simple, stable browser launch
            launch_args = {
                "headless": bool(headless),  # default headless for stability
                "args": ["--no-sandbox", "--disable-dev-shm-usage"]
            }
            
            try:
                self.browser = browser_engine.launch(**launch_args)
                logger.info(f"✅ {browser_type} browser launched successfully")
            except Exception as launch_e:
                logger.error(f"Browser launch failed: {launch_e}")
                # Try with absolutely minimal args
                self.browser = browser_engine.launch()

            # Simple context args without problematic features
            dev = self._device_preset(self._pw, mobile_device_name)
            if dev:
                ctx_args = {**dev}
            else:
                try:
                    w, h = [int(x) for x in (window_size or "1920,1080").split(",")]
                except Exception:
                    w, h = 1920, 1080
                ctx_args = {"viewport": {"width": w, "height": h}}
            
            # Add video recording if requested
            if self.recording_enabled:
                try:
                    import tempfile as _tmp
                    self.video_dir = _tmp.mkdtemp(prefix="pw_video_")
                    # Playwright expects record_video_dir & optional size
                    ctx_args.update({
                        "record_video_dir": self.video_dir,
                        "record_video_size": ctx_args.get("viewport", {"width": 1920, "height": 1080}),
                    })
                    logger.info(f"🎥 Video recording enabled to dir: {self.video_dir}")
                except Exception as _e:
                    logger.warning(f"Could not enable video recording, continuing without it: {_e}")
                    self.recording_enabled = False
            
            # Live preview: start later after page is created
            
            # Create context with progressive fallback
            fallback_attempts = [
                ("with device/viewport settings", ctx_args),
                ("with basic viewport", {"viewport": {"width": 1920, "height": 1080}}),
                ("with minimal settings", {}),
            ]
            
            success = False
            for attempt_name, attempt_args in fallback_attempts:
                try:
                    logger.info(f"Creating browser context {attempt_name}...")
                    self.context = self.browser.new_context(**attempt_args)
                    self.page = self.context.new_page()
                    logger.info(f"✅ Browser context created successfully {attempt_name}")
                    success = True
                    break
                except Exception as context_e:
                    logger.warning(f"Context creation {attempt_name} failed: {context_e}")
                    if self.context:
                        try:
                            self.context.close()
                        except:
                            pass
                        self.context = None
                    continue
            
            if not success:
                raise Exception("All browser context creation attempts failed")
            
            # Set conservative timeouts
            self.page.set_default_timeout(60000)  # 60 seconds
            self.page.set_default_navigation_timeout(60000)
            
            # Set a simple user agent
            try:
                self.page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
            except Exception:
                pass
            
            # Start live preview worker if enabled
            if self.live_preview_enabled:
                try:
                    self._start_live_preview()
                except Exception as _e:
                    logger.warning(f"Could not start live preview: {_e}")
                    self.live_preview_enabled = False
                
            logger.info("✅ Playwright driver setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"_setup_playwright_sync failed: {e}")
            return False

    def capture_screenshot(self, url, full_page=True, wait_time=5, max_retries=3):
        if not self.setup_driver():
            logger.error("Failed to setup browser driver")
            return None
        
        # Validate URL format
        if not url or not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL format: {url}")
            return None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Screenshot attempt {attempt + 1}/{max_retries + 1} for {url}")
                else:
                    logger.info(f"Capturing screenshot for: {url}")
                
                # Test basic connectivity first
                try:
                    import requests
                    response = requests.head(url, timeout=10, allow_redirects=True)
                    logger.info(f"URL connectivity test: {response.status_code}")
                except Exception as conn_e:
                    logger.warning(f"URL connectivity test failed: {conn_e}, proceeding anyway...")
                
                # Navigate with increased timeout and better error handling
                logger.info("Navigating to URL...")
                self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
                
                if wait_time:
                    logger.info(f"Waiting {wait_time} seconds for page to stabilize...")
                    self.page.wait_for_timeout(int(wait_time * 1000))
                
                # Wait for any lazy-loaded content with better timeout handling
                try:
                    logger.info("Waiting for network idle...")
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                    logger.info("Network idle achieved")
                except Exception:
                    # If networkidle times out, try load state instead
                    try:
                        self.page.wait_for_load_state("load", timeout=5000)
                        logger.info("Page load state achieved")
                    except Exception:
                        logger.info("Load state timeout, proceeding with screenshot anyway")
                
                # Take screenshot with increased timeout
                logger.info(f"Taking screenshot (full_page={full_page})")
                png = self.page.screenshot(full_page=bool(full_page), timeout=90000)
                logger.info("✅ Screenshot captured successfully")
                return Image.open(BytesIO(png))
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Screenshot attempt {attempt + 1} failed for {url}: {error_msg}")
                
                # Provide specific error guidance
                if "timeout" in error_msg.lower():
                    logger.info("💡 Suggestion: The page may be slow to load. Try reducing 'wait_time' or unchecking 'Full Page Screenshot'")
                elif "net::" in error_msg.lower() or "dns" in error_msg.lower():
                    logger.info("💡 Suggestion: Check if the URL is correct and accessible from your network")
                elif "blocked" in error_msg.lower():
                    logger.info("💡 Suggestion: The site may be blocking automated access. Try a different URL")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                
                # Final attempt with fallback strategies
                logger.info("Attempting fallback strategies...")
                
                # Try without full page
                if full_page:
                    logger.info("Fallback: trying screenshot without full_page...")
                    try:
                        png = self.page.screenshot(full_page=False, timeout=45000)
                        logger.info("✅ Fallback screenshot (viewport only) captured successfully")
                        return Image.open(BytesIO(png))
                    except Exception as fallback_e:
                        logger.error(f"❌ Viewport fallback also failed: {fallback_e}")
                
                # Try with reduced wait time
                logger.info("Fallback: trying with reduced wait time...")
                try:
                    self.page.goto(url, wait_until="commit", timeout=30000)
                    self.page.wait_for_timeout(2000)  # Reduced wait time
                    png = self.page.screenshot(full_page=False, timeout=30000)
                    logger.info("✅ Quick fallback screenshot captured successfully")
                    return Image.open(BytesIO(png))
                except Exception as quick_fallback_e:
                    logger.error(f"❌ Quick fallback also failed: {quick_fallback_e}")
                
                return None

    def get_targeted_dom_inspection(self) -> str:
        if not self.page:
            return "Could not get page styles: driver not available."
        script = """
            (() => {
                const getElementInfo = (element) => {
                    if (!element) return null;
                    const style = window.getComputedStyle(element);
                    return {
                        tagName: element.tagName,
                        class: element.className,
                        id: element.id,
                        text: (element.innerText || '').substring(0, 50),
                        styles: {
                            'font-family': style.fontFamily,
                            'font-size': style.fontSize,
                            'color': style.color,
                            'background-color': style.backgroundColor,
                            'padding': style.padding,
                            'margin': style.margin,
                            'border': style.border,
                            'border-radius': style.borderRadius,
                            'box-shadow': style.boxShadow
                        }
                    };
                };
                const selectors = ['h1','h2','p','a','button','nav','footer','[class*="hero"]','[class*="card"]','[class*="button"]'];
                const inspection = {};
                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    if (el) inspection[selector] = getElementInfo(el);
                }
                return inspection;
            })();
        """
        try:
            styles = self.page.evaluate(script)
            logger.info("✅ Extracted targeted DOM inspection data from web page.")
            return json.dumps(styles, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to extract targeted DOM inspection data: {e}")
            return f"Error extracting styles: {e}"

    def count_elements(self, selector: str) -> int:
        if not self.page:
            return 0
        try:
            return self.page.locator(selector).count()
        except Exception:
            return 0

    def navigate(self, url: str, wait_time: float = 2.0):
        if not self.page:
            return False
        try:
            logger.info(f"Navigating to: {url}")
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if wait_time:
                self.page.wait_for_timeout(int(wait_time * 1000))
            logger.info("✅ Navigation completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Navigation failed for {url}: {e}")
            return False

    def close(self):
        # Stop live preview thread
        if self.live_preview_thread:
            self.live_preview_enabled = False
            try:
                self.live_preview_thread.join(timeout=2)
            except Exception:
                pass
            self.live_preview_thread = None
            
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

    def detect_sections(self,
                        min_height: int = 280,
                        min_width: int = 400,
                        max_sections: int = 12,
                        custom_selectors: Optional[List[str]] = None,
                        root_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect content sections on the page using common landmarks and heuristics.
        Optionally accepts custom CSS selectors to control which elements are treated as sections.
        Returns a list of dicts: {label, selector, bbox, image(PIL)} ordered by Y position.
        """
        results: List[Dict[str, Any]] = []
        if not self.page:
            return results
        try:
            # Determine base root
            root_sel = root_selector or 'main'
            try:
                root_count = self.page.locator(root_sel).count()
            except Exception:
                root_count = 0
            if root_count < 1:
                root_sel = '[role="main"]'
                try:
                    root_count = self.page.locator(root_sel).count()
                except Exception:
                    root_count = 0
                if root_count < 1:
                    root_sel = 'body'

            candidates: List[Dict[str, Any]] = []
            # Candidate groups with priority. If custom selectors provided, use them first.
            group_selectors: List[str] = []
            if custom_selectors:
                # Normalize and qualify with root if selector is not absolute
                for sel in custom_selectors:
                    s = (sel or '').strip()
                    if not s:
                        continue
                    # If selector starts with body/html or is :root, use as-is; else qualify under root
                    if s.startswith(('body', 'html', ':root', '#', '.', '[')):
                        group_selectors.append(s)
                    else:
                        group_selectors.append(f"{root_sel} {s}")
            # Fallback defaults appended after customs
            group_selectors.extend([
                f"{root_sel} section",
                f"{root_sel} article",
                f"{root_sel} div[class*='section']",
                f"{root_sel} div[class*='container']",
            ])

            for css in group_selectors:
                loc = self.page.locator(css)
                try:
                    cnt = loc.count()
                except Exception:
                    cnt = 0
                for i in range(cnt):
                    el = loc.nth(i)
                    try:
                        bb = el.bounding_box()
                        if not bb:
                            continue
                        if bb.get('height', 0) < min_height or bb.get('width', 0) < min_width:
                            continue
                        # Grab first heading text as label
                        label = None
                        try:
                            h = el.locator('h1, h2, h3').first
                            if h.count() > 0:
                                text = h.inner_text(timeout=1000) or ''
                                label = text.strip()[:80]
                        except Exception:
                            label = None
                        if not label:
                            label = f"{css} @y={int(bb.get('y',0))}"
                        # Screenshot element
                        try:
                            png = el.screenshot(timeout=15000)
                            img = Image.open(BytesIO(png)).convert('RGB')
                        except Exception:
                            img = None
                        candidates.append({
                            'selector': css,
                            'index': i,
                            'bbox': bb,
                            'label': label,
                            'image': img,
                        })
                    except Exception:
                        continue

            # Deduplicate overlapping candidates (keep larger height) and sort by y
            def key_y(c):
                return c['bbox'].get('y', 0)
            candidates.sort(key=key_y)

            def overlaps(a, b, thresh=0.5):
                ax, ay, aw, ah = a['bbox']['x'], a['bbox']['y'], a['bbox']['width'], a['bbox']['height']
                bx, by, bw, bh = b['bbox']['x'], b['bbox']['y'], b['bbox']['width'], b['bbox']['height']
                ix = max(0, min(ax+aw, bx+bw) - max(ax, bx))
                iy = max(0, min(ay+ah, by+bh) - max(ay, by))
                inter = ix * iy
                if inter <= 0:
                    return False
                area = min(aw*ah, bw*bh)
                return inter/area > thresh

            filtered: List[Dict[str, Any]] = []
            for c in candidates:
                if c.get('image') is None:
                    continue
                drop = False
                for f in filtered:
                    if overlaps(c, f):
                        # keep the taller one
                        if c['bbox']['height'] <= f['bbox']['height']:
                            drop = True
                            break
                        else:
                            # replace
                            filtered.remove(f)
                            break
                if not drop:
                    filtered.append(c)
                if len(filtered) >= max_sections:
                    break

            logger.info(f"✅ Detected {len(filtered)} content section(s) for comparison")
            return filtered
        except Exception as e:
            logger.error(f"❌ Section detection failed: {e}")
            return results

    def capture_fluid_breakpoint_animation(self, url, start_width=320, end_width=1200, steps=15, frame_duration=0.2, wait_time=3):
        if not self.setup_driver(headless=True):
            return None
        try:
            logger.info(f"Starting fluid breakpoint capture for {url} from {start_width}px to {end_width}px.")
            self.page.goto(url, wait_until="domcontentloaded")
            if wait_time:
                self.page.wait_for_timeout(int(wait_time * 1000))
            images = []
            fixed_height = 1080
            for i in range(steps):
                current_width = start_width + int((end_width - start_width) * (i / max(1, (steps - 1))))
                try:
                    self.page.set_viewport_size({"width": current_width, "height": fixed_height})
                except Exception:
                    # fallback on context if needed
                    try:
                        self.context.set_viewport_size({"width": current_width, "height": fixed_height})
                    except Exception:
                        pass
                self.page.wait_for_timeout(100)
                png = self.page.screenshot(full_page=False)
                images.append(Image.open(BytesIO(png)).convert("RGB"))
            # Ensure all frames have the same size (pad to max width)
            if not images:
                return None
            max_width = max(img.width for img in images)
            target_size = (max_width, fixed_height)
            padded_frames = []
            for img in images:
                if img.size == target_size:
                    padded_frames.append(img)
                else:
                    canvas = Image.new("RGB", target_size, (255, 255, 255))
                    canvas.paste(img, (0, 0))
                    padded_frames.append(canvas)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as f:
                gif_path = f.name
            imageio.mimsave(gif_path, padded_frames, duration=frame_duration, loop=0)
            logger.info(f"✅ Successfully created fluid breakpoint GIF at: {gif_path}")
            return gif_path
        except Exception as e:
            logger.error(f"❌ Fluid breakpoint animation failed for {url}: {e}", exc_info=True)
            return None
    
    def _start_live_preview(self):
        """Start a background thread that captures live screenshots for the preview."""
        import threading
        
        def live_preview_worker():
            logger.info("✅ Live preview worker thread started")
            while self.live_preview_enabled and self.page:
                try:
                    if self.page and self.live_preview_callback:
                        # Capture a small screenshot for live preview with timeout
                        # Use a longer timeout and catch greenlet errors
                        try:
                            png = self.page.screenshot(full_page=False, timeout=5000)
                            img = Image.open(BytesIO(png))
                            # Resize for faster transmission
                            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                            self.live_preview_callback(img)
                        except Exception as screenshot_err:
                            # If greenlet or threading issues occur, disable live preview
                            if "greenlet" in str(screenshot_err).lower() or "switch to a different thread" in str(screenshot_err):
                                logger.warning("Live preview disabled due to threading conflicts")
                                self.live_preview_enabled = False
                                break
                            logger.debug(f"Live preview screenshot error: {screenshot_err}")
                        
                        time.sleep(1.0)  # Update every 1 second (reduced frequency)
                    else:
                        time.sleep(2)  # Wait longer if page/callback not available
                except Exception as e:
                    logger.debug(f"Live preview worker error: {e}")
                    time.sleep(3)  # Wait longer on error to avoid spam
            logger.info("✅ Live preview worker thread stopped")
        
        self.live_preview_thread = threading.Thread(target=live_preview_worker, daemon=True)
        self.live_preview_thread.start()
    
    def get_video_path(self):
        """Get the path to the recorded video file."""
        if not self.video_dir or not self.page:
            logger.warning("No video directory or page available for video recording")
            return None
        try:
            # Close the page to finalize the video
            video_path = self.page.video.path()
            if video_path and os.path.exists(video_path):
                logger.info(f"Video recording found at: {video_path}")
                return video_path
            else:
                logger.warning(f"Video file not found at expected path: {video_path}")
                # Try to find any webm files in the video directory
                import glob
                video_files = glob.glob(os.path.join(self.video_dir, "*.webm"))
                if video_files:
                    logger.info(f"Found video file: {video_files[0]}")
                    return video_files[0]
                return None
        except Exception as e:
            logger.warning(f"Could not get video path: {e}")
            # Try to find any video files in the directory
            try:
                import glob
                video_files = glob.glob(os.path.join(self.video_dir, "*.webm"))
                if video_files:
                    logger.info(f"Found video file via directory search: {video_files[0]}")
                    return video_files[0]
            except Exception as e2:
                logger.warning(f"Could not search video directory: {e2}")
            return None
    
    def save_video_recording(self, destination_path: str) -> Optional[str]:
        """Save the recorded video to a specific location."""
        try:
            if not self.recording_enabled:
                return None
                
            # Close the page to finalize the video
            if self.page:
                video_path = self.get_video_path()
                self.page.close()
                self.page = None
                
                if video_path and os.path.exists(video_path):
                    import shutil
                    shutil.move(video_path, destination_path)
                    logger.info(f"✅ Video recording saved to: {destination_path}")
                    return destination_path
            return None
        except Exception as e:
            logger.error(f"❌ Failed to save video recording: {e}")
            return None

class EnhancedJiraIntegration:
    def __init__(self):
        self.server_url = os.getenv("JIRA_SERVER_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        self.jira_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        if all([self.server_url, self.email, self.api_token, self.project_key]):
            try:
                self.jira_client = JIRA(server=self.server_url, basic_auth=(self.email, self.api_token))
                logger.info(f"Jira client initialized for project '{self.project_key}'")
            except Exception as e:
                logger.error(f"Failed to initialize Jira client: {e}")
        else:
            logger.warning("Jira configuration is incomplete. Integration disabled.")
    
    def create_design_qa_ticket(self, issue_details: dict, assignee_email: Optional[str] = None, attachments: Optional[List[str]] = None):
        if not self.jira_client:
            return {"success": False, "error": "Jira client not initialized. Check configuration."}
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': issue_details.get('title', 'Automated Design QA Issue'),
                'description': issue_details.get('description', 'No description provided.'),
                'issuetype': {'name': 'Bug'},
                'priority': {'name': issue_details.get('priority', 'Medium')}
            }
            if assignee_email:
                users = self.jira_client.search_users(query=assignee_email)
                if users:
                    issue_dict['assignee'] = {'accountId': users[0].accountId}
                    logger.info(f"Found user {users[0].displayName} for assignment.")
                else:
                    logger.warning(f"Could not find Jira user with email: {assignee_email}")
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            logger.info(f"Successfully created Jira ticket: {new_issue.key}")
            
            if attachments:
                for attachment_path in attachments:
                    try:
                        with open(attachment_path, 'rb') as f:
                            self.jira_client.add_attachment(issue=new_issue, attachment=f)
                        logger.info(f"Added attachment '{os.path.basename(attachment_path)}' to {new_issue.key}")
                    except Exception as e:
                        logger.error(f"Failed to add attachment {attachment_path} to {new_issue.key}: {e}")
            
            return {
                "success": True, 
                "ticket_key": new_issue.key, 
                "ticket_url": f"{self.server_url}/browse/{new_issue.key}"
            }
        except JIRAError as e:
            logger.error(f"Jira API Error: Status {e.status_code} - {e.text}")
            return {"success": False, "error": f"Jira API Error: {e.text}"}
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

class FigmaDesignComparator:
    def __init__(self):
        self.figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": self.figma_token} if self.figma_token else {}
        logger.info(f"Figma token configured: {'Yes' if self.figma_token else 'No'}")

    def get_specific_node_from_url(self, figma_url: str):
        try:
            s = (figma_url or "").strip()
            file_key_match = re.search(r'/(?:design|file)/([A-Za-z0-9_-]{22,})', s)
            if not file_key_match: return None
            file_key = file_key_match.group(1)
            node_id_match = re.search(r'[?&]node-id=([\d-]+)', s)
            node_id = node_id_match.group(1).replace('-', ':') if node_id_match else "0:1"
            return {"file_id": file_key, "node_id": node_id}
        except Exception: return None

    def get_node_image(self, file_id, node_id, scale=3):
        if not self.figma_token:
            logger.error("Figma access token not configured. Please set FIGMA_ACCESS_TOKEN environment variable.")
            return None
        if not file_id:
            logger.error("Figma file ID is required but not provided.")
            return None
            
        try:
            api_url = f"{self.base_url}/images/{file_id}"
            params = {'ids': node_id, 'scale': scale, 'format': 'png'}
            response = requests.get(api_url, headers=self.headers, params=params, timeout=60)
            
            # Enhanced error handling for different HTTP status codes
            if response.status_code == 403:
                logger.error(f"Figma API access denied (403). Token may not have permission for file: {file_id}")
                return None
            elif response.status_code == 404:
                logger.error(f"Figma file not found (404). File ID may be invalid or private: {file_id}")
                return None
            elif response.status_code == 401:
                logger.error(f"Figma API unauthorized (401). Token may be invalid or expired.")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            # Check for Figma API-specific errors
            if data.get('err'):
                logger.error(f"Figma API error: {data.get('err')}")
                return None
            if not data.get('images', {}).get(node_id):
                logger.error(f"No image returned for node {node_id} in file {file_id}. Node may not exist or be visible.")
                return None
                
            img_response = requests.get(data['images'][node_id], timeout=60)
            img_response.raise_for_status()
            return Image.open(BytesIO(img_response.content))
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error accessing Figma API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving Figma image: {e}")
            return None

    def _traverse_and_extract(self, node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not node:
            return None
        props = {}
        node_type = node.get('type')
        if node_type == 'TEXT':
            props['type'] = 'Text'
            props['characters'] = node.get('characters')
            style = node.get('style', {})
            props['font'] = {
                'family': style.get('fontFamily'),
                'size': style.get('fontSize'),
                'weight': style.get('fontWeight'),
                'lineHeight': style.get('lineHeightPx'),
                'textAlign': style.get('textAlignHorizontal')
            }
            props['color'] = node.get('fills')
        elif node_type in ['RECTANGLE', 'FRAME', 'COMPONENT', 'INSTANCE']:
            props['type'] = node_type
            props['size'] = node.get('absoluteBoundingBox')
            props['backgroundColor'] = node.get('fills')
            props['stroke'] = node.get('strokes')
            props['cornerRadius'] = node.get('cornerRadius')
        if 'children' in node and props:
            props['children'] = [self._traverse_and_extract(child) for child in node['children'] if child]
            props['children'] = [child for child in props['children'] if child]
        return props if props else None

    def get_node_properties(self, file_id: str, node_id: str) -> str:
        if not self.figma_token:
            error_msg = "Figma access token not configured. Please set FIGMA_ACCESS_TOKEN environment variable."
            logger.error(error_msg)
            return f"Could not get Figma properties: {error_msg}"
        if not file_id or not node_id:
            error_msg = "Missing file_id or node_id parameters."
            logger.error(error_msg)
            return f"Could not get Figma properties: {error_msg}"
            
        api_url = f"{self.base_url}/files/{file_id}/nodes"
        params = {'ids': node_id, 'geometry': 'paths'}
        
        try:
            response = requests.get(api_url, headers=self.headers, params=params, timeout=30)
            
            # Enhanced error handling for different HTTP status codes
            if response.status_code == 403:
                error_msg = f"Figma API access denied (403). Token may not have permission for file: {file_id}"
                logger.error(error_msg)
                return f"Error getting Figma properties: {error_msg}"
            elif response.status_code == 404:
                error_msg = f"Figma file not found (404). File ID may be invalid or private: {file_id}"
                logger.error(error_msg)
                return f"Error getting Figma properties: {error_msg}"
            elif response.status_code == 401:
                error_msg = "Figma API unauthorized (401). Token may be invalid or expired."
                logger.error(error_msg)
                return f"Error getting Figma properties: {error_msg}"
                
            response.raise_for_status()
            data = response.json()
            
            # Check for Figma API-specific errors
            if data.get('err'):
                error_msg = f"Figma API error: {data.get('err')}"
                logger.error(error_msg)
                return f"Error getting Figma properties: {error_msg}"
                
            root_node = data.get('nodes', {}).get(node_id, {}).get('document')
            if not root_node:
                error_msg = f"Node {node_id} not found in file {file_id}. Node may not exist or be accessible."
                logger.error(error_msg)
                return f"Error getting Figma properties: {error_msg}"
                
            extracted_properties = self._traverse_and_extract(root_node)
            logger.info("✅ Extracted rich 'Inspect' property tree from Figma API.")
            return json.dumps(extracted_properties, indent=2)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error accessing Figma API: {e}"
            logger.error(error_msg)
            return f"Error getting Figma properties: {error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error retrieving Figma properties: {e}"
            logger.error(error_msg)
            return f"Error getting Figma properties: {error_msg}"

    def compare_images(self, image1, image2, diff_color=(255, 50, 50)):
        """
        UPGRADED: Compares two images, calculates SSIM, and generates a visual diff image.
        """
        if not image1 or not image2:
            return 0.0, None

        try:
            # Convert both images to RGB for consistent processing
            img1_rgb = image1.convert('RGB')
            img2_rgb = image2.convert('RGB')

            # Resize into a common canvas, preserving aspect (letterbox) to avoid distortion
            def _fit_to_canvas(src: Image.Image, target_size: tuple[int,int]) -> Image.Image:
                tw, th = target_size
                r = min(tw / src.width, th / src.height)
                new_w, new_h = max(1, int(src.width * r)), max(1, int(src.height * r))
                resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)
                canvas = Image.new('RGB', target_size, (255, 255, 255))
                x = (tw - new_w) // 2
                y = (th - new_h) // 2
                canvas.paste(resized, (x, y))
                return canvas

            target_w = max(img1_rgb.width, img2_rgb.width)
            target_h = max(img1_rgb.height, img2_rgb.height)
            # Cap target size to avoid huge images blowing up memory
            MAX_SIDE = 3000
            scale = min(MAX_SIDE / max(1, target_w), MAX_SIDE / max(1, target_h), 1.0)
            target_w = max(50, int(target_w * scale))
            target_h = max(50, int(target_h * scale))

            img1_resized = _fit_to_canvas(img1_rgb, (target_w, target_h))
            img2_resized = _fit_to_canvas(img2_rgb, (target_w, target_h))

            # Convert to grayscale for SSIM calculation
            img1_gray = img1_resized.convert('L')
            img2_gray = img2_resized.convert('L')

            # Calculate Structural Similarity
            similarity_score = float(ssim(np.array(img1_gray), np.array(img2_gray)))

            # --- Generate Visual Diff ---
            # Create a difference image using absolute difference
            diff = ImageChops.difference(img1_resized, img2_resized)

            # Convert to grayscale for thresholding
            diff_gray = diff.convert('L')

            # Use a more conservative threshold to highlight only significant differences
            threshold = 60  # Increased threshold to reduce noise
            diff_thresholded = diff_gray.point(lambda p: 255 if p > threshold else 0)

            # Apply morphological operations to clean up the mask
            diff_array = np.array(diff_thresholded)

            # Remove small noise using more conservative morphological operations
            kernel = np.ones((3, 3))
            diff_array = ndimage.binary_closing(diff_array, structure=kernel).astype(np.uint8)
            diff_array = ndimage.binary_opening(diff_array, structure=kernel).astype(np.uint8) * 255

            # Convert back to PIL Image
            diff_mask = Image.fromarray(diff_array, 'L')

            # Create a red-tinted version of the web screenshot for highlighting differences
            red_tint_overlay = Image.new('RGB', img2_resized.size, diff_color)
            
            # Blend the web screenshot with the red tint to create the highlighted version
            highlighted_version = Image.blend(img2_resized, red_tint_overlay, alpha=0.4)

            # Use the mask to composite the highlighted version onto the original web screenshot
            # Where the mask is white (differences), use the highlighted version.
            # Where the mask is black (no differences), use the original web screenshot.
            diff_highlighted = Image.composite(highlighted_version, img2_resized, diff_mask)

            logger.info("✅ Generated visual difference highlight image.")

            return similarity_score, diff_highlighted

        except Exception as e:
            logger.error(f"❌ Image comparison or diff generation failed: {e}", exc_info=True)
            return 0.0, None

class AutomatedDesignValidator:
    def __init__(self, driver):
        self.driver = driver

    def validate_page(self, url):
        if not self.driver.setup_driver():
            return []
        issues = []
        try:
            self.driver.navigate(url)
            time.sleep(2)
            h1_count = self.driver.count_elements("h1")
            if h1_count > 1:
                issues.append({"category": "Content Structure", "type": "SEO/Accessibility", "description": f"Multiple H1 headings found ({h1_count}).", "severity": "Medium"})
            return issues
        except Exception:
            return []

class DesignQAProcessor:
    def __init__(self):
        self.figma_comparator = FigmaDesignComparator()
        # Switch to Playwright-based driver
        self.chrome_driver = EnhancedPlaywrightDriver()
        self.jira_integration = EnhancedJiraIntegration()
        self.validator = AutomatedDesignValidator(self.chrome_driver)
        self.ai_client = None
        try:
            # Primary: default env-based configuration
            self.ai_client = OpenAI()
            logger.info("OpenAI AI client initialized.")
        except Exception as e1:
            # Fallback: disable proxy/env influence
            try:
                self.ai_client = OpenAI(http_client=httpx.Client(trust_env=False))
                logger.info("OpenAI AI client initialized with proxy-disabled HTTP client.")
            except Exception as e2:
                self.ai_client = None
                logger.error(f"Failed to initialize OpenAI client: {e2}")

    def _ensure_dir(self, path: str):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass

    def _save_design_artifacts(self,
                               base_dir: str,
                               page_name: str,
                               figma_image: Image.Image,
                               web_image: Image.Image,
                               diff_image: Optional[Image.Image],
                               comparison_image: Optional[Image.Image],
                               figma_props: str,
                               web_dom_inspection: str,
                               similarity: float,
                               web_url: str,
                               figma_url: str,
                               device: str,
                               video_path: Optional[str] = None,
                               animation_gif_path: Optional[str] = None) -> Dict[str, str]:
        """Save images, JSON/text, video, and build an HTML report; try PDF if pdfkit is installed."""
        # Create run folder with webpage info
        try:
            from datetime import datetime as _dt
            from urllib.parse import urlparse
            timestamp = _dt.now().strftime("%Y%m%d_%H%M%S")
            
            # Extract domain/path from web URL for folder name
            parsed_url = urlparse(web_url)
            domain_part = parsed_url.netloc.replace('www.', '').replace('.', '_')
            path_part = parsed_url.path.strip('/').replace('/', '_') if parsed_url.path.strip('/') else 'home'
            
            # Limit length and clean filename
            webpage_part = f"{domain_part}_{path_part}"[:30].rstrip('_')
            stamp = f"test_report_{webpage_part}_{timestamp}"
        except Exception:
            stamp = f"test_report_{_dt.now().strftime('%Y%m%d_%H%M%S')}"
        run_dir = os.path.join(base_dir, stamp)
        self._ensure_dir(run_dir)
        shots_dir = os.path.join(run_dir, "screenshots")
        self._ensure_dir(shots_dir)

        paths: Dict[str, str] = {}
        # Save images
        try:
            fig_path = os.path.join(shots_dir, "figma.png")
            figma_image.save(fig_path, format="PNG")
            paths["figma_image"] = fig_path
        except Exception:
            pass
        try:
            web_path = os.path.join(shots_dir, "web.png")
            web_image.save(web_path, format="PNG")
            paths["web_image"] = web_path
        except Exception:
            pass
        try:
            if diff_image:
                diff_path = os.path.join(shots_dir, "diff.png")
                diff_image.save(diff_path, format="PNG")
                paths["diff_image"] = diff_path
        except Exception:
            pass
        try:
            if comparison_image:
                comp_path = os.path.join(run_dir, "comparison.png")
                comparison_image.save(comp_path, format="PNG")
                paths["comparison_image"] = comp_path
        except Exception:
            pass
        
        # Save video recording if available
        try:
            if video_path and os.path.exists(video_path):
                video_dest = os.path.join(run_dir, "test_recording.webm")
                import shutil
                shutil.copy2(video_path, video_dest)
                paths["video_recording"] = video_dest
                logger.info(f"✅ Video recording saved to artifacts: {video_dest}")
        except Exception as e:
            logger.warning(f"Failed to save video recording: {e}")

        # Save responsive animation GIF if provided
        try:
            if animation_gif_path and os.path.exists(animation_gif_path):
                import shutil
                gif_dest = os.path.join(run_dir, "responsive.gif")
                shutil.copy2(animation_gif_path, gif_dest)
                paths["responsive_gif"] = gif_dest
                logger.info(f"✅ Responsive animation GIF saved to artifacts: {gif_dest}")
        except Exception as e:
            logger.warning(f"Failed to save responsive GIF: {e}")

        # Save props and dom
        try:
            with open(os.path.join(run_dir, "figma_props.json"), "w", encoding="utf-8") as f:
                f.write(figma_props or "")
            paths["figma_props"] = os.path.join(run_dir, "figma_props.json")
        except Exception:
            pass
        try:
            with open(os.path.join(run_dir, "web_dom_inspection.json"), "w", encoding="utf-8") as f:
                f.write(web_dom_inspection or "")
            paths["web_dom_inspection"] = os.path.join(run_dir, "web_dom_inspection.json")
        except Exception:
            pass

        # Build HTML report
        def esc(s: str) -> str:
            import html
            return html.escape(s or "")
        report_html = os.path.join(run_dir, "design_report.html")
        try:
            rows = []
            if os.path.exists(paths.get("figma_image", "")):
                rows.append(f'<div><h3>Figma</h3><img src="screenshots/figma.png" style="max-width:100%;border:1px solid #ddd"/></div>')
            if os.path.exists(paths.get("web_image", "")):
                rows.append(f'<div><h3>Web</h3><img src="screenshots/web.png" style="max-width:100%;border:1px solid #ddd"/></div>')
            if os.path.exists(paths.get("diff_image", "")):
                rows.append(f'<div><h3>Visual Diff</h3><img src="screenshots/diff.png" style="max-width:100%;border:1px solid #ddd"/></div>')
            if os.path.exists(paths.get("comparison_image", "")):
                rows.append(f'<div><h3>Side-by-Side</h3><img src="comparison.png" style="max-width:100%;border:1px solid #ddd"/></div>')
            
            # Add video player if video is available
            if os.path.exists(paths.get("video_recording", "")):
                rows.append(f'<div><h3>Test Recording</h3><video controls style="max-width:100%;border:1px solid #ddd"><source src="test_recording.webm" type="video/webm">Your browser does not support the video tag.</video></div>')
            # Add responsive GIF if available
            if os.path.exists(paths.get("responsive_gif", "")):
                rows.append(f'<div><h3>Responsive Animation</h3><img src="responsive.gif" style="max-width:100%;border:1px solid #ddd"/></div>')
                
            blocks = "\n".join(rows)
            html_body = f"""
<!DOCTYPE html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/>
<title>Design QA Report</title>
<style>
 body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
 .summary {{ background:#f5f7fa; padding:10px 12px; border-radius:8px; margin-bottom: 16px; }}
 img, video {{ margin-bottom:14px; }}
 pre {{ background:#f2f2f2; padding:10px; border-radius:6px; overflow:auto; }}
 h2, h3 {{ margin-bottom: 8px; }}
 .pass {{ color:#0a7f3f; }} .fail {{ color:#b00020; }}
 .meta {{ color:#666; }}
 .grid {{ display:grid; grid-template-columns: 1fr; gap: 20px; }}
 @media(min-width: 1200px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
 </style></head>
<body>
 <h1>Design QA Report</h1>
 <div class=\"summary\">
   <div class=\"meta\"><strong>Page:</strong> {esc(page_name)} &nbsp;|&nbsp; <strong>Device:</strong> {esc(device)}</div>
   <div><strong>Web URL:</strong> <code>{esc(web_url)}</code></div>
   <div><strong>Figma URL:</strong> <code>{esc(figma_url)}</code></div>
   <div><strong>Similarity Score:</strong> {similarity:.2%}</div>
 </div>
 <div class=\"grid\">
   {blocks}
 </div>
 <h2>Technical Details</h2>
 <h3>Figma Properties (truncated)</h3>
 <pre>{esc((figma_props or '')[:4000])}</pre>
 <h3>Web DOM Inspection (truncated)</h3>
 <pre>{esc((web_dom_inspection or '')[:4000])}</pre>
</body></html>
"""
            with open(report_html, "w", encoding="utf-8") as f:
                f.write(html_body)
            paths["report_html"] = report_html
        except Exception as e:
            logger.warning(f"Failed to write design HTML report: {e}")

        # Optional PDF via pdfkit
        try:
            import pdfkit  # type: ignore
            report_pdf = os.path.join(run_dir, "design_report.pdf")
            try:
                pdfkit.from_file(report_html, report_pdf)
                paths["report_pdf"] = report_pdf
            except Exception as e:
                logger.info(f"Design PDF generation skipped/failed: {e}")
        except Exception:
            pass

        return paths

    def _save_fluid_artifacts(self,
                               base_dir: str,
                               gif_path: str,
                               web_url: str,
                               start_width: int,
                               end_width: int,
                               steps: int,
                               frame_duration: float,
                               device: str = "Desktop") -> Dict[str, str]:
        """Save the fluid breakpoint GIF into a run folder and build an HTML report (and optional PDF)."""
        try:
            from datetime import datetime as _dt
            from urllib.parse import urlparse
            timestamp = _dt.now().strftime("%Y%m%d_%H%M%S")
            
            # Extract domain/path from web URL for folder name
            parsed_url = urlparse(web_url)
            domain_part = parsed_url.netloc.replace('www.', '').replace('.', '_')
            path_part = parsed_url.path.strip('/').replace('/', '_') if parsed_url.path.strip('/') else 'home'
            
            # Limit length and clean filename
            webpage_part = f"{domain_part}_{path_part}"[:30].rstrip('_')
            stamp = f"fluid_report_{webpage_part}_{timestamp}"
        except Exception:
            stamp = f"fluid_report_{_dt.now().strftime('%Y%m%d_%H%M%S')}"
        run_dir = os.path.join(base_dir, stamp)
        self._ensure_dir(run_dir)
        paths: Dict[str, str] = {}
        # Copy GIF into run folder
        try:
            import shutil
            dest_gif = os.path.join(run_dir, "fluid.gif")
            shutil.copyfile(gif_path, dest_gif)
            paths["gif"] = dest_gif
        except Exception as e:
            logger.warning(f"Failed to copy GIF: {e}")

        # Create HTML report
        def esc(s: str) -> str:
            import html
            return html.escape(str(s) if s is not None else "")
        report_html = os.path.join(run_dir, "fluid_report.html")
        try:
            html_body = f"""
<!DOCTYPE html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/>
<title>Fluid Breakpoint Report</title>
<style>
 body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
 .summary {{ background:#f5f7fa; padding:10px 12px; border-radius:8px; margin-bottom: 16px; }}
 img {{ max-width:100%; border:1px solid #ddd; }}
 .meta {{ color:#666; }}
 code {{ background:#f2f2f2; padding:2px 4px; border-radius:4px; }}
 </style></head>
<body>
 <h1>Fluid Breakpoint Report</h1>
 <div class=\"summary\">
   <div class=\"meta\"><strong>Device:</strong> {esc(device)}</div>
   <div><strong>Web URL:</strong> <code>{esc(web_url)}</code></div>
   <div><strong>Range:</strong> {esc(start_width)}px → {esc(end_width)}px</div>
   <div><strong>Frames:</strong> {esc(steps)} &nbsp;|&nbsp; <strong>Frame Duration:</strong> {esc(frame_duration)}s</div>
 </div>
 <h2>Animation</h2>
 <img src=\"fluid.gif\" alt=\"Responsive layout animation\" />
</body></html>
"""
            with open(report_html, "w", encoding="utf-8") as f:
                f.write(html_body)
            paths["report_html"] = report_html
        except Exception as e:
            logger.warning(f"Failed to write fluid HTML report: {e}")

        # Optional PDF via pdfkit
        try:
            import pdfkit  # type: ignore
            report_pdf = os.path.join(run_dir, "fluid_report.pdf")
            try:
                pdfkit.from_file(report_html, report_pdf)
                paths["report_pdf"] = report_pdf
            except Exception as e:
                logger.info(f"Fluid PDF generation skipped/failed: {e}")
        except Exception:
            pass

        return paths

    # ---------- Section-based comparison (alternative pipeline) ----------
    def _cv_match_figma_region(self, figma_img: Image.Image, section_img: Image.Image, scales: List[float] = [0.8, 0.9, 1.0, 1.1, 1.25]) -> Optional[Image.Image]:
        """Find the best-matching region in the Figma image for a given web section using template matching.
        Returns a cropped PIL image from Figma aligned to the section's area.
        """
        try:
            fig_rgb = figma_img.convert('RGB')
            sec_rgb = section_img.convert('RGB')
            fig_np = np.array(fig_rgb)  # RGB
            sec_np = np.array(sec_rgb)
            # Convert to grayscale
            fig_gray = cv2.cvtColor(fig_np, cv2.COLOR_RGB2GRAY)
            sec_gray = cv2.cvtColor(sec_np, cv2.COLOR_RGB2GRAY)
            h, w = sec_gray.shape[:2]
            # Cap Figma width to reduce compute (keeps proportions)
            MAX_FIG_W = 2400
            fh, fw = fig_gray.shape[:2]
            base_scale = 1.0
            if fw > MAX_FIG_W:
                base_scale = MAX_FIG_W / float(fw)
                fig_gray = cv2.resize(fig_gray, (int(fw * base_scale), int(fh * base_scale)), interpolation=cv2.INTER_AREA)
                fh, fw = fig_gray.shape[:2]
            best = None
            t0 = time.time()
            for s in scales:
                # Resize figma for this scale
                new_fw, new_fh = int(fw * s), int(fh * s)
                if new_fw < w or new_fh < h:
                    continue
                fig_scaled = cv2.resize(fig_gray, (new_fw, new_fh), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(fig_scaled, sec_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if (best is None) or (max_val > best[0]):
                    best = (max_val, max_loc, s, (new_fw, new_fh))
            if not best:
                return None
            _, (x, y), s, (new_fw, new_fh) = best
            # Map back to original figma coords
            scale_total = s * base_scale
            x0 = int(x / scale_total)
            y0 = int(y / scale_total)
            x1 = int((x + w) / scale_total)
            y1 = int((y + h) / scale_total)
            x0 = max(0, min(fig_rgb.width - 1, x0))
            y0 = max(0, min(fig_rgb.height - 1, y0))
            x1 = max(1, min(fig_rgb.width, x1))
            y1 = max(1, min(fig_rgb.height, y1))
            if x1 <= x0 or y1 <= y0:
                return None
            crop = fig_rgb.crop((x0, y0, x1, y1))
            logger.debug(f"Template matching done in {time.time()-t0:.2f}s; scale={s:.2f}, base_scale={base_scale:.3f}")
            return crop
        except Exception as e:
            logger.debug(f"Figma region matching failed: {e}")
            return None

    def _ssim_heatmap(self, a: Image.Image, b: Image.Image) -> tuple[float, Image.Image]:
        """Compute SSIM score and heatmap image (false color; red=diff) for two RGB images."""
        a_r = a.convert('RGB')
        b_r = b.convert('RGB')
        # Resize b to a's size for comparison
        b_resized = b_r.resize(a_r.size, Image.Resampling.LANCZOS)
        a_gray = np.array(a_r.convert('L'))
        b_gray = np.array(b_resized.convert('L'))
        score, ssim_map = ssim(a_gray, b_gray, full=True)
        # Heat where 1-ssim is high
        heat = (1.0 - ssim_map)
        # NumPy 2.0: ndarray.ptp() removed; use np.ptp(heat)
        heat_range = float(np.ptp(heat))
        if heat_range == 0.0:
            norm = np.zeros_like(heat)
        else:
            norm = (heat - heat.min()) / (heat_range + 1e-8)
        heat_uint8 = (np.clip(norm, 0, 1) * 255).astype(np.uint8)
        heat_color = cv2.applyColorMap(heat_uint8, cv2.COLORMAP_JET)
        heat_pil = Image.fromarray(cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGB)).resize(a_r.size, Image.Resampling.NEAREST)
        return float(score), heat_pil

    def _compose_section_row(self, fig_crop: Image.Image, web_sec: Image.Image, heatmap: Image.Image, score: float, title: str) -> Image.Image:
        """Compose a single row: Figma | Web | Heatmap with a header."""
        # Normalize height
        target_h = 600
        def scale_to_h(img):
            r = target_h / img.height
            return img.resize((max(1, int(img.width * r)), target_h), Image.Resampling.LANCZOS)
        f = scale_to_h(fig_crop)
        w = scale_to_h(web_sec)
        h = scale_to_h(heatmap)
        padding = 16
        header_h = 48
        total_w = f.width + w.width + h.width + padding * 4
        total_h = target_h + header_h + padding
        canvas = Image.new('RGB', (total_w, total_h), (28, 28, 28))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("arial.ttf", 22)
        except IOError:
            font = ImageFont.load_default()
        title_text = f"{title}  |  SSIM: {score:.2%}"
        draw.text((padding, 12), title_text, fill=(255,255,255), font=font)
        x = padding
        y = header_h
        canvas.paste(f, (x, y)); x += f.width + padding
        canvas.paste(w, (x, y)); x += w.width + padding
        canvas.paste(h, (x, y))
        return canvas

    def _save_section_report(self, base_dir: str, web_url: str, figma_url: str, device: str, rows: List[Image.Image]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        try:
            ts = _dt.now().strftime('%Y%m%d_%H%M%S')
            parsed_url = urlparse(web_url)
            domain_part = parsed_url.netloc.replace('www.', '').replace('.', '_')
            path_part = parsed_url.path.strip('/').replace('/', '_') if parsed_url.path.strip('/') else 'home'
            stamp = f"sections_{domain_part}_{path_part}_{ts}"[:80]
            run_dir = os.path.join(base_dir, f"test_report_{stamp}")
            self._ensure_dir(run_dir)
            shots_dir = os.path.join(run_dir, 'screenshots')
            self._ensure_dir(shots_dir)
            # Save combined strip
            combined_h = sum(r.height for r in rows) + 20 * (len(rows)+1)
            combined_w = max(r.width for r in rows) if rows else 1600
            combined = Image.new('RGB', (combined_w, combined_h), (20,20,20))
            y = 20
            for i, r in enumerate(rows):
                x = 10
                # center if narrower
                if r.width < combined_w:
                    x = (combined_w - r.width)//2
                combined.paste(r, (x, y))
                y += r.height + 20
            combined_path = os.path.join(run_dir, 'sections_comparison.png')
            combined.save(combined_path)
            out['sections_image'] = combined_path

            # Simple HTML wrapper
            html = os.path.join(run_dir, 'design_report_sections.html')
            with open(html, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html><html><head><meta charset='utf-8'/>
<title>Section-based Design QA Report</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:16px;background:#111;color:#eee}} img{{max-width:100%;border:1px solid #333}}</style>
</head><body>
<h1>Section-based Design QA</h1>
<div>Web URL: <code>{web_url}</code></div>
<div>Figma URL: <code>{figma_url}</code></div>
<div>Device: <code>{device}</code></div>
<hr/>
<img src='sections_comparison.png'/>
</body></html>
""")
            out['report_html'] = html
        except Exception as e:
            logger.warning(f"Failed to save section report: {e}")
        return out

    def process_qa_sections(self,
                            figma_url: str,
                            web_url: str,
                            device: Optional[str] = None,
                            save_reports_dir: Optional[str] = None,
                            max_sections: int = 12,
                            min_section_height: int = 280,
                            min_section_width: int = 400,
                            custom_section_selectors: Optional[List[str]] = None,
                            root_selector: Optional[str] = None,
                            progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Alternative pipeline: section-based, auto-aligned diffs with SSIM heatmaps per section."""
        result: Dict[str, Any] = {"success": False}
        try:
            ok = self.chrome_driver.setup_driver(headless=True, mobile_device_name=device)
            if not ok:
                return {"success": False, "error": "Failed to initialize browser."}

            # Fetch Figma top-level image
            node = self.figma_comparator.get_specific_node_from_url(figma_url)
            if not node:
                return {"success": False, "error": "Invalid Figma URL (missing node-id)."}
            figma_img = self.figma_comparator.get_node_image(node['file_id'], node['node_id'])
            if not figma_img:
                return {"success": False, "error": "Could not fetch Figma image."}

            # Navigate so we can detect sections
            if not self.chrome_driver.navigate(web_url, wait_time=2.0):
                return {"success": False, "error": "Could not load web URL."}
            sections = self.chrome_driver.detect_sections(
                min_height=min_section_height,
                min_width=min_section_width,
                max_sections=max_sections,
                custom_selectors=custom_section_selectors,
                root_selector=root_selector,
            )
            if not sections:
                return {"success": False, "error": "No content sections detected on page."}

            rows: List[Image.Image] = []
            scores: List[float] = []
            for idx, sec in enumerate(sections):
                if progress_callback:
                    try:
                        progress_callback(idx + 1, len(sections), f"Matching section {idx + 1}/{len(sections)}: {sec.get('label','')}")
                    except Exception:
                        pass
                web_img: Image.Image = sec.get('image')
                if not web_img:
                    continue
                fig_crop = self._cv_match_figma_region(figma_img, web_img)
                if not fig_crop:
                    # Fallback: rough crop at the same vertical position ratio
                    bb = sec.get('bbox', {})
                    y = int(bb.get('y', 0))
                    # Map y proportionally into figma height
                    fy0 = max(0, min(figma_img.height-1, int((y / max(1, self.chrome_driver.page.viewport_size['height'])) * figma_img.height)))
                    fy1 = min(figma_img.height, fy0 + int(web_img.height * (figma_img.width / max(1, web_img.width))))
                    fig_crop = figma_img.crop((0, fy0, figma_img.width, fy1))
                # Compute heatmap/score
                if progress_callback:
                    try:
                        progress_callback(idx + 1, len(sections), f"Computing SSIM for section {idx + 1}/{len(sections)}")
                    except Exception:
                        pass
                score, heat = self._ssim_heatmap(fig_crop, web_img)
                row = self._compose_section_row(fig_crop, web_img, heat, score, title=sec.get('label', f'Section {idx+1}'))
                rows.append(row)
                scores.append(score)

            artifacts: Dict[str, str] = {}
            if save_reports_dir and rows:
                artifacts = self._save_section_report(save_reports_dir, web_url, figma_url, device or 'Desktop', rows)

            result.update({
                'success': True,
                'sections_reviewed': len(rows),
                'average_ssim': float(np.mean(scores)) if scores else None,
                'artifacts': artifacts,
            })
            return result
        except Exception as e:
            logger.error(f"Section-based QA failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def process_fluid_breakpoints(self,
                                  web_url: str,
                                  start_width: int = 320,
                                  end_width: int = 1200,
                                  steps: int = 20,
                                  frame_duration: float = 0.2,
                                  device: Optional[str] = None,
                                  save_reports_dir: Optional[str] = None,
                                  attach_report_to_jira: bool = False,
                                  jira_assignee: Optional[str] = None) -> Dict[str, Any]:
        """Capture a fluid breakpoint GIF, save an HTML/PDF report if requested, and optionally create a Jira ticket."""
        result: Dict[str, Any] = {"success": False}
        try:
            ok = self.chrome_driver.setup_driver(headless=True, mobile_device_name=device)
            if not ok:
                return {"success": False, "error": "Failed to initialize browser."}
            gif_path = self.chrome_driver.capture_fluid_breakpoint_animation(web_url, start_width, end_width, steps, frame_duration)
            if not gif_path:
                return {"success": False, "error": "Failed to generate GIF."}
            result["gif_path"] = gif_path

            artifacts: Dict[str, str] = {}
            if save_reports_dir:
                try:
                    artifacts = self._save_fluid_artifacts(save_reports_dir, gif_path, web_url, start_width, end_width, steps, frame_duration, device or "Desktop")
                except Exception as e:
                    logger.warning(f"Failed to save fluid artifacts: {e}")
            result["artifacts"] = artifacts

            ticket_info = None
            if attach_report_to_jira:
                attachments = []
                try:
                    if gif_path and os.path.exists(gif_path):
                        attachments.append(gif_path)
                    # Only attach PDF report, not HTML to avoid large attachments
                    p = artifacts.get("report_pdf")
                    if p and os.path.exists(p):
                        attachments.append(p)
                except Exception:
                    pass
                issue_details = {
                    "title": f"Responsive Layout Report ({device or 'Desktop'})",
                    "description": (
                        f"h2. Fluid Breakpoint Animation Generated\n\n"
                        f"*URL:* {web_url}\n\n"
                        f"*Range:* {start_width}px to {end_width}px\n\n"
                        f"*Frames:* {steps}, *Frame Duration:* {frame_duration}s\n\n"
                        f"This ticket includes the responsive layout animation and report."
                    ),
                    "priority": "Medium",
                }
                ticket_info = self.jira_integration.create_design_qa_ticket(issue_details, jira_assignee, attachments)
            result["ticket"] = ticket_info
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"Fluid processing failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        
    def get_ai_visual_analysis(self, figma_image: Image.Image, web_image: Image.Image, figma_props: str, web_dom_inspection: str) -> str:
        """
        UPGRADED: Analyzes images AND technical properties from both Figma and the live DOM.
        """
        if not self.ai_client:
            return "AI analysis is unavailable. OpenAI client not initialized."

        try:
            # Reduce image size more aggressively to save tokens
            max_size = (512, 512)  # Reduced from (1024, 1024)
            figma_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            web_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            def image_to_base64(img):
                buffered = BytesIO()
                img.save(buffered, format="PNG", optimize=True, quality=85)  # Compress images
                return base64.b64encode(buffered.getvalue()).decode('utf-8')

            figma_base64 = image_to_base64(figma_image)
            web_base64 = image_to_base64(web_image)

            logger.info("Sending compressed images and technical specs to OpenAI for enhanced analysis...")
            
            # Truncate the technical specifications to reduce token usage
            max_props_length = 2000  # Limit technical specs length
            if len(figma_props) > max_props_length:
                figma_props = figma_props[:max_props_length] + "...[truncated]"
            if len(web_dom_inspection) > max_props_length:
                web_dom_inspection = web_dom_inspection[:max_props_length] + "...[truncated]"
            
            # Shortened, more focused prompt to reduce token usage
            prompt_text = f"""You are a QA engineer comparing a Figma design with its web implementation.

TASK: Identify visual discrepancies between the two images and cross-reference with technical specs below.

**Figma Properties (truncated):**
```json
{figma_props}
```

**Web DOM Inspection (truncated):**
```json
{web_dom_inspection}
```

Provide a concise bulleted list of key differences found."""
            
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use the cheaper, faster model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{figma_base64}"}},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{web_base64}"}},
                        ],
                    }
                ],
                max_tokens=1000,  # Reduced from 2048
            )
            
            analysis = response.choices[0].message.content
            logger.info("✅ Enhanced AI analysis received successfully.")
            return analysis
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ AI visual analysis failed: {e}")
            
            # Handle rate limit errors gracefully
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                return "AI analysis temporarily unavailable due to rate limits. Please try again in a few minutes. Visual comparison completed successfully without AI insights."
            elif "tokens" in error_msg.lower():
                return "Request too large for AI analysis. Consider using smaller images or shorter technical specifications."
            else:
                return f"AI analysis encountered an error: {error_msg}"

    def create_designer_style_diff_with_callouts(self, figma_image: Image.Image, web_image: Image.Image, ai_feedback: str = None) -> Optional[Image.Image]:
        """
        Creates a designer-style QA report with clean callouts instead of red heatmap overlay.
        Uses AI feedback to place specific annotations on the comparison.
        """
        if not figma_image or not web_image:
            return None
            
        try:
            # Convert to RGB
            figma_image = figma_image.convert('RGB')
            web_image = web_image.convert('RGB')
            
            # Determine target size - use reasonable desktop dimensions
            target_height = 1200
            figma_ratio = figma_image.width / figma_image.height
            web_ratio = web_image.width / web_image.height
            
            # Resize maintaining aspect ratio
            figma_resized = figma_image.resize((int(target_height * figma_ratio), target_height), Image.Resampling.LANCZOS)
            web_resized = web_image.resize((int(target_height * web_ratio), target_height), Image.Resampling.LANCZOS)
            
            # Create canvas for designer-style layout
            padding = 40
            header_height = 80
            label_height = 40
            canvas_width = figma_resized.width + web_resized.width + (padding * 3)
            canvas_height = target_height + header_height + label_height + (padding * 2)
            
            # Create white background like designer reports
            canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)
            
            # Add title header
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
                label_font = ImageFont.truetype("arial.ttf", 16)
                callout_font = ImageFont.truetype("arial.ttf", 14)
            except IOError:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
                callout_font = ImageFont.load_default()
            
            # Title
            draw.text((padding, 20), "DESIGN QA COMPARISON", fill=(0, 0, 0), font=title_font)
            
            # Position images
            figma_x = padding
            figma_y = header_height + label_height
            web_x = figma_resized.width + (padding * 2)
            web_y = header_height + label_height
            
            # Add labels
            draw.text((figma_x, header_height), "Design", fill=(217, 70, 239), font=label_font)  # Purple
            draw.text((web_x, header_height), "Live site", fill=(217, 70, 239), font=label_font)  # Purple
            
            # Paste images
            canvas.paste(figma_resized, (figma_x, figma_y))
            canvas.paste(web_resized, (web_x, web_y))
            
            # Add clean callouts based on AI feedback instead of red heatmap
            if ai_feedback:
                # Parse feedback for key issues and add clean annotations
                callout_y = figma_y + 50
                callout_spacing = 35
                
                # Extract key issues from AI feedback
                issues = []
                if "alignment" in ai_feedback.lower():
                    issues.append("⚠️ Alignment issues detected")
                if "color" in ai_feedback.lower() or "button" in ai_feedback.lower():
                    issues.append("🎨 Color discrepancies found")
                if "font" in ai_feedback.lower() or "typography" in ai_feedback.lower():
                    issues.append("📝 Typography needs adjustment")
                if "spacing" in ai_feedback.lower() or "padding" in ai_feedback.lower():
                    issues.append("📏 Spacing/padding issues")
                if "size" in ai_feedback.lower() or "dimension" in ai_feedback.lower():
                    issues.append("📐 Component sizing problems")
                
                # Draw clean callout boxes
                for i, issue in enumerate(issues[:5]):  # Limit to 5 issues
                    y_pos = callout_y + (i * callout_spacing)
                    # Clean callout box
                    box_rect = [figma_x, y_pos - 5, figma_x + 300, y_pos + 20]
                    draw.rectangle(box_rect, fill=(255, 255, 255), outline=(217, 70, 239), width=1)
                    draw.text((figma_x + 10, y_pos), issue, fill=(0, 0, 0), font=callout_font)
                    
                    # Draw connecting line to web version
                    line_start = (figma_x + 300, y_pos + 7)
                    line_end = (web_x - 10, y_pos + 7)
                    draw.line([line_start, line_end], fill=(217, 70, 239), width=2)
                    
                    # Arrow pointing to issue area
                    arrow_x, arrow_y = line_end
                    draw.polygon([(arrow_x, arrow_y), (arrow_x - 10, arrow_y - 5), (arrow_x - 10, arrow_y + 5)], 
                               fill=(217, 70, 239))
            
            return canvas
            
        except Exception as e:
            logger.error(f"Failed to create designer-style diff with callouts: {e}")
            return None

    def create_designer_style_diff(self, figma_image: Image.Image, web_image: Image.Image, differences: List[Dict] = None) -> Optional[Image.Image]:
        """
        Creates a designer-style QA report matching the format designers use for feedback.
        Shows side-by-side comparison with callouts and annotations for differences.
        """
        if not figma_image or not web_image:
            return None
            
        try:
            # Convert to RGB
            figma_image = figma_image.convert('RGB')
            web_image = web_image.convert('RGB')
            
            # Determine target size - use reasonable desktop dimensions
            target_height = 1200
            figma_ratio = figma_image.width / figma_image.height
            web_ratio = web_image.width / web_image.height
            
            # Resize maintaining aspect ratio
            figma_resized = figma_image.resize((int(target_height * figma_ratio), target_height), Image.Resampling.LANCZOS)
            web_resized = web_image.resize((int(target_height * web_ratio), target_height), Image.Resampling.LANCZOS)
            
            # Create canvas for designer-style layout
            padding = 40
            header_height = 80
            label_height = 40
            canvas_width = figma_resized.width + web_resized.width + (padding * 3)
            canvas_height = target_height + header_height + label_height + (padding * 2)
            
            # Create white background like designer reports
            canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)
            
            # Add title header
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
                label_font = ImageFont.truetype("arial.ttf", 16)
            except IOError:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
            
            # Title
            draw.text((padding, 20), "DESIGN QA COMPARISON", fill=(0, 0, 0), font=title_font)
            
            # Position images
            figma_x = padding
            figma_y = header_height + label_height
            web_x = figma_resized.width + (padding * 2)
            web_y = header_height + label_height
            
            # Add labels
            draw.text((figma_x, header_height), "Design", fill=(217, 70, 239), font=label_font)  # Purple like in screenshot
            draw.text((web_x, header_height), "Live site", fill=(217, 70, 239), font=label_font)  # Purple like in screenshot
            
            # Paste images
            canvas.paste(figma_resized, (figma_x, figma_y))
            canvas.paste(web_resized, (web_x, web_y))
            
            # Add difference indicators/callouts if differences detected
            if differences:
                # Add priority indicators (High/Medium/Low dots like in screenshot)
                priority_y = 15
                priority_colors = {"HIGH": (255, 0, 0), "MEDIUM": (255, 165, 0), "LOW": (0, 128, 0)}
                legend_x = canvas_width - 300
                
                draw.text((legend_x, priority_y), "PRIORITY KEY:", fill=(0, 0, 0), font=label_font)
                
                dot_x = legend_x + 120
                for priority, color in priority_colors.items():
                    draw.ellipse([dot_x, priority_y + 5, dot_x + 10, priority_y + 15], fill=color)
                    draw.text((dot_x + 15, priority_y), priority, fill=(0, 0, 0), font=ImageFont.load_default())
                    dot_x += 80
            
            return canvas
            
        except Exception as e:
            logger.error(f"Failed to create designer-style diff: {e}")
            return None
            
    def create_designer_style_diff_with_callouts(self, figma_image: Image.Image, web_image: Image.Image, ai_feedback: str) -> Optional[Image.Image]:
        """
        Creates an enhanced designer-style QA report with specific callouts based on AI feedback.
        Replaces the red heatmap with clean, professional designer-style callouts.
        """
        if not figma_image or not web_image or not ai_feedback:
            return None
            
        try:
            # Start with basic designer diff layout
            canvas = self.create_designer_style_diff(figma_image, web_image)
            if not canvas:
                return None
                
            draw = ImageDraw.Draw(canvas)
            
            # Set up fonts for callouts
            try:
                callout_font = ImageFont.truetype("arial.ttf", 14)
                callout_bold_font = ImageFont.truetype("arial.ttf", 14, encoding="unic", layout_engine=ImageFont.LAYOUT_BASIC)
            except (IOError, AttributeError):
                callout_font = ImageFont.load_default()
                callout_bold_font = ImageFont.load_default()
            
            # Parse AI feedback into callout items
            callouts = []
            for line in ai_feedback.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Extract issue type and description
                parts = line.split(':', 1)
                if len(parts) == 2:
                    issue_type = parts[0].strip()
                    description = parts[1].strip()
                    callouts.append({
                        "type": issue_type,
                        "description": description,
                        # Determine priority based on keywords
                        "priority": "HIGH" if any(kw in line.lower() for kw in ['critical', 'broken', 'major', 'wrong']) 
                                   else "MEDIUM" if any(kw in line.lower() for kw in ['should', 'improve', 'better']) 
                                   else "LOW"
                    })
            
            # Calculate layout dimensions
            padding = 40
            header_height = 80
            label_height = 40
            images_y = header_height + label_height
            figma_x = padding
            web_x = canvas.width // 2
            
            # Add callout arrows and text boxes
            callout_colors = {
                "HIGH": (255, 0, 0),     # Red
                "MEDIUM": (255, 165, 0),  # Orange
                "LOW": (0, 128, 0)        # Green
            }
            
            # Position callouts strategically around both images
            y_positions = [images_y + (i * (canvas.height - images_y - 100) // max(len(callouts), 1)) + 100 for i in range(len(callouts))]
            
            for i, (callout, y_pos) in enumerate(zip(callouts, y_positions)):
                # Alternate between left and right image
                is_left = i % 2 == 0
                image_x = figma_x if is_left else web_x
                image_center_x = image_x + (canvas.width // 4)
                
                # Draw arrow
                arrow_color = callout_colors[callout["priority"]]
                arrow_start_x = image_center_x
                arrow_end_x = image_center_x + 150 if is_left else image_center_x - 150
                
                # Draw arrow line
                draw.line([(arrow_start_x, y_pos), (arrow_end_x, y_pos)], fill=arrow_color, width=2)
                
                # Draw arrow tip
                arrow_tip_size = 8
                draw.polygon([
                    (arrow_end_x, y_pos), 
                    (arrow_end_x - arrow_tip_size if is_left else arrow_end_x + arrow_tip_size, y_pos - arrow_tip_size),
                    (arrow_end_x - arrow_tip_size if is_left else arrow_end_x + arrow_tip_size, y_pos + arrow_tip_size)
                ], fill=arrow_color)
                
                # Draw text box
                text_x = arrow_end_x + 10 if is_left else arrow_end_x - 210
                text_box_width = 200
                text_box_padding = 8
                
                # Wrap text to fit in box
                wrapped_type = self._wrap_text(callout["type"], text_box_width - 2*text_box_padding, callout_font)
                wrapped_description = self._wrap_text(callout["description"], text_box_width - 2*text_box_padding, callout_font)
                
                # Calculate text box height
                type_height = len(wrapped_type) * 18
                desc_height = len(wrapped_description) * 18
                text_box_height = type_height + desc_height + 3*text_box_padding
                
                # Draw text box background with priority color border
                draw.rectangle(
                    [(text_x, y_pos - text_box_height // 2), 
                     (text_x + text_box_width, y_pos + text_box_height // 2)],
                    fill=(255, 255, 255),
                    outline=arrow_color,
                    width=2
                )
                
                # Draw text
                text_y = y_pos - text_box_height // 2 + text_box_padding
                # Draw issue type in bold (or colored to simulate bold)
                draw.text((text_x + text_box_padding, text_y), "\n".join(wrapped_type), 
                          fill=arrow_color, font=callout_bold_font)
                
                # Draw description
                text_y += type_height + text_box_padding
                draw.text((text_x + text_box_padding, text_y), "\n".join(wrapped_description), 
                          fill=(0, 0, 0), font=callout_font)
            
            return canvas
            
        except Exception as e:
            logger.error(f"Failed to create designer-style diff with callouts: {e}")
            return None
            
    def _wrap_text(self, text: str, width: int, font) -> List[str]:
        """Helper function to wrap text to fit within a specified width."""
        words = text.split()
        if not words:
            return []
            
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            try:
                # Check if adding this word exceeds the width
                test_line = current_line + " " + word
                # Use getbbox() for newer PIL versions, fallback to getsize()
                try:
                    test_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
                except AttributeError:
                    test_width = font.getsize(test_line)[0]
                    
                if test_width <= width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            except Exception:
                # If any error in measurement, just add the word and continue
                lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        return lines

    def create_designer_style_diff_with_callouts(self, figma_image: Image.Image, web_image: Image.Image, ai_feedback: Optional[str]) -> Optional[Image.Image]:
        """
        Creates a designer-style report and overlays numbered callouts derived from AI feedback
        directly on the canvas (clean, readable; no heatmaps). If specific positions are not known,
        callouts are arranged along the right edge of the Web image with a small connector.
        """
        try:
            base = self.create_designer_style_diff(figma_image, web_image)
            if base is None:
                return None
            draw = ImageDraw.Draw(base)
            # Attempt fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 20)
                body_font = ImageFont.truetype("arial.ttf", 16)
            except IOError:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()

            if not ai_feedback:
                return base

            # Parse feedback into items (simple split by lines or bullets)
            raw_lines = [l.strip().lstrip('-•').strip() for l in ai_feedback.splitlines()]
            items = [l for l in raw_lines if l]
            if not items:
                return base

            # Detect layout from the earlier function
            # We know labels occupy header area of height ~120, then images placed at positions we used
            # Recompute the same placements
            padding = 40
            header_height = 80
            label_height = 40

            # Infer image sizes by reading pixel colors to find separation? Too heavy.
            # Instead, recreate scaled sizes like in create_designer_style_diff
            target_height = 1200
            f_w = int(figma_image.width * (target_height / max(1, figma_image.height)))
            w_w = int(web_image.width * (target_height / max(1, web_image.height)))
            figma_x = padding
            web_x = f_w + (padding * 2)
            img_y = header_height + label_height

            # Callout lane parameters on the right of the Web image
            right_margin = 20
            lane_x = web_x + w_w - 10  # near right edge of web image
            box_max_width = 420
            # Place callouts from top with spacing
            top = img_y + 20
            vgap = 18
            circle_r = 11

            def wrap_text(text: str, max_chars_per_line: int = 58) -> List[str]:
                words = text.split()
                lines: List[str] = []
                cur = []
                count = 0
                for w in words:
                    if count + len(w) + (1 if cur else 0) > max_chars_per_line:
                        lines.append(' '.join(cur))
                        cur = [w]
                        count = len(w)
                    else:
                        cur.append(w)
                        count += len(w) + (1 if cur[:-1] else 0)
                if cur:
                    lines.append(' '.join(cur))
                return lines

            for idx, text in enumerate(items, start=1):
                # Build text lines
                lines = wrap_text(text)
                # Compute box height
                line_h = 18
                box_h = max(36, 10 + len(lines) * line_h + 10)
                # Box rectangle anchored right of web image (over image area)
                box_w = box_max_width
                box_x1 = lane_x - box_w
                box_y1 = top
                box_x2 = lane_x
                box_y2 = top + box_h

                # Draw semi-opaque white box with subtle border
                rect_fill = (255, 255, 255, 230)
                rect_border = (220, 220, 220)
                # Since base is RGB, we draw solid; emulate alpha with border only
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(255, 255, 255), outline=rect_border, width=1)

                # Numbered circle
                cx = box_x1 - 20
                cy = box_y1 + 16
                draw.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r], fill=(237, 64, 84))
                num = str(idx)
                # Use textbbox instead of deprecated textsize
                bbox = draw.textbbox((0, 0), num, font=title_font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text((cx - tw/2, cy - th/2), num, fill=(255, 255, 255), font=title_font)

                # Connector line from circle to box
                draw.line([(cx + circle_r, cy), (box_x1, cy)], fill=(180, 180, 180), width=2)

                # Text inside box
                tx = box_x1 + 10
                ty = box_y1 + 10
                for ln in lines:
                    draw.text((tx, ty), ln, fill=(30, 30, 30), font=body_font)
                    ty += line_h

                # Advance top
                top = box_y2 + vgap

                # Stop if we spill below the image
                if top > img_y + target_height - 60:
                    break

            return base
        except Exception as e:
            logger.error(f"Failed to create designer-style diff with callouts: {e}")
            return None

    def create_side_by_side_comparison(self, image1: Image.Image, image2: Image.Image, diff_image: Optional[Image.Image] = None) -> Optional[Image.Image]:
        """
        UPGRADED: Creates a side-by-side comparison including the visual diff image.
        """
        if not image1 or not image2: return None
        try:
            # Convert all images to RGB to ensure consistency
            image1 = image1.convert('RGB')
            image2 = image2.convert('RGB')
            if diff_image:
                diff_image = diff_image.convert('RGB')

            # Determine common height and resize
            h1, h2 = image1.height, image2.height
            # Use the larger height to avoid shrinking; cap to a safe upper bound
            new_h = min(max(h1, h2), 6000)
            w1 = int(image1.width * (new_h / h1))
            w2 = int(image2.width * (new_h / h2))
            
            img1_resized = image1.resize((w1, new_h), Image.Resampling.LANCZOS)
            img2_resized = image2.resize((w2, new_h), Image.Resampling.LANCZOS)
            
            images_to_display = [("Figma Design", img1_resized), ("Web Implementation", img2_resized)]

            # Add the diff image if it exists
            if diff_image:
                w3 = int(diff_image.width * (new_h / diff_image.height))
                diff_resized = diff_image.resize((w3, new_h), Image.Resampling.LANCZOS)
                images_to_display.append(("Visual Difference", diff_resized))

            # Removed unreadable overlay blend/outlines panel per user feedback

            header_height, padding = 60, 20
            total_width = sum(img.width for _, img in images_to_display) + (padding * (len(images_to_display) + 1))
            total_height = new_h + header_height + padding

            # Create the composite image
            comparison_img = Image.new('RGB', (total_width, total_height), (28, 28, 28))
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except IOError:
                font = ImageFont.load_default()
            draw = ImageDraw.Draw(comparison_img)

            current_x = padding
            for title, img in images_to_display:
                # Draw title
                draw.text((current_x, 15), title, fill=(255, 255, 255), font=font)
                # Paste image
                comparison_img.paste(img, (current_x, header_height))
                current_x += img.width + padding
            
            return comparison_img
        except Exception as e:
            logger.error(f"❌ Failed to create side-by-side comparison: {e}", exc_info=True)
            return None

    def process_qa_request(self, figma_url, web_url, jira_assignee=None, similarity_threshold=0.95, mobile_device=None, browser_type="Chromium", full_page=True, overlay_grid=False, live_feedback_callback=None, step_finder=None, should_stop_callback=None, save_reports_dir: Optional[str] = None, attach_report_to_jira: bool = False, enable_video_recording: bool = False, live_preview_callback=None, phase_update_callback=None):
        
        def update_step(step_name_fragment, status, details=""):
            """Safely call the feedback callback if it exists."""
            try:
                if live_feedback_callback and step_finder:
                    step_index = step_finder(step_name_fragment)
                    if step_index != -1:
                        live_feedback_callback(step_index, status, details)
                elif live_feedback_callback:
                    # Fallback: pass the name when we don't have a step_finder/indexed UI
                    live_feedback_callback(step_name_fragment, status, details)
            except Exception as e:
                logger.warning(f"Failed to update step '{step_name_fragment}': {e}")

        def update_phase(phase_name):
            """Update the processing phase if callback exists and we're in main thread."""
            try:
                if phase_update_callback:
                    # Only call if we're likely in the main thread (to avoid ScriptRunContext warnings)
                    import threading
                    if threading.current_thread() is threading.main_thread():
                        phase_update_callback(phase_name)
                    else:
                        # Background thread - push to queue instead
                        try:
                            phase_update_callback(phase_name)  # This should use queue
                        except Exception:
                            pass  # Ignore ScriptRunContext warnings in background
            except Exception:
                pass

        try:
            logger.info(f"🚀 Starting QA process (Device: {mobile_device or 'Desktop'}, Full Page: {full_page}, Grid: {overlay_grid}, Video: {enable_video_recording})")
            
            update_phase("Validating URLs and parsing Figma node...")
            update_step("Parse & Validate Inputs", "running", f"Validating Figma URL: {figma_url[:50]}... and Web URL: {web_url[:50]}...")
            if should_stop_callback and should_stop_callback():
                return {"success": False, "stopped": True}
            
            # Setup driver with video recording if enabled
            self.chrome_driver.setup_driver(
                mobile_device_name=mobile_device,
                browser_type=browser_type,
                enable_video_recording=enable_video_recording,
                enable_live_preview=(live_preview_callback is not None),
                live_preview_callback=live_preview_callback
            )
            
            node_info = self.figma_comparator.get_specific_node_from_url(figma_url)
            if not node_info:
                update_step("Parse & Validate Inputs", "error", "Could not parse Figma URL. Ensure it contains a 'node-id'.")
                return {"success": False, "error": "ERROR_STEP_PARSE: Could not parse Figma URL."}
            update_step("Parse & Validate Inputs", "success", "URLs validated successfully.")

            update_phase("Fetching Figma design image and properties...")
            update_step("Retrieve Figma Design", "running", f"Fetching Figma node '{node_info['node_id']}'...")
            if should_stop_callback and should_stop_callback():
                return {"success": False, "stopped": True}
            figma_image = self.figma_comparator.get_node_image(node_info['file_id'], node_info['node_id'])
            figma_properties = self.figma_comparator.get_node_properties(node_info['file_id'], node_info['node_id'])
            if not figma_image:
                update_step("Retrieve Figma Design", "error", "❌ Failed to retrieve Figma image. This typically happens when:\n• The Figma URL is from a different organization than the configured token\n• The file is private and token lacks access\n• The node ID doesn't exist\n• The Figma API token is invalid or expired")
                return {"success": False, "error": "ERROR_STEP_FIGMA_IMG: Failed to retrieve Figma image. The configured token may not have access to this file."}
            update_step("Retrieve Figma Design", "success", "Figma design image and properties retrieved.")

            update_phase("Capturing web page screenshot...")
            update_step("Capture Web Page Screenshot", "running", f"Capturing screenshot of {web_url}...")
            if should_stop_callback and should_stop_callback():
                return {"success": False, "stopped": True}
            web_screenshot = self.chrome_driver.capture_screenshot(web_url, full_page=full_page)
            if not web_screenshot:
                update_step("Capture Web Page Screenshot", "error", "Failed to capture web screenshot. Check if the URL is accessible and not timing out (60s limit). Consider unchecking 'Full Page Screenshot' if the page is very long.")
                return {"success": False, "error": "ERROR_STEP_SCREENSHOT: Failed to capture web screenshot. URL may be unreachable or timing out."}
            web_dom_inspection = self.chrome_driver.get_targeted_dom_inspection()
            update_step("Capture Web Page Screenshot", "success", "Web page screenshot and DOM data captured.")

            update_phase("Comparing images and calculating similarity...")
            update_step("Compare Design vs. Web", "running", "Calculating similarity and generating visual diff...")
            if should_stop_callback and should_stop_callback():
                return {"success": False, "stopped": True}
            similarity_score, diff_image = self.figma_comparator.compare_images(figma_image, web_screenshot)
            update_step("Compare Design vs. Web", "success", f"Visual comparison complete. Similarity Score: {similarity_score:.1%}")
            
            # --- Grid Overlay ---
            if overlay_grid:
                update_step("Compare Design vs. Web", "running", "Overlaying grid on images...")
                if should_stop_callback and should_stop_callback():
                    return {"success": False, "stopped": True}
                web_screenshot = self.overlay_grid(web_screenshot)
                if diff_image:
                    diff_image = self.overlay_grid(diff_image)
                update_step("Compare Design vs. Web", "success", f"Grid overlay applied. Similarity: {similarity_score:.1%}")

            tickets_created = []
            page_name = urlparse(web_url).path.strip('/').replace('/', ' ').title() or "Homepage"
            
            # Create both traditional and designer-style comparisons
            comparison_image = self.create_side_by_side_comparison(figma_image, web_screenshot, diff_image)
            
            # Note: Designer diff will be created after AI feedback is generated
            
            # Use AI to analyze differences and generate designer-style feedback
            ai_feedback = None
            if self.ai_client and similarity_score < 0.95:  # Only analyze if significant differences
                try:
                    update_step("AI Analysis", "in_progress", "🤖 AI analyzing visual differences...")
                    
                    # Prepare images for AI analysis
                    figma_bytes = BytesIO()
                    figma_image.save(figma_bytes, format='PNG')
                    figma_b64 = base64.b64encode(figma_bytes.getvalue()).decode()
                    
                    web_bytes = BytesIO()
                    web_screenshot.save(web_bytes, format='PNG')
                    web_b64 = base64.b64encode(web_bytes.getvalue()).decode()
                    
                    ai_prompt = f"""
You are a senior UX/UI designer conducting a design QA review. Compare these two images and provide feedback in the exact style that designers give to developers.

Image 1: Figma Design (the intended design)
Image 2: Web Implementation (what was actually built)

**FIGMA DESIGN SPECIFICATIONS:**
{figma_properties[:2000] if len(figma_properties) > 2000 else figma_properties}

Based on the Figma design specifications above and visual comparison, analyze the differences and provide feedback as a designer would, focusing on:

**Visual Alignment Issues**
- Reference specific layers, text elements, and positioning from the Figma spec
- Compare actual spacing values vs implemented spacing

**Color Discrepancies**  
- Reference specific color values from Figma (hex codes, gradients)
- Compare button colors, background colors, text colors

**Typography Problems**
- Reference specific font families, weights, sizes from Figma layers
- Compare line heights and character spacing

**Spacing/Padding Issues**
- Reference specific padding and margin values from Figma
- Compare component spacing vs design specifications

**Component Sizing**
- Reference specific width/height values from Figma layers
- Compare image dimensions, button sizes, container widths

**Interactive Element Styling**
- Reference button styles, hover states from design system
- Compare form elements, links, interactive components

Current similarity score: {similarity_score:.1%}

Format your response with specific references to Figma layers/properties and actionable developer tasks.
"""

                    response = self.ai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user", 
                                "content": [
                                    {"type": "text", "text": ai_prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{figma_b64}"}},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{web_b64}"}}
                                ]
                            }
                        ],
                        max_tokens=500
                    )
                    ai_feedback = response.choices[0].message.content
                    update_step("AI Analysis", "success", f"🤖 AI feedback generated ({len(ai_feedback)} chars)")
                    logger.info("AI visual analysis completed")
                    
                except Exception as e:
                    update_step("AI Analysis", "error", f"AI analysis failed: {str(e)}")
                    logger.warning(f"AI analysis failed: {e}")
                    ai_feedback = "AI analysis unavailable"
            
            # ENHANCED: Create designer-style diff report with AI-powered callouts
            # This is done after AI feedback to include smart callouts
            designer_diff = self.create_designer_style_diff_with_callouts(figma_image, web_screenshot, ai_feedback)
            
            # Create designer-style image with AI callouts (preferable for stakeholders)
            callout_image_path = None
            try:
                callout_img = self.create_designer_style_diff_with_callouts(figma_image, web_screenshot, ai_feedback)
                if callout_img:
                    with tempfile.NamedTemporaryFile(delete=False, suffix="_designer_callouts.png") as f:
                        callout_img.save(f.name)
                        callout_image_path = f.name
            except Exception as e:
                logger.debug(f"Callout image generation skipped: {e}")

            # Save comparison image to a temporary file to be used for results and attachments
            comparison_image_path = None
            designer_diff_path = None
            if comparison_image:
                with tempfile.NamedTemporaryFile(delete=False, suffix="_comparison.png") as f:
                    comparison_image.save(f.name)
                    comparison_image_path = f.name
            
            # Save designer-style diff
            if designer_diff:
                with tempfile.NamedTemporaryFile(delete=False, suffix="_designer_diff.png") as f:
                    designer_diff.save(f.name)
                    designer_diff_path = f.name

            # Optional: Save full Design QA artifacts and HTML/PDF report
            artifacts: Dict[str, str] = {}
            video_path = None
            responsive_gif = None
            
            # If video recording was requested, finalize and retrieve path. Fallback to responsive GIF if unavailable.
            if enable_video_recording:
                try:
                    import tempfile as _tmp
                    tmp_dir = _tmp.mkdtemp(prefix="qa_video_")
                    dest_path = os.path.join(tmp_dir, "test_recording.webm")
                    saved = self.chrome_driver.save_video_recording(dest_path)
                    if saved and os.path.exists(saved):
                        video_path = saved
                        logger.info(f"🎥 Video saved for QA run: {video_path}")
                    else:
                        logger.info("Video not available, generating responsive GIF as fallback...")
                        responsive_gif = self.chrome_driver.capture_fluid_breakpoint_animation(web_url, start_width=320, end_width=1200, steps=12, frame_duration=0.25)
                except Exception as e:
                    logger.warning(f"Video recording finalize failed: {e}")
                    try:
                        responsive_gif = self.chrome_driver.capture_fluid_breakpoint_animation(web_url, start_width=320, end_width=1200, steps=12, frame_duration=0.25)
                    except Exception as e2:
                        logger.warning(f"Responsive GIF fallback failed: {e2}")
            
            if save_reports_dir:
                try:
                    artifacts = self._save_design_artifacts(
                        base_dir=save_reports_dir,
                        page_name=page_name,
                        figma_image=figma_image,
                        web_image=web_screenshot,
                        diff_image=diff_image,
                        comparison_image=comparison_image,
                        figma_props=figma_properties,
                        web_dom_inspection=web_dom_inspection,
                        similarity=similarity_score,
                        web_url=web_url,
                        figma_url=figma_url,
                        device=mobile_device or "Desktop",
                        video_path=video_path,
                        animation_gif_path=responsive_gif,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save design artifacts: {e}")

            if similarity_score < similarity_threshold:
                update_phase("Analyzing discrepancy with AI...")
                update_step("Compare Design vs. Web", "running", "Discrepancy detected. Sending to AI for detailed analysis...")
                if should_stop_callback and should_stop_callback():
                    return {"success": False, "stopped": True}
                ai_description = self.get_ai_visual_analysis(figma_image.copy(), web_screenshot.copy(), figma_properties, web_dom_inspection)
                update_step("Compare Design vs. Web", "success", f"AI analysis complete. Similarity: {similarity_score:.1%}")
                
                update_phase("Creating Jira ticket for visual regression...")
                update_step("Create Jira Tickets", "running", "Creating visual regression ticket...")
                if should_stop_callback and should_stop_callback():
                    return {"success": False, "stopped": True}
                attachments = [comparison_image_path] if comparison_image_path else []
                if attach_report_to_jira and artifacts:
                    # Only attach PDF report, not HTML to avoid large attachments
                    p = artifacts.get("report_pdf")
                    if p and os.path.exists(p):
                        attachments.append(p)
                
                issue_details = self._format_jira_ticket(
                    page_name=page_name, web_url=web_url, category="Visual Regression",
                    issue_type="Design Discrepancy", severity="High" if similarity_score < 0.85 else "Medium",
                    description=f"Visual similarity score of {similarity_score:.2%} is below the {similarity_threshold:.2%} threshold.",
                    recommendation=ai_description,
                    device=mobile_device or "Desktop"
                )
                ticket_result = self.jira_integration.create_design_qa_ticket(issue_details, jira_assignee, attachments)
                tickets_created.append(ticket_result)
            
            update_step("Run Functional Validations", "running", "Running automated functional checks (e.g., H1 tags)...")
            if should_stop_callback and should_stop_callback():
                return {"success": False, "stopped": True}
            functional_issues = self.validator.validate_page(web_url)
            update_step("Run Functional Validations", "success", f"Found {len(functional_issues)} functional issue(s).")

            if functional_issues:
                update_step("Create Jira Tickets", "running", f"Creating {len(functional_issues)} functional issue ticket(s)...")
                if should_stop_callback and should_stop_callback():
                    return {"success": False, "stopped": True}
                for issue in functional_issues:
                    issue_details = self._format_jira_ticket(
                        page_name=page_name, web_url=web_url, category=issue['category'],
                        issue_type=issue['type'], severity=issue['severity'],
                        description=issue['description'],
                        recommendation="Review and fix this functional issue.",
                        device=mobile_device or "Desktop"
                    )
                    ticket_result = self.jira_integration.create_design_qa_ticket(issue_details, jira_assignee)
                    tickets_created.append(ticket_result)
            
            total_tickets = len([t for t in tickets_created if t.get('success')])
            update_step("Create Jira Tickets", "success", f"Successfully created {total_tickets} Jira ticket(s).")

            # Clean up the temp comparison image if it was created
            # if comparison_image_path and os.path.exists(comparison_image_path):
            #     os.unlink(comparison_image_path)

            update_phase("Design QA Analysis Complete!")
            return {
                'success': True, 
                'similarity_score': similarity_score, 
                'functional_issues_found': len(functional_issues), 
                'tickets_created': tickets_created,
                'comparison_image_path': comparison_image_path, # Return path to the main comparison image
                'designer_diff_path': designer_diff_path, # Return path to designer-style diff
                'designer_callouts_path': callout_image_path, # Return path to designer-style diff with callouts
                'ai_feedback': ai_feedback, # AI-generated designer feedback
                'artifacts': artifacts,
                'video_recording_path': video_path,  # Include video path in results
            }
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            update_step("Generate Final Report", "error", error_message)
            logger.error(f"❌ Unhandled QA processing error: {e}", exc_info=True)
            return {"success": False, "error": f"ERROR_STEP_UNHANDLED: {error_message}"}

    def _format_jira_ticket(self, page_name, web_url, category, issue_type, severity, description, recommendation, device="Desktop"):
        title = f"Design QA - {category} ({device}): {page_name}"
        desc_body = f"""h2. Automated Design QA Issue
*Page:* {page_name}
*URL:* {web_url}
*Device:* {device}
*Category:* {category}
*Issue Type:* {issue_type}
*Severity:* {severity}

h3. Issue Description:
{description}

h3. AI Analysis & Recommendation:
{recommendation}

*Detection Date:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Detected by:* Monster QA Agent
"""
        return {"title": title, "description": desc_body, "priority": severity}
    
    def overlay_grid(self, image: Image.Image, columns=12, color=(255, 100, 100, 100)) -> Image.Image:
        """Overlays a column grid on the given image."""
        try:
            img_with_grid = image.copy().convert("RGBA")
            draw = ImageDraw.Draw(img_with_grid)
            width, height = img_with_grid.size
            column_width = width / columns
            
            for i in range(1, columns):
                x = i * column_width
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            
            logger.info(f"✅ Applied {columns}-column grid overlay.")
            return img_with_grid
        except Exception as e:
            logger.error(f"❌ Failed to overlay grid: {e}")
            return image # Return original image on failure

    def cleanup(self):
        self.chrome_driver.close()

# NOTE: ALL STREAMLIT UI CODE HAS BEEN REMOVED FROM THIS FILE.
# This file should ONLY contain the library classes above.
# The Streamlit application code should be in your main script (monster2.py).
 