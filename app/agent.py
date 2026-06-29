"""
Agentic RAG system for DocuMind.

WHY: Extends the basic RAG system with autonomous decision-making capabilities.
The agent can choose between searching private documents, web search, or calculations
based on the user's query, providing more flexible and intelligent responses.
"""

from typing import Generator, List, Dict, Any, Optional
import re
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import SystemMessage
from config.settings import get_settings
from app.rag_engine import RAGEngine


def simple_calculator(expression: str) -> str:
    """
    Safe mathematical expression evaluator.

    Args:
        expression: Mathematical expression as string

    Returns:
        Result of calculation or error message
    """
    try:
        # Only allow safe characters: digits, operators, parentheses, decimals, spaces
        if not re.match(r'^[\d+\-*/().\s]+$', expression):
            return "Error: Invalid characters in expression"

        # Evaluate safely
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def get_rag_search_tool(rag_engine: RAGEngine) -> Tool:
    """
    Creates a LangChain Tool for searching through uploaded private documents.

    WHY: Wraps the existing RAGEngine.query() method to make it available
    as a LangChain tool that the agent can invoke autonomously.
    """
    def rag_search_func(query: str) -> str:
        """Execute the RAG search and return formatted context."""
        print(f"🔍 [RAG Search] Query: {query}")
        chunks = rag_engine.query(
            user_query=query,
            top_k=5,
            use_reranker=True
        )

        if not chunks:
            return "No relevant documents found in the knowledge base."

        # Format chunks for the LLM
        result = "Relevant document excerpts:\n\n"
        for i, chunk in enumerate(chunks, 1):
            result += f"[{i}] {chunk}\n\n"

        print(f"✅ [RAG Search] Found {len(chunks)} relevant chunks")
        return result

    return Tool(
        name="rag_search",
        func=rag_search_func,
        description="Use this to search through uploaded private documents (PDFs, resumes) for specific information. Use this when the user asks about their uploaded documents, resume, or any content they have provided."
    )


def get_web_search_tool() -> Tool:
    """
    Creates a web search tool using DuckDuckGo.

    WHY: Provides real-time information access for current events and facts
    not contained in the uploaded documents.

    Returns:
        LangChain Tool for web search
    """
    search = DuckDuckGoSearchResults(max_results=5)
    print("✅ Using DuckDuckGo for web search")
    
    return Tool(
        name="web_search",
        func=search.run,
        description="Use this to search the internet for real-time information, current events, news, or facts not in the uploaded documents. Use this for questions about current prices, recent events, or general knowledge."
    )


def get_calculator_tool() -> Tool:
    """
    Creates a calculator tool for mathematical operations.

    WHY: Enables the agent to perform accurate mathematical calculations
    instead of relying on the LLM's potentially unreliable arithmetic.

    Returns:
        LangChain Tool for calculations
    """
    return Tool(
        name="calculator",
        func=simple_calculator,
        description="Use this to perform mathematical calculations. Accepts expressions like '2 + 2', '10 * 5', '(3 + 7) / 2', '100 / 7'."
    )


