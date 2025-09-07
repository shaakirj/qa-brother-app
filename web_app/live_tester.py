"""
LiveTestRunner - Handles real-time browser automation using Playwright
"""
import asyncio
from playwright.async_api import async_playwright
import os
import uuid

class LiveTestRunner:
    def __init__(self, socketio):
        self.socketio = socketio
        self.browsers = {}

    async def start_test(self, url, session_id):
        """Starts a new live test session."""
        try:
            p = await async_playwright().start()
            browser = await p.chromium.launch(headless=False) # Run in headed mode for visibility
            context = await browser.new_context()
            page = await context.new_page()
            self.browsers[session_id] = {'browser': browser, 'page': page, 'playwright': p}
            
            await page.goto(url, wait_until="networkidle")
            self.socketio.emit('test_started', {'sessionId': session_id, 'url': url}, room=session_id)
            
            # Start monitoring and sending updates
            await self.monitor_page(page, session_id)

        except Exception as e:
            self.socketio.emit('test_error', {'error': str(e)}, room=session_id)
            await self.stop_test(session_id)

    async def monitor_page(self, page, session_id):
        """Monitors the page for actions and sends updates."""
        # Continuously take screenshots and send them to the client
        while session_id in self.browsers:
            screenshot_path = os.path.join('static', 'screenshots', f'{session_id}.png')
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await page.screenshot(path=screenshot_path)
            
            self.socketio.emit('screenshot_update', {'screenshot_path': f'/{screenshot_path}'}, room=session_id)
            
            # Simulate an action log
            self.socketio.emit('action_update', {'action': f'Checked page at {page.url}'}, room=session_id)

            await asyncio.sleep(2) # Update every 2 seconds

    async def stop_test(self, session_id):
        """Stops a live test session."""
        if session_id in self.browsers:
            browser_info = self.browsers.pop(session_id)
            await browser_info['browser'].close()
            await browser_info['playwright'].stop()
            self.socketio.emit('test_stopped', {'sessionId': session_id}, room=session_id)
