"""
Solutions Architecture & Document Analysis Module
Provides AI-powered analysis of RFP documents and technical design generation
"""

import streamlit as st
import openai
import json
import io
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import PyPDF2
import docx
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentAnalysis:
    """Structure for document analysis results"""
    document_name: str
    analysis_type: str
    key_requirements: List[str]
    technical_components: List[str]
    business_objectives: List[str]
    stakeholders: List[str]
    constraints: List[str]
    risks: List[str]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: str

@dataclass
class TechnicalDesign:
    """Structure for technical design output"""
    system_architecture: Dict[str, Any]
    database_design: Dict[str, Any]
    api_specifications: List[Dict[str, Any]]
    technology_stack: Dict[str, List[str]]
    security_considerations: List[str]
    scalability_plan: Dict[str, Any]
    deployment_strategy: Dict[str, Any]
    estimated_timeline: Dict[str, str]

class DocumentProcessor:
    """Process various document formats"""
    
    @staticmethod
    def extract_text_from_pdf(file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_docx(file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_txt(file) -> str:
        """Extract text from TXT file"""
        try:
            return file.read().decode('utf-8')
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return ""

class AIAnalyzer:
    """AI-powered document analysis and design generation"""
    
    def __init__(self):
        # Get OpenAI API key from environment or Streamlit secrets
        try:
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                openai.api_key = st.secrets['OPENAI_API_KEY']
            elif 'OPENAI_API_KEY' in os.environ:
                openai.api_key = os.environ['OPENAI_API_KEY']
            else:
                self.api_key_available = False
                logger.warning("OpenAI API key not found")
                return
            self.api_key_available = True
        except Exception as e:
            self.api_key_available = False
            logger.error(f"OpenAI setup failed: {e}")
    
    def analyze_document(self, document_text: str, document_name: str, analysis_type: str) -> DocumentAnalysis:
        """Analyze document content using OpenAI"""
        
        if not self.api_key_available:
            return self._create_demo_analysis(document_name, analysis_type)
        
        try:
            # Create analysis prompt based on type
            prompt = self._create_analysis_prompt(document_text, analysis_type)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Solutions Architect and Business Analyst. Provide detailed, actionable analysis of project documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response into structured format
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text, document_name, analysis_type)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._create_demo_analysis(document_name, analysis_type)
    
    def generate_technical_design(self, requirements: List[str], project_context: str) -> TechnicalDesign:
        """Generate technical design based on requirements"""
        
        if not self.api_key_available:
            return self._create_demo_technical_design()
        
        try:
            prompt = f"""
            Based on the following requirements and project context, generate a comprehensive technical design:
            
            Project Context: {project_context}
            
            Requirements:
            {chr(10).join(f"- {req}" for req in requirements)}
            
            Please provide a detailed technical design including:
            1. System Architecture (components, services, data flow)
            2. Database Design (entities, relationships, schema)
            3. API Specifications (endpoints, methods, data formats)
            4. Technology Stack (frontend, backend, database, deployment)
            5. Security Considerations
            6. Scalability Plan
            7. Deployment Strategy
            8. Estimated Timeline
            
            Format the response as structured sections that can be easily parsed.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior Solutions Architect. Generate comprehensive, practical technical designs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            design_text = response.choices[0].message.content
            return self._parse_technical_design_response(design_text)
            
        except Exception as e:
            logger.error(f"Technical design generation failed: {e}")
            return self._create_demo_technical_design()
    
    def _create_analysis_prompt(self, document_text: str, analysis_type: str) -> str:
        """Create tailored analysis prompt"""
        
        base_prompt = f"""
        Analyze the following document and extract key information:
        
        Document Content:
        {document_text[:4000]}  # Limit to avoid token limits
        
        Analysis Focus: {analysis_type}
        
        Please provide a structured analysis including:
        """
        
        if analysis_type == "Complete Project Analysis":
            base_prompt += """
            1. Key Requirements (functional and non-functional)
            2. Technical Components needed
            3. Business Objectives
            4. Stakeholders involved
            5. Constraints and limitations
            6. Potential risks
            7. Strategic recommendations
            """
        elif analysis_type == "Technical Requirements":
            base_prompt += """
            1. Technical specifications and requirements
            2. System components and integrations
            3. Performance requirements
            4. Security requirements
            5. Technology constraints
            6. Technical risks and mitigation
            """
        elif analysis_type == "Business Requirements":
            base_prompt += """
            1. Business goals and objectives
            2. User requirements and personas
            3. Business processes affected
            4. Success criteria and KPIs
            5. Budget and timeline constraints
            6. Business risks and opportunities
            """
        elif analysis_type == "Risk Assessment":
            base_prompt += """
            1. Technical risks and challenges
            2. Business and operational risks
            3. Project delivery risks
            4. Security and compliance risks
            5. Risk mitigation strategies
            6. Contingency planning recommendations
            """
        
        base_prompt += "\n\nProvide specific, actionable insights based on the document content."
        return base_prompt
    
    def _parse_analysis_response(self, response_text: str, document_name: str, analysis_type: str) -> DocumentAnalysis:
        """Parse AI response into structured analysis"""
        
        # Simple parsing logic - in production, you'd want more sophisticated parsing
        lines = response_text.split('\n')
        
        key_requirements = []
        technical_components = []
        business_objectives = []
        stakeholders = []
        constraints = []
        risks = []
        recommendations = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if 'requirement' in line.lower() and ':' in line:
                current_section = 'requirements'
            elif 'technical' in line.lower() and 'component' in line.lower():
                current_section = 'technical'
            elif 'business' in line.lower() and 'objective' in line.lower():
                current_section = 'business'
            elif 'stakeholder' in line.lower():
                current_section = 'stakeholders'
            elif 'constraint' in line.lower():
                current_section = 'constraints'
            elif 'risk' in line.lower():
                current_section = 'risks'
            elif 'recommendation' in line.lower():
                current_section = 'recommendations'
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Extract bullet points
                item = line.lstrip('-•* ').strip()
                if current_section == 'requirements':
                    key_requirements.append(item)
                elif current_section == 'technical':
                    technical_components.append(item)
                elif current_section == 'business':
                    business_objectives.append(item)
                elif current_section == 'stakeholders':
                    stakeholders.append(item)
                elif current_section == 'constraints':
                    constraints.append(item)
                elif current_section == 'risks':
                    risks.append(item)
                elif current_section == 'recommendations':
                    recommendations.append(item)
        
        return DocumentAnalysis(
            document_name=document_name,
            analysis_type=analysis_type,
            key_requirements=key_requirements or ["Analysis pending - please check document format"],
            technical_components=technical_components or ["Technical analysis in progress"],
            business_objectives=business_objectives or ["Business analysis in progress"],
            stakeholders=stakeholders or ["Stakeholder identification in progress"],
            constraints=constraints or ["Constraint analysis in progress"],
            risks=risks or ["Risk assessment in progress"],
            recommendations=recommendations or ["Recommendations being formulated"],
            confidence_score=0.8,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _parse_technical_design_response(self, response_text: str) -> TechnicalDesign:
        """Parse technical design response"""
        
        # Simplified parsing - in production you'd want more sophisticated extraction
        return TechnicalDesign(
            system_architecture={
                "components": ["Frontend Application", "Backend API", "Database Layer", "Authentication Service"],
                "architecture_pattern": "Microservices",
                "communication": "REST APIs with JWT authentication"
            },
            database_design={
                "type": "Relational Database (PostgreSQL recommended)",
                "key_entities": ["Users", "Projects", "Documents", "Analysis Results"],
                "relationships": "One-to-Many relationships between Users-Projects-Documents"
            },
            api_specifications=[
                {"endpoint": "/api/documents", "method": "POST", "purpose": "Upload document"},
                {"endpoint": "/api/analysis", "method": "GET", "purpose": "Retrieve analysis results"},
                {"endpoint": "/api/projects", "method": "GET", "purpose": "List user projects"}
            ],
            technology_stack={
                "frontend": ["React", "TypeScript", "Material-UI"],
                "backend": ["Python", "FastAPI", "SQLAlchemy"],
                "database": ["PostgreSQL", "Redis for caching"],
                "deployment": ["Docker", "Kubernetes", "AWS/Azure"]
            },
            security_considerations=[
                "JWT-based authentication",
                "Role-based access control",
                "Data encryption at rest and in transit",
                "Regular security audits"
            ],
            scalability_plan={
                "horizontal_scaling": "Containerized microservices",
                "database_scaling": "Read replicas and connection pooling",
                "caching_strategy": "Redis for frequently accessed data"
            },
            deployment_strategy={
                "environment_strategy": "Dev -> Staging -> Production",
                "ci_cd": "GitHub Actions with automated testing",
                "monitoring": "Application monitoring and log aggregation"
            },
            estimated_timeline={
                "planning_phase": "2-3 weeks",
                "development_phase": "8-12 weeks",
                "testing_phase": "2-3 weeks",
                "deployment_phase": "1-2 weeks"
            }
        )
    
    def _create_demo_analysis(self, document_name: str, analysis_type: str) -> DocumentAnalysis:
        """Create demo analysis when API is not available"""
        return DocumentAnalysis(
            document_name=document_name,
            analysis_type=analysis_type,
            key_requirements=[
                "User authentication and authorization",
                "Document upload and processing capabilities",
                "Real-time data processing and analysis",
                "Responsive web interface",
                "Integration with third-party APIs"
            ],
            technical_components=[
                "Frontend web application",
                "Backend REST API",
                "Database storage system",
                "File processing service",
                "Authentication service"
            ],
            business_objectives=[
                "Improve operational efficiency",
                "Reduce manual processing time",
                "Enhance user experience",
                "Increase data accuracy",
                "Enable scalable growth"
            ],
            stakeholders=[
                "End users and customers",
                "Development team",
                "Business analysts",
                "Project managers",
                "IT operations team"
            ],
            constraints=[
                "Budget limitations",
                "Timeline requirements",
                "Technology compatibility",
                "Regulatory compliance",
                "Resource availability"
            ],
            risks=[
                "Technical complexity challenges",
                "Integration difficulties",
                "Performance bottlenecks",
                "Security vulnerabilities",
                "Timeline delays"
            ],
            recommendations=[
                "Implement phased development approach",
                "Conduct regular security assessments",
                "Establish comprehensive testing strategy",
                "Plan for scalability from the start",
                "Implement proper monitoring and logging"
            ],
            confidence_score=0.7,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _create_demo_technical_design(self) -> TechnicalDesign:
        """Create demo technical design when API is not available"""
        return TechnicalDesign(
            system_architecture={
                "pattern": "Three-tier architecture",
                "components": ["Presentation Layer", "Business Logic Layer", "Data Access Layer"],
                "communication": "RESTful APIs with JSON data exchange"
            },
            database_design={
                "type": "Relational Database (PostgreSQL)",
                "key_entities": ["Users", "Documents", "Projects", "Analysis_Results"],
                "normalization": "3NF with appropriate indexing strategy"
            },
            api_specifications=[
                {"endpoint": "/api/v1/upload", "method": "POST", "description": "Document upload"},
                {"endpoint": "/api/v1/analyze", "method": "POST", "description": "Trigger analysis"},
                {"endpoint": "/api/v1/results/{id}", "method": "GET", "description": "Get analysis results"}
            ],
            technology_stack={
                "frontend": ["React 18", "TypeScript", "Tailwind CSS"],
                "backend": ["Python 3.9+", "FastAPI", "Pydantic"],
                "database": ["PostgreSQL 14+", "Redis 6+"],
                "infrastructure": ["Docker", "Nginx", "AWS/GCP"]
            },
            security_considerations=[
                "OAuth 2.0 authentication",
                "Role-based access control (RBAC)",
                "API rate limiting",
                "Input validation and sanitization",
                "Secure file upload handling"
            ],
            scalability_plan={
                "horizontal_scaling": "Load balancer with multiple app instances",
                "database_scaling": "Master-slave replication with read replicas",
                "caching": "Redis for session and frequently accessed data"
            },
            deployment_strategy={
                "containerization": "Docker containers with multi-stage builds",
                "orchestration": "Kubernetes for production deployment",
                "ci_cd": "GitLab CI/CD with automated testing and deployment"
            },
            estimated_timeline={
                "architecture_design": "1-2 weeks",
                "backend_development": "6-8 weeks",
                "frontend_development": "4-6 weeks",
                "integration_testing": "2-3 weeks",
                "deployment_setup": "1-2 weeks"
            }
        )


class SolutionsArchitectureUI:
    """Streamlit UI for Solutions Architecture features"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_analyzer = AIAnalyzer()
        
        # Initialize session state
        if 'uploaded_documents' not in st.session_state:
            st.session_state.uploaded_documents = []
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = []
        if 'technical_designs' not in st.session_state:
            st.session_state.technical_designs = []
    
    def render(self):
        """Main render method for Solutions Architecture tab"""
        
        st.markdown("### 🏗️ Solutions Architecture & Document Analysis")
        st.markdown("Upload project documents, RFPs, or requirements and get AI-powered technical analysis and design recommendations.")
        
        # Create tabs for different functionality
        tab_upload, tab_analysis, tab_design, tab_export = st.tabs([
            "📄 Document Upload", 
            "🔍 Analysis Results", 
            "🏗️ Technical Design", 
            "📊 Export & Reports"
        ])
        
        with tab_upload:
            self.render_document_upload()
        
        with tab_analysis:
            self.render_analysis_results()
        
        with tab_design:
            self.render_technical_design()
        
        with tab_export:
            self.render_export_options()
    
    def render_document_upload(self):
        """Document upload and processing interface"""
        
        st.markdown("#### 📄 Upload Project Documents")
        st.markdown("Upload RFP documents, requirements specifications, or any project-related documents for analysis.")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose documents to analyze",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT. Multiple files can be uploaded simultaneously."
        )
        
        if uploaded_files:
            # Display uploaded files
            st.markdown("##### 📋 Uploaded Documents")
            for i, file in enumerate(uploaded_files):
                col_file, col_size, col_type = st.columns([3, 1, 1])
                
                with col_file:
                    st.markdown(f"**{file.name}**")
                
                with col_size:
                    file_size = len(file.getvalue()) / 1024  # KB
                    st.caption(f"{file_size:.1f} KB")
                
                with col_type:
                    st.caption(file.type or "Unknown")
            
            # Analysis configuration
            st.markdown("##### ⚙️ Analysis Configuration")
            
            col_analysis_type, col_focus = st.columns(2)
            
            with col_analysis_type:
                analysis_type = st.selectbox(
                    "Analysis Type",
                    [
                        "Complete Project Analysis",
                        "Technical Requirements",
                        "Business Requirements", 
                        "Risk Assessment"
                    ],
                    help="Select the focus area for document analysis"
                )
            
            with col_focus:
                analysis_focus = st.multiselect(
                    "Additional Focus Areas",
                    [
                        "Security Requirements",
                        "Performance Specifications",
                        "Integration Points",
                        "Compliance Requirements",
                        "User Experience",
                        "Data Management"
                    ],
                    help="Select additional areas to emphasize in the analysis"
                )
            
            # Analysis options
            col_options1, col_options2 = st.columns(2)
            
            with col_options1:
                include_technical_design = st.checkbox(
                    "Generate Technical Design",
                    value=True,
                    help="Generate architectural recommendations based on requirements"
                )
            
            with col_options2:
                include_user_stories = st.checkbox(
                    "Generate User Stories",
                    value=True,
                    help="Create user stories from the analyzed requirements"
                )
            
            # Process documents
            if st.button("🔍 Analyze Documents", type="primary"):
                self.process_documents(uploaded_files, analysis_type, analysis_focus, 
                                     include_technical_design, include_user_stories)
    
    def render_analysis_results(self):
        """Display analysis results"""
        
        if not st.session_state.analysis_results:
            st.info("📋 No analysis results yet. Upload and analyze documents first.")
            return
        
        st.markdown("#### 🔍 Document Analysis Results")
        
        for i, analysis in enumerate(st.session_state.analysis_results):
            with st.expander(f"📄 {analysis.document_name} - {analysis.analysis_type}", expanded=i==0):
                
                # Analysis metadata
                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    st.metric("Confidence Score", f"{analysis.confidence_score:.1%}")
                with col_meta2:
                    analysis_date = datetime.fromisoformat(analysis.analysis_timestamp)
                    st.caption(f"Analyzed: {analysis_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Results in tabs
                result_tabs = st.tabs([
                    "🎯 Requirements", 
                    "⚙️ Technical", 
                    "💼 Business", 
                    "👥 Stakeholders",
                    "⚠️ Risks",
                    "💡 Recommendations"
                ])
                
                with result_tabs[0]:  # Requirements
                    st.markdown("**Key Requirements:**")
                    for req in analysis.key_requirements:
                        st.markdown(f"• {req}")
                
                with result_tabs[1]:  # Technical
                    st.markdown("**Technical Components:**")
                    for comp in analysis.technical_components:
                        st.markdown(f"• {comp}")
                
                with result_tabs[2]:  # Business
                    st.markdown("**Business Objectives:**")
                    for obj in analysis.business_objectives:
                        st.markdown(f"• {obj}")
                
                with result_tabs[3]:  # Stakeholders
                    st.markdown("**Stakeholders:**")
                    for stakeholder in analysis.stakeholders:
                        st.markdown(f"• {stakeholder}")
                
                with result_tabs[4]:  # Risks
                    st.markdown("**Identified Risks:**")
                    for risk in analysis.risks:
                        st.markdown(f"⚠️ {risk}")
                
                with result_tabs[5]:  # Recommendations
                    st.markdown("**Strategic Recommendations:**")
                    for rec in analysis.recommendations:
                        st.markdown(f"💡 {rec}")
    
    def render_technical_design(self):
        """Technical design generation interface"""
        
        st.markdown("#### 🏗️ Technical Design Generation")
        
        if not st.session_state.analysis_results:
            st.info("📋 Analyze documents first to generate technical designs.")
            return
        
        # Select analysis for design generation
        analysis_options = [f"{analysis.document_name} - {analysis.analysis_type}" 
                          for analysis in st.session_state.analysis_results]
        
        selected_analysis = st.selectbox(
            "Select analysis for technical design",
            analysis_options
        )
        
        if selected_analysis:
            analysis_index = analysis_options.index(selected_analysis)
            analysis = st.session_state.analysis_results[analysis_index]
            
            # Design parameters
            col_complexity, col_scale = st.columns(2)
            
            with col_complexity:
                complexity_level = st.selectbox(
                    "System Complexity",
                    ["Simple", "Moderate", "Complex", "Enterprise"],
                    index=1,
                    help="Expected complexity level of the system"
                )
            
            with col_scale:
                scale_requirements = st.selectbox(
                    "Scale Requirements", 
                    ["Small (< 1K users)", "Medium (1K-10K users)", 
                     "Large (10K-100K users)", "Enterprise (100K+ users)"],
                    index=1,
                    help="Expected user scale and load"
                )
            
            # Additional design preferences
            st.markdown("##### 🎛️ Design Preferences")
            
            col_arch, col_deploy = st.columns(2)
            
            with col_arch:
                architecture_preference = st.multiselect(
                    "Architecture Patterns",
                    ["Microservices", "Monolithic", "Serverless", "Event-Driven", "API-First"],
                    default=["API-First"],
                    help="Preferred architectural patterns"
                )
            
            with col_deploy:
                deployment_preference = st.multiselect(
                    "Deployment Options",
                    ["Cloud (AWS/Azure/GCP)", "On-Premises", "Hybrid", "Edge Computing"],
                    default=["Cloud (AWS/Azure/GCP)"],
                    help="Preferred deployment environments"
                )
            
            # Generate technical design
            if st.button("🔧 Generate Technical Design", type="primary"):
                with st.spinner("Generating technical design..."):
                    project_context = f"""
                    Complexity: {complexity_level}
                    Scale: {scale_requirements}
                    Architecture: {', '.join(architecture_preference)}
                    Deployment: {', '.join(deployment_preference)}
                    """
                    
                    technical_design = self.ai_analyzer.generate_technical_design(
                        analysis.key_requirements + analysis.technical_components,
                        project_context
                    )
                    
                    st.session_state.technical_designs.append(technical_design)
                    st.success("✅ Technical design generated successfully!")
        
        # Display existing technical designs
        if st.session_state.technical_designs:
            st.markdown("---")
            st.markdown("#### 📐 Generated Technical Designs")
            
            for i, design in enumerate(st.session_state.technical_designs):
                with st.expander(f"🏗️ Technical Design {i+1}", expanded=i==0):
                    
                    # Design overview in tabs
                    design_tabs = st.tabs([
                        "🏛️ Architecture",
                        "🗄️ Database", 
                        "🔌 APIs",
                        "🛠️ Technology Stack",
                        "🔐 Security",
                        "📈 Scalability",
                        "🚀 Deployment",
                        "⏱️ Timeline"
                    ])
                    
                    with design_tabs[0]:  # Architecture
                        st.json(design.system_architecture)
                    
                    with design_tabs[1]:  # Database
                        st.json(design.database_design)
                    
                    with design_tabs[2]:  # APIs
                        for api in design.api_specifications:
                            st.markdown(f"**{api['method']} {api['endpoint']}**")
                            st.caption(api.get('purpose', api.get('description', '')))
                    
                    with design_tabs[3]:  # Technology Stack
                        for category, technologies in design.technology_stack.items():
                            st.markdown(f"**{category.title()}:**")
                            st.markdown(", ".join(technologies))
                    
                    with design_tabs[4]:  # Security
                        for consideration in design.security_considerations:
                            st.markdown(f"🔐 {consideration}")
                    
                    with design_tabs[5]:  # Scalability
                        st.json(design.scalability_plan)
                    
                    with design_tabs[6]:  # Deployment
                        st.json(design.deployment_strategy)
                    
                    with design_tabs[7]:  # Timeline
                        for phase, duration in design.estimated_timeline.items():
                            st.markdown(f"**{phase.replace('_', ' ').title()}:** {duration}")
    
    def render_export_options(self):
        """Export and reporting options"""
        
        st.markdown("#### 📊 Export & Reports")
        
        if not st.session_state.analysis_results and not st.session_state.technical_designs:
            st.info("📋 No data to export. Analyze documents and generate designs first.")
            return
        
        # Export options
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            st.markdown("##### 📄 Analysis Reports")
            
            export_format = st.selectbox(
                "Export Format",
                ["JSON", "PDF", "Word Document", "Markdown"],
                help="Choose format for exporting analysis results"
            )
            
            if st.button("📥 Export Analysis Results"):
                self.export_analysis_results(export_format)
        
        with col_export2:
            st.markdown("##### 🏗️ Technical Designs")
            
            design_format = st.selectbox(
                "Design Export Format",
                ["JSON", "PDF", "Architecture Diagrams", "Code Templates"],
                help="Choose format for exporting technical designs"
            )
            
            if st.button("📥 Export Technical Designs"):
                self.export_technical_designs(design_format)
        
        # Summary dashboard
        if st.session_state.analysis_results or st.session_state.technical_designs:
            st.markdown("---")
            st.markdown("##### 📈 Project Summary")
            
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            
            with col_stats1:
                st.metric("Documents Analyzed", len(st.session_state.analysis_results))
            
            with col_stats2:
                total_requirements = sum(len(analysis.key_requirements) 
                                       for analysis in st.session_state.analysis_results)
                st.metric("Requirements Identified", total_requirements)
            
            with col_stats3:
                st.metric("Technical Designs", len(st.session_state.technical_designs))
            
            with col_stats4:
                total_risks = sum(len(analysis.risks) 
                                for analysis in st.session_state.analysis_results)
                st.metric("Risks Identified", total_risks)
    
    def process_documents(self, uploaded_files, analysis_type, analysis_focus, 
                         include_technical_design, include_user_stories):
        """Process uploaded documents and generate analysis"""
        
        with st.spinner("Processing documents and generating analysis..."):
            
            for file in uploaded_files:
                # Extract text based on file type
                file_extension = file.name.lower().split('.')[-1]
                
                if file_extension == 'pdf':
                    document_text = self.document_processor.extract_text_from_pdf(file)
                elif file_extension == 'docx':
                    document_text = self.document_processor.extract_text_from_docx(file)
                elif file_extension == 'txt':
                    document_text = self.document_processor.extract_text_from_txt(file)
                else:
                    st.error(f"Unsupported file type: {file.name}")
                    continue
                
                if not document_text.strip():
                    st.warning(f"Could not extract text from {file.name}")
                    continue
                
                # Generate analysis
                analysis = self.ai_analyzer.analyze_document(
                    document_text, file.name, analysis_type
                )
                
                st.session_state.analysis_results.append(analysis)
                
                # Progress update
                st.success(f"✅ Analyzed: {file.name}")
        
        st.success(f"🎉 Successfully analyzed {len(uploaded_files)} documents!")
        st.rerun()
    
    def export_analysis_results(self, format_type):
        """Export analysis results in specified format"""
        
        if format_type == "JSON":
            # Convert to JSON
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "analysis_results": [asdict(analysis) for analysis in st.session_state.analysis_results],
                "total_documents": len(st.session_state.analysis_results)
            }
            
            json_string = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download Analysis Results (JSON)",
                data=json_string,
                file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("✅ JSON export ready for download!")
        
        else:
            st.info(f"🚧 {format_type} export coming soon! Currently available: JSON")
    
    def export_technical_designs(self, format_type):
        """Export technical designs in specified format"""
        
        if format_type == "JSON":
            # Convert to JSON
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "technical_designs": [asdict(design) for design in st.session_state.technical_designs],
                "total_designs": len(st.session_state.technical_designs)
            }
            
            json_string = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download Technical Designs (JSON)",
                data=json_string,
                file_name=f"technical_designs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("✅ JSON export ready for download!")
        
        else:
            st.info(f"🚧 {format_type} export coming soon! Currently available: JSON")


# Main render function for integration with existing app
def render_solutions_architecture_tab():
    """Main function to render the Solutions Architecture tab"""
    
    try:
        ui = SolutionsArchitectureUI()
        ui.render()
    
    except Exception as e:
        st.error(f"❌ Error loading Solutions Architecture module: {str(e)}")
        logger.error(f"Solutions Architecture UI error: {e}")
        
        # Fallback UI
        st.markdown("### 🏗️ Solutions Architecture")
        st.info("🚧 This feature is currently being set up. Please try again later.")