class AgentBrain:
    """
    Main agent orchestrator using LangGraph ReAct pattern.

    WHY: Encapsulates the agent creation, tool management, and execution logic.
    Uses the ReAct (Reason + Act) pattern for transparent decision-making.
    """

    # System prompt for the agent
    SYSTEM_PROMPT = """You are DocuMind Agent, an intelligent AI assistant that helps users by choosing the right tools to answer their questions.

**Available Tools:**
You have access to these tools (use ONLY these):
1. **rag_search** - Search through uploaded private documents (PDFs, resumes)
2. **calculator** - Perform mathematical calculations

**IMPORTANT:** Do NOT attempt to use tools that are not listed above. If you need information that requires web search, politely inform the user that you don't have access to real-time internet data.

**Decision Making Rules:**
- If the user asks about their uploaded documents, resume, or provided content → use `rag_search`
- If the user asks a mathematical question → use `calculator`
- If the user asks about current events, news, prices, or general knowledge → politely say "I don't have access to real-time internet data. I can only search your uploaded documents or perform calculations."
- If the question requires multiple tools, use them one by one

**Response Guidelines:**
- Always explain your reasoning before using a tool
- Be concise and professional in your final answer
- If you cannot find relevant information in documents, say so clearly
- Do not make up information - only use what the tools provide
- If a tool returns no results, inform the user honestly

Begin!"""

    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the agent with tools and LLM.

        Args:
            rag_engine: Initialized RAGEngine instance for document search
        """
        self.rag_engine = rag_engine
        self.settings = get_settings()

        # Initialize tools as proper LangChain Tools
        self.tools = [
            get_rag_search_tool(rag_engine),
            # get_web_search_tool(),
            get_calculator_tool()
        ]

        # Initialize LLM with Groq
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=self.settings.GROQ_API_KEY,
            temperature=0.1,  # Lower temperature for more deterministic tool selection
        )

        # Create the ReAct agent using LangGraph prebuilt (LangGraph 1.2.6 syntax)
        # Note: prompt parameter removed - we'll use system message in invoke()
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )

        print("✅ Agent Brain initialized with 3 tools: RAG Search, Web Search, Calculator")

    def _extract_thoughts_and_answer(self, output: dict) -> tuple[list, str]:
        """
        Extract intermediate thoughts and final answer from agent output.

        Args:
            output: Raw output from agent executor

        Returns:
            Tuple of (thoughts_list, final_answer)
        """
        final_answer = ""
        thoughts = []

        messages = output.get('messages', [])

        for msg in messages:
            msg_type = getattr(msg, 'type', None)
            content = getattr(msg, 'content', '')

            # Check if it's an AI message with tool calls (thoughts)
            if msg_type == 'ai':
                # Look for tool calls in additional_kwargs
                additional_kwargs = getattr(msg, 'additional_kwargs', {})
                tool_calls = additional_kwargs.get('tool_calls', [])

                for tool_call in tool_calls:
                    function_name = tool_call.get('function', {}).get('name', 'unknown')
                    thoughts.append({
                        'type': 'thought',
                        'content': f"I need to use {function_name} to find information."
                    })
                    thoughts.append({
                        'type': 'action',
                        'content': f"Using tool: {function_name}"
                    })

            # Check if it's a tool message (observation)
            elif msg_type == 'tool':
                observation_content = str(content)[:500]  # Truncate long observations
                thoughts.append({
                    'type': 'observation',
                    'content': observation_content
                })

            # Final answer is typically the last AI message without tool calls
            if msg_type == 'ai' and content:
                final_answer = content

        return thoughts, final_answer

    def chat(self, query: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a query through the agent and return response with thoughts.

        Args:
            query: User's question
            history: Optional conversation history

        Returns:
            Dictionary with thoughts, final_answer, and metadata
        """
        # Build context from history if provided
        context_query = query
        if history and len(history) > 0:
            # Append recent history to provide context
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-4:]
            ])
            context_query = f"Conversation history:\n{history_text}\n\nCurrent question: {query}"

        print(f"\n🤖 [Agent] Processing query: {query}")

        try:
            # Run the agent using LangGraph invoke with system message
            output = self.agent.invoke({
                "messages": [
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    ("user", context_query)
                ]
            })

            # Extract thoughts and answer
            thoughts, final_answer = self._extract_thoughts_and_answer(output)

            return {
                'thoughts': thoughts,
                'final_answer': final_answer,
                'success': True
            }

        except Exception as e:
            print(f"❌ [Agent] Error: {e}")
            return {
                'thoughts': [],
                'final_answer': f"Sorry, I encountered an error while processing your request: {str(e)}",
                'success': False
            }

    def chat_stream(self, query: str, history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming version of chat that yields thoughts and answer tokens.

        Args:
            query: User's question
            history: Optional conversation history

        Yields:
            Dictionary chunks with type indicator and content
        """
        # Build context from history if provided
        context_query = query
        if history and len(history) > 0:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-4:]
            ])
            context_query = f"Conversation history:\n{history_text}\n\nCurrent question: {query}"

        print(f"\n🤖 [Agent Streaming] Processing query: {query}")

        try:
            # Yield thinking start marker
            yield {'type': 'thinking_start', 'content': ''}

            # Run the agent with system message
            output = self.agent.invoke({
                "messages": [
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    ("user", context_query)
                ]
            })

            # Extract and yield thoughts
            thoughts, final_answer = self._extract_thoughts_and_answer(output)

            for thought in thoughts:
                yield {'type': 'thought', 'content': thought['content']}

            # Yield thinking end marker
            yield {'type': 'thinking_end', 'content': ''}

            # Stream the final answer word by word
            yield {'type': 'answer_start', 'content': ''}

            words = final_answer.split()
            for word in words:
                yield {'type': 'answer_token', 'content': word + ' '}

            yield {'type': 'answer_end', 'content': ''}
            yield {'type': 'done', 'content': ''}

        except Exception as e:
            print(f"❌ [Agent Streaming] Error: {e}")
            yield {'type': 'error', 'content': f"Error: {str(e)}"}
            yield {'type': 'done', 'content': ''}


# Global agent instance factory
_agent_instance: Optional[AgentBrain] = None


def get_agent(rag_engine: RAGEngine) -> AgentBrain:
    """
    Get or create the global agent instance.

    Args:
        rag_engine: Initialized RAGEngine instance

    Returns:
        AgentBrain instance
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentBrain(rag_engine)
    return _agent_instance