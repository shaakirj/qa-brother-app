from typing import Dict, List, Any, Optional
from enhanced_qa_phase1 import EnhancedDesignIssue, IssuePattern, Priority, IssueCategory, ConfigurationManager, IntelligentIssueManager, logger
from enhanced_qa_phase2 import AdvancedChromeDriver, EnhancedFigmaIntegration

class AdvancedReportGenerator:
    """Advanced report generation with multiple formats and business intelligence"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.report_templates = {
            'executive_summary': self._generate_executive_summary,
            'technical_details': self._generate_technical_details,
            'implementation_guide': self._generate_implementation_guide,
            'trend_analysis': self._generate_trend_analysis,
            'business_intelligence': self._generate_business_intelligence
        }
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                    format_type: str = 'html') -> str:
        """Generate comprehensive report in specified format"""
        
        if format_type == 'html':
            return self._generate_html_report(analysis_results)
        elif format_type == 'pdf':
            return self._generate_pdf_report(analysis_results)
        elif format_type == 'json':
            return self._generate_json_report(analysis_results)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive HTML report"""
        
        # Extract key metrics
        compliance_score = results.get('compliance_metrics', {}).get('overall_score', 0)
        total_issues = len(results.get('processed_issues', []))
        patterns_detected = len(results.get('issue_patterns', []))
        
        # Generate sections
        sections = {}
        for section_name, generator in self.report_templates.items():
            try:
                sections[section_name] = generator(results)
            except Exception as e:
                logger.error(f"Section generation failed for {section_name}: {e}")
                sections[section_name] = f"<p>Error generating {section_name}: {str(e)}</p>"
        
        # Build complete HTML report
        html_report = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enhanced Design QA Report - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>{self._get_comprehensive_css()}</style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="report-container">
                <header class="report-header">
                    <div class="header-content">
                        <h1>🎨 Enhanced Design QA Analysis Report</h1>
                        <div class="header-metrics">
                            <div class="metric-item">
                                <span class="metric-value {self._get_score_class(compliance_score)}">{compliance_score}%</span>
                                <span class="metric-label">Compliance Score</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">{total_issues}</span>
                                <span class="metric-label">Issues Found</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">{patterns_detected}</span>
                                <span class="metric-label">Patterns Detected</span>
                            </div>
                        </div>
                        <div class="analysis-info">
                            <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Figma Design:</strong> <a href="{results.get('analysis_metadata', {}).get('figma_url', '#')}" target="_blank">View Design</a></p>
                            <p><strong>Web Implementation:</strong> <a href="{results.get('analysis_metadata', {}).get('web_url', '#')}" target="_blank">View Page</a></p>
                        </div>
                    </div>
                </header>
                
                <nav class="report-nav">
                    <a href="#executive-summary" class="nav-link">📊 Executive Summary</a>
                    <a href="#technical-details" class="nav-link">🔧 Technical Details</a>
                    <a href="#implementation-guide" class="nav-link">📋 Implementation Guide</a>
                    <a href="#business-intelligence" class="nav-link">💼 Business Intelligence</a>
                    <a href="#trend-analysis" class="nav-link">📈 Trend Analysis</a>
                </nav>
                
                <main class="report-content">
                    <section id="executive-summary" class="report-section">
                        {sections.get('executive_summary', '')}
                    </section>
                    
                    <section id="technical-details" class="report-section">
                        {sections.get('technical_details', '')}
                    </section>
                    
                    <section id="implementation-guide" class="report-section">
                        {sections.get('implementation_guide', '')}
                    </section>
                    
                    <section id="business-intelligence" class="report-section">
                        {sections.get('business_intelligence', '')}
                    </section>
                    
                    <section id="trend-analysis" class="report-section">
                        {sections.get('trend_analysis', '')}
                    </section>
                </main>
                
                <footer class="report-footer">
                    <div class="footer-content">
                        <p>Generated by Enhanced Design QA System v2.0</p>
                        <p>Powered by AI Analysis Engine & Computer Vision</p>
                        <p>Report ID: {results.get('analysis_metadata', {}).get('analysis_id', 'N/A')}</p>
                    </div>
                </footer>
            </div>
            
            <script>{self._get_report_javascript()}</script>
        </body>
        </html>
        """
        
        return html_report
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary with key insights"""
        
        metrics = results.get('compliance_metrics', {})
        issues = results.get('processed_issues', [])
        patterns = results.get('issue_patterns', [])
        insights = results.get('intelligent_insights', [])
        
        # Calculate key statistics
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i.severity == Priority.CRITICAL])
        high_issues = len([i for i in issues if i.severity == Priority.HIGH])
        
        # Determine overall health
        overall_score = metrics.get('overall_score', 0)
        health_status = self._determine_health_status(overall_score, critical_issues)
        
        # Risk assessment
        risk_level = self._assess_risk_level(critical_issues, high_issues, patterns)
        
        summary_html = f"""
        <div class="executive-summary">
            <h2>📊 Executive Summary</h2>
            
            <div class="health-overview">
                <div class="health-indicator {health_status['class']}">
                    <div class="health-score">{overall_score}%</div>
                    <div class="health-label">{health_status['label']}</div>
                </div>
                
                <div class="health-details">
                    <div class="detail-item">
                        <span class="detail-value">{total_issues}</span>
                        <span class="detail-label">Total Issues</span>
                    </div>
                    <div class="detail-item critical">
                        <span class="detail-value">{critical_issues}</span>
                        <span class="detail-label">Critical</span>
                    </div>
                    <div class="detail-item high">
                        <span class="detail-value">{high_issues}</span>
                        <span class="detail-label">High Priority</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-value">{len(patterns)}</span>
                        <span class="detail-label">Patterns</span>
                    </div>
                </div>
            </div>
            
            <div class="risk-assessment">
                <h3>🎯 Risk Assessment</h3>
                <div class="risk-indicator {risk_level['class']}">
                    <div class="risk-level">{risk_level['level']}</div>
                    <div class="risk-description">{risk_level['description']}</div>
                </div>
            </div>
            
            <div class="key-insights">
                <h3>💡 Key Insights</h3>
                <div class="insights-grid">
        """
        
        # Add AI-generated insights
        for insight in insights[:4]:  # Top 4 insights
            insight_icon = {'pattern_detection': '🔍', 'quality_concern': '⚠️', 'positive_finding': '✨'}.get(insight.get('type'), '💡')
            summary_html += f"""
                    <div class="insight-card">
                        <div class="insight-header">
                            <span class="insight-icon">{insight_icon}</span>
                            <span class="insight-title">{insight.get('title', 'Insight')}</span>
                        </div>
                        <div class="insight-description">{insight.get('description', '')}</div>
                        <div class="insight-recommendation">
                            <strong>Recommendation:</strong> {insight.get('recommendation', '')}
                        </div>
                    </div>
            """
        
        summary_html += """
                </div>
            </div>
            
            <div class="immediate-actions">
                <h3>🚀 Immediate Action Items</h3>
                <div class="action-list">
        """
        
        # Generate immediate action items
        if critical_issues > 0:
            summary_html += f"""
                    <div class="action-item critical">
                        <strong>CRITICAL:</strong> Fix {critical_issues} critical issue{'s' if critical_issues != 1 else ''} immediately
                        <span class="timeline">Timeline: Today</span>
                    </div>
            """
        
        if patterns:
            high_frequency_patterns = [p for p in patterns if p.frequency >= 5]
            if high_frequency_patterns:
                summary_html += f"""
                    <div class="action-item high">
                        <strong>HIGH:</strong> Address {len(high_frequency_patterns)} systematic pattern{'s' if len(high_frequency_patterns) != 1 else ''}
                        <span class="timeline">Timeline: This Sprint</span>
                    </div>
                """
        
        if total_issues == 0:
            summary_html += """
                    <div class="action-item success">
                        <strong>SUCCESS:</strong> No issues detected - maintain current quality standards
                    </div>
            """
        
        summary_html += """
                </div>
            </div>
        </div>
        """
        
        return summary_html
    
    def _generate_technical_details(self, results: Dict[str, Any]) -> str:
        """Generate detailed technical analysis section"""
        
        issues = results.get('processed_issues', [])
        performance_metrics = results.get('performance_metrics', {})
        validation_results = results.get('validation_results', {})
        
        # Group issues by category for detailed breakdown
        issues_by_category = defaultdict(list)
        for issue in issues:
            issues_by_category[issue.category.value].append(issue)
        
        technical_html = f"""
        <div class="technical-details">
            <h2>🔧 Technical Analysis</h2>
            
            <div class="analysis-performance">
                <h3>⚡ Analysis Performance</h3>
                <div class="performance-grid">
                    <div class="perf-metric">
                        <span class="perf-value">{performance_metrics.get('total_analysis_duration', 0):.1f}s</span>
                        <span class="perf-label">Total Duration</span>
                    </div>
                    <div class="perf-metric">
                        <span class="perf-value">{results.get('web_analysis', {}).get('total_elements_analyzed', 'N/A')}</span>
                        <span class="perf-label">Elements Analyzed</span>
                    </div>
                    <div class="perf-metric">
                        <span class="perf-value">{len(results.get('web_analysis', {}).get('screenshots', {}))}</span>
                        <span class="perf-label">Viewports Tested</span>
                    </div>
                </div>
            </div>
            
            <div class="validation-summary">
                <h3>🔍 Validation Results</h3>
                <div class="validation-modules">
        """
        
        # Add validation module results
        validation_modules = [
            ('Accessibility', 'accessibility_score', 90),
            ('Typography', 'typography_score', 85),
            ('Responsive Design', 'responsive_score', 85),
            ('Performance', 'performance_score', 80),
            ('Brand Compliance', 'brand_score', 75)
        ]
        
        for module_name, score_key, threshold in validation_modules:
            score = validation_results.get(score_key, 100)
            status = 'pass' if score >= threshold else 'fail'
            
            technical_html += f"""
                    <div class="validation-module {status}">
                        <div class="module-header">
                            <span class="module-name">{module_name}</span>
                            <span class="module-score">{score}%</span>
                        </div>
                        <div class="module-threshold">Threshold: {threshold}%</div>
                    </div>
            """
        
        technical_html += """
                </div>
            </div>
            
            <div class="category-breakdown">
                <h3>📂 Issues by Category</h3>
        """
        
        # Add detailed category breakdowns
        for category, category_issues in issues_by_category.items():
            severity_counts = defaultdict(int)
            for issue in category_issues:
                severity_counts[issue.severity.label] += 1
            
            avg_confidence = sum(issue.confidence_score for issue in category_issues) / len(category_issues)
            
            technical_html += f"""
                <div class="category-section">
                    <div class="category-header">
                        <h4>{category}</h4>
                        <span class="issue-count">{len(category_issues)} issues</span>
                        <span class="confidence-score">Avg Confidence: {avg_confidence:.1%}</span>
                    </div>
                    
                    <div class="severity-breakdown">
            """
            
            for severity, count in severity_counts.items():
                if count > 0:
                    technical_html += f"""
                        <span class="severity-badge {severity.lower()}">{severity}: {count}</span>
                    """
            
            technical_html += """
                    </div>
                    
                    <div class="top-issues">
            """
            
            # Show top 3 issues per category
            top_issues = sorted(category_issues, key=lambda x: x.severity.weight, reverse=True)[:3]
            for issue in top_issues:
                technical_html += f"""
                        <div class="issue-detail {issue.severity.label.lower()}">
                            <div class="issue-header">
                                <span class="issue-severity">{issue.severity.label}</span>
                                <span class="issue-confidence">{issue.confidence_score:.0%}</span>
                            </div>
                            <div class="issue-description">{issue.description}</div>
                            <div class="issue-element"><code>{issue.element_selector or 'N/A'}</code></div>
                            <div class="issue-fix">{issue.suggested_fix}</div>
                        </div>
                """
            
            technical_html += """
                    </div>
                </div>
            """
        
        technical_html += """
            </div>
        </div>
        """
        
        return technical_html
    
    def _generate_implementation_guide(self, results: Dict[str, Any]) -> str:
        """Generate actionable implementation guide"""
        
        recommendations = results.get('systematic_recommendations', [])
        patterns = results.get('issue_patterns', [])
        next_actions = results.get('next_actions', [])
        
        guide_html = f"""
        <div class="implementation-guide">
            <h2>📋 Implementation Guide</h2>
            
            <div class="implementation-overview">
                <p>This guide provides prioritized, actionable steps to resolve identified design issues 
                and implement systematic improvements.</p>
            </div>
        """
        
        # Priority action items
        if next_actions:
            guide_html += """
            <div class="priority-actions">
                <h3>🚀 Priority Action Items</h3>
                <div class="action-timeline">
            """
            
            for action in next_actions[:5]:  # Top 5 actions
                priority_class = f"priority-{action.get('priority', 3)}"
                
                guide_html += f"""
                    <div class="action-item {priority_class}">
                        <div class="action-header">
                            <span class="action-title">{action.get('title', action.get('action', 'Action Item'))}</span>
                            <span class="action-timeline">{action.get('timeline', 'TBD')}</span>
                        </div>
                        <div class="action-description">{action.get('description', '')}</div>
                        <div class="action-meta">
                            <span class="effort">Effort: {action.get('estimated_effort', 'TBD')}</span>
                            <span class="owner">Owner: {action.get('owner', 'TBD')}</span>
                        </div>
                    </div>
                """
            
            guide_html += """
                </div>
            </div>
            """
        
        # Systematic fixes for patterns
        if patterns:
            guide_html += """
            <div class="systematic-fixes">
                <h3>🔄 Systematic Pattern Fixes</h3>
                <div class="pattern-fixes">
            """
            
            for pattern in patterns:
                if pattern.frequency >= 3:
                    guide_html += f"""
                        <div class="pattern-fix">
                            <div class="pattern-header">
                                <h4>{pattern.issue_type}</h4>
                                <span class="pattern-frequency">{pattern.frequency} occurrences</span>
                                <span class="pattern-confidence">{pattern.confidence:.0%} confidence</span>
                            </div>
                            
                            <div class="pattern-analysis">
                                <div class="root-cause">
                                    <strong>Root Cause:</strong> {pattern.root_cause_hypothesis}
                                </div>
                                <div class="systematic-fix">
                                    <strong>Systematic Fix:</strong> {pattern.suggested_systematic_fix}
                                </div>
                                <div class="business-impact">
                                    <strong>Business Impact:</strong> {pattern.business_impact}
                                </div>
                            </div>
                            
                            <div class="affected-elements">
                                <strong>Affected Elements:</strong>
                                <ul>
                    """
                    
                    for element in pattern.elements_affected[:5]:
                        guide_html += f"<li><code>{element}</code></li>"
                    
                    if len(pattern.elements_affected) > 5:
                        guide_html += f"<li>... and {len(pattern.elements_affected) - 5} more</li>"
                    
                    guide_html += """
                                </ul>
                            </div>
                        </div>
                    """
            
            guide_html += """
                </div>
            </div>
            """
        
        # Implementation checklist
        guide_html += """
        <div class="implementation-checklist">
            <h3>✅ Implementation Checklist</h3>
            <div class="checklist-items">
                <div class="checklist-item">
                    <input type="checkbox" id="review-critical">
                    <label for="review-critical">Review and prioritize critical issues</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="assign-ownership">
                    <label for="assign-ownership">Assign ownership for each issue category</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="create-tickets">
                    <label for="create-tickets">Create Jira tickets for tracking</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="plan-systematic">
                    <label for="plan-systematic">Plan systematic fixes for recurring patterns</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="setup-monitoring">
                    <label for="setup-monitoring">Set up monitoring for future QA cycles</label>
                </div>
            </div>
        </div>
        """
        
        guide_html += """
        </div>
        """
        
        return guide_html
    
    def _generate_business_intelligence(self, results: Dict[str, Any]) -> str:
        """Generate business intelligence section with ROI analysis"""
        
        issues = results.get('processed_issues', [])
        patterns = results.get('issue_patterns', [])
        compliance_metrics = results.get('compliance_metrics', {})
        
        # Calculate business impact metrics
        impact_analysis = self._calculate_business_impact(issues, patterns)
        
        bi_html = f"""
        <div class="business-intelligence">
            <h2>💼 Business Intelligence</h2>
            
            <div class="impact-overview">
                <h3>📈 Business Impact Analysis</h3>
                <div class="impact-metrics">
                    <div class="impact-metric">
                        <div class="metric-value">${impact_analysis['estimated_cost_impact']:,.0f}</div>
                        <div class="metric-label">Estimated Cost Impact</div>
                        <div class="metric-detail">Lost conversion potential</div>
                    </div>
                    <div class="impact-metric">
                        <div class="metric-value">{impact_analysis['user_experience_impact']:.1%}</div>
                        <div class="metric-label">UX Impact Score</div>
                        <div class="metric-detail">User experience degradation</div>
                    </div>
                    <div class="impact-metric">
                        <div class="metric-value">{impact_analysis['brand_risk_score']}</div>
                        <div class="metric-label">Brand Risk Level</div>
                        <div class="metric-detail">Reputation impact assessment</div>
                    </div>
                </div>
            </div>
            
            <div class="roi-analysis">
                <h3>💰 ROI Analysis for Fixes</h3>
                <div class="roi-breakdown">
                    <div class="roi-item">
                        <div class="roi-category">Critical Issues Fix</div>
                        <div class="roi-investment">Investment: {impact_analysis['critical_fix_cost']}</div>
                        <div class="roi-return">Expected Return: {impact_analysis['critical_fix_roi']}</div>
                        <div class="roi-payback">Payback Period: {impact_analysis['critical_payback']}</div>
                    </div>
                    
                    <div class="roi-item">
                        <div class="roi-category">Systematic Pattern Fixes</div>
                        <div class="roi-investment">Investment: {impact_analysis['pattern_fix_cost']}</div>
                        <div class="roi-return">Expected Return: {impact_analysis['pattern_fix_roi']}</div>
                        <div class="roi-payback">Payback Period: {impact_analysis['pattern_payback']}</div>
                    </div>
                </div>
            </div>
            
            <div class="stakeholder-impact">
                <h3>👥 Stakeholder Impact Matrix</h3>
                <div class="stakeholder-grid">
        """
        
        # Stakeholder impact analysis
        stakeholders = [
            ('End Users', impact_analysis['user_impact'], 'User experience and satisfaction'),
            ('Development Team', impact_analysis['dev_impact'], 'Technical debt and maintenance'),
            ('Design Team', impact_analysis['design_impact'], 'Design system consistency'),
            ('Business', impact_analysis['business_impact'], 'Conversion and brand perception'),
            ('QA Team', impact_analysis['qa_impact'], 'Testing efficiency and coverage')
        ]
        
        for stakeholder, impact_level, description in stakeholders:
            impact_class = impact_level.lower().replace(' ', '-')
            
            bi_html += f"""
                    <div class="stakeholder-item {impact_class}">
                        <div class="stakeholder-name">{stakeholder}</div>
                        <div class="stakeholder-impact">{impact_level}</div>
                        <div class="stakeholder-description">{description}</div>
                    </div>
            """
        
        bi_html += """
                </div>
            </div>
        </div>
        """
        
        return bi_html
    
    def _calculate_business_impact(self, issues: List[EnhancedDesignIssue], 
                                 patterns: List[IssuePattern]) -> Dict[str, Any]:
        """Calculate comprehensive business impact metrics"""
        
        # Estimate cost impact based on issue severity and frequency
        critical_count = len([i for i in issues if i.severity == Priority.CRITICAL])
        high_count = len([i for i in issues if i.severity == Priority.HIGH])
        
        # Simplified cost impact calculation (would be more sophisticated in real implementation)
        estimated_cost = (critical_count * 5000) + (high_count * 2000) + (len(patterns) * 3000)
        
        # UX impact score based on accessibility and usability issues
        ux_affecting_categories = [IssueCategory.ACCESSIBILITY, IssueCategory.RESPONSIVE_DESIGN, IssueCategory.UI_ELEMENTS]
        ux_issues = [i for i in issues if i.category in ux_affecting_categories]
        ux_impact = min(1.0, len(ux_issues) * 0.1)
        
        # Brand risk assessment
        brand_issues = [i for i in issues if i.category == IssueCategory.BRAND_CONSISTENCY]
        visual_issues = [i for i in issues if i.category == IssueCategory.VISUAL_DESIGN]
        brand_risk = "High" if len(brand_issues) > 5 else "Medium" if len(visual_issues) > 10 else "Low"
        
        return {
            'estimated_cost_impact': estimated_cost,
            'user_experience_impact': ux_impact,
            'brand_risk_score': brand_risk,
            'critical_fix_cost': '$5,000 - $15,000',
            'critical_fix_roi': '300% - 500%',
            'critical_payback': '1-2 weeks',
            'pattern_fix_cost': '$10,000 - $25,000',
            'pattern_fix_roi': '200% - 400%',
            'pattern_payback': '4-8 weeks',
            'user_impact': 'High' if ux_impact > 0.5 else 'Medium' if ux_impact > 0.2 else 'Low',
            'dev_impact': 'High' if len(patterns) > 3 else 'Medium',
            'design_impact': 'High' if len(brand_issues) > 3 else 'Medium',
            'business_impact': 'High' if critical_count > 0 else 'Medium',
            'qa_impact': 'Medium'
        }
    
    def _determine_health_status(self, score: float, critical_issues: int) -> Dict[str, str]:
        """Determine overall health status based on score and critical issues"""
        
        if critical_issues > 0:
            return {'label': 'Unhealthy', 'class': 'unhealthy'}
        elif score >= 85:
            return {'label': 'Healthy', 'class': 'healthy'}
        elif score >= 70:
            return {'label': 'At Risk', 'class': 'at-risk'}
        else:
            return {'label': 'Unhealthy', 'class': 'unhealthy'}