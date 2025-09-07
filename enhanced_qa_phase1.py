"""
Enhanced Design QA System - Phase 1: Core Architecture and Foundation
Merges practical UI from design7.py with advanced analytics from oldcode.py
"""

# import streamlit as st  # Removed for Flask compatibility
import os
import asyncio
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from collections import defaultdict, Counter
from enum import Enum
import json
import hashlib
import tempfile
import shutil
from pathlib import Path

# Core logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Priority(Enum):
    """Enhanced priority levels with confidence weighting"""
    CRITICAL = ("Critical", 15)
    HIGH = ("High", 10) 
    MEDIUM = ("Medium", 5)
    LOW = ("Low", 2)
    MINIMAL = ("Minimal", 1)
    
    def __init__(self, label, weight):
        self.label = label
        self.weight = weight

class IssueCategory(Enum):
    """Comprehensive issue categories"""
    VISUAL_DESIGN = "Visual Design"
    RESPONSIVE_DESIGN = "Responsive Design"
    ACCESSIBILITY = "Accessibility"
    UI_ELEMENTS = "UI Elements"
    TYPOGRAPHY = "Typography"
    COLOR_USAGE = "Color Usage"
    SPACING_LAYOUT = "Spacing & Layout"
    PERFORMANCE = "Performance"
    BRAND_CONSISTENCY = "Brand Consistency"

