"""
Enhanced Design QA Module

This module provides advanced design QA capabilities including intelligent issue detection,
pattern recognition, and comprehensive reporting.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional, Any, Tuple, Union
import json
import asyncio
from datetime import datetime, timedelta
import hashlib
import numpy as np
from collections import defaultdict, Counter
import logging
from pathlib import Path

@dataclass
class DesignIssue:
    """Represents a design issue found during QA analysis"""
    issue_id: str
    severity: str  # Critical, High, Medium, Low
    category: str  # Typography, Color, Spacing, Layout, etc.
    element_selector: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    description: str = ""
    screenshot_coords: Optional[Dict[str, int]] = None
    figma_layer_name: Optional[str] = None
    confidence_score: float = 1.0
    suggested_fix: str = ""
    impact_assessment: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

logger = logging.getLogger(__name__)

@dataclass
class IssuePattern:
    """Represents a recurring issue pattern across analyses"""
    pattern_id: str
    issue_type: str
    frequency: int
    elements_affected: List[str]
    root_cause_hypothesis: str
    suggested_systematic_fix: str
    confidence: float
    business_impact: str

class IntelligentIssueManager:
    """Advanced issue management with pattern detection and learning"""
    
    def __init__(self, learning_enabled: bool = True):
        self.learning_enabled = learning_enabled
        self.issue_history: List[DesignIssue] = []
        self.pattern_database: Dict[str, IssuePattern] = {}
        self.false_positive_patterns: Set[str] = set()
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
        
    def process_issues(self, issues: List[DesignIssue], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process issues with intelligent filtering and enhancement"""
        
        # Step 1: Filter false positives based on learned patterns
        filtered_issues = self._filter_false_positives(issues)
        
        # Step 2: Detect recurring patterns
        patterns = self._detect_issue_patterns(filtered_issues)
        
        # Step 3: Enhance issues with context and suggestions
        enhanced_issues = self._enhance_issues_with_context(filtered_issues, context, patterns)
        
        # Step 4: Group related issues
        issue_groups = self._group_related_issues(enhanced_issues)
        
        # Step 5: Generate systematic recommendations
        systematic_recommendations = self._generate_systematic_recommendations(patterns, issue_groups)
        
        # Step 6: Update learning database
        if self.learning_enabled:
            self._update_learning_database(enhanced_issues, patterns)
        
        return {
            'processed_issues': enhanced_issues,
            'issue_patterns': patterns,
            'issue_groups': issue_groups,
            'systematic_recommendations': systematic_recommendations,
            'filtering_stats': {
                'original_count': len(issues),
                'filtered_count': len(filtered_issues),
                'false_positives_removed': len(issues) - len(filtered_issues)
            }
        }
    
    def _filter_false_positives(self, issues: List[DesignIssue]) -> List[DesignIssue]:
        """Filter out known false positive patterns"""
        filtered_issues = []
        
        for issue in issues:
            issue_signature = self._generate_issue_signature(issue)
            
            # Check against known false positive patterns
            is_false_positive = any(
                pattern in issue_signature 
                for pattern in self.false_positive_patterns
            )
            
            # Additional heuristic filtering
            if not is_false_positive:
                is_false_positive = self._is_likely_false_positive(issue)
            
            if not is_false_positive:
                filtered_issues.append(issue)
            else:
                logger.debug(f"Filtered false positive: {issue.description}")
        
        return filtered_issues
    
    def _is_likely_false_positive(self, issue: DesignIssue) -> bool:
        """Use heuristics to identify likely false positives"""
        
        # Very low confidence issues
        if issue.confidence_score < 0.3:
            return True
            
        # Issues with browser-specific differences that might be acceptable
        browser_specific_keywords = ['webkit', 'moz', 'scroll', 'shadow', 'outline']
        if any(keyword in issue.description.lower() for keyword in browser_specific_keywords):
            if issue.severity == 'Minor':
                return True
        
        # Micro-differences in spacing (< 2px) for minor issues
        if issue.category == 'Spacing' and issue.severity == 'Minor':
            try:
                if any(char.isdigit() for char in issue.description):
                    # Extract numbers from description
                    import re
                    numbers = re.findall(r'\d+', issue.description)
                    if numbers and all(int(num) <= 2 for num in numbers):
                        return True
            except:
                pass
        
        return False
    
    def _detect_issue_patterns(self, issues: List[DesignIssue]) -> List[IssuePattern]:
        """Detect recurring patterns in design issues"""
        patterns = []
        
        # Group issues by category and element type
        category_groups = defaultdict(list)
        element_groups = defaultdict(list)
        
        for issue in issues:
            category_groups[issue.category].append(issue)
            
            # Extract element type from selector
            element_type = self._extract_element_type(issue.element_selector)
            element_groups[element_type].append(issue)
        
        # Detect category patterns
        for category, category_issues in category_groups.items():
            if len(category_issues) >= 3:  # Minimum threshold for pattern
                pattern = self._analyze_category_pattern(category, category_issues)
                if pattern:
                    patterns.append(pattern)
        
        # Detect element-specific patterns
        for element_type, element_issues in element_groups.items():
            if len(element_issues) >= 2:
                pattern = self._analyze_element_pattern(element_type, element_issues)
                if pattern:
                    patterns.append(pattern)
        
        # Detect cross-cutting concerns
        cross_cutting_patterns = self._detect_cross_cutting_patterns(issues)
        patterns.extend(cross_cutting_patterns)
        
        return patterns
    
    def _analyze_category_pattern(self, category: str, issues: List[DesignIssue]) -> Optional[IssuePattern]:
        """Analyze pattern within a specific category"""
        
        # Common descriptions/keywords
        descriptions = [issue.description.lower() for issue in issues]
        common_keywords = self._find_common_keywords(descriptions)
        
        if not common_keywords:
            return None
        
        # Determine root cause hypothesis
        root_cause_map = {
            'Typography': {
                'font': 'Inconsistent font loading or CSS font-family declarations',
                'size': 'Missing or incorrect font-size declarations in design system',
                'weight': 'Font weight variations not properly mapped in CSS',
                'line': 'Line-height values not standardized'
            },
            'Color': {
                'hex': 'Hard-coded color values instead of design tokens',
                'background': 'Missing CSS custom properties for background colors',
                'contrast': 'Insufficient contrast validation in design system'
            },
            'Spacing': {
                'margin': 'Inconsistent margin utilities or missing spacing tokens',
                'padding': 'Component padding not standardized',
                'gap': 'Grid/flexbox gap values not defined in design system'
            }
        }
        
        root_cause = "Multiple issues suggest systematic problem"
        systematic_fix = "Review and update design system implementation"
        
        # Look for specific root cause
        for keyword in common_keywords:
            if category in root_cause_map:
                for pattern_key, hypothesis in root_cause_map[category].items():
                    if pattern_key in keyword:
                        root_cause = hypothesis
                        systematic_fix = self._generate_systematic_fix(category, pattern_key)
                        break
        
        return IssuePattern(
            pattern_id=f"{category.lower()}_{hashlib.md5(''.join(common_keywords).encode()).hexdigest()[:8]}",
            issue_type=f"{category} Pattern",
            frequency=len(issues),
            elements_affected=[issue.element_selector for issue in issues],
            root_cause_hypothesis=root_cause,
            suggested_systematic_fix=systematic_fix,
            confidence=min(0.9, sum(issue.confidence_score for issue in issues) / len(issues)),
            business_impact=self._assess_business_impact(category, len(issues))
        )
    
    def _detect_cross_cutting_patterns(self, issues: List[DesignIssue]) -> List[IssuePattern]:
        """Detect patterns that span multiple categories"""
        patterns = []
        
        # Responsive design issues
        mobile_issues = [i for i in issues if 'mobile' in i.description.lower() or '375' in str(i.screenshot_coords)]
        if len(mobile_issues) >= 3:
            patterns.append(IssuePattern(
                pattern_id=f"responsive_{len(mobile_issues)}",
                issue_type="Responsive Design",
                frequency=len(mobile_issues),
                elements_affected=[i.element_selector for i in mobile_issues],
                root_cause_hypothesis="Responsive design implementation gaps",
                suggested_systematic_fix="Comprehensive responsive design audit and mobile-first approach",
                confidence=0.8,
                business_impact="High - Mobile user experience significantly impacted"
            ))
        
        # Accessibility issues
        a11y_keywords = ['contrast', 'color', 'text', 'readable']
        a11y_issues = [i for i in issues if any(keyword in i.description.lower() for keyword in a11y_keywords)]
        if len(a11y_issues) >= 2:
            patterns.append(IssuePattern(
                pattern_id=f"accessibility_{len(a11y_issues)}",
                issue_type="Accessibility",
                frequency=len(a11y_issues),
                elements_affected=[i.element_selector for i in a11y_issues],
                root_cause_hypothesis="Insufficient accessibility considerations in implementation",
                suggested_systematic_fix="Implement automated accessibility testing and WCAG compliance audit",
                confidence=0.85,
                business_impact="High - Legal compliance and user inclusivity at risk"
            ))
        
        return patterns
    
    def _enhance_issues_with_context(self, issues: List[DesignIssue], context: Dict[str, Any], patterns: List[IssuePattern]) -> List[DesignIssue]:
        """Enhance issues with additional context and improved suggestions"""
        enhanced_issues = []
        
        for issue in issues:
            # Find related patterns
            related_patterns = [p for p in patterns if issue.element_selector in p.elements_affected]
            
            # Enhance description with pattern context
            enhanced_description = issue.description
            if related_patterns:
                pattern_context = f" (Part of {related_patterns[0].issue_type} pattern affecting {related_patterns[0].frequency} elements)"
                enhanced_description += pattern_context
            
            # Improve suggested fix with pattern-aware recommendations
            enhanced_fix = issue.suggested_fix
            if related_patterns:
                enhanced_fix += f" Consider systematic fix: {related_patterns[0].suggested_systematic_fix}"
            
            # Create enhanced issue
            enhanced_issue = DesignIssue(
                issue_id=issue.issue_id,
                severity=issue.severity,
                category=issue.category,
                element_selector=issue.element_selector,
                expected_value=issue.expected_value,
                actual_value=issue.actual_value,
                description=enhanced_description,
                screenshot_coords=issue.screenshot_coords,
                figma_layer_name=issue.figma_layer_name,
                confidence_score=issue.confidence_score,
                suggested_fix=enhanced_fix,
                impact_assessment=self._enhance_impact_assessment(issue, related_patterns, context)
            )
            
            enhanced_issues.append(enhanced_issue)
        
        return enhanced_issues
    
    def _generate_systematic_recommendations(self, patterns: List[IssuePattern], issue_groups: Dict[str, List[DesignIssue]]) -> List[Dict[str, Any]]:
        """Generate systematic recommendations based on patterns"""
        recommendations = []
        
        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.frequency >= 3:  # High-impact patterns
                recommendations.append({
                    'type': 'systematic_fix',
                    'priority': 'High' if pattern.frequency >= 5 else 'Medium',
                    'title': f"Address {pattern.issue_type} Pattern",
                    'description': pattern.suggested_systematic_fix,
                    'affected_elements': len(pattern.elements_affected),
                    'estimated_impact': pattern.business_impact,
                    'implementation_steps': self._generate_implementation_steps(pattern),
                    'success_metrics': self._define_success_metrics(pattern)
                })
        
        # Design system recommendations
        if any('design system' in p.suggested_systematic_fix.lower() for p in patterns):
            recommendations.append({
                'type': 'design_system',
                'priority': 'High',
                'title': 'Design System Implementation Review',
                'description': 'Multiple issues indicate design system implementation gaps',
                'implementation_steps': [
                    'Audit current design token implementation',
                    'Identify missing or incorrectly implemented tokens',
                    'Update component library with correct token usage',
                    'Implement automated design token validation',
                    'Create comprehensive design system documentation'
                ],
                'estimated_effort': '2-3 sprints',
                'success_metrics': ['Reduced design inconsistencies by 80%', 'Improved compliance score above 90%']
            })
        
        return recommendations
    
    def _generate_implementation_steps(self, pattern: IssuePattern) -> List[str]:
        """Generate specific implementation steps for pattern fixes"""
        steps_map = {
            'Typography': [
                'Audit font loading and CSS font-family declarations',
                'Standardize font-size, font-weight, and line-height values',
                'Implement design system typography tokens',
                'Update component library with standardized typography'
            ],
            'Color': [
                'Replace hard-coded color values with CSS custom properties',
                'Implement design system color tokens',
                'Validate color contrast ratios',
                'Update brand color usage guidelines'
            ],
            'Spacing': [
                'Audit margin and padding implementations',
                'Implement standardized spacing scale',
                'Update layout components with consistent spacing',
                'Add spacing utilities to design system'
            ],
            'Responsive': [
                'Conduct mobile-first design review',
                'Implement responsive breakpoint strategy',
                'Test across all target devices',
                'Update responsive design documentation'
            ]
        }
        
        for key, steps in steps_map.items():
            if key.lower() in pattern.issue_type.lower():
                return steps
        
        return ['Analyze root cause', 'Implement systematic fix', 'Validate across affected elements']

