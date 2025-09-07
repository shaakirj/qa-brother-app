"""
Functional QA Agent - A script to perform automated front-end functional testing.
"""

import os
import io
import json
import logging
from typing import List, Dict, Any, Optional, Callable

from openai import OpenAI
from PIL import Image

# Reuse integrations that exist in design8.py
from design8 import FigmaDesignComparator, EnhancedJiraIntegration

# Use Playwright for browser automation
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _truncate(text: str, max_len: int = 4000) -> str:
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "... [truncated]"


def _strip_code_fences(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s.startswith("```") and s.endswith("```"):
        # remove the first and last code fence
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()


def _robust_json_parse(s: str):
    """Try multiple strategies to parse JSON content returned by model."""
    import json as _json
    if not isinstance(s, str):
        return None
    txt = _strip_code_fences(s)
    try:
        return _json.loads(txt)
    except Exception:
        pass
    # Try to find the largest enclosing JSON object
    try:
        start = txt.find('{')
        end = txt.rfind('}')
        if start != -1 and end != -1 and end > start:
            return _json.loads(txt[start:end+1])
    except Exception:
        pass
    # Try to find JSON array
    try:
        start = txt.find('[')
        end = txt.rfind(']')
        if start != -1 and end != -1 and end > start:
            return _json.loads(txt[start:end+1])
    except Exception:
        pass
    return None


def _clean_ux_content(text: str) -> str:
    """Lightly normalize UX text: collapse whitespace, strip control chars, keep bullets and headings."""
    if not isinstance(text, str):
        return ""
    import re
    # Replace Windows newlines and tabs
    t = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    # Collapse more than 2 blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Trim trailing spaces per line
    t = "\n".join([ln.rstrip() for ln in t.splitlines()])
    # Collapse spaces
    t = re.sub(r"[ \u00A0]{2,}", " ", t)
    return t.strip()


def _extract_ux_key_points(text: str, max_points: int = 25) -> List[str]:
    """Heuristically extract bullet-like key points from UX text to emphasize in prompts."""
    import re
    points: List[str] = []
    if not text:
        return points
    for ln in text.splitlines():
        l = ln.strip()
        if not l:
            continue
        # Capture common bullet/number formats or key phrases
        if re.match(r"^[-*•]\s+", l) or re.match(r"^\d+\.\s+", l) or re.search(r"\bAs a\b|\bI want\b|\bSo that\b|\bAcceptance Criteria\b|\bUser can\b|\bThe system should\b", l, re.IGNORECASE):
            # Remove bullet prefix
            l = re.sub(r"^([-*•]|\d+\.)\s+", "", l)
            points.append(l.strip())
        if len(points) >= max_points:
            break
    # If nothing matched, fall back to first N non-empty lines
    if not points:
        for l in [ln.strip() for ln in text.splitlines() if ln.strip()][:max_points]:
            points.append(l)
    return points


class FunctionalQAAgent:
    """An agent that performs automated functional testing using Playwright, informed by Figma, Jira, and a UX doc."""

    def __init__(self, jira_assignee: Optional[str] = None):
        self.jira_assignee = jira_assignee
        self.figma = FigmaDesignComparator()
        self.jira = EnhancedJiraIntegration()
        try:
            # Use default constructor which reads OPENAI_API_KEY from env
            self.ai_client = OpenAI()
            logger.info("OpenAI client initialized for Functional QA Agent.")
        except Exception as e1:
            try:
                import httpx
                self.ai_client = OpenAI(http_client=httpx.Client(trust_env=False))
                logger.info("OpenAI client initialized for Functional QA Agent with proxy-disabled HTTP client.")
            except Exception as e2:
                self.ai_client = None
                logger.error(f"Failed to initialize OpenAI client: {e2}")

    def get_jira_acceptance_criteria(self, ticket_id: str) -> str:
        """Fetch description + acceptance criteria from Jira (best-effort)."""
        try:
            # Validate Jira issue key pattern like PROJ-123
            import re
            if not ticket_id or not re.match(r"^[A-Z][A-Z0-9_]+-\d+$", str(ticket_id).strip(), re.IGNORECASE):
                return "Jira issue key not provided or invalid format (expected e.g., QA-123). Proceeding without Jira details."
            if not self.jira.jira_client:
                return "Jira not configured."
            issue = self.jira.jira_client.issue(ticket_id)
            description = getattr(issue.fields, "description", "") or ""
            # Adjust this custom field to your Jira instance
            acceptance_criteria = ""
            try:
                acceptance_criteria = getattr(issue.fields, "customfield_10005", "") or ""
            except Exception:
                pass
            content = f"Description:\n{description}\n\nAcceptance Criteria:\n{acceptance_criteria}"
            logger.info(f"Fetched details for Jira ticket {ticket_id}")
            return content
        except Exception as e:
            logger.error(f"Failed to fetch Jira ticket {ticket_id}: {e}")
            return f"Could not fetch details for Jira ticket {ticket_id}."

    def _get_figma_properties_from_url(self, figma_url: str) -> str:
        node = self.figma.get_specific_node_from_url(figma_url)
        if not node:
            return "Could not parse Figma URL."
        return self.figma.get_node_properties(node.get("file_id"), node.get("node_id"))

    def generate_user_stories_from_ux(self, ux_content: str, jira_content: str) -> Dict[str, Any]:
        """Summarize UX doc + Jira into concise user stories with acceptance criteria. UX is prioritized."""
        if not self.ai_client:
            return {"error": "AI not available"}
        try:
            ux_clean = _clean_ux_content(ux_content)
            key_points = _extract_ux_key_points(ux_clean, max_points=30)
            ux_points_text = "\n- " + "\n- ".join(key_points) if key_points else ""
            prompt = (
                "You are a senior product owner. Create 3-6 concise user stories from the UX document FIRST, using Jira only to clarify.\n"
                "- STRICT JSON ONLY (no prose, no markdown).\n"
                "- Schema: {\"user_stories\":[{\"as\":str,\"i_want\":str,\"so_that\":str,\"acceptance_criteria\":[str,...]}],\"ux_key_points\":[str,...]}\n"
                "- Rules: Prefer UX key points verbatim when possible; acceptance criteria must be testable and specific.\n\n"
                f"UX key points (extracted):{ux_points_text}\n\n"
                f"UX document (truncated, normalized):\n{_truncate(ux_clean, 2000)}\n\n"
                f"Jira details (truncated):\n{_truncate(jira_content, 800)}\n"
            )
            resp = self.ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1400,
            )
            data = _robust_json_parse(resp.choices[0].message.content) or {}
            # Ensure ux_key_points are present to help downstream visibility in UI
            if "ux_key_points" not in data:
                data["ux_key_points"] = key_points
            return data
        except Exception as e:
            logger.error(f"User story generation failed: {e}")
            return {"error": str(e)}

    def _extract_text_from_figma_props(self, props: Any) -> str:
        """Recursively collect textual content from Figma node properties tree."""
        texts: List[str] = []

        def walk(node: Any):
            if isinstance(node, dict):
                node_type = node.get("type")
                if node_type and str(node_type).lower() == "text":
                    val = node.get("characters")
                    if isinstance(val, str) and val.strip():
                        texts.append(val.strip())
                # Continue traversal
                for k, v in node.items():
                    if k in ("children",):
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(props)
        return "\n".join(texts)

    def get_ux_text_from_figma_url(self, figma_ux_url: str) -> str:
        """Fetch Figma node properties and extract visible text as UX content."""
        try:
            node = self.figma.get_specific_node_from_url(figma_ux_url)
            if not node:
                return ""
            props_json = self.figma.get_node_properties(node.get("file_id"), node.get("node_id"))
            try:
                props = json.loads(props_json) if isinstance(props_json, str) else props_json
            except Exception:
                # If API returned an error string, just return it as context
                return str(props_json)
            return self._extract_text_from_figma_props(props)
        except Exception as e:
            logger.error(f"Failed to get UX text from Figma: {e}")
            return ""

    def generate_test_cases_from_ai(self, figma_url: str, jira_content: str, ux_content: str) -> List[Dict[str, Any]]:
        """Use OpenAI to generate Playwright-style test cases informed by Figma, Jira, and UX doc."""
        if not self.ai_client:
            logger.error("AI client not available.")
            return []

        try:
            figma_props = self._get_figma_properties_from_url(figma_url)
            ux_clean = _clean_ux_content(ux_content)
            key_points = _extract_ux_key_points(ux_clean, max_points=25)
            ux_points_text = "\n- " + "\n- ".join(key_points) if key_points else ""
            prompt = f"""
            You are a senior QA automation engineer. Return STRICT JSON (no prose, no markdown).
            - Return only this object shape: {{"test_cases": [{{"description": str, "steps": [{{"action": one of [navigate, click, type, assert_visible, assert_text], "selector"?: css, "url"?: str, "text"?: str}}]}}]}}
            - 3-6 tests max; 5-8 steps per test max.
            - CSS selectors only; keep them robust and specific.
            - Prioritize UX key points; use Jira acceptance criteria to refine only.

            UX key points (extracted):{ux_points_text}

            Figma Properties (truncated):
            {_truncate(figma_props, 1600)}

            Jira (truncated):
            {_truncate(jira_content, 1000)}

            UX Document (truncated):
            {_truncate(ux_clean, 1500)}
            """

            logger.info("Sending request to OpenAI to generate test cases...")
            response = self.ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000,
            )

            payload = _robust_json_parse(response.choices[0].message.content) or {}
            if isinstance(payload, dict):
                test_cases = payload.get("test_cases", [])
            elif isinstance(payload, list):
                test_cases = payload
            else:
                test_cases = []

            # Safe fallback: if parsing failed, provide a minimal smoke test
            if not test_cases:
                logger.warning("AI response could not be parsed into test cases. Using a minimal fallback test.")
                test_cases = [
                    {
                        "description": "Smoke: Landing page loads",
                        "steps": [
                            {"action": "navigate", "url": "/"},
                            {"action": "assert_visible", "selector": "body"}
                        ],
                    }
                ]
            logger.info(f"Successfully generated {len(test_cases)} test cases from AI.")
            return test_cases
        except Exception as e:
            logger.error(f"Failed to generate test cases from AI: {e}")
            return []

    def execute_test_suite(self, web_url: str, test_cases: List[Dict[str, Any]], live_feedback_callback=None, should_stop_callback: Optional[Callable[[], bool]] = None) -> List[Dict[str, Any]]:
        """Execute test cases with Playwright and return results."""
        results: List[Dict[str, Any]] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                # Auto-augment tests for stability
                test_cases = self._augment_test_cases(test_cases)
                for i, test_case in enumerate(test_cases):
                    if should_stop_callback and should_stop_callback():
                        logger.info("Stop requested. Halting test execution loop.")
                        break
                    test_description = test_case.get("description", f"Test Case {i+1}")
                    if live_feedback_callback:
                        live_feedback_callback(f"Running: {test_description}")

                    passed = True
                    failure_reason = ""
                    screenshot_img = None

                    try:
                        steps = test_case.get("steps", [])
                        for idx, step in enumerate(steps):
                            if should_stop_callback and should_stop_callback():
                                raise RuntimeError("Stop requested during step execution.")
                            self._execute_test_step(page, web_url, step)
                            # Heuristic: after navigate, if next step uses a selector, give a short grace wait
                            if step.get("action") == "navigate" and idx + 1 < len(steps):
                                nxt = steps[idx + 1]
                                if nxt.get("selector"):
                                    try:
                                        page.wait_for_timeout(500)  # 0.5s stabilization
                                    except Exception:
                                        pass
                    except Exception as e:
                        passed = False
                        failure_reason = f"Step failed: {step}. Reason: {e}"
                        try:
                            png = page.screenshot(full_page=False)
                            screenshot_img = Image.open(io.BytesIO(png))
                        except Exception:
                            screenshot_img = None

                    results.append({
                        "description": test_description,
                        "passed": passed,
                        "failure_reason": failure_reason,
                        "screenshot": screenshot_img,
                    })
            finally:
                context.close()
                browser.close()
        return results

    def _execute_test_step(self, page, base_url: str, step: Dict[str, Any]):
        action = (step.get("action") or "").strip()
        selector = step.get("selector")
        timeout = int(step.get("timeout_ms", 15000))

        if action == "navigate":
            # Normalize URL: support absolute and relative paths, trim whitespace
            url_raw = step.get("url") or step.get("path") or "/"
            url = str(url_raw).strip()
            try:
                import re
                if re.match(r"^https?://", url, re.IGNORECASE):
                    full_url = url
                else:
                    # Ensure relative path starts with '/'
                    if not url.startswith('/'):
                        url = '/' + url
                    base = (base_url or '').strip()
                    if not base:
                        raise ValueError("Base URL is required for relative navigation steps.")
                    full_url = base.rstrip('/') + url
                logger.info(f"Navigating to: {full_url}")
                page.goto(full_url, timeout=timeout)
                # Allow page to stabilize; configurable via 'load_state'
                load_state = (step.get('load_state') or 'domcontentloaded').strip()
                try:
                    page.wait_for_load_state(load_state, timeout=timeout)
                except Exception:
                    # Non-fatal; continue with next step
                    pass
            except Exception as e:
                raise RuntimeError(f"Navigation failed for url='{url}': {e}")

        elif action == "click":
            loc = page.locator(selector)
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(timeout=timeout)

        elif action == "type":
            text = step.get("text", "")
            loc = page.locator(selector)
            loc.wait_for(state="visible", timeout=timeout)
            # Clear and type
            try:
                loc.fill("", timeout=timeout)
            except Exception:
                pass
            loc.type(text, timeout=timeout)

        elif action == "assert_visible":
            page.locator(selector).wait_for(state="visible", timeout=timeout)

        elif action == "assert_text":
            expected_text = step.get("text", "")
            loc = page.locator(selector)
            loc.wait_for(state="visible", timeout=timeout)
            actual = loc.inner_text(timeout=timeout)
            if expected_text not in actual:
                raise AssertionError(f"Text not found. Expected contains '{expected_text}', actual: '{actual}'")

        elif action in ("wait", "sleep"):
            # Passive wait in milliseconds
            ms = int(step.get("ms", step.get("milliseconds", 1000)))
            page.wait_for_timeout(ms)

        elif action == "wait_for_selector":
            # Wait until selector is attached/visible; defaults to visible
            state = (step.get("state") or "visible").strip()
            page.locator(selector).wait_for(state=state, timeout=timeout)

        elif action == "wait_for_url":
            # Wait until the current URL contains a substring
            substring = (step.get("substring") or step.get("contains") or "").strip()
            if not substring:
                raise ValueError("wait_for_url requires 'substring' or 'contains'.")
            page.wait_for_url(lambda url: substring in str(url), timeout=timeout)

        elif action == "assert_url_contains":
            substring = (step.get("substring") or step.get("contains") or "").strip()
            if not substring:
                raise ValueError("assert_url_contains requires 'substring' or 'contains'.")
            current = page.url
            if substring not in current:
                raise AssertionError(f"URL assertion failed. Expected to contain '{substring}', got '{current}'")

        else:
            raise ValueError(
                "Unknown action: "
                f"{action}\nSupported: navigate, click, type, assert_visible, assert_text, wait/sleep, "
                "wait_for_selector, wait_for_url, assert_url_contains"
            )

    def _url_substring(self, url: str) -> str:
        """Derive a URL substring suitable for wait/assert checks (path + query)."""
        try:
            from urllib.parse import urlparse
            u = urlparse(url)
            # If full URL, use path+query; else treat as relative
            if u.scheme and u.netloc:
                path = u.path or "/"
                if u.query:
                    path += f"?{u.query}"
                return path
            # relative path
            if not url.startswith("/"):
                return f"/{url}"
            return url
        except Exception:
            return url

    def _augment_test_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert stability waits after navigate: wait_for_url and wait_for_selector when helpful."""
        if not isinstance(steps, list):
            return steps
        augmented: List[Dict[str, Any]] = []
        i = 0
        while i < len(steps):
            step = steps[i]
            augmented.append(step)
            try:
                action = (step.get("action") or "").strip()
                if action == "navigate":
                    url = str(step.get("url") or step.get("path") or "/").strip()
                    timeout = int(step.get("timeout_ms", 20000))
                    contains = self._url_substring(url)
                    # Add wait_for_url unless it's already the next step
                    next_action = (steps[i + 1].get("action") if i + 1 < len(steps) else None) or ""
                    if next_action.strip() != "wait_for_url":
                        augmented.append({
                            "action": "wait_for_url",
                            "contains": contains,
                            "timeout_ms": timeout,
                        })
                    # If next step uses a selector and not already a wait_for_selector, insert one
                    if i + 1 < len(steps):
                        nxt = steps[i + 1]
                        if nxt.get("selector") and (nxt.get("action") or "").strip() != "wait_for_selector":
                            augmented.append({
                                "action": "wait_for_selector",
                                "selector": nxt.get("selector"),
                                "state": "visible",
                                "timeout_ms": max(timeout, int(nxt.get("timeout_ms", 0)) or 15000),
                            })
            except Exception:
                # Non-fatal; keep original flow
                pass
            i += 1
        return augmented

    def _augment_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply _augment_test_steps to every test case."""
        if not isinstance(test_cases, list):
            return test_cases
        out: List[Dict[str, Any]] = []
        for tc in test_cases:
            steps = tc.get("steps", [])
            new_tc = dict(tc)
            new_tc["steps"] = self._augment_test_steps(steps)
            out.append(new_tc)
        return out

    def log_failed_tests_to_jira(self, test_results: List[Dict[str, Any]], web_url: str, figma_url: str, jira_ticket_id: str, should_stop_callback: Optional[Callable[[], bool]] = None, attachments_extra: Optional[List[str]] = None):
        """Create Jira bug tickets for any failed tests (uses design8's Jira helper)."""
        tickets_created = []
        for result in test_results:
            if should_stop_callback and should_stop_callback():
                logger.info("Stop requested. Halting Jira logging loop.")
                break
            if result.get("passed"):
                continue

            issue_details = self._format_jira_ticket_functional(
                web_url=web_url,
                figma_url=figma_url,
                original_ticket=jira_ticket_id,
                test_description=result.get('description', ''),
                failure_reason=result.get('failure_reason', '')
            )

            # design8.create_design_qa_ticket expects paths; dump screenshot if available
            attachments_paths: List[str] = []
            try:
                if result.get('screenshot'):
                    img: Image.Image = result['screenshot']
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                        img.save(f.name, format="PNG")
                        attachments_paths.append(f.name)
            except Exception as e:
                logger.warning(f"Could not prepare screenshot attachment: {e}")
            # Add any extra report artifacts
            if attachments_extra:
                for p in attachments_extra:
                    try:
                        if p and os.path.exists(p):
                            attachments_paths.append(p)
                    except Exception:
                        pass

            ticket_result = self.jira.create_design_qa_ticket(
                issue_details,
                assignee_email=self.jira_assignee,
                attachments=attachments_paths
            )
            tickets_created.append(ticket_result)
        return tickets_created

    def _format_jira_ticket_functional(self, web_url: str, figma_url: str, original_ticket: str, test_description: str, failure_reason: str) -> dict:
        """Format for EnhancedJiraIntegration.create_design_qa_ticket (expects title/description/priority)."""
        title = f"Functional Testing - Failure: {test_description}"
        description = f"""
h2. Automated Functional Test Failure

*Test Case:* {test_description}

*Failure Reason:*
{{code}}
{failure_reason}
{{code}}

h3. Context
* Web URL: {web_url}
* Figma Design: {figma_url}
* Original Story: {original_ticket}

h3. Recommendation
Please investigate the failure reason and check the attached screenshot for details.
"""
        return {"title": title, "description": description, "priority": "Medium"}

    def cleanup(self):
        """No long-lived browser resources to clean; Playwright contexts are per-run."""
        pass

    def _save_artifacts_internal(
        self,
        save_dir: str,
        web_url: str,
        figma_url: str,
        jira_ticket_id: str,
        user_stories: Dict[str, Any],
        test_cases: List[Dict[str, Any]],
        test_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Save JSON artifacts and generate an HTML report. Attempt PDF if available.
        Returns a dict of saved paths including report_html/report_pdf and screenshot paths.
        """
        os.makedirs(save_dir, exist_ok=True)
        screenshots_dir = os.path.join(save_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        # Serialize results: save screenshots and strip PIL objects
        serializable_results: List[Dict[str, Any]] = []
        screenshot_paths: List[str] = []
        for idx, r in enumerate(test_results):
            r2 = {
                "description": r.get("description"),
                "passed": bool(r.get("passed")),
                "failure_reason": r.get("failure_reason") or "",
                "screenshot_path": None,
            }
            img = r.get("screenshot")
            if img is not None:
                try:
                    fn = f"fail_{idx+1}.png"
                    fp = os.path.join(screenshots_dir, fn)
                    img.save(fp, format="PNG")
                    r2["screenshot_path"] = fp
                    screenshot_paths.append(fp)
                except Exception:
                    r2["screenshot_path"] = None
            serializable_results.append(r2)

        # Save JSON files
        import json as _json
        us_path = os.path.join(save_dir, "user_stories.json")
        tc_path = os.path.join(save_dir, "test_cases.json")
        tr_path = os.path.join(save_dir, "test_results.json")
        with open(us_path, "w", encoding="utf-8") as f:
            _json.dump(user_stories or {}, f, indent=2)
        with open(tc_path, "w", encoding="utf-8") as f:
            _json.dump(test_cases or [], f, indent=2)
        with open(tr_path, "w", encoding="utf-8") as f:
            _json.dump(serializable_results or [], f, indent=2)

        # Build HTML report
        from datetime import datetime as _dt
        passed = sum(1 for r in serializable_results if r.get("passed"))
        failed = len(serializable_results) - passed
        ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
        def _html_escape(s: str) -> str:
            import html
            return html.escape(s or "")
        rows = []
        for r in serializable_results:
            status = "PASS" if r.get("passed") else "FAIL"
            desc = _html_escape(r.get("description") or "")
            reason = _html_escape(r.get("failure_reason") or "")
            shot = r.get("screenshot_path")
            img_tag = f'<img src="{os.path.basename(shot)}" style="max-width:480px;border:1px solid #ddd;" />' if (shot and os.path.exists(shot)) else ""
            rows.append(f"<tr><td>{status}</td><td>{desc}</td><td>{reason}</td><td>{img_tag}</td></tr>")
        table_html = "\n".join(rows)
        html_content = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Functional Test Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
    h1, h2 {{ margin-bottom: 0.3rem; }}
    .meta {{ color: #666; margin-bottom: 1rem; }}
    .summary {{ background: #f5f7fa; padding: 10px 12px; border-radius: 8px; margin: 1rem 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #fafafa; text-align: left; }}
    .pass {{ color: #0a7f3f; font-weight: 600; }}
    .fail {{ color: #b00020; font-weight: 600; }}
    code {{ background: #f2f2f2; padding: 2px 4px; border-radius: 4px; }}
  </style>
  <base href="{_html_escape(screenshots_dir)}/" />
  <!-- The base tag allows using just the screenshot file names in img src -->
  <script> </script>
  
</head>
<body>
  <h1>Functional Test Report</h1>
  <div class="meta">Generated: {ts}</div>
  <div class="summary">
    <div>Web URL: <code>{_html_escape(web_url)}</code></div>
    <div>Figma URL: <code>{_html_escape(figma_url)}</code></div>
    <div>Jira Ticket: <code>{_html_escape(jira_ticket_id)}</code></div>
    <div>Total: <strong>{len(serializable_results)}</strong> &nbsp;|&nbsp; <span class="pass">Passed: {passed}</span> &nbsp;|&nbsp; <span class="fail">Failed: {failed}</span></div>
  </div>
  <h2>Results</h2>
  <table>
    <thead><tr><th>Status</th><th>Description</th><th>Failure Reason</th><th>Screenshot</th></tr></thead>
    <tbody>
      {table_html}
    </tbody>
  </table>
</body>
</html>
"""
        report_html_path = os.path.join(save_dir, "report.html")
        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Attempt to produce a PDF using pdfkit/wkhtmltopdf if available
        report_pdf_path = None
        try:
            import pdfkit  # type: ignore
            try:
                report_pdf_path = os.path.join(save_dir, "report.pdf")
                pdfkit.from_file(report_html_path, report_pdf_path)
            except Exception as e:
                logger.info(f"PDF generation skipped/failed: {e}")
                report_pdf_path = None
        except Exception:
            report_pdf_path = None

        return {
            "user_stories": us_path,
            "test_cases": tc_path,
            "test_results": tr_path,
            "report_html": report_html_path,
            **({"report_pdf": report_pdf_path} if report_pdf_path else {}),
            "screenshots": screenshot_paths,
        }

    def save_artifacts(
        self,
        save_dir: str,
        web_url: str,
        figma_url: str,
        jira_ticket_id: str,
        user_stories: Dict[str, Any],
        test_cases: List[Dict[str, Any]],
        test_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Public wrapper to save artifacts and build HTML/PDF report."""
        try:
            return self._save_artifacts_internal(save_dir, web_url, figma_url, jira_ticket_id, user_stories, test_cases, test_results)
        except Exception as e:
            logger.warning(f"Failed to save artifacts: {e}")
            return {}

    def run_full_test_cycle(
        self,
        figma_url: str,
        web_url: str,
        jira_ticket_id: str,
        figma_ux_url: Optional[str] = None,
        ux_file_content: Optional[str] = None,
        live_feedback_callback=None,
    should_stop_callback: Optional[Callable[[], bool]] = None,
    save_dir: Optional[str] = None,
    attach_report_to_jira: bool = False,
    ):
        """End-to-end: pull Jira context, generate user stories, generate tests, run with Playwright, and log failures."""
        if live_feedback_callback:
            live_feedback_callback("Fetching details from Jira...")
        if should_stop_callback and should_stop_callback():
            return {"stopped": True}
        jira_content = self.get_jira_acceptance_criteria(jira_ticket_id)

        # Build UX content from file and/or Figma UX URL
        ux_text_sources: List[str] = []
        if ux_file_content:
            ux_text_sources.append(ux_file_content)
        if figma_ux_url:
            if live_feedback_callback:
                live_feedback_callback("Reading UX text from Figma...")
            if should_stop_callback and should_stop_callback():
                return {"stopped": True}
            ux_figma_text = self.get_ux_text_from_figma_url(figma_ux_url)
            if ux_figma_text:
                ux_text_sources.append(ux_figma_text)

        ux_combined = "\n\n---\n\n".join([t for t in ux_text_sources if t])

        user_stories = {}
        if ux_combined:
            if live_feedback_callback:
                live_feedback_callback("Generating user stories from UX document...")
            if should_stop_callback and should_stop_callback():
                return {"stopped": True}
            user_stories = self.generate_user_stories_from_ux(ux_combined, jira_content)

        if live_feedback_callback:
            live_feedback_callback("Generating test cases with AI...")
        if should_stop_callback and should_stop_callback():
            return {"stopped": True}
        test_cases = self.generate_test_cases_from_ai(figma_url, jira_content, ux_combined)

        if not test_cases:
            return {"error": "Failed to generate test cases."}

        if live_feedback_callback:
            live_feedback_callback(f"Executing {len(test_cases)} test cases...")
        if should_stop_callback and should_stop_callback():
            return {"stopped": True}
        test_results = self.execute_test_suite(web_url, test_cases, live_feedback_callback, should_stop_callback)

        # Save artifacts if requested (HTML and optional PDF)
        saved_paths: Dict[str, Any] = {}
        if save_dir:
            saved_paths = self.save_artifacts(save_dir, web_url, figma_url, jira_ticket_id, user_stories, test_cases, test_results)

        if live_feedback_callback:
            live_feedback_callback("Logging failed tests to Jira...")
        if should_stop_callback and should_stop_callback():
            return {
                "user_stories_generated": user_stories,
                "test_cases_generated": test_cases,
                "test_results": test_results,
                "jira_tickets_created": [],
                "artifacts": saved_paths,
                "stopped": True,
            }
        attachments_extra = []
        if attach_report_to_jira and saved_paths:
            for key in ("report_pdf", "report_html", "test_cases", "test_results"):
                p = saved_paths.get(key)
                if p:
                    attachments_extra.append(p)
        tickets = self.log_failed_tests_to_jira(test_results, web_url, figma_url, jira_ticket_id, should_stop_callback, attachments_extra=attachments_extra)

        return {
            "user_stories_generated": user_stories,
            "test_cases_generated": test_cases,
            "test_results": test_results,
            "jira_tickets_created": tickets,
            "artifacts": saved_paths,
        }