@dataclass
class EnhancedDesignIssue:
    """Enhanced design issue with intelligence capabilities"""
    issue_id: str
    severity: Priority
    category: IssueCategory
    subcategory: str
    description: str
    
    # Technical details
    element_selector: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    screenshot_coords: Optional[Dict[str, int]] = None
    
    # Intelligence features
    confidence_score: float = 1.0
    pattern_match: Optional[str] = None
    suggested_fix: str = ""
    impact_assessment: Optional[Dict[str, Any]] = None
    
    # Context
    figma_layer_name: Optional[str] = None
    viewport_context: Optional[str] = None
    browser_context: Optional[str] = None
    
    # Metadata
    detection_method: str = "automated"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IssuePattern:
    """Represents recurring issue patterns"""
    pattern_id: str
    issue_type: str
    frequency: int
    elements_affected: List[str]
    root_cause_hypothesis: str
    suggested_systematic_fix: str
    confidence: float
    business_impact: str
    first_detected: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ConfigurationManager:
    """Enhanced configuration management with validation"""
    
    def __init__(self):
        self.config = self._load_default_config()
        self._validate_environment()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration with all required settings"""
        return {
            'api_keys': {
                'groq_api_key': os.getenv("GROQ_API_KEY", ""),
                'figma_access_token': os.getenv("FIGMA_ACCESS_TOKEN", ""),
                'openai_api_key': os.getenv("OPENAI_API_KEY", "")
            },
            'jira': {
                'server_url': os.getenv("JIRA_SERVER_URL", ""),
                'email': os.getenv("JIRA_EMAIL", ""),
                'api_token': os.getenv("JIRA_API_TOKEN", ""),
                'project_key': os.getenv("JIRA_PROJECT_KEY", "")
            },
            'analysis': {
                'viewports': [
                    {'width': 1920, 'height': 1080, 'name': 'Desktop'},
                    {'width': 1024, 'height': 768, 'name': 'Tablet'},
                    {'width': 375, 'height': 667, 'name': 'Mobile'}
                ],
                'similarity_threshold': 0.95,
                'confidence_threshold': 0.7,
                'max_issues_per_category': 20
            },
            'quality_gates': {
                'min_compliance_score': 85,
                'max_critical_issues': 0,
                'min_accessibility_score': 90
            },
            'features': {
                'learning_enabled': True,
                'pattern_detection': True,
                'auto_jira_creation': False,
                'advanced_reporting': True
            }
        }
    
    def _validate_environment(self):
        """Validate environment configuration"""
        required_keys = [
            'GROQ_API_KEY', 'FIGMA_ACCESS_TOKEN'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            logger.warning(f"Missing environment variables: {missing_keys}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, updates)
        logger.info("Configuration updated")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()

class IntelligentIssueManager:
    """Advanced issue management with pattern detection and learning"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.learning_enabled = config.get('features', {}).get('learning_enabled', True)
        self.issue_history: List[EnhancedDesignIssue] = []
        self.pattern_database: Dict[str, IssuePattern] = {}
        self.false_positive_patterns: Set[str] = set()
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
    
    def process_issues(self, issues: List[EnhancedDesignIssue], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process issues with intelligent filtering and enhancement"""
        
        logger.info(f"Processing {len(issues)} issues with intelligent analysis")
        
        # Step 1: Filter false positives
        filtered_issues = self._filter_false_positives(issues)
        logger.info(f"Filtered {len(issues) - len(filtered_issues)} false positives")
        
        # Step 2: Detect patterns
        patterns = self._detect_issue_patterns(filtered_issues)
        logger.info(f"Detected {len(patterns)} issue patterns")
        
        # Step 3: Enhance with context
        enhanced_issues = self._enhance_issues_with_context(filtered_issues, context, patterns)
        
        # Step 4: Group related issues
        issue_groups = self._group_related_issues(enhanced_issues)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_systematic_recommendations(patterns, issue_groups)
        
        # Step 6: Update learning database
        if self.learning_enabled:
            self._update_learning_database(enhanced_issues, patterns)
        
        return {
            'processed_issues': enhanced_issues,
            'issue_patterns': patterns,
            'issue_groups': issue_groups,
            'systematic_recommendations': recommendations,
            'filtering_stats': {
                'original_count': len(issues),
                'filtered_count': len(filtered_issues),
                'false_positives_removed': len(issues) - len(filtered_issues)
            }
        }
    
    def _filter_false_positives(self, issues: List[EnhancedDesignIssue]) -> List[EnhancedDesignIssue]:
        """Filter out known false positive patterns"""
        filtered_issues = []
        confidence_threshold = self.config.get('analysis', {}).get('confidence_threshold', 0.7)
        
        for issue in issues:
            # Check confidence score
            if issue.confidence_score < confidence_threshold:
                logger.debug(f"Filtered low confidence issue: {issue.description}")
                continue
            
            # Check against known false positive patterns
            issue_signature = self._generate_issue_signature(issue)
            if issue_signature in self.false_positive_patterns:
                logger.debug(f"Filtered known false positive: {issue.description}")
                continue
            
            # Heuristic filtering
            if self._is_likely_false_positive(issue):
                logger.debug(f"Filtered heuristic false positive: {issue.description}")
                continue
            
            filtered_issues.append(issue)
        
        return filtered_issues
    
    def _generate_issue_signature(self, issue: EnhancedDesignIssue) -> str:
        """Generate unique signature for issue identification"""
        content = f"{issue.category.value}_{issue.subcategory}_{issue.element_selector}_{issue.description[:50]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_likely_false_positive(self, issue: EnhancedDesignIssue) -> bool:
        """Use heuristics to identify likely false positives"""
        
        # Very low confidence
        if issue.confidence_score < 0.3:
            return True
        
        # Browser-specific differences for minor issues
        browser_keywords = ['webkit', 'moz', 'scroll', 'shadow', 'outline']
        if any(keyword in issue.description.lower() for keyword in browser_keywords):
            if issue.severity in [Priority.LOW, Priority.MINIMAL]:
                return True
        
        # Micro-differences in spacing (< 2px) for minor issues
        if issue.category == IssueCategory.SPACING_LAYOUT and issue.severity == Priority.LOW:
            import re
            numbers = re.findall(r'\d+', issue.description)
            if numbers and all(int(num) <= 2 for num in numbers):
                return True
        
        return False
    
    def _detect_issue_patterns(self, issues: List[EnhancedDesignIssue]) -> List[IssuePattern]:
        """Detect recurring patterns in design issues"""
        patterns = []
        
        # Group by category and subcategory
        category_groups = defaultdict(list)
        element_groups = defaultdict(list)
        
        for issue in issues:
            category_groups[issue.category.value].append(issue)
            
            if issue.element_selector:
                element_type = self._extract_element_type(issue.element_selector)
                element_groups[element_type].append(issue)
        
        # Analyze category patterns
        for category, category_issues in category_groups.items():
            if len(category_issues) >= 3:  # Minimum threshold
                pattern = self._analyze_category_pattern(category, category_issues)
                if pattern:
                    patterns.append(pattern)
        
        # Analyze element-specific patterns
        for element_type, element_issues in element_groups.items():
            if len(element_issues) >= 2:
                pattern = self._analyze_element_pattern(element_type, element_issues)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _extract_element_type(self, selector: str) -> str:
        """Extract element type from CSS selector"""
        if not selector:
            return 'unknown'
        
        if selector.startswith('#'):
            return 'id_element'
        elif selector.startswith('.'):
            class_name = selector.split('.')[1].split(' ')[0].split(':')[0]
            return f'class_{class_name}'
        elif any(tag in selector.lower() for tag in ['button', 'input', 'form', 'nav', 'header', 'footer']):
            for tag in ['button', 'input', 'form', 'nav', 'header', 'footer']:
                if tag in selector.lower():
                    return tag
        return 'generic_element'
    
    def _analyze_category_pattern(self, category: str, issues: List[EnhancedDesignIssue]) -> Optional[IssuePattern]:
        """Analyze pattern within a category"""
        
        # Find common keywords in descriptions
        descriptions = [issue.description.lower() for issue in issues]
        common_keywords = self._find_common_keywords(descriptions)
        
        if not common_keywords:
            return None
        
        # Generate root cause hypothesis
        root_cause_map = {
            'Visual Design': 'Inconsistent implementation of design system components',
            'Typography': 'Missing or incorrect font-family/size declarations in CSS',
            'Color Usage': 'Hard-coded color values instead of design tokens',
            'Spacing & Layout': 'Inconsistent spacing utilities or missing design tokens',
            'Accessibility': 'Insufficient accessibility implementation across components'
        }
        
        root_cause = root_cause_map.get(category, 'Multiple related issues suggest systematic problem')
        
        pattern_id = f"{category.lower().replace(' ', '_')}_{hashlib.md5(''.join(common_keywords).encode()).hexdigest()[:8]}"
        
        return IssuePattern(
            pattern_id=pattern_id,
            issue_type=f"{category} Pattern",
            frequency=len(issues),
            elements_affected=[issue.element_selector for issue in issues if issue.element_selector],
            root_cause_hypothesis=root_cause,
            suggested_systematic_fix=self._generate_systematic_fix(category, common_keywords),
            confidence=min(0.9, sum(issue.confidence_score for issue in issues) / len(issues)),
            business_impact=self._assess_business_impact(category, len(issues))
        )
    
    def _find_common_keywords(self, descriptions: List[str], min_frequency: int = 2) -> List[str]:
        """Find common keywords in descriptions"""
        all_words = []
        stop_words = {'this', 'that', 'with', 'from', 'should', 'does', 'have', 'been', 'the', 'and', 'or'}
        
        for desc in descriptions:
            words = [w for w in desc.lower().split() if len(w) > 3 and w not in stop_words]
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.items() if count >= min_frequency][:10]
    
    def _generate_systematic_fix(self, category: str, keywords: List[str]) -> str:
        """Generate systematic fix recommendations"""
        fix_templates = {
            'Visual Design': 'Review and standardize component implementation across design system',
            'Typography': 'Implement consistent typography scale and font loading strategy',
            'Color Usage': 'Replace hard-coded colors with CSS custom properties and design tokens',
            'Spacing & Layout': 'Standardize spacing utilities and implement consistent grid system',
            'Accessibility': 'Conduct comprehensive accessibility audit and implement WCAG 2.1 guidelines'
        }
        
        return fix_templates.get(category, 'Analyze root cause and implement systematic solution')
    
    def _assess_business_impact(self, category: str, issue_count: int) -> str:
        """Assess business impact of issue pattern"""
        impact_map = {
            'Accessibility': 'High - Legal compliance and user inclusivity at risk',
            'Visual Design': 'Medium - Brand consistency and user trust affected',
            'Typography': 'Medium - Readability and user experience impacted',
            'Responsive Design': 'High - Mobile user experience significantly affected',
            'Performance': 'High - User conversion and engagement at risk'
        }
        
        base_impact = impact_map.get(category, 'Medium - User experience affected')
        
        if issue_count >= 10:
            return f"Critical - {base_impact} (widespread issue)"
        elif issue_count >= 5:
            return f"High - {base_impact} (multiple occurrences)"
        else:
            return base_impact
    
    def _enhance_issues_with_context(self, issues: List[EnhancedDesignIssue], 
                                   context: Dict[str, Any], 
                                   patterns: List[IssuePattern]) -> List[EnhancedDesignIssue]:
        """Enhance issues with additional context and improved suggestions"""
        enhanced_issues = []
        
        for issue in issues:
            # Find related patterns
            related_patterns = [p for p in patterns if issue.element_selector in p.elements_affected]
            
            # Create enhanced version
            enhanced_issue = EnhancedDesignIssue(
                issue_id=issue.issue_id,
                severity=issue.severity,
                category=issue.category,
                subcategory=issue.subcategory,
                description=issue.description,
                element_selector=issue.element_selector,
                expected_value=issue.expected_value,
                actual_value=issue.actual_value,
                screenshot_coords=issue.screenshot_coords,
                confidence_score=issue.confidence_score,
                pattern_match=related_patterns[0].pattern_id if related_patterns else None,
                suggested_fix=self._enhance_suggested_fix(issue, related_patterns),
                impact_assessment=self._calculate_impact_assessment(issue, related_patterns, context),
                figma_layer_name=issue.figma_layer_name,
                viewport_context=context.get('current_viewport'),
                browser_context=context.get('browser_info'),
                detection_method=issue.detection_method,
                timestamp=issue.timestamp,
                metadata=issue.metadata
            )
            
            enhanced_issues.append(enhanced_issue)
        
        return enhanced_issues
    
    def _enhance_suggested_fix(self, issue: EnhancedDesignIssue, 
                             related_patterns: List[IssuePattern]) -> str:
        """Generate enhanced fix suggestions with pattern context"""
        base_fix = issue.suggested_fix
        
        if related_patterns:
            pattern = related_patterns[0]
            enhanced_fix = f"{base_fix} (Pattern-based fix: {pattern.suggested_systematic_fix})"
            return enhanced_fix
        
        return base_fix or self._generate_default_fix(issue)
    
    def _generate_default_fix(self, issue: EnhancedDesignIssue) -> str:
        """Generate default fix suggestion based on issue type"""
        fix_map = {
            IssueCategory.TYPOGRAPHY: "Review font-family, font-size, or line-height declarations",
            IssueCategory.COLOR_USAGE: "Update color values to match design specifications",
            IssueCategory.SPACING_LAYOUT: "Adjust margin, padding, or grid/flexbox properties",
            IssueCategory.ACCESSIBILITY: "Add proper ARIA labels, improve contrast, or enhance keyboard navigation",
            IssueCategory.RESPONSIVE_DESIGN: "Update responsive breakpoints and mobile-specific styles"
        }
        
        return fix_map.get(issue.category, "Review implementation against design specifications")
    
    def _calculate_impact_assessment(self, issue: EnhancedDesignIssue,
                                   related_patterns: List[IssuePattern],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive impact assessment"""
        
        # Base impact calculation
        severity_impact = {
            Priority.CRITICAL: 0.9,
            Priority.HIGH: 0.7,
            Priority.MEDIUM: 0.5,
            Priority.LOW: 0.3,
            Priority.MINIMAL: 0.1
        }
        
        base_impact = severity_impact.get(issue.severity, 0.5)
        
        # Pattern multiplier
        pattern_multiplier = 1.5 if related_patterns else 1.0
        
        # Viewport context multiplier
        viewport_multiplier = 1.3 if issue.viewport_context == 'Mobile' else 1.0
        
        final_impact = min(1.0, base_impact * pattern_multiplier * viewport_multiplier)
        
        return {
            'impact_score': round(final_impact, 2),
            'user_groups_affected': self._identify_affected_user_groups(issue),
            'business_areas_impacted': self._identify_business_impact_areas(issue),
            'technical_debt_contribution': self._calculate_tech_debt_impact(issue),
            'resolution_priority': self._calculate_resolution_priority(issue, final_impact)
        }
    
    def _identify_affected_user_groups(self, issue: EnhancedDesignIssue) -> List[str]:
        """Identify which user groups are affected"""
        groups = []
        
        if issue.category == IssueCategory.ACCESSIBILITY:
            groups.extend(['Users with disabilities', 'Screen reader users', 'Keyboard-only users'])
        
        if issue.viewport_context == 'Mobile':
            groups.append('Mobile users')
        elif issue.viewport_context == 'Tablet':
            groups.append('Tablet users')
        
        if issue.category == IssueCategory.TYPOGRAPHY:
            groups.append('All users (readability)')
        
        return groups or ['General users']
    
    def _identify_business_impact_areas(self, issue: EnhancedDesignIssue) -> List[str]:
        """Identify business areas impacted"""
        impact_areas = []
        
        severity_to_areas = {
            Priority.CRITICAL: ['User conversion', 'Brand reputation', 'Legal compliance'],
            Priority.HIGH: ['User experience', 'Customer satisfaction'],
            Priority.MEDIUM: ['User engagement', 'Design consistency'],
            Priority.LOW: ['Polish', 'Professional appearance']
        }
        
        return severity_to_areas.get(issue.severity, ['General quality'])
    
    def _calculate_tech_debt_impact(self, issue: EnhancedDesignIssue) -> str:
        """Calculate technical debt contribution"""
        if issue.pattern_match:
            return "High - Contributes to systematic design debt"
        elif issue.severity in [Priority.CRITICAL, Priority.HIGH]:
            return "Medium - Individual high-impact issue"
        else:
            return "Low - Isolated minor issue"
    
    def _calculate_resolution_priority(self, issue: EnhancedDesignIssue, impact_score: float) -> int:
        """Calculate resolution priority (1-5, 1 being highest)"""
        if issue.severity == Priority.CRITICAL:
            return 1
        elif issue.severity == Priority.HIGH and impact_score > 0.7:
            return 2
        elif issue.pattern_match:  # Part of a pattern
            return 2
        elif issue.severity == Priority.MEDIUM:
            return 3
        elif issue.severity == Priority.LOW:
            return 4
        else:
            return 5
    
    def _group_related_issues(self, issues: List[EnhancedDesignIssue]) -> Dict[str, List[EnhancedDesignIssue]]:
        """Group related issues for batch processing"""
        groups = defaultdict(list)
        
        for issue in issues:
            # Group by pattern if available
            if issue.pattern_match:
                groups[f"pattern_{issue.pattern_match}"].append(issue)
            # Group by category and viewport
            elif issue.viewport_context:
                groups[f"{issue.category.value}_{issue.viewport_context}"].append(issue)
            # Group by category
            else:
                groups[issue.category.value].append(issue)
        
        return dict(groups)
    
    def _generate_systematic_recommendations(self, patterns: List[IssuePattern], 
                                           issue_groups: Dict[str, List[EnhancedDesignIssue]]) -> List[Dict[str, Any]]:
        """Generate systematic recommendations"""
        recommendations = []
        
        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.frequency >= 3:
                recommendations.append({
                    'type': 'systematic_fix',
                    'priority': 'High' if pattern.frequency >= 5 else 'Medium',
                    'title': f"Address {pattern.issue_type}",
                    'description': pattern.suggested_systematic_fix,
                    'affected_elements': len(pattern.elements_affected),
                    'business_impact': pattern.business_impact,
                    'implementation_effort': self._estimate_implementation_effort(pattern),
                    'success_metrics': self._define_success_metrics(pattern)
                })
        
        # Design system recommendations
        design_system_issues = sum(1 for p in patterns if 'design system' in p.suggested_systematic_fix.lower())
        if design_system_issues >= 2:
            recommendations.append({
                'type': 'design_system_audit',
                'priority': 'High',
                'title': 'Design System Implementation Review',
                'description': 'Multiple patterns indicate systematic design system implementation gaps',
                'estimated_effort': '2-3 sprints',
                'deliverables': [
                    'Updated design token implementation',
                    'Component library audit and fixes',
                    'Automated validation rules',
                    'Implementation guidelines'
                ]
            })
        
        return recommendations
    
    def _estimate_implementation_effort(self, pattern: IssuePattern) -> str:
        """Estimate implementation effort for pattern fix"""
        if pattern.frequency >= 10:
            return "High (3-5 days)"
        elif pattern.frequency >= 5:
            return "Medium (1-2 days)"
        else:
            return "Low (2-4 hours)"
    
    def _define_success_metrics(self, pattern: IssuePattern) -> List[str]:
        """Define success metrics for pattern resolution"""
        return [
            f"Reduce {pattern.issue_type} issues by 90%",
            f"Improve consistency score in {pattern.issue_type} category",
            "Pass automated validation checks",
            "Maintain fix across future deployments"
        ]
    
    def _update_learning_database(self, issues: List[EnhancedDesignIssue], 
                                patterns: List[IssuePattern]):
        """Update learning database with new insights"""
        if not self.learning_enabled:
            return
        
        # Store issue history
        self.issue_history.extend(issues)
        
        # Update pattern database
        for pattern in patterns:
            if pattern.pattern_id in self.pattern_database:
                # Update existing pattern
                existing = self.pattern_database[pattern.pattern_id]
                existing.frequency += pattern.frequency
                existing.confidence = (existing.confidence + pattern.confidence) / 2
            else:
                # Store new pattern
                self.pattern_database[pattern.pattern_id] = pattern
        
        logger.info(f"Updated learning database: {len(self.issue_history)} total issues, {len(self.pattern_database)} patterns")

class PerformanceMonitor:
    """Monitor system performance and analysis metrics"""
    
    def __init__(self):
        self.analysis_times = {}
        self.start_times = {}
        self.metrics = defaultdict(list)
    
    def start_analysis(self, analysis_type: str):
        """Start timing an analysis phase"""
        self.start_times[analysis_type] = datetime.now()
    
    def end_analysis(self, analysis_type: str, metadata: Dict[str, Any] = None):
        """End timing and record metrics"""
        if analysis_type in self.start_times:
            duration = (datetime.now() - self.start_times[analysis_type]).total_seconds()
            self.analysis_times[analysis_type] = duration
            
            if metadata:
                self.metrics[analysis_type].append({
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    **metadata
                })
            
            logger.info(f"{analysis_type} completed in {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'total_analysis_duration': sum(self.analysis_times.values()),
            'phase_durations': self.analysis_times.copy(),
            'detailed_metrics': dict(self.metrics)
        }

class EnhancedDesignQASystem:
    """Main system orchestrator combining UI and advanced analytics"""
    
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.issue_manager = IntelligentIssueManager(self.config_manager.get_config())
        self.performance_monitor = PerformanceMonitor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize session state (removed streamlit dependency)
        # if 'qa_system' not in st.session_state:
        #     st.session_state.qa_system = {
        #         'analysis_history': [],
        #         'current_analysis': None,
        #         'config_validated': False
        #     }
    
    def setup_streamlit_ui(self):
        """Setup Streamlit UI with enhanced features (disabled for Flask)"""
        pass
        # st.set_page_config(
        #     page_title="Enhanced Design QA System",
        #     page_icon="🎨",
        #     layout="wide",
        #     initial_sidebar_state="expanded"
        # )
        
        # Custom CSS for enhanced UI
        # st.markdown("""
        # <style>
        # .main-header {
        #     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        #     padding: 2rem;
        #     border-radius: 10px;
        #     color: white;
        #     margin-bottom: 2rem;
        # }
        # .metric-card {
        #     background: white;
        #     padding: 1.5rem;
        #     border-radius: 8px;
        #     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        #     border-left: 4px solid #667eea;
        # }
        # .issue-card {
        #     background: #f8f9fa;
        #     padding: 1rem;
        #     border-radius: 6px;
        #     margin: 0.5rem 0;
        #     border-left: 4px solid #dc3545;
        # }
        # .issue-card.high { border-left-color: #fd7e14; }
        # .issue-card.medium { border-left-color: #ffc107; }
        # .issue-card.low { border-left-color: #28a745; }
        # </style>
        # """, unsafe_allow_html=True)
    
    def render_main_interface(self):
        """Render the main interface (disabled for Flask)"""
        