class AdvancedReportGenerator:
    """Generate comprehensive reports with insights and recommendations"""
    
    def __init__(self):
        self.report_templates = {
            'executive_summary': self._generate_executive_summary,
            'technical_details': self._generate_technical_details,
            'implementation_guide': self._generate_implementation_guide,
            'trend_analysis': self._generate_trend_analysis
        }
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate HTML report with multiple sections"""
        
        # Extract data
        issues = analysis_results.get('design_issues', [])
        patterns = analysis_results.get('issue_patterns', [])
        compliance_metrics = analysis_results.get('compliance_metrics', {})
        recommendations = analysis_results.get('recommendations', [])
        
        # Generate report sections
        sections = {}
        for section_name, generator in self.report_templates.items():
            sections[section_name] = generator(analysis_results)
        
        # Build HTML report
        html_report = self._build_html_report(sections, analysis_results)
        
        return html_report
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary with key metrics and insights"""
        metrics = results.get('compliance_metrics', {})
        total_issues = results.get('analysis_metadata', {}).get('total_issues_found', 0)
        
        # Calculate trend indicators (would be based on historical data in real implementation)
        compliance_score = metrics.get('overall_score', 0)
        score_trend = "improving" if compliance_score > 80 else "needs attention"
        
        # Risk assessment
        critical_issues = metrics.get('critical_issues', 0)
        risk_level = "High" if critical_issues > 5 else "Medium" if critical_issues > 0 else "Low"
        
        summary = f"""
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            
            <div class="key-metrics">
                <div class="metric">
                    <h3>Design Compliance Score</h3>
                    <div class="score {score_trend}">{compliance_score}%</div>
                    <div class="trend">Trend: {score_trend.title()}</div>
                </div>
                
                <div class="metric">
                    <h3>Total Issues</h3>
                    <div class="count">{total_issues}</div>
                    <div class="breakdown">
                        Critical: {metrics.get('critical_issues', 0)} | 
                        Major: {metrics.get('major_issues', 0)} | 
                        Minor: {metrics.get('minor_issues', 0)}
                    </div>
                </div>
                
                <div class="metric">
                    <h3>Risk Level</h3>
                    <div class="risk {risk_level.lower()}">{risk_level}</div>
                    <div class="impact">Business impact assessment</div>
                </div>
            </div>
            
            <div class="key-insights">
                <h3>Key Insights</h3>
                <ul>
                    <li>Most common issues are in <strong>{self._get_top_category(metrics)}</strong> category</li>
                    <li>{'No critical issues detected' if critical_issues == 0 else f'{critical_issues} critical issues require immediate attention'}</li>
                    <li>Design system implementation shows {'good consistency' if compliance_score > 85 else 'opportunities for improvement'}</li>
                </ul>
            </div>
        </div>
        """
        
        return summary
    
    def _generate_technical_details(self, results: Dict[str, Any]) -> str:
        """Generate detailed technical analysis"""
        issues = results.get('design_issues', [])
        performance_metrics = results.get('performance_metrics', {})
        
        # Group issues by category
        category_breakdown = defaultdict(list)
        for issue in issues:
            category_breakdown[issue.get('category', 'Unknown')].append(issue)
        
        technical_details = f"""
        <div class="technical-details">
            <h2>Technical Analysis</h2>
            
            <div class="analysis-metadata">
                <h3>Analysis Performance</h3>
                <p>Total analysis time: {performance_metrics.get('total_analysis_duration', 'N/A')} seconds</p>
                <p>Elements analyzed: {results.get('webpage_analysis', {}).get('total_elements_analyzed', 'N/A')}</p>
                <p>Viewports tested: {len(results.get('webpage_analysis', {}).get('viewports_tested', []))}</p>
            </div>
            
            <div class="category-analysis">
                <h3>Issues by Category</h3>
        """
        
        for category, category_issues in category_breakdown.items():
            technical_details += f"""
                <div class="category-section">
                    <h4>{category} ({len(category_issues)} issues)</h4>
                    <div class="issue-list">
            """
            
            for issue in category_issues[:5]:  # Show top 5 per category
                technical_details += f"""
                        <div class="issue-item {issue.get('severity', '').lower()}">
                            <div class="issue-header">
                                <span class="severity">{issue.get('severity', 'Unknown')}</span>
                                <span class="confidence">Confidence: {issue.get('confidence_score', 0):.2f}</span>
                            </div>
                            <div class="issue-description">{issue.get('description', '')}</div>
                            <div class="issue-fix">{issue.get('suggested_fix', '')}</div>
                        </div>
                """
            
            technical_details += """
                    </div>
                </div>
            """
        
        technical_details += """
            </div>
        </div>
        """
        
        return technical_details
    
    def _build_html_report(self, sections: Dict[str, str], results: Dict[str, Any]) -> str:
        """Build complete HTML report with styling"""
        
        timestamp = results.get('analysis_metadata', {}).get('timestamp', datetime.now().isoformat())
        figma_url = results.get('analysis_metadata', {}).get('figma_url', '')
        webpage_url = results.get('analysis_metadata', {}).get('webpage_url', '')
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Design QA Report - {timestamp}</title>
            <style>
                {self._get_report_styles()}
            </style>
        </head>
        <body>
            <div class="report-container">
                <header class="report-header">
                    <h1>🎨 AI Design QA Analysis Report</h1>
                    <div class="analysis-info">
                        <p><strong>Analysis Date:</strong> {timestamp}</p>
                        <p><strong>Figma Design:</strong> <a href="{figma_url}" target="_blank">View Design</a></p>
                        <p><strong>Webpage URL:</strong> <a href="{webpage_url}" target="_blank">View Page</a></p>
                    </div>
                </header>
                
                <nav class="report-nav">
                    <a href="#executive-summary">Summary</a>
                    <a href="#technical-details">Technical Details</a>
                    <a href="#implementation-guide">Implementation Guide</a>
                    <a href="#trend-analysis">Trends</a>
                </nav>
                
                <main class="report-content">
                    <section id="executive-summary">
                        {sections.get('executive_summary', '')}
                    </section>
                    
                    <section id="technical-details">
                        {sections.get('technical_details', '')}
                    </section>
                    
                    <section id="implementation-guide">
                        {sections.get('implementation_guide', '')}
                    </section>
                    
                    <section id="trend-analysis">
                        {sections.get('trend_analysis', '')}
                    </section>
                </main>
                
                <footer class="report-footer">
                    <p>Generated by Enhanced AI Design QA Agent v2.0</p>
                    <p>Powered by GPT-4 Vision + Computer Vision Analysis</p>
                </footer>
            </div>
            
            <script>
                {self._get_report_javascript()}
            </script>
        </body>
        </html>
        """
        
        return html_template
    
    def _get_report_styles(self) -> str:
        """Get comprehensive CSS styles for the report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .report-header h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .analysis-info p {
            margin: 0.5rem 0;
        }
        
        .analysis-info a {
            color: #fff;
            text-decoration: underline;
        }
        
        .report-nav {
            background: #2c3e50;
            padding: 1rem 2rem;
            display: flex;
            gap: 2rem;
        }
        
        .report-nav a {
            color: #ecf0f1;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.3s;
        }
        
        .report-nav a:hover {
            background: #34495e;
        }
        
        .report-content {
            padding: 2rem;
        }
        
        section {
            margin-bottom: 3rem;
            padding: 2rem;
            border-radius: 8px;
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .key-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        
        .metric {
            text-align: center;
            padding: 1.5rem;
            border-radius: 8px;
            background: #f8f9fa;
        }
        
        .score {
            font-size: 3rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .score.improving {
            color: #27ae60;
        }
        
        .score.needs-attention {
            color: #e74c3c;
        }
        
        .risk {
            font-size: 1.5rem;
            font-weight: bold;
            padding: 0.5rem;
            border-radius: 4px;
        }
        
        .risk.high {
            color: #e74c3c;
            background: #fadbd8;
        }
        
        .risk.medium {
            color: #f39c12;
            background: #fef9e7;
        }
        
        .risk.low {
            color: #27ae60;
            background: #d5f4e6;
        }
        
        .issue-item {
            border-left: 4px solid #bdc3c7;
            padding: 1rem;
            margin: 1rem 0;
            background: #f8f9fa;
        }
        
        .issue-item.critical {
            border-left-color: #e74c3c;
        }
        
        .issue-item.major {
            border-left-color: #f39c12;
        }
        
        .issue-item.minor {
            border-left-color: #3498db;
        }
        
        .issue-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .severity {
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .confidence {
            font-size: 0.9em;
            color: #666;
        }
        
        .report-footer {
            background: #2c3e50;
            color: #ecf0f1;
            text-align: center;
            padding: 2rem;
        }
        
        @media (max-width: 768px) {
            .report-nav {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .key-metrics {
                grid-template-columns: 1fr;
            }
            
            .report-header h1 {
                font-size: 2rem;
            }
        }
        """
    
    def _get_report_javascript(self) -> str:
        """Get JavaScript for report interactivity"""
        return """
        // Smooth scrolling for navigation
        document.querySelectorAll('.report-nav a').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Add interactive features
        document.addEventListener('DOMContentLoaded', function() {
            // Highlight current section in navigation
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        document.querySelectorAll('.report-nav a').forEach(link => {
                            link.classList.remove('active');
                        });
                        const activeLink = document.querySelector(`.report-nav a[href="#${id}"]`);
                        if (activeLink) {
                            activeLink.classList.add('active');
                        }
                    }
                });
            }, { threshold: 0.5 });
            
            document.querySelectorAll('section').forEach(section => {
                observer.observe(section);
            });
        });
        """
    
    def _get_top_category(self, metrics: Dict[str, Any]) -> str:
        """Get the category with the most issues"""
        category_scores = metrics.get('category_scores', {})
        if not category_scores:
            return "General"
        
        # Find category with lowest score (most issues)
        top_category = min(category_scores.keys(), 
                          key=lambda k: category_scores[k].get('score', 100))
        return top_category
    
    # Placeholder methods for other report sections
    def _generate_implementation_guide(self, results: Dict[str, Any]) -> str:
        return "<div class='implementation-guide'><h2>Implementation Guide</h2><p>Detailed implementation steps would be generated here based on patterns and recommendations.</p></div>"
    
    def _generate_trend_analysis(self, results: Dict[str, Any]) -> str:
        return "<div class='trend-analysis'><h2>Trend Analysis</h2><p>Historical trend analysis would be shown here with charts and insights.</p></div>"

# Utility functions for the enhanced system
def generate_issue_signature(issue: DesignIssue) -> str:
    """Generate unique signature for issue deduplication"""
    content = f"{issue.category}_{issue.element_selector}_{issue.description[:50]}"
    return hashlib.md5(content.encode()).hexdigest()

def extract_element_type(selector: str) -> str:
    """Extract element type from CSS selector"""
    if selector.startswith('#'):
        return 'id_element'
    elif selector.startswith('.'):
        # Extract first class name
        class_name = selector.split('.')[1].split(' ')[0]
        return f'class_{class_name}'
    elif any(tag in selector.lower() for tag in ['button', 'input', 'form', 'nav', 'header', 'footer']):
        for tag in ['button', 'input', 'form', 'nav', 'header', 'footer']:
            if tag in selector.lower():
                return tag
    return 'generic_element'

def find_common_keywords(descriptions: List[str], min_frequency: int = 2) -> List[str]:
    """Find common keywords in issue descriptions"""
    # Tokenize and count
    all_words = []
    for desc in descriptions:
        words = desc.lower().split()
        # Filter out common words
        filtered_words = [w for w in words if len(w) > 3 and w not in {'this', 'that', 'with', 'from', 'should', 'does', 'have', 'been'}]
        all_words.extend(filtered_words)
    
    # Count frequency
    word_counts = Counter(all_words)
    
    # Return words that appear at least min_frequency times
    common_words = [word for word, count in word_counts.items() if count >= min_frequency]
    return common_words[:10]  # Top 10 most common

# Advanced Configuration and Orchestration
class EnhancedQAOrchestrator:
    """Main orchestrator that coordinates all QA components with advanced features"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.figma_analyzer = EnhancedFigmaAnalyzer(config['figma']['access_token'])
        self.webpage_analyzer = AdvancedWebpageAnalyzer()
        self.openai_client = AsyncOpenAI(api_key=config['openai']['api_key'])
        self.comparator = IntelligentDesignComparator(self.openai_client)
        self.issue_manager = IntelligentIssueManager(learning_enabled=config.get('learning_enabled', True))
        self.report_generator = AdvancedReportGenerator()
        
        # Initialize integrations
        self.jira_integration = None
        if config.get('jira', {}).get('url'):
            self.jira_integration = EnhancedJiraIntegration(config['jira'])
        
        self.performance_monitor = PerformanceMonitor()
        
    async def run_comprehensive_qa_analysis(
        self, 
        figma_url: str, 
        webpage_url: str, 
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run comprehensive QA analysis with all advanced features"""
        
        options = options or {}
        self.performance_monitor.start_analysis('total_execution')
        
        try:
            # Phase 1: Data Collection
            logger.info("Phase 1: Collecting design and implementation data")
            self.performance_monitor.start_analysis('data_collection')
            
            # Parallel data collection for efficiency
            figma_task = self.figma_analyzer.extract_design_specifications(figma_url)
            
            viewports = self.config.get('testing', {}).get('viewports', [
                {'width': 1920, 'height': 1080, 'name': 'Desktop'},
                {'width': 768, 'height': 1024, 'name': 'Tablet'},  
                {'width': 375, 'height': 667, 'name': 'Mobile'}
            ])
            webpage_task = self.webpage_analyzer.analyze_webpage(webpage_url, viewports)
            
            figma_data, webpage_data = await asyncio.gather(figma_task, webpage_task)
            
            self.performance_monitor.end_analysis('data_collection', {
                'figma_components': len(figma_data.get('component_specs', {})),
                'webpage_elements': sum(len(data.get('visual_elements', {}).get('ui_components', [])) for data in webpage_data.values())
            })
            
            # Phase 2: Intelligent Analysis
            logger.info("Phase 2: Performing intelligent design comparison")
            self.performance_monitor.start_analysis('design_comparison')
            
            comparison_rules = self.config.get('comparison_rules', {})
            raw_issues = await self.comparator.compare_designs(figma_data, webpage_data, comparison_rules)
            
            self.performance_monitor.end_analysis('design_comparison', {
                'raw_issues_found': len(raw_issues)
            })
            
            # Phase 3: Issue Processing & Enhancement
            logger.info("Phase 3: Processing and enhancing issues with AI")
            self.performance_monitor.start_analysis('issue_processing')
            
            context = {
                'figma_url': figma_url,
                'webpage_url': webpage_url,
                'viewports': viewports,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            processed_results = self.issue_manager.process_issues(raw_issues, context)
            
            self.performance_monitor.end_analysis('issue_processing', {
                'issues_filtered': processed_results['filtering_stats']['false_positives_removed'],
                'patterns_detected': len(processed_results['issue_patterns'])
            })
            
            # Phase 4: Generate Comprehensive Results
            logger.info("Phase 4: Generating comprehensive analysis results")
            
            compliance_metrics = self._calculate_advanced_compliance_metrics(
                processed_results['processed_issues'], 
                figma_data, 
                webpage_data
            )
            
            # Phase 5: Create Reports and Tickets (if enabled)
            if options.get('create_jira_tickets') and self.jira_integration:
                await self._create_comprehensive_jira_tickets(processed_results)
            
            self.performance_monitor.end_analysis('total_execution')
            
            # Compile final results
            final_results = {
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'figma_url': figma_url,
                    'webpage_url': webpage_url,
                    'total_issues_found': len(processed_results['processed_issues']),
                    'analysis_version': '2.0',
                    'ai_model_used': self.config['openai'].get('model', 'gpt-4-vision-preview')
                },
                'figma_analysis': {
                    'design_tokens_extracted': len(figma_data.get('design_tokens', {}).get('colors', {})),
                    'components_analyzed': len(figma_data.get('component_specs', {})),
                    'screenshots_generated': len(figma_data.get('screenshots', {}))
                },
                'webpage_analysis': {
                    'viewports_tested': list(webpage_data.keys()),
                    'total_elements_analyzed': sum(
                        len(data.get('visual_elements', {}).get('ui_components', [])) 
                        for data in webpage_data.values()
                    ),
                    'performance_scores': self._extract_performance_scores(webpage_data)
                },
                'design_issues': [asdict(issue) for issue in processed_results['processed_issues']],
                'issue_patterns': [asdict(pattern) for pattern in processed_results['issue_patterns']],
                'issue_groups': processed_results['issue_groups'],
                'systematic_recommendations': processed_results['systematic_recommendations'],
                'compliance_metrics': compliance_metrics,
                'intelligent_insights': self._generate_intelligent_insights(processed_results, compliance_metrics),
                'performance_metrics': self.performance_monitor.get_performance_summary(),
                'quality_gates': self._evaluate_quality_gates(compliance_metrics, processed_results),
                'next_actions': self._generate_next_actions(processed_results, compliance_metrics)
            }
            
            return final_results
            
        except Exception as e:
            logger.error(f"Comprehensive QA analysis failed: {e}")
            self.performance_monitor.end_analysis('total_execution')
            raise
    
    def _calculate_advanced_compliance_metrics(
        self, 
        issues: List[DesignIssue], 
        figma_data: Dict, 
        webpage_data: Dict
    ) -> Dict[str, Any]:
        """Calculate advanced compliance metrics with contextual scoring"""
        
        if not issues:
            return {
                "overall_score": 100,
                "category_scores": {},
                "advanced_metrics": {
                    "design_system_adherence": 100,
                    "responsive_consistency": 100,
                    "accessibility_score": 100,
                    "brand_compliance": 100
                }
            }
        
        # Base compliance calculation
        severity_weights = {"Critical": 15, "Major": 8, "Minor": 3}
        category_penalties = defaultdict(int)
        total_penalty = 0
        
        for issue in issues:
            penalty = severity_weights.get(issue.severity, 3)
            # Apply confidence multiplier
            adjusted_penalty = penalty * issue.confidence_score
            
            total_penalty += adjusted_penalty
            category_penalties[issue.category] += adjusted_penalty
        
        # Calculate base scores
        overall_score = max(0, 100 - total_penalty)
        
        category_scores = {}
        for category in ['Typography', 'Color', 'Spacing', 'Layout', 'Content']:
            category_issues = [i for i in issues if i.category == category]
            if category_issues:
                category_penalty = sum(
                    severity_weights.get(i.severity, 3) * i.confidence_score 
                    for i in category_issues
                )
                category_score = max(0, 100 - category_penalty)
                
                category_scores[category] = {
                    "score": round(category_score, 1),
                    "issue_count": len(category_issues),
                    "severity_breakdown": {
                        "Critical": len([i for i in category_issues if i.severity == "Critical"]),
                        "Major": len([i for i in category_issues if i.severity == "Major"]),
                        "Minor": len([i for i in category_issues if i.severity == "Minor"])
                    },
                    "confidence_average": round(
                        sum(i.confidence_score for i in category_issues) / len(category_issues), 2
                    )
                }
        
        # Advanced metrics
        advanced_metrics = self._calculate_advanced_design_metrics(issues, figma_data, webpage_data)
        
        return {
            "overall_score": round(overall_score, 1),
            "category_scores": category_scores,
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i.severity == "Critical"]),
            "major_issues": len([i for i in issues if i.severity == "Major"]),
            "minor_issues": len([i for i in issues if i.severity == "Minor"]),
            "average_confidence": round(sum(i.confidence_score for i in issues) / len(issues), 2),
            "advanced_metrics": advanced_metrics
        }
    
    def _calculate_advanced_design_metrics(
        self, 
        issues: List[DesignIssue], 
        figma_data: Dict, 
        webpage_data: Dict
    ) -> Dict[str, Any]:
        """Calculate advanced design system and UX metrics"""
        
        # Design System Adherence Score
        design_system_issues = [i for i in issues if any(
            keyword in i.description.lower() 
            for keyword in ['token', 'design system', 'consistent', 'standard']
        )]
        design_system_score = max(0, 100 - len(design_system_issues) * 10)
        
        # Responsive Consistency Score
        mobile_issues = [i for i in issues if 'mobile' in i.description.lower() or '375' in str(i.screenshot_coords)]
        tablet_issues = [i for i in issues if 'tablet' in i.description.lower() or '768' in str(i.screenshot_coords)]
        responsive_score = max(0, 100 - (len(mobile_issues) + len(tablet_issues)) * 8)
        
        # Accessibility Score
        a11y_keywords = ['contrast', 'color', 'text', 'readable', 'accessibility', 'wcag']
        a11y_issues = [i for i in issues if any(keyword in i.description.lower() for keyword in a11y_keywords)]
        accessibility_score = max(0, 100 - len(a11y_issues) * 12)
        
        # Brand Compliance Score
        brand_keywords = ['color', 'font', 'typography', 'brand', 'logo', 'style']
        brand_issues = [i for i in issues if any(keyword in i.description.lower() for keyword in brand_keywords)]
        brand_score = max(0, 100 - len(brand_issues) * 8)
        
        # Performance Impact Score (based on issue types that affect performance)
        performance_keywords = ['large', 'size', 'optimization', 'loading', 'performance']
        performance_issues = [i for i in issues if any(keyword in i.description.lower() for keyword in performance_keywords)]
        performance_score = max(0, 100 - len(performance_issues) * 15)
        
        return {
            "design_system_adherence": round(design_system_score, 1),
            "responsive_consistency": round(responsive_score, 1),
            "accessibility_score": round(accessibility_score, 1),
            "brand_compliance": round(brand_score, 1),
            "performance_impact": round(performance_score, 1),
            "ux_consistency": round((design_system_score + responsive_score) / 2, 1)
        }
    
    def _generate_intelligent_insights(
        self, 
        processed_results: Dict[str, Any], 
        compliance_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered insights from the analysis"""
        
        insights = []
        
        issues = processed_results['processed_issues']
        patterns = processed_results['issue_patterns']
        
        # Pattern-based insights
        if patterns:
            most_frequent_pattern = max(patterns, key=lambda p: p.frequency)
            insights.append({
                'type': 'pattern_insight',
                'title': f'Recurring {most_frequent_pattern.issue_type} Pattern Detected',
                'description': f'Found {most_frequent_pattern.frequency} similar issues suggesting systematic problem',
                'impact': 'high',
                'recommendation': most_frequent_pattern.suggested_systematic_fix,
                'confidence': most_frequent_pattern.confidence
            })
        
        # Compliance trend insights
        overall_score = compliance_metrics['overall_score']
        if overall_score >= 90:
            insights.append({
                'type': 'positive_insight',
                'title': 'Excellent Design Implementation Quality',
                'description': f'Achieved {overall_score}% compliance with minimal critical issues',
                'impact': 'positive',
                'recommendation': 'Focus on minor optimizations and maintain current quality standards'
            })
        elif overall_score < 70:
            critical_count = compliance_metrics['critical_issues']
            insights.append({
                'type': 'concern_insight',
                'title': 'Design Implementation Needs Attention',
                'description': f'Compliance score of {overall_score}% with {critical_count} critical issues',
                'impact': 'high',
                'recommendation': 'Prioritize critical issue resolution and implement systematic improvements'
            })
        
        # Category-specific insights
        category_scores = compliance_metrics.get('category_scores', {})
        if category_scores:
            lowest_category = min(category_scores.keys(), key=lambda k: category_scores[k]['score'])
            lowest_score = category_scores[lowest_category]['score']
            
            if lowest_score < 80:
                insights.append({
                    'type': 'category_insight',
                    'title': f'{lowest_category} Category Requires Focus',
                    'description': f'{lowest_category} scored {lowest_score}% with {category_scores[lowest_category]["issue_count"]} issues',
                    'impact': 'medium',
                    'recommendation': f'Conduct focused {lowest_category.lower()} review and implement systematic fixes'
                })
        
        # Advanced metrics insights
        advanced_metrics = compliance_metrics.get('advanced_metrics', {})
        if advanced_metrics.get('accessibility_score', 100) < 85:
            insights.append({
                'type': 'accessibility_insight',
                'title': 'Accessibility Improvements Needed',
                'description': f'Accessibility score of {advanced_metrics["accessibility_score"]}% indicates compliance gaps',
                'impact': 'high',
                'recommendation': 'Conduct comprehensive accessibility audit and implement WCAG 2.1 guidelines',
                'compliance_risk': True
            })
        
        return insights
    
    def _evaluate_quality_gates(
        self, 
        compliance_metrics: Dict[str, Any], 
        processed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate quality gates for CI/CD integration"""
        
        gates = {
            'overall_compliance': {
                'threshold': self.config.get('quality_gates', {}).get('min_compliance_score', 85),
                'current': compliance_metrics['overall_score'],
                'status': 'pass' if compliance_metrics['overall_score'] >= self.config.get('quality_gates', {}).get('min_compliance_score', 85) else 'fail'
            },
            'critical_issues': {
                'threshold': self.config.get('quality_gates', {}).get('max_critical_issues', 0),
                'current': compliance_metrics['critical_issues'],
                'status': 'pass' if compliance_metrics['critical_issues'] <= self.config.get('quality_gates', {}).get('max_critical_issues', 0) else 'fail'
            },
            'accessibility_score': {
                'threshold': self.config.get('quality_gates', {}).get('min_accessibility_score', 90),
                'current': compliance_metrics.get('advanced_metrics', {}).get('accessibility_score', 100),
                'status': 'pass' if compliance_metrics.get('advanced_metrics', {}).get('accessibility_score', 100) >= self.config.get('quality_gates', {}).get('min_accessibility_score', 90) else 'fail'
            }
        }
        
        # Overall gate status
        all_passed = all(gate['status'] == 'pass' for gate in gates.values())
        
        return {
            'overall_status': 'pass' if all_passed else 'fail',
            'individual_gates': gates,
            'summary': f"{'All quality gates passed' if all_passed else 'Some quality gates failed'}"
        }
    
    def _generate_next_actions(
        self, 
        processed_results: Dict[str, Any], 
        compliance_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized next actions based on analysis"""
        
        actions = []
        
        # Critical issue actions
        critical_issues = [i for i in processed_results['processed_issues'] if i.severity == 'Critical']
        if critical_issues:
            actions.append({
                'priority': 1,
                'action': 'Fix Critical Issues',
                'description': f'Address {len(critical_issues)} critical design issues immediately',
                'estimated_effort': 'High',
                'timeline': 'This Sprint',
                'owner': 'Development Team',
                'tickets_to_create': len(critical_issues)
            })
        
        # Pattern-based actions
        patterns = processed_results['issue_patterns']
        high_impact_patterns = [p for p in patterns if p.frequency >= 5]
        if high_impact_patterns:
            actions.append({
                'priority': 2,
                'action': 'Implement Systematic Fixes',
                'description': f'Address {len(high_impact_patterns)} recurring patterns affecting multiple elements',
                'estimated_effort': 'Medium',
                'timeline': 'Next Sprint',
                'owner': 'Design System Team',
                'systematic_impact': True
            })
        
        # Design system actions
        if compliance_metrics.get('advanced_metrics', {}).get('design_system_adherence', 100) < 80:
            actions.append({
                'priority': 3,
                'action': 'Design System Audit',
                'description': 'Comprehensive review and update of design system implementation',
                'estimated_effort': 'High',
                'timeline': '2-3 Sprints',
                'owner': 'Design System Team',
                'deliverable': 'Updated design system documentation and tokens'
            })
        
        return actions
    
    async def _create_comprehensive_jira_tickets(self, processed_results: Dict[str, Any]):
        """Create comprehensive Jira tickets with enhanced information"""
        
        if not self.jira_integration:
            logger.warning("Jira integration not configured")
            return
        
        ticket_ids = []
        
        # Create individual issue tickets
        for issue in processed_results['processed_issues']:
            if issue.severity in ['Critical', 'Major']:  # Only create tickets for important issues
                ticket_id = await self.jira_integration.create_design_issue_ticket(
                    issue, 
                    {}  # Screenshots would be included in real implementation
                )
                ticket_ids.append(ticket_id)
        
        # Create pattern-based epic tickets
        for pattern in processed_results['issue_patterns']:
            if pattern.frequency >= 3:  # Significant patterns
                epic_ticket = await self.jira_integration.create_pattern_epic(pattern)
                ticket_ids.append(epic_ticket)
        
        logger.info(f"Created {len(ticket_ids)} Jira tickets")
        return ticket_ids
    
    def _extract_performance_scores(self, webpage_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract performance scores from webpage analysis data"""
        # This would extract actual performance metrics in a real implementation
        return {
            'loading_time': 2.5,  # seconds
            'layout_shift': 0.1,  # CLS score
            'render_time': 1.8,   # seconds
            'accessibility_score': 92  # percentage
        }

# Entry point for the enhanced system
async def main():
    """Main entry point demonstrating the enhanced Design QA Agent"""
    
    # Load configuration
    config = ConfigurationManager.load_config()
    
    # Initialize orchestrator
    orchestrator = EnhancedQAOrchestrator(config)
    
    # Example usage
    try:
        results = await orchestrator.run_comprehensive_qa_analysis(
            figma_url="https://www.figma.com/file/example/design-file",
            webpage_url="https://example.com/page-to-test",
            options={
                'create_jira_tickets': True,
                'generate_comprehensive_report': True
            }
        )
        
        # Print summary
        print(f"\n🎉 Enhanced Design QA Analysis Complete!")
        print(f"📊 Overall Compliance Score: {results['compliance_metrics']['overall_score']}%")
        print(f"🐛 Total Issues: {results['analysis_metadata']['total_issues_found']}")
        print(f"🔍 Patterns Detected: {len(results['issue_patterns'])}")
        print(f"⚡ Analysis Time: {results['performance_metrics']['total_analysis_duration']:.2f}s")
        
        # Quality gates status
        gates_status = results['quality_gates']['overall_status']
        print(f"🚪 Quality Gates: {'✅ PASSED' if gates_status == 'pass' else '❌ FAILED'}")
        
        # Next actions summary
        next_actions = results['next_actions']
        if next_actions:
            print(f"\n📋 Next Actions ({len(next_actions)}):")
            for action in next_actions[:3]:
                print(f"  {action['priority']}. {action['action']} - {action['timeline']}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())