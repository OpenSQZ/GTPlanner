import asyncio
import json
import os
from datetime import datetime

async def store_conversation_async(conversation_turn, history=None):
    """
    Asynchronously stores a conversation turn and updates the conversation history.
    
    Args:
        conversation_turn (dict): The current conversation turn with 'role' and 'content'
        history (list, optional): Existing conversation history
        
    Returns:
        list: Updated conversation history
    """
    if history is None:
        history = []
    
    # Validate the conversation turn format
    if not isinstance(conversation_turn, dict) or 'role' not in conversation_turn or 'content' not in conversation_turn:
        raise ValueError("Conversation turn must be a dict with 'role' and 'content' keys")
    
    # Validate the role
    if conversation_turn['role'] not in ['user', 'assistant', 'system']:
        raise ValueError("Role must be one of: 'user', 'assistant', 'system'")
    
    # Add timestamp to the turn
    conversation_turn['timestamp'] = datetime.now().isoformat()
    
    # Append the turn to history
    history.append(conversation_turn)
    
    # Simulate async processing
    await asyncio.sleep(0.01)
    
    return history

async def save_conversation_to_file_async(history, filename="conversation_history.json"):
    """
    Asynchronously saves the conversation history to a file.
    
    Args:
        history (list): Conversation history to save
        filename (str, optional): Path to save the conversation history
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        # Simulate async processing
        await asyncio.sleep(0.01)
        
        return True
    except Exception as e:
        print(f"Error saving conversation history: {e}")
        return False

async def load_conversation_from_file_async(filename="conversation_history.json"):
    """
    Asynchronously loads conversation history from a file.
    
    Args:
        filename (str, optional): Path to the conversation history file
        
    Returns:
        list: Loaded conversation history or empty list if file doesn't exist
    """
    try:
        if not os.path.exists(filename):
            return []
        
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # Simulate async processing
        await asyncio.sleep(0.01)
        
        return history
    except Exception as e:
        print(f"Error loading conversation history: {e}")
        return []

# Synchronous versions for backward compatibility
def store_conversation(conversation_turn, history=None):
    """Synchronous wrapper for store_conversation_async"""
    return asyncio.run(store_conversation_async(conversation_turn, history))

def save_conversation_to_file(history, filename="conversation_history.json"):
    """Synchronous wrapper for save_conversation_to_file_async"""
    return asyncio.run(save_conversation_to_file_async(history, filename))

def load_conversation_from_file(filename="conversation_history.json"):
    """Synchronous wrapper for load_conversation_from_file_async"""
    return asyncio.run(load_conversation_from_file_async(filename))

# Example usage
if __name__ == "__main__":
    async def test():
        # Create a new conversation
        history = []
        
        # Add a system message
        history = await store_conversation_async({
            "role": "system",
            "content": "You are a helpful assistant."
        }, history)
        
        # Add a user message
        history = await store_conversation_async({
            "role": "user",
            "content": "What can you do to help me with project requirements?"
        }, history)
        
        # Add an assistant message
        history = await store_conversation_async({
            "role": "assistant",
            "content": "I can help analyze your requirements, suggest optimizations, and generate technical documentation."
        }, history)
        
        # Save the conversation
        success = await save_conversation_to_file_async(history, "example_conversation.json")
        print(f"Conversation saved: {success}")
        
        # Load the conversation
        loaded_history = await load_conversation_from_file_async("example_conversation.json")
        print(f"Loaded {len(loaded_history)} conversation turns")
    
    asyncio.run(test()) 