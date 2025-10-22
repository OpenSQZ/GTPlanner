import asyncio
import os
from datetime import datetime

async def format_documentation_async(content_dict):
    """
    Asynchronously formats the documentation content according to industry standards.
    
    Args:
        content_dict (dict): Dictionary containing documentation content sections
        
    Returns:
        str: Formatted documentation as a string
    """
    # Header section
    header = f"""# Technical Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    # Requirements section
    requirements = "## Requirements\n\n"
    
    if "functional" in content_dict.get("requirements", {}):
        requirements += "### Functional Requirements\n\n"
        for i, req in enumerate(content_dict["requirements"]["functional"], 1):
            requirements += f"{i}. {req}\n"
        requirements += "\n"
    
    if "non_functional" in content_dict.get("requirements", {}):
        requirements += "### Non-Functional Requirements\n\n"
        for i, req in enumerate(content_dict["requirements"]["non_functional"], 1):
            requirements += f"{i}. {req}\n"
        requirements += "\n"
    
    if "constraints" in content_dict.get("requirements", {}):
        requirements += "### Constraints\n\n"
        for i, req in enumerate(content_dict["requirements"]["constraints"], 1):
            requirements += f"{i}. {req}\n"
        requirements += "\n"
    
    # Optimizations section
    optimizations = "## Design Optimizations\n\n"
    for i, opt in enumerate(content_dict.get("optimizations", []), 1):
        optimizations += f"{i}. {opt}\n"
    optimizations += "\n"
    
    # Additional sections
    implementation = "## Implementation Notes\n\n"
    if "implementation_notes" in content_dict:
        implementation += content_dict["implementation_notes"]
    else:
        implementation += "No implementation notes provided.\n"
    implementation += "\n"
    
    conclusion = "## Conclusion\n\n"
    if "conclusion" in content_dict:
        conclusion += content_dict["conclusion"]
    else:
        conclusion += "This document outlines the technical requirements and design optimizations for the project.\n"
    conclusion += "\n"
    
    # Combine all sections
    full_documentation = header + requirements + optimizations + implementation + conclusion
    
    # Simulate async processing
    await asyncio.sleep(0.01)
    
    return full_documentation

# Synchronous version for backward compatibility
def format_documentation(content_dict):
    """Synchronous wrapper for format_documentation_async"""
    return asyncio.run(format_documentation_async(content_dict))

# Example usage
if __name__ == "__main__":
    async def test():
        content = {
            "requirements": {
                "functional": [
                    "User authentication system",
                    "Data storage and retrieval",
                    "Reporting functionality"
                ],
                "non_functional": [
                    "99.9% uptime",
                    "Response time under 200ms",
                    "Secure data storage"
                ],
                "constraints": [
                    "Must use existing database",
                    "Budget limitations"
                ]
            },
            "optimizations": [
                "Implement caching for frequent queries",
                "Use asynchronous processing for long-running tasks",
                "Optimize database schema for read performance"
            ]
        }
        
        formatted_doc = await format_documentation_async(content)
        print(formatted_doc)
        
        # Optionally save to file
        with open("example_documentation.md", "w") as f:
            f.write(formatted_doc)
    
    asyncio.run(test()) 