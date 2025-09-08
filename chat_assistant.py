"""
AI Chat Assistant Module
Interactive chat interface for project consultation and guidance
"""

import streamlit as st
import openai
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Structure for chat messages"""
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: str
    message_type: str  # text, code, analysis, recommendation
    metadata: Dict[str, Any]

@dataclass
class ChatSession:
    """Structure for chat sessions"""
    id: str
    title: str
    messages: List[ChatMessage]
    created_timestamp: str
    last_updated: str
    context_summary: str
    tags: List[str]

class ProjectChatAssistant:
    """AI-powered project chat assistant"""
    
    def __init__(self):
        # Initialize OpenAI
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
        
        # System context for the assistant
        self.system_context = """
        You are a Senior Solutions Architect and Business Analyst AI Assistant. 
        
        Your expertise includes:
        - Solutions Architecture and System Design
        - Business Analysis and Requirements Gathering  
        - Agile Methodologies and User Story Creation
        - Technical Design and Implementation Planning
        - Risk Assessment and Mitigation Strategies
        - Technology Stack Recommendations
        - Project Planning and Estimation
        
        You help users with:
        1. Analyzing project requirements and documents
        2. Designing technical solutions and architectures
        3. Creating user stories and acceptance criteria
        4. Planning project timelines and resources
        5. Identifying risks and mitigation strategies
        6. Recommending technology stacks and tools
        7. Providing best practices and industry guidance
        
        Always provide:
        - Practical, actionable advice
        - Industry best practices
        - Specific examples when helpful
        - Clear explanations for complex concepts
        - Multiple options when appropriate
        
        Tone: Professional, helpful, and consultative
        """
    
    def get_chat_response(self, message: str, chat_history: List[ChatMessage], 
                         project_context: Dict[str, Any] = None) -> ChatMessage:
        """Get response from AI assistant"""
        
        if not self.api_key_available:
            return self._create_demo_response(message)
        
        try:
            # Prepare conversation history
            messages = [{"role": "system", "content": self.system_context}]
            
            # Add project context if available
            if project_context:
                context_message = self._format_project_context(project_context)
                messages.append({"role": "system", "content": f"Project Context: {context_message}"})
            
            # Add recent chat history (last 10 messages to stay within token limits)
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            for chat_msg in recent_history:
                if chat_msg.role != "system":
                    messages.append({
                        "role": chat_msg.role,
                        "content": chat_msg.content
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Get AI response
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            assistant_response = response.choices[0].message.content
            
            return ChatMessage(
                id=str(uuid.uuid4()),
                role="assistant",
                content=assistant_response,
                timestamp=datetime.now().isoformat(),
                message_type="text",
                metadata={"model": "gpt-4", "tokens": response.usage.total_tokens}
            )
            
        except Exception as e:
            logger.error(f"Chat response failed: {e}")
            return self._create_error_response(str(e))
    
    def _format_project_context(self, context: Dict[str, Any]) -> str:
        """Format project context for AI"""
        formatted_context = ""
        
        # Add document analysis results if available
        if 'analysis_results' in context and context['analysis_results']:
            formatted_context += "Analyzed Documents:\n"
            for analysis in context['analysis_results']:
                formatted_context += f"- {analysis.document_name}: {len(analysis.key_requirements)} requirements identified\n"
        
        # Add user stories if available
        if 'user_stories' in context and context['user_stories']:
            formatted_context += f"\nProject has {len(context['user_stories'])} user stories defined.\n"
        
        # Add technical designs if available
        if 'technical_designs' in context and context['technical_designs']:
            formatted_context += f"\nProject has {len(context['technical_designs'])} technical designs.\n"
        
        return formatted_context
    
    def _create_demo_response(self, message: str) -> ChatMessage:
        """Create demo response when API is not available"""
        
        # Simple keyword-based responses for demo
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['architecture', 'design', 'system']):
            response = """
            For system architecture, I recommend considering these key aspects:

            1. **Scalability**: Design for growth with microservices or modular architecture
            2. **Security**: Implement defense in depth with authentication, authorization, and encryption
            3. **Reliability**: Use circuit breakers, retries, and health checks
            4. **Performance**: Consider caching strategies and database optimization
            5. **Maintainability**: Follow SOLID principles and clean code practices

            Would you like me to elaborate on any of these aspects or discuss specific architectural patterns for your use case?
            """
        
        elif any(word in message_lower for word in ['user story', 'requirements', 'business']):
            response = """
            For effective user stories and requirements:

            1. **User-Centered**: Always write from the user's perspective
            2. **Value-Focused**: Clearly articulate the business value
            3. **Testable**: Include measurable acceptance criteria
            4. **Independent**: Stories should be self-contained when possible
            5. **Negotiable**: Allow for discussion and refinement

            Example format:
            "As a [user type], I want [functionality] so that [business value]"

            What specific requirements or user stories would you like help with?
            """
        
        elif any(word in message_lower for word in ['risk', 'challenge', 'problem']):
            response = """
            Common project risks and mitigation strategies:

            **Technical Risks:**
            - Integration complexity → Proof of concepts and early testing
            - Performance issues → Load testing and monitoring
            - Security vulnerabilities → Security reviews and penetration testing

            **Business Risks:**
            - Scope creep → Clear requirements and change control
            - Timeline delays → Buffer time and milestone tracking
            - Resource constraints → Capacity planning and skill assessment

            What specific risks or challenges are you facing in your project?
            """
        
        elif any(word in message_lower for word in ['technology', 'stack', 'tools']):
            response = """
            Technology stack recommendations depend on your specific needs:

            **For Web Applications:**
            - Frontend: React/Angular/Vue.js with TypeScript
            - Backend: Node.js/Python/Java with REST APIs
            - Database: PostgreSQL/MongoDB based on data structure
            - Cloud: AWS/Azure/GCP for scalability

            **Key Considerations:**
            - Team expertise and learning curve
            - Performance and scalability requirements
            - Budget and licensing costs
            - Community support and documentation

            What type of application are you building? I can provide more specific recommendations.
            """
        
        else:
            response = """
            Thank you for your question! As your AI Solutions Architect and Business Analyst assistant, I'm here to help with:

            - 🏗️ **Architecture Design**: System design, patterns, and best practices
            - 📋 **Requirements Analysis**: User stories, acceptance criteria, and business analysis
            - ⚖️ **Risk Assessment**: Identifying and mitigating project risks
            - 🛠️ **Technology Selection**: Choosing the right tools and technologies
            - 📊 **Project Planning**: Timelines, resources, and estimation

            Could you provide more details about what you'd like assistance with? The more context you share, the better I can help!
            """
        
        return ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=response,
            timestamp=datetime.now().isoformat(),
            message_type="text",
            metadata={"model": "demo", "demo_mode": True}
        )
    
    def _create_error_response(self, error_message: str) -> ChatMessage:
        """Create error response"""
        return ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=f"I apologize, but I encountered an error while processing your request: {error_message}\n\nPlease try rephrasing your question or contact support if the issue persists.",
            timestamp=datetime.now().isoformat(),
            message_type="error",
            metadata={"error": error_message}
        )
    
    def generate_conversation_title(self, messages: List[ChatMessage]) -> str:
        """Generate a title for the conversation"""
        
        if not messages:
            return "New Conversation"
        
        # Use first user message to generate title
        first_user_message = next((msg for msg in messages if msg.role == "user"), None)
        if not first_user_message:
            return "New Conversation"
        
        content = first_user_message.content[:50]
        
        # Simple title generation based on keywords
        if any(word in content.lower() for word in ['architecture', 'design', 'system']):
            return "Architecture Discussion"
        elif any(word in content.lower() for word in ['user story', 'requirements', 'business']):
            return "Requirements Analysis"
        elif any(word in content.lower() for word in ['risk', 'challenge']):
            return "Risk Assessment"
        elif any(word in content.lower() for word in ['technology', 'stack']):
            return "Technology Consultation"
        else:
            return f"Discussion: {content}..."


class ChatUI:
    """Streamlit UI for Chat Assistant"""
    
    def __init__(self):
        self.chat_assistant = ProjectChatAssistant()
        
        # Initialize session state
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = []
        if 'current_chat_session' not in st.session_state:
            st.session_state.current_chat_session = None
        if 'chat_input_key' not in st.session_state:
            st.session_state.chat_input_key = 0
    
    def render(self):
        """Main render method for Chat Assistant tab"""
        
        st.markdown("### 💬 AI Project Chat Assistant")
        st.markdown("Get expert guidance from your AI Solutions Architect and Business Analyst.")
        
        # Chat interface layout
        col_sidebar, col_main = st.columns([1, 3])
        
        with col_sidebar:
            self.render_chat_sidebar()
        
        with col_main:
            self.render_chat_main()
    
    def render_chat_sidebar(self):
        """Render chat sessions sidebar"""
        
        st.markdown("#### 💬 Chat Sessions")
        
        # New chat button
        if st.button("➕ New Chat", type="primary", use_container_width=True):
            self.create_new_chat_session()
        
        # Session management
        if st.session_state.chat_sessions:
            st.markdown("---")
            st.markdown("**Recent Sessions:**")
            
            for i, session in enumerate(st.session_state.chat_sessions[-10:]):  # Show last 10
                
                # Session button
                if st.button(
                    f"📝 {session.title}",
                    key=f"session_{session.id}",
                    help=f"Created: {datetime.fromisoformat(session.created_timestamp).strftime('%Y-%m-%d %H:%M')}",
                    use_container_width=True
                ):
                    st.session_state.current_chat_session = session
                    st.rerun()
                
                # Delete session button (small)
                if st.button("🗑️", key=f"delete_{session.id}", help="Delete session"):
                    self.delete_chat_session(session.id)
        
        # Context information
        st.markdown("---")
        st.markdown("#### 🔍 Available Context")
        
        context_info = []
        
        # Check for document analysis
        if hasattr(st.session_state, 'analysis_results') and st.session_state.analysis_results:
            context_info.append(f"📄 {len(st.session_state.analysis_results)} analyzed documents")
        
        # Check for user stories
        if hasattr(st.session_state, 'user_stories') and st.session_state.user_stories:
            context_info.append(f"📋 {len(st.session_state.user_stories)} user stories")
        
        # Check for technical designs
        if hasattr(st.session_state, 'technical_designs') and st.session_state.technical_designs:
            context_info.append(f"🏗️ {len(st.session_state.technical_designs)} technical designs")
        
        if context_info:
            for info in context_info:
                st.caption(info)
        else:
            st.caption("No project context available")
        
        # Quick help
        st.markdown("---")
        with st.expander("💡 Chat Tips", expanded=False):
            st.markdown("""
            **Ask me about:**
            - System architecture and design patterns
            - Requirements analysis and user stories
            - Technology recommendations
            - Risk assessment and mitigation
            - Project planning and estimation
            - Best practices and industry standards
            
            **For better responses:**
            - Provide specific context about your project
            - Ask focused questions
            - Share relevant constraints or requirements
            """)
    
    def render_chat_main(self):
        """Render main chat interface"""
        
        if not st.session_state.current_chat_session:
            # Welcome screen
            self.render_welcome_screen()
        else:
            # Active chat session
            self.render_active_chat()
    
    def render_welcome_screen(self):
        """Render welcome screen when no chat is active"""
        
        st.markdown("#### 👋 Welcome to Your AI Project Assistant!")
        
        col_welcome1, col_welcome2 = st.columns(2)
        
        with col_welcome1:
            st.markdown("""
            **I can help you with:**
            
            🏗️ **Solutions Architecture**
            - System design and architecture patterns
            - Technology stack recommendations
            - Scalability and performance planning
            
            📋 **Business Analysis**
            - Requirements gathering and analysis
            - User story creation and refinement
            - Acceptance criteria development
            
            ⚖️ **Risk Management**
            - Risk identification and assessment
            - Mitigation strategies
            - Contingency planning
            """)
        
        with col_welcome2:
            st.markdown("""
            **🚀 Quick Start Options:**
            """)
            
            if st.button("💡 Ask about Architecture Patterns", use_container_width=True):
                self.quick_start_chat("What are the most effective architecture patterns for modern web applications?")
            
            if st.button("📝 Help with User Stories", use_container_width=True):
                self.quick_start_chat("How can I write better user stories with clear acceptance criteria?")
            
            if st.button("🛠️ Technology Recommendations", use_container_width=True):
                self.quick_start_chat("What technology stack would you recommend for a scalable business application?")
            
            if st.button("⚠️ Risk Assessment Guidance", use_container_width=True):
                self.quick_start_chat("What are common project risks and how can I mitigate them?")
        
        # Sample questions
        st.markdown("---")
        st.markdown("#### 💭 Example Questions You Can Ask:")
        
        sample_questions = [
            "How should I structure a microservices architecture for my e-commerce platform?",
            "What's the best way to handle user authentication in a multi-tenant SaaS application?",
            "Can you help me break down this requirement into user stories?",
            "What are the security considerations for a healthcare data management system?",
            "How do I estimate story points for complex technical tasks?",
            "What deployment strategy would work best for our CI/CD pipeline?"
        ]
        
        for question in sample_questions:
            if st.button(f"💬 {question}", key=f"sample_{hash(question)}", use_container_width=True):
                self.quick_start_chat(question)
    
    def render_active_chat(self):
        """Render active chat session"""
        
        session = st.session_state.current_chat_session
        
        # Chat header
        col_title, col_actions = st.columns([3, 1])
        
        with col_title:
            st.markdown(f"#### 💬 {session.title}")
            st.caption(f"Started: {datetime.fromisoformat(session.created_timestamp).strftime('%Y-%m-%d %H:%M')}")
        
        with col_actions:
            if st.button("🏷️ Rename"):
                self.show_rename_dialog()
            if st.button("🗑️ Delete"):
                self.delete_current_session()
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Display messages
            for message in session.messages:
                self.render_chat_message(message)
        
        # Chat input
        st.markdown("---")
        user_input = st.chat_input(
            "Ask your AI Solutions Architect and Business Analyst...",
            key=f"chat_input_{st.session_state.chat_input_key}"
        )
        
        if user_input:
            self.handle_user_message(user_input)
        
        # Quick action buttons
        self.render_quick_actions()
    
    def render_chat_message(self, message: ChatMessage):
        """Render individual chat message"""
        
        if message.role == "user":
            # User message
            with st.chat_message("user"):
                st.markdown(message.content)
                
        elif message.role == "assistant":
            # Assistant message
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message.content)
                
                # Show metadata if available
                if message.metadata and 'demo_mode' not in message.metadata:
                    with st.expander("ℹ️ Response Details", expanded=False):
                        st.caption(f"Timestamp: {datetime.fromisoformat(message.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                        if 'tokens' in message.metadata:
                            st.caption(f"Tokens used: {message.metadata['tokens']}")
        
        elif message.role == "system":
            # System message (rarely displayed)
            st.info(message.content)
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        
        st.markdown("#### ⚡ Quick Actions")
        
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        
        with col_q1:
            if st.button("🏗️ Architecture Help", key="qa_arch"):
                self.add_quick_message("Can you help me with system architecture design for my project?")
        
        with col_q2:
            if st.button("📋 User Stories", key="qa_stories"):
                self.add_quick_message("I need help creating user stories from my requirements.")
        
        with col_q3:
            if st.button("⚠️ Risk Analysis", key="qa_risks"):
                self.add_quick_message("What risks should I be aware of in my project?")
        
        with col_q4:
            if st.button("🛠️ Tech Stack", key="qa_tech"):
                self.add_quick_message("What technology stack do you recommend for my use case?")
    
    def create_new_chat_session(self):
        """Create a new chat session"""
        
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            title="New Conversation",
            messages=[],
            created_timestamp=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            context_summary="",
            tags=[]
        )
        
        st.session_state.chat_sessions.append(new_session)
        st.session_state.current_chat_session = new_session
        st.rerun()
    
    def delete_chat_session(self, session_id: str):
        """Delete a chat session"""
        
        st.session_state.chat_sessions = [s for s in st.session_state.chat_sessions if s.id != session_id]
        
        # If deleted session was current, clear current session
        if (st.session_state.current_chat_session and 
            st.session_state.current_chat_session.id == session_id):
            st.session_state.current_chat_session = None
        
        st.success("Chat session deleted!")
        st.rerun()
    
    def delete_current_session(self):
        """Delete the current chat session"""
        
        if st.session_state.current_chat_session:
            self.delete_chat_session(st.session_state.current_chat_session.id)
    
    def quick_start_chat(self, initial_message: str):
        """Start a new chat with an initial message"""
        
        self.create_new_chat_session()
        self.handle_user_message(initial_message)
    
    def add_quick_message(self, message: str):
        """Add a quick message to current chat"""
        
        if st.session_state.current_chat_session:
            self.handle_user_message(message)
        else:
            self.quick_start_chat(message)
    
    def handle_user_message(self, message: str):
        """Handle user message and get AI response"""
        
        if not st.session_state.current_chat_session:
            return
        
        session = st.session_state.current_chat_session
        
        # Add user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=message,
            timestamp=datetime.now().isoformat(),
            message_type="text",
            metadata={}
        )
        
        session.messages.append(user_message)
        
        # Get project context
        project_context = self.gather_project_context()
        
        # Get AI response
        with st.spinner("Thinking..."):
            ai_response = self.chat_assistant.get_chat_response(
                message, session.messages, project_context
            )
        
        session.messages.append(ai_response)
        
        # Update session title if this is the first exchange
        if len(session.messages) == 2:  # User message + AI response
            session.title = self.chat_assistant.generate_conversation_title(session.messages)
        
        # Update session metadata
        session.last_updated = datetime.now().isoformat()
        
        # Increment input key to reset chat input
        st.session_state.chat_input_key += 1
        
        st.rerun()
    
    def gather_project_context(self) -> Dict[str, Any]:
        """Gather available project context for AI"""
        
        context = {}
        
        # Add analysis results
        if hasattr(st.session_state, 'analysis_results'):
            context['analysis_results'] = st.session_state.analysis_results
        
        # Add user stories
        if hasattr(st.session_state, 'user_stories'):
            context['user_stories'] = st.session_state.user_stories
        
        # Add technical designs
        if hasattr(st.session_state, 'technical_designs'):
            context['technical_designs'] = st.session_state.technical_designs
        
        return context
    
    def show_rename_dialog(self):
        """Show rename dialog (placeholder)"""
        st.info("🚧 Rename functionality coming soon!")


# Main render function for integration
def render_chat_assistant_tab():
    """Main function to render the Chat Assistant tab"""
    
    try:
        ui = ChatUI()
        ui.render()
    
    except Exception as e:
        st.error(f"❌ Error loading Chat Assistant module: {str(e)}")
        logger.error(f"Chat Assistant UI error: {e}")
        
        # Fallback UI
        st.markdown("### 💬 AI Project Chat Assistant")
        st.info("🚧 This feature is currently being set up. Please try again later.")
