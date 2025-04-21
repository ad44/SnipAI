"""
LLM service module for the Contexta application.
Handles LangChain setup and interaction with Groq API using the Llama3 model.
"""
import logging
import time
import os
import ssl
import urllib3
import httpx  # Import httpx
from operator import itemgetter

# Disable SSL warnings since we're disabling verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory

import config

# Configure logging
logger = logging.getLogger(__name__)

# Configure SSL environment variable - disable verification
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['SSL_CERT_FILE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Create a custom SSL context that accepts any certificate
# This might still be needed for other underlying libraries
ssl._create_default_https_context = ssl._create_unverified_context

class GroqLLMService:
    """
    Service for interacting with Groq API via LangChain.
    """
    
    def __init__(self, api_key, model_name):
        """
        Initialize the Groq LLM service.
        
        Args:
            api_key (str): Groq API key.
            model_name (str): Name of the Groq model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        
        logger.info(f"Initializing GroqLLMService with model: {model_name}")

        # Create an insecure httpx client
        # This is the primary method to disable SSL for ChatGroq
        insecure_client = httpx.Client(verify=False)

        # Initialize the LLM, passing the insecure httpx client
        # Removed the groq_api_base parameter which caused the URL duplication
        self.llm = ChatGroq(
            api_key=api_key,
            model_name=model_name,
            temperature=0.7,
            http_client=insecure_client
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Create prompt template
        # Get system prompt directly as plain text (not as a template with variables)
        system_prompt_text = config.get_system_prompt()
        # Create system message directly without specifying format
        system_prompt = SystemMessagePromptTemplate.from_template(system_prompt_text)
        human_prompt = HumanMessagePromptTemplate.from_template("{human_input}")
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            human_prompt
        ])
        
        # Create LangChain chain using LCEL
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=RunnableLambda(self.memory.load_memory_variables) | itemgetter("chat_history")
            )
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        logger.info("GroqLLMService initialized successfully")
    
    def invoke_chain(self, user_input):
        """
        Invoke the LangChain chain with user input.
        
        Args:
            user_input (str): User message text.
            
        Returns:
            str: AI response text.
        """
        try:
            logger.info(f"Invoking LLM with user input ({len(user_input)} chars)")
            
            # Simply invoke the chain directly
            ai_response = self.chain.invoke({"human_input": user_input})
            
            # Check if response is empty or None
            if not ai_response or ai_response.strip() == "":
                raise Exception("No response received from LLM service")
            
            # Save context to memory
            self.memory.save_context(
                {"human_input": user_input},
                {"output": ai_response}
            )
            
            logger.info(f"LLM response received ({len(ai_response)} chars)")
            return ai_response
            
        except Exception as e:
            error_msg = f"Error invoking LLM: {str(e)}"
            logger.error(error_msg)
            
            # Check for common API key related errors
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str or "auth" in error_str:
                return "API_KEY_ERROR: Your API key appears to be invalid or has expired. Please check your API key in the settings."
            elif "timeout" in error_str or "connection" in error_str or "network" in error_str:
                return "CONNECTION_ERROR: Unable to connect to the LLM service. Please check your internet connection."
            elif "no response" in error_str:
                return "NO_RESPONSE_ERROR: No response received from the LLM service. The service might be experiencing high load."
            else:
                return f"ERROR: {str(e)}\n\nPlease try again in a moment."
    
    def prepare_initial_conversation(self, selected_text):
        """
        Prepare the initial conversation with selected text.
        
        Args:
            selected_text (str): Text selected by the user.
            
        Returns:
            str: Initial AI response.
        """
        # Clear any existing memory
        self.memory.clear()
        
        # Format the initial user message
        initial_prompt_template = config.get_initial_user_prompt_template()
        initial_prompt = initial_prompt_template.format(selected_text=selected_text)
        
        logger.info("Preparing initial conversation with selected text")
        return self.invoke_chain(initial_prompt)

# Test function for when this module is run directly
def test_llm_service():
    """
    Test function to run when this module is executed directly.
    Tests the connection to Groq API and runs a simple conversation.
    """
    import os
    import time
    from dotenv import load_dotenv
    
    # Configure logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load environment variables
    load_dotenv()
    
    # Get API key and model name
    api_key = os.environ.get("GROQ_API_KEY", "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")
    model_name = "llama-3.3-70b-versatile"
    
    print("\n⚠️ SSL VERIFICATION IS COMPLETELY DISABLED - THIS IS INSECURE ⚠️")
    print("This configuration should only be used for testing purposes.")
    
    # Sample text for testing
    sample_text = """The function of education is to teach one to think intensively and to think critically. 
    Intelligence plus character - that is the goal of true education. - Martin Luther King Jr."""
    
    print("Initializing GroqLLMService...")
    llm_service = GroqLLMService(api_key, model_name)
    
    try:
        print("\nTesting initial conversation with sample text...")
        print(f"Sample text: {sample_text}\n")
        
        print("Waiting for response...")
        start = time.time()
        response = llm_service.prepare_initial_conversation(sample_text)
        elapsed = time.time() - start
        
        print(f"\nResponse received in {elapsed:.2f} seconds:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        # Test follow-up question
        follow_up = "Can you explain more about critical thinking?"
        print(f"\nSending follow-up: '{follow_up}'")
        
        start = time.time()
        response2 = llm_service.invoke_chain(follow_up)
        elapsed = time.time() - start
        
        print(f"\nResponse received in {elapsed:.2f} seconds:")
        print("-" * 50)
        print(response2)
        print("-" * 50)
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()

# Run test if this file is executed directly
if __name__ == "__main__":
    test_llm_service()