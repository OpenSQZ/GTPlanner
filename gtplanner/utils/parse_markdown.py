import re
import asyncio

async def parse_markdown_async(markdown_content):
    """
    Asynchronously parses markdown content into a structured format.
    
    Args:
        markdown_content (str): Raw markdown text
        
    Returns:
        dict: Structured representation of the markdown content
    """
    # This is a simplified parser that extracts headers and content
    result = {
        "headers": [],
        "sections": {},
        "lists": [],
        "codeblocks": []
    }
    
    # Extract headers
    header_pattern = r'^(#{1,6})\s+(.+)$'
    for line in markdown_content.split('\n'):
        header_match = re.match(header_pattern, line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            result["headers"].append({"level": level, "text": text})
    
    # Extract sections (content between headers)
    lines = markdown_content.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        header_match = re.match(header_pattern, line)
        if header_match:
            # If we were building a section, save it
            if current_section:
                result["sections"][current_section] = '\n'.join(section_content)
            
            # Start a new section
            current_section = header_match.group(2).strip()
            section_content = []
        elif current_section:
            section_content.append(line)
    
    # Save the last section if any
    if current_section:
        result["sections"][current_section] = '\n'.join(section_content)
    
    # Extract lists
    list_pattern = r'^\s*[-*+]\s+(.+)$'
    current_list = []
    
    for line in lines:
        list_match = re.match(list_pattern, line)
        if list_match:
            current_list.append(list_match.group(1).strip())
        elif current_list and line.strip() == '':
            if current_list:
                result["lists"].append(current_list)
                current_list = []
    
    # Add the last list if any
    if current_list:
        result["lists"].append(current_list)
    
    # Extract code blocks
    code_pattern = r'```(.+?)```'
    code_blocks = re.findall(code_pattern, markdown_content, re.DOTALL)
    result["codeblocks"] = code_blocks
    
    # Simulate async processing
    await asyncio.sleep(0.01)
    
    return result

# Synchronous version for backward compatibility
def parse_markdown(markdown_content):
    """Synchronous wrapper for parse_markdown_async"""
    return asyncio.run(parse_markdown_async(markdown_content))

# Example usage
if __name__ == "__main__":
    async def test():
        md_content = """
# Sample Document

This is a sample markdown document.

## Section 1

- Item 1
- Item 2
- Item 3

## Section 2

```python
def hello_world():
    print("Hello, World!")
```
"""
        result = await parse_markdown_async(md_content)
        print(result)
    
    asyncio.run(test()) 