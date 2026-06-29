"""
Quick CLI test for Agent Brain
"""
from app.rag_engine import RAGEngine
from app.agent import get_agent

def main():
    print("🚀 Initializing DocuMind Agent...")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    print("✅ RAG Engine ready")
    
    # Get agent instance
    agent = get_agent(rag_engine)
    print("✅ Agent Brain ready")
    
    print("\n" + "="*60)
    print("🤖 DocuMind Agent - CLI Test Mode")
    print("Type 'quit' to exit")
    print("="*60 + "\n")
    
    while True:
        # Get user input
        query = input("👤 You: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not query:
            continue
        
        print("\n🤖 Agent thinking...")
        
        # Test queries
        if "calculate" in query.lower() or any(op in query for op in ['+', '-', '*', '/']):
            print("🧮 Using calculator tool...")
        elif "search" in query.lower() or "web" in query.lower():
            print("🌐 Using web search tool...")
        else:
            print("🔍 Using RAG search tool...")
        
        # Call agent
        try:
            result = agent.chat(query=query, history=[])
            
            # Display thoughts
            if result['thoughts']:
                print("\n💭 Agent's Thoughts:")
                for thought in result['thoughts']:
                    print(f"   → {thought['content']}")
            
            # Display final answer
            print(f"\n✅ Final Answer:\n{result['final_answer']}")
            print("\n" + "-"*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n" + "-"*60 + "\n")

if __name__ == "__main__":
    main()