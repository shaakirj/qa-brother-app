"""
User Story Generation Module
Business Analyst functionality for converting requirements into user stories
"""

import streamlit as st
import openai
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserStory:
    """Structure for individual user stories"""
    id: str
    title: str
    story: str  # As a [user], I want [goal] so that [benefit]
    acceptance_criteria: List[str]
    priority: str  # High, Medium, Low
    story_points: int
    epic: str
    tags: List[str]
    business_value: str
    technical_notes: str
    created_timestamp: str

@dataclass
class Epic:
    """Structure for epics containing multiple user stories"""
    id: str
    title: str
    description: str
    business_objective: str
    user_stories: List[str]  # List of story IDs
    estimated_effort: str
    priority: str
    stakeholders: List[str]
    created_timestamp: str

@dataclass
class StoryGenerationConfig:
    """Configuration for story generation"""
    complexity_level: str  # Simple, Standard, Detailed
    include_acceptance_criteria: bool
    include_story_points: bool
    story_format: str  # Standard, Gherkin, Custom
    prioritization_method: str  # MoSCoW, Value-based, Risk-based
    target_audience: List[str]

class UserStoryGenerator:
    """AI-powered user story generation"""
    
    def __init__(self):
        # Get OpenAI API key from environment or Streamlit secrets
        try:
            # Check multiple locations for the API key
            api_key = None
            
            # Method 1: Direct access (top-level secrets)
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                api_key = st.secrets['OPENAI_API_KEY']
            # Method 2: Nested in api_keys section
            elif hasattr(st, 'secrets') and 'api_keys' in st.secrets and 'openai_api_key' in st.secrets['api_keys']:
                api_key = st.secrets['api_keys']['openai_api_key']
            # Method 3: Environment variables
            elif 'OPENAI_API_KEY' in os.environ:
                api_key = os.environ['OPENAI_API_KEY']
            
            if api_key:
                openai.api_key = api_key
                self.api_key_available = True
                logger.info("OpenAI API key loaded successfully")
            else:
                self.api_key_available = False
                logger.warning("OpenAI API key not found in any location")
                return
                
        except Exception as e:
            self.api_key_available = False
            logger.error(f"OpenAI setup failed: {e}")
            return
    
    def generate_user_stories(self, requirements: List[str], config: StoryGenerationConfig, 
                            project_context: str = "") -> Dict[str, Any]:
        """Generate user stories from requirements"""
        
        if not self.api_key_available:
            return self._create_demo_stories(requirements, config)
        
        try:
            prompt = self._create_story_generation_prompt(requirements, config, project_context)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Business Analyst and Agile coach. Generate comprehensive, well-structured user stories from requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            stories_text = response.choices[0].message.content
            return self._parse_stories_response(stories_text, config)
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return self._create_demo_stories(requirements, config)
    
    def generate_epics(self, user_stories: List[UserStory], project_context: str = "") -> List[Epic]:
        """Generate epics from user stories"""
        
        if not self.api_key_available:
            return self._create_demo_epics(user_stories)
        
        try:
            prompt = f"""
            Based on the following user stories, create logical epics that group related functionality:
            
            Project Context: {project_context}
            
            User Stories:
            {self._format_stories_for_prompt(user_stories)}
            
            Generate 3-5 epics that:
            1. Group related user stories logically
            2. Represent meaningful business value
            3. Can be delivered incrementally
            4. Align with typical user workflows
            
            For each epic, provide:
            - Title and description
            - Business objective
            - List of related story IDs
            - Estimated effort (S/M/L/XL)
            - Priority (High/Medium/Low)
            - Key stakeholders
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Product Owner. Create meaningful epics that deliver business value."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            epics_text = response.choices[0].message.content
            return self._parse_epics_response(epics_text)
            
        except Exception as e:
            logger.error(f"Epic generation failed: {e}")
            return self._create_demo_epics(user_stories)
    
    def estimate_story_points(self, user_stories: List[UserStory]) -> List[UserStory]:
        """Estimate story points for user stories using AI"""
        
        if not self.api_key_available:
            return self._add_demo_story_points(user_stories)
        
        try:
            stories_for_estimation = self._format_stories_for_estimation(user_stories)
            
            prompt = f"""
            Estimate story points (1, 2, 3, 5, 8, 13, 21) for the following user stories using the Fibonacci sequence.
            Consider complexity, effort, and uncertainty. Provide reasoning for each estimation.
            
            User Stories for Estimation:
            {stories_for_estimation}
            
            Provide estimates in format: Story_ID: Points (Reasoning)
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Scrum Master. Provide accurate story point estimations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            estimations = self._parse_story_point_response(response.choices[0].message.content)
            return self._apply_story_point_estimates(user_stories, estimations)
            
        except Exception as e:
            logger.error(f"Story point estimation failed: {e}")
            return self._add_demo_story_points(user_stories)
    
    def _create_story_generation_prompt(self, requirements: List[str], config: StoryGenerationConfig, 
                                       project_context: str) -> str:
        """Create prompt for story generation"""
        
        prompt = f"""
        Generate user stories from the following requirements:
        
        Project Context: {project_context}
        
        Requirements:
        {chr(10).join(f"- {req}" for req in requirements)}
        
        Configuration:
        - Complexity Level: {config.complexity_level}
        - Include Acceptance Criteria: {config.include_acceptance_criteria}
        - Include Story Points: {config.include_story_points}
        - Story Format: {config.story_format}
        - Prioritization: {config.prioritization_method}
        - Target Audience: {', '.join(config.target_audience)}
        
        Generate comprehensive user stories that:
        """
        
        if config.story_format == "Standard":
            prompt += """
            1. Follow the format: "As a [user type], I want [goal] so that [benefit]"
            2. Include clear, testable acceptance criteria
            3. Are appropriately sized for a sprint
            4. Have clear business value
            """
        elif config.story_format == "Gherkin":
            prompt += """
            1. Use Given-When-Then format for acceptance criteria
            2. Include background context where needed
            3. Cover both happy path and edge cases
            4. Be specific and testable
            """
        
        if config.complexity_level == "Detailed":
            prompt += """
            5. Include technical considerations and dependencies
            6. Provide detailed acceptance criteria (5-8 criteria per story)
            7. Include edge cases and error scenarios
            8. Add implementation notes where helpful
            """
        elif config.complexity_level == "Standard":
            prompt += """
            5. Include 3-5 acceptance criteria per story
            6. Cover main functionality and basic edge cases
            7. Provide clear definition of done
            """
        else:  # Simple
            prompt += """
            5. Include 2-3 essential acceptance criteria
            6. Focus on core functionality
            7. Keep stories concise and actionable
            """
        
        return prompt
    
    def _parse_stories_response(self, response_text: str, config: StoryGenerationConfig) -> Dict[str, Any]:
        """Parse AI response into structured user stories"""
        
        stories = []
        epics = []
        
        # Split response into sections
        sections = re.split(r'\n(?=(?:Story|Epic)\s*\d+|#{1,3}\s)', response_text)
        
        current_epic = None
        story_counter = 1
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if this is a story section
            if re.match(r'(?:Story|User Story)\s*\d*', section, re.IGNORECASE):
                story = self._parse_individual_story(section, story_counter, config)
                if story:
                    stories.append(story)
                    story_counter += 1
            
            # Check if this is an epic section
            elif re.match(r'Epic\s*\d*', section, re.IGNORECASE):
                epic = self._parse_individual_epic(section)
                if epic:
                    epics.append(epic)
        
        # If no structured stories found, create them from the raw text
        if not stories:
            stories = self._extract_stories_from_text(response_text, config)
        
        return {
            "user_stories": stories,
            "epics": epics,
            "generation_timestamp": datetime.now().isoformat(),
            "total_stories": len(stories),
            "total_epics": len(epics)
        }
    
    def _parse_individual_story(self, story_text: str, story_id: int, config: StoryGenerationConfig) -> Optional[UserStory]:
        """Parse individual story from text"""
        
        try:
            lines = story_text.split('\n')
            
            # Extract title and story
            title = ""
            story = ""
            acceptance_criteria = []
            priority = "Medium"
            story_points = 3
            epic = "General"
            tags = []
            business_value = ""
            technical_notes = ""
            
            # Parse the text
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if 'title:' in line.lower() or line.startswith('**') and line.endswith('**'):
                    title = re.sub(r'[\*\#]*\s*title:\s*', '', line, flags=re.IGNORECASE).strip('*# ')
                elif line.startswith('As a ') or line.startswith('As an '):
                    story = line
                elif 'acceptance criteria' in line.lower():
                    current_section = 'acceptance'
                elif 'priority' in line.lower():
                    priority_match = re.search(r'(high|medium|low)', line, re.IGNORECASE)
                    if priority_match:
                        priority = priority_match.group(1).title()
                elif 'story points' in line.lower() or 'points:' in line.lower():
                    points_match = re.search(r'(\d+)', line)
                    if points_match:
                        story_points = int(points_match.group(1))
                elif line.startswith('- ') or line.startswith('• '):
                    if current_section == 'acceptance':
                        acceptance_criteria.append(line.lstrip('- • '))
            
            # Generate defaults if not found
            if not title:
                title = f"User Story {story_id}"
            if not story and len(lines) > 1:
                # Try to find a story-like line
                for line in lines:
                    if 'As a' in line or 'I want' in line:
                        story = line
                        break
            
            if not story:
                story = f"As a user, I want functionality related to story {story_id}"
            
            if not acceptance_criteria:
                acceptance_criteria = [
                    "The functionality works as expected",
                    "All edge cases are handled",
                    "User interface is intuitive"
                ]
            
            return UserStory(
                id=f"STORY-{story_id:03d}",
                title=title,
                story=story,
                acceptance_criteria=acceptance_criteria,
                priority=priority,
                story_points=story_points,
                epic=epic,
                tags=tags,
                business_value=business_value,
                technical_notes=technical_notes,
                created_timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error parsing story: {e}")
            return None
    
    def _extract_stories_from_text(self, text: str, config: StoryGenerationConfig) -> List[UserStory]:
        """Extract stories when no clear structure is found"""
        
        stories = []
        story_counter = 1
        
        # Look for "As a" patterns
        story_matches = re.findall(r'As\s+a\s+[^,]++,\s*I\s+want\s+[^.!?]*[.!?]?', text, re.IGNORECASE | re.MULTILINE)
        
        for match in story_matches:
            story = UserStory(
                id=f"STORY-{story_counter:03d}",
                title=f"User Story {story_counter}",
                story=match.strip(),
                acceptance_criteria=[
                    "Functionality works as described",
                    "User interface is intuitive",
                    "Edge cases are handled appropriately"
                ],
                priority="Medium",
                story_points=3,
                epic="General",
                tags=[],
                business_value="Standard business value",
                technical_notes="",
                created_timestamp=datetime.now().isoformat()
            )
            stories.append(story)
            story_counter += 1
        
        # If still no stories, create some defaults
        if not stories:
            stories = self._create_demo_stories_from_requirements([], config)
        
        return stories
    
    def _create_demo_stories(self, requirements: List[str], config: StoryGenerationConfig) -> Dict[str, Any]:
        """Create demo user stories when API is not available"""
        
        demo_stories = [
            UserStory(
                id="STORY-001",
                title="User Authentication",
                story="As a user, I want to log in securely so that I can access my personalized content and data",
                acceptance_criteria=[
                    "User can log in with valid email and password",
                    "Invalid credentials show appropriate error messages",
                    "Password reset functionality is available",
                    "User session is maintained across browser sessions",
                    "Account lockout after multiple failed attempts"
                ],
                priority="High",
                story_points=5,
                epic="User Management",
                tags=["authentication", "security", "core"],
                business_value="Essential for user data security and personalization",
                technical_notes="Implement OAuth 2.0 with JWT tokens",
                created_timestamp=datetime.now().isoformat()
            ),
            UserStory(
                id="STORY-002",
                title="Document Upload",
                story="As a business analyst, I want to upload project documents so that I can analyze requirements and generate technical specifications",
                acceptance_criteria=[
                    "Support for PDF, DOCX, and TXT file formats",
                    "File size validation (max 10MB per file)",
                    "Multiple file upload capability",
                    "Upload progress indicator shown",
                    "Virus scanning on uploaded files"
                ],
                priority="High",
                story_points=8,
                epic="Document Management",
                tags=["upload", "documents", "core"],
                business_value="Core functionality enabling document analysis workflows",
                technical_notes="Implement chunked upload for large files, use cloud storage",
                created_timestamp=datetime.now().isoformat()
            ),
            UserStory(
                id="STORY-003",
                title="Requirements Analysis",
                story="As a solutions architect, I want AI-powered analysis of uploaded documents so that I can quickly identify key requirements and technical components",
                acceptance_criteria=[
                    "Documents are processed and analyzed automatically",
                    "Key requirements are extracted and categorized",
                    "Technical components are identified",
                    "Analysis confidence score is provided",
                    "Results are saved for future reference"
                ],
                priority="High",
                story_points=13,
                epic="AI Analysis",
                tags=["ai", "analysis", "requirements"],
                business_value="Accelerates requirements gathering and reduces manual effort",
                technical_notes="Integrate OpenAI API with proper prompt engineering",
                created_timestamp=datetime.now().isoformat()
            ),
            UserStory(
                id="STORY-004",
                title="Technical Design Generation",
                story="As a solutions architect, I want to generate technical designs from analyzed requirements so that I can provide comprehensive system architecture recommendations",
                acceptance_criteria=[
                    "System architecture diagrams are generated",
                    "Database schema recommendations provided",
                    "API specifications are outlined",
                    "Technology stack suggestions included",
                    "Scalability considerations addressed"
                ],
                priority="Medium",
                story_points=21,
                epic="AI Analysis",
                tags=["ai", "design", "architecture"],
                business_value="Provides structured technical guidance for development teams",
                technical_notes="Complex AI prompt engineering, possible integration with diagramming tools",
                created_timestamp=datetime.now().isoformat()
            ),
            UserStory(
                id="STORY-005",
                title="User Story Generation",
                story="As a business analyst, I want to automatically generate user stories from requirements so that I can quickly create development-ready backlog items",
                acceptance_criteria=[
                    "User stories follow standard format",
                    "Acceptance criteria are included",
                    "Stories are prioritized appropriately",
                    "Story points are estimated",
                    "Stories are grouped into logical epics"
                ],
                priority="Medium",
                story_points=8,
                epic="Story Management",
                tags=["stories", "backlog", "agile"],
                business_value="Streamlines agile development process and backlog creation",
                technical_notes="Template-based generation with AI refinement",
                created_timestamp=datetime.now().isoformat()
            )
        ]
        
        demo_epics = [
            Epic(
                id="EPIC-001",
                title="User Management",
                description="Complete user authentication and profile management system",
                business_objective="Secure user access and personalized experience",
                user_stories=["STORY-001"],
                estimated_effort="Medium",
                priority="High",
                stakeholders=["End Users", "Security Team", "Development Team"],
                created_timestamp=datetime.now().isoformat()
            ),
            Epic(
                id="EPIC-002", 
                title="Document Management",
                description="Document upload, processing, and management capabilities",
                business_objective="Enable efficient document handling and processing workflows",
                user_stories=["STORY-002"],
                estimated_effort="Large",
                priority="High",
                stakeholders=["Business Analysts", "Solutions Architects", "End Users"],
                created_timestamp=datetime.now().isoformat()
            ),
            Epic(
                id="EPIC-003",
                title="AI Analysis",
                description="AI-powered document analysis and technical design generation",
                business_objective="Accelerate requirements analysis and technical design processes",
                user_stories=["STORY-003", "STORY-004"],
                estimated_effort="Extra Large",
                priority="High",
                stakeholders=["Solutions Architects", "Business Analysts", "Development Teams"],
                created_timestamp=datetime.now().isoformat()
            )
        ]
        
        return {
            "user_stories": demo_stories,
            "epics": demo_epics,
            "generation_timestamp": datetime.now().isoformat(),
            "total_stories": len(demo_stories),
            "total_epics": len(demo_epics)
        }
    
    def _format_stories_for_prompt(self, user_stories: List[UserStory]) -> str:
        """Format user stories for AI prompt"""
        formatted = ""
        for story in user_stories:
            formatted += f"""
            Story ID: {story.id}
            Title: {story.title}
            Story: {story.story}
            Priority: {story.priority}
            Points: {story.story_points}
            ---
            """
        return formatted
    
    def _parse_epics_response(self, response_text: str) -> List[Epic]:
        """Parse epics from AI response"""
        # Simplified parsing - in production you'd want more sophisticated parsing
        return []  # Placeholder
    
    def _create_demo_epics(self, user_stories: List[UserStory]) -> List[Epic]:
        """Create demo epics"""
        return []  # Placeholder
    
    def _add_demo_story_points(self, user_stories: List[UserStory]) -> List[UserStory]:
        """Add demo story points"""
        for story in user_stories:
            if story.story_points == 0:
                story.story_points = 3  # Default
        return user_stories
    
    def _format_stories_for_estimation(self, user_stories: List[UserStory]) -> str:
        """Format stories for estimation"""
        return ""  # Placeholder
    
    def _parse_story_point_response(self, response_text: str) -> Dict[str, int]:
        """Parse story point estimations"""
        return {}  # Placeholder
    
    def _apply_story_point_estimates(self, user_stories: List[UserStory], 
                                   estimations: Dict[str, int]) -> List[UserStory]:
        """Apply story point estimates"""
        return user_stories  # Placeholder


class UserStoryUI:
    """Streamlit UI for User Story Generation"""
    
    def __init__(self):
        self.story_generator = UserStoryGenerator()
        
        # Initialize session state
        if 'user_stories' not in st.session_state:
            st.session_state.user_stories = []
        if 'epics' not in st.session_state:
            st.session_state.epics = []
        if 'story_generation_config' not in st.session_state:
            st.session_state.story_generation_config = StoryGenerationConfig(
                complexity_level="Standard",
                include_acceptance_criteria=True,
                include_story_points=True,
                story_format="Standard",
                prioritization_method="MoSCoW",
                target_audience=["End Users"]
            )
    
    def render(self):
        """Main render method for User Story Generation tab"""
        
        st.markdown("### 📋 User Story Generation & Management")
        st.markdown("Convert requirements into development-ready user stories with AI assistance.")
        
        # Create tabs
        tab_generate, tab_manage, tab_epics, tab_export = st.tabs([
            "✨ Generate Stories",
            "📝 Manage Stories", 
            "🎯 Epic Planning",
            "📊 Export & Reports"
        ])
        
        with tab_generate:
            self.render_story_generation()
        
        with tab_manage:
            self.render_story_management()
        
        with tab_epics:
            self.render_epic_planning()
        
        with tab_export:
            self.render_export_options()
    
    def render_story_generation(self):
        """Story generation interface"""
        
        st.markdown("#### ✨ Generate User Stories")
        
        # Input methods
        input_method = st.radio(
            "Requirements Input Method",
            ["Manual Entry", "From Document Analysis", "Import from File"],
            help="Choose how to provide requirements for story generation"
        )
        
        requirements = []
        
        if input_method == "Manual Entry":
            st.markdown("##### 📝 Enter Requirements")
            
            # Text area for requirements
            requirements_text = st.text_area(
                "Requirements (one per line)",
                placeholder="Enter each requirement on a new line:\n• User authentication system\n• Document upload functionality\n• Analysis reporting dashboard",
                height=150,
                help="Enter functional and non-functional requirements"
            )
            
            if requirements_text:
                requirements = [req.strip().lstrip('•-* ') for req in requirements_text.split('\n') 
                              if req.strip() and not req.strip().startswith('#')]
        
        elif input_method == "From Document Analysis":
            # Check if analysis results exist
            analysis_results = getattr(st.session_state, 'analysis_results', [])
            
            if analysis_results:
                selected_analysis = st.selectbox(
                    "Select Analysis Results",
                    [f"{analysis.document_name} - {analysis.analysis_type}" 
                     for analysis in analysis_results]
                )
                
                if selected_analysis:
                    analysis_index = [f"{analysis.document_name} - {analysis.analysis_type}" 
                                    for analysis in analysis_results].index(selected_analysis)
                    analysis = analysis_results[analysis_index]
                    
                    # Combine requirements from analysis
                    requirements = (analysis.key_requirements + 
                                  analysis.technical_components + 
                                  analysis.business_objectives)
                    
                    st.info(f"✅ Loaded {len(requirements)} requirements from analysis")
            else:
                st.warning("📋 No document analysis results found. Analyze documents first in the Solutions Architecture tab.")
        
        elif input_method == "Import from File":
            uploaded_file = st.file_uploader(
                "Upload Requirements File",
                type=['txt', 'json', 'csv'],
                help="Upload a file containing requirements"
            )
            
            if uploaded_file:
                # Process uploaded requirements file
                requirements = self.process_requirements_file(uploaded_file)
        
        # Story generation configuration
        if requirements:
            st.markdown("---")
            st.markdown("##### ⚙️ Story Generation Configuration")
            
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                complexity_level = st.selectbox(
                    "Story Complexity",
                    ["Simple", "Standard", "Detailed"],
                    index=1,
                    help="Level of detail in generated stories"
                )
                
                story_format = st.selectbox(
                    "Story Format",
                    ["Standard", "Gherkin", "Custom"],
                    help="Format for user stories and acceptance criteria"
                )
                
                include_acceptance_criteria = st.checkbox(
                    "Include Acceptance Criteria",
                    value=True,
                    help="Generate detailed acceptance criteria for each story"
                )
            
            with col_config2:
                prioritization_method = st.selectbox(
                    "Prioritization Method",
                    ["MoSCoW", "Value-based", "Risk-based", "Effort-based"],
                    help="Method for prioritizing generated stories"
                )
                
                include_story_points = st.checkbox(
                    "Include Story Point Estimates",
                    value=True,
                    help="Generate story point estimates using Fibonacci sequence"
                )
                
                target_audience = st.multiselect(
                    "Target Audience",
                    ["End Users", "Administrators", "Developers", "Business Users", "System Integrators"],
                    default=["End Users"],
                    help="Primary users for the generated stories"
                )
            
            # Project context
            project_context = st.text_area(
                "Project Context (Optional)",
                placeholder="Brief description of the project, technology constraints, business goals...",
                help="Additional context to improve story generation quality"
            )
            
            # Generate stories
            col_generate, col_preview = st.columns([1, 1])
            
            with col_generate:
                if st.button("✨ Generate User Stories", type="primary"):
                    config = StoryGenerationConfig(
                        complexity_level=complexity_level,
                        include_acceptance_criteria=include_acceptance_criteria,
                        include_story_points=include_story_points,
                        story_format=story_format,
                        prioritization_method=prioritization_method,
                        target_audience=target_audience
                    )
                    
                    with st.spinner("Generating user stories..."):
                        result = self.story_generator.generate_user_stories(
                            requirements, config, project_context
                        )
                        
                        # Store results
                        st.session_state.user_stories.extend(result['user_stories'])
                        st.session_state.epics.extend(result['epics'])
                        
                        st.success(f"✅ Generated {result['total_stories']} user stories and {result['total_epics']} epics!")
                        st.rerun()
            
            with col_preview:
                if st.button("👁️ Preview Requirements"):
                    st.markdown("**Requirements to be processed:**")
                    for i, req in enumerate(requirements, 1):
                        st.markdown(f"{i}. {req}")
        
        else:
            st.info("📝 Enter or import requirements to generate user stories.")
    
    def render_story_management(self):
        """Story management interface"""
        
        if not st.session_state.user_stories:
            st.info("📋 No user stories yet. Generate stories first!")
            return
        
        st.markdown("#### 📝 User Story Management")
        
        # Filter and search
        col_search, col_filter_priority, col_filter_epic = st.columns([2, 1, 1])
        
        with col_search:
            search_term = st.text_input("🔍 Search stories", placeholder="Search by title or content...")
        
        with col_filter_priority:
            priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
        
        with col_filter_epic:
            epic_options = ["All"] + list(set(story.epic for story in st.session_state.user_stories))
            epic_filter = st.selectbox("Epic", epic_options)
        
        # Apply filters
        filtered_stories = self.filter_stories(st.session_state.user_stories, search_term, 
                                             priority_filter, epic_filter)
        
        # Display stories
        for story in filtered_stories:
            with st.expander(f"📋 {story.id}: {story.title}", expanded=False):
                
                # Story header info
                col_priority, col_points, col_epic = st.columns([1, 1, 2])
                
                with col_priority:
                    priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                    st.markdown(f"**Priority:** {priority_color.get(story.priority, '⚪')} {story.priority}")
                
                with col_points:
                    st.markdown(f"**Points:** {story.story_points}")
                
                with col_epic:
                    st.markdown(f"**Epic:** {story.epic}")
                
                # Story content
                st.markdown("**User Story:**")
                st.markdown(f"*{story.story}*")
                
                # Acceptance criteria
                if story.acceptance_criteria:
                    st.markdown("**Acceptance Criteria:**")
                    for i, criteria in enumerate(story.acceptance_criteria, 1):
                        st.markdown(f"{i}. {criteria}")
                
                # Additional info
                if story.business_value:
                    st.markdown(f"**Business Value:** {story.business_value}")
                
                if story.technical_notes:
                    st.markdown(f"**Technical Notes:** {story.technical_notes}")
                
                if story.tags:
                    st.markdown(f"**Tags:** {', '.join(story.tags)}")
                
                # Story actions
                col_edit, col_clone, col_delete = st.columns(3)
                
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_{story.id}"):
                        self.edit_story(story)
                
                with col_clone:
                    if st.button("📋 Clone", key=f"clone_{story.id}"):
                        self.clone_story(story)
                
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{story.id}"):
                        self.delete_story(story.id)
        
        # Batch operations
        if filtered_stories:
            st.markdown("---")
            st.markdown("##### ⚡ Batch Operations")
            
            col_batch1, col_batch2, col_batch3 = st.columns(3)
            
            with col_batch1:
                if st.button("📊 Estimate All Stories"):
                    with st.spinner("Estimating story points..."):
                        updated_stories = self.story_generator.estimate_story_points(filtered_stories)
                        st.success("✅ Story points estimated!")
            
            with col_batch2:
                if st.button("🎯 Create Epics"):
                    with st.spinner("Generating epics..."):
                        new_epics = self.story_generator.generate_epics(filtered_stories)
                        st.session_state.epics.extend(new_epics)
                        st.success(f"✅ Created {len(new_epics)} epics!")
            
            with col_batch3:
                if st.button("📤 Export Stories"):
                    self.export_stories(filtered_stories)
    
    def render_epic_planning(self):
        """Epic planning interface"""
        
        st.markdown("#### 🎯 Epic Planning & Management")
        
        if not st.session_state.epics and not st.session_state.user_stories:
            st.info("📋 No epics or stories yet. Generate stories first!")
            return
        
        # Epic creation/management tabs
        epic_tab1, epic_tab2 = st.tabs(["➕ Create Epic", "📚 Manage Epics"])
        
        with epic_tab1:
            self.render_epic_creation()
        
        with epic_tab2:
            self.render_epic_management()
    
    def render_epic_creation(self):
        """Epic creation interface"""
        
        st.markdown("##### ➕ Create New Epic")
        
        # Epic details
        epic_title = st.text_input("Epic Title", placeholder="e.g., User Management System")
        epic_description = st.text_area("Epic Description", 
                                       placeholder="Describe the overall goal and scope of this epic...")
        
        business_objective = st.text_input("Business Objective", 
                                         placeholder="What business value does this epic deliver?")
        
        # Story assignment
        if st.session_state.user_stories:
            st.markdown("**Assign User Stories:**")
            
            available_stories = [f"{story.id}: {story.title}" for story in st.session_state.user_stories]
            selected_stories = st.multiselect(
                "Select Stories for this Epic",
                available_stories,
                help="Choose which user stories belong to this epic"
            )
            
            # Epic sizing and prioritization
            col_effort, col_priority = st.columns(2)
            
            with col_effort:
                estimated_effort = st.selectbox("Estimated Effort", ["Small", "Medium", "Large", "Extra Large"])
            
            with col_priority:
                priority = st.selectbox("Epic Priority", ["High", "Medium", "Low"])
            
            # Stakeholders
            stakeholders = st.multiselect(
                "Key Stakeholders",
                ["End Users", "Business Analysts", "Solutions Architects", "Development Team", 
                 "Product Owner", "QA Team", "DevOps Team", "Security Team"],
                help="Who are the key stakeholders for this epic?"
            )
            
            # Create epic
            if st.button("🎯 Create Epic", type="primary"):
                if epic_title and epic_description:
                    new_epic = Epic(
                        id=f"EPIC-{len(st.session_state.epics) + 1:03d}",
                        title=epic_title,
                        description=epic_description,
                        business_objective=business_objective,
                        user_stories=[story.split(':')[0] for story in selected_stories],
                        estimated_effort=estimated_effort,
                        priority=priority,
                        stakeholders=stakeholders,
                        created_timestamp=datetime.now().isoformat()
                    )
                    
                    st.session_state.epics.append(new_epic)
                    st.success(f"✅ Epic '{epic_title}' created successfully!")
                    st.rerun()
                else:
                    st.error("Please provide epic title and description.")
    
    def render_epic_management(self):
        """Epic management interface"""
        
        if not st.session_state.epics:
            st.info("📋 No epics created yet. Create your first epic above!")
            return
        
        st.markdown("##### 📚 Manage Epics")
        
        for epic in st.session_state.epics:
            with st.expander(f"🎯 {epic.id}: {epic.title}", expanded=False):
                
                # Epic info
                col_priority, col_effort, col_stories = st.columns([1, 1, 1])
                
                with col_priority:
                    priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                    st.markdown(f"**Priority:** {priority_color.get(epic.priority, '⚪')} {epic.priority}")
                
                with col_effort:
                    st.markdown(f"**Effort:** {epic.estimated_effort}")
                
                with col_stories:
                    st.markdown(f"**Stories:** {len(epic.user_stories)}")
                
                # Epic content
                st.markdown(f"**Description:** {epic.description}")
                st.markdown(f"**Business Objective:** {epic.business_objective}")
                
                if epic.stakeholders:
                    st.markdown(f"**Stakeholders:** {', '.join(epic.stakeholders)}")
                
                # Assigned stories
                if epic.user_stories:
                    st.markdown("**Assigned Stories:**")
                    for story_id in epic.user_stories:
                        matching_story = next((s for s in st.session_state.user_stories if s.id == story_id), None)
                        if matching_story:
                            st.markdown(f"• {story_id}: {matching_story.title}")
    
    def render_export_options(self):
        """Export and reporting options"""
        
        st.markdown("#### 📊 Export & Reports")
        
        if not st.session_state.user_stories:
            st.info("📋 No data to export. Generate stories first!")
            return
        
        # Export options
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            st.markdown("##### 📄 User Stories")
            
            export_format = st.selectbox(
                "Export Format",
                ["JSON", "CSV", "Excel", "Jira Import", "Azure DevOps"]
            )
            
            if st.button("📥 Export User Stories"):
                self.export_user_stories(export_format)
        
        with col_export2:
            st.markdown("##### 🎯 Epics")
            
            epic_format = st.selectbox(
                "Epic Export Format", 
                ["JSON", "CSV", "Project Plan", "Roadmap"]
            )
            
            if st.button("📥 Export Epics"):
                self.export_epics(epic_format)
        
        # Summary metrics
        st.markdown("---")
        st.markdown("##### 📈 Story Summary")
        
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        
        with col_metrics1:
            st.metric("Total Stories", len(st.session_state.user_stories))
        
        with col_metrics2:
            total_points = sum(story.story_points for story in st.session_state.user_stories)
            st.metric("Total Story Points", total_points)
        
        with col_metrics3:
            high_priority = len([s for s in st.session_state.user_stories if s.priority == "High"])
            st.metric("High Priority Stories", high_priority)
        
        with col_metrics4:
            st.metric("Total Epics", len(st.session_state.epics))
    
    def process_requirements_file(self, uploaded_file) -> List[str]:
        """Process uploaded requirements file"""
        try:
            if uploaded_file.type == "text/plain":
                content = uploaded_file.read().decode('utf-8')
                requirements = [line.strip().lstrip('•-* ') for line in content.split('\n') 
                              if line.strip() and not line.strip().startswith('#')]
                return requirements
            else:
                st.error("File format not supported yet. Please use TXT format.")
                return []
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return []
    
    def filter_stories(self, stories: List[UserStory], search_term: str, 
                      priority_filter: str, epic_filter: str) -> List[UserStory]:
        """Filter stories based on criteria"""
        filtered = stories
        
        if search_term:
            filtered = [s for s in filtered if search_term.lower() in s.title.lower() 
                       or search_term.lower() in s.story.lower()]
        
        if priority_filter != "All":
            filtered = [s for s in filtered if s.priority == priority_filter]
        
        if epic_filter != "All":
            filtered = [s for s in filtered if s.epic == epic_filter]
        
        return filtered
    
    def edit_story(self, story: UserStory):
        """Edit story functionality (placeholder)"""
        st.info("🚧 Story editing feature coming soon!")
    
    def clone_story(self, story: UserStory):
        """Clone story functionality (placeholder)"""
        st.info("🚧 Story cloning feature coming soon!")
    
    def delete_story(self, story_id: str):
        """Delete story"""
        st.session_state.user_stories = [s for s in st.session_state.user_stories if s.id != story_id]
        st.success(f"✅ Story {story_id} deleted!")
        st.rerun()
    
    def export_user_stories(self, format_type: str):
        """Export user stories"""
        if format_type == "JSON":
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "user_stories": [asdict(story) for story in st.session_state.user_stories],
                "total_stories": len(st.session_state.user_stories)
            }
            
            json_string = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download User Stories (JSON)",
                data=json_string,
                file_name=f"user_stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info(f"🚧 {format_type} export coming soon!")
    
    def export_epics(self, format_type: str):
        """Export epics"""
        if format_type == "JSON":
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "epics": [asdict(epic) for epic in st.session_state.epics],
                "total_epics": len(st.session_state.epics)
            }
            
            json_string = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download Epics (JSON)",
                data=json_string,
                file_name=f"epics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info(f"🚧 {format_type} export coming soon!")


# Main render function for integration
def render_user_story_generation_tab():
    """Main function to render the User Story Generation tab"""
    
    try:
        ui = UserStoryUI()
        ui.render()
    
    except Exception as e:
        st.error(f"❌ Error loading User Story Generation module: {str(e)}")
        logger.error(f"User Story Generation UI error: {e}")
        
        # Fallback UI
        st.markdown("### 📋 User Story Generation")
        st.info("🚧 This feature is currently being set up. Please try again later.")
