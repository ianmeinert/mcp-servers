"""
PII (Personally Identifiable Information) Handler Server

This server provides functionality to detect, mask, and restore PII in text.
It uses SQLite for storing PII mappings and provides an MCP interface for integration
with Claude.ai desktop.

Features:
- Detects common PII types (names, addresses, contact info, etc.)
- Masks PII with standardized placeholders
- Restores original PII values
- Maintains text structure and formatting
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("PIIHandler")

# Database configuration
DB_PATH = "pii_mappings.db"

@dataclass
class PIIPattern:
    """Configuration for a PII detection pattern"""
    pattern: str
    label: str
    description: str

class PIIDatabase:
    """Handles all database operations for PII mappings"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for storing PII mappings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS pii_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masked_value TEXT NOT NULL,
                original_value TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def clear_mappings(self) -> None:
        """Clear all existing PII mappings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM pii_mappings")
        conn.commit()
        conn.close()
    
    def store_mapping(self, masked: str, original: str, pii_type: str) -> None:
        """Store a new PII mapping"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO pii_mappings (masked_value, original_value, pii_type) VALUES (?, ?, ?)",
            (masked, original, pii_type)
        )
        conn.commit()
        conn.close()
    
    def get_mappings(self) -> Dict[str, str]:
        """Retrieve all PII mappings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT masked_value, original_value FROM pii_mappings ORDER BY created_at DESC")
        mappings = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return mappings

class PIIHandler:
    """Handles PII detection, masking, and restoration"""
    
    def __init__(self):
        self.db = PIIDatabase(DB_PATH)
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, PIIPattern]:
        """Initialize PII detection patterns"""
        return {
            'name': PIIPattern(
                pattern=r'(?:Name:\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                label='Name:',
                description='Full names with proper capitalization'
            ),
            'address': PIIPattern(
                pattern=r'(?:Address:\s*)?(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl))',
                label='Address:',
                description='Street addresses with number and street name'
            ),
            'city_state_zip': PIIPattern(
                pattern=r'(?:City,\s*State,\s*Zip:\s*)?([A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)',
                label='City, State, Zip:',
                description='City, state, and ZIP code combinations'
            ),
            'email': PIIPattern(
                pattern=r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                label='Email:',
                description='Email addresses'
            ),
            'phone': PIIPattern(
                pattern=r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                label='Phone:',
                description='Phone numbers in various formats'
            ),
            'credit_card': PIIPattern(
                pattern=r'\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}',
                label='Credit Card Number:',
                description='Credit card numbers'
            )
        }
    
    def _process_line(self, line: str, operation: str) -> str:
        """
        Process a single line of text for PII handling
        
        Args:
            line: The line of text to process
            operation: Either 'mask' or 'restore'
        
        Returns:
            The processed line
        """
        if not line.strip():
            return line
            
        if operation == 'mask':
            return self._mask_line(line)
        else:
            return self._restore_line(line)
    
    def _mask_line(self, line: str) -> str:
        """Mask PII in a single line"""
        current_line = line
        
        for pii_type, pattern_config in self.patterns.items():
            if pattern_config.label in current_line:
                matches = re.finditer(pattern_config.pattern, current_line, re.IGNORECASE)
                for match in matches:
                    original = match.group(1) if match.groups() else match.group(0)
                    masked = f"[{pii_type.upper()}]"
                    
                    if original in current_line:
                        current_line = current_line.replace(original, masked)
                        self.db.store_mapping(masked, original, pii_type)
        
        return current_line
    
    def _restore_line(self, line: str) -> str:
        """Restore PII in a single line"""
        current_line = line
        mappings = self.db.get_mappings()
        
        for masked, original in mappings.items():
            if masked in current_line:
                current_line = current_line.replace(masked, original)
        
        return current_line

# Initialize the PII handler
pii_handler = PIIHandler()

@mcp.tool()
def sanitize_input(text: str) -> str:
    """
    Sanitize input text by masking PII.
    
    Args:
        text (str): Input text containing PII
    
    Returns:
        str: Text with PII masked
    """
    pii_handler.db.clear_mappings()
    lines = text.split('\n')
    processed_lines = [pii_handler._process_line(line, 'mask') for line in lines]
    return '\n'.join(processed_lines)

@mcp.tool()
def restore_pii(text: str) -> str:
    """
    Restore original PII values in the text.
    
    Args:
        text (str): Text with masked PII
    
    Returns:
        str: Text with original PII values restored
    """
    lines = text.split('\n')
    processed_lines = [pii_handler._process_line(line, 'restore') for line in lines]
    return '\n'.join(processed_lines)

@mcp.tool()
def process_with_pii(text: str) -> str:
    """
    Process text with PII handling: sanitize, process, and restore PII.
    
    This function:
    1. Sanitizes the input text to mask PII
    2. Processes the sanitized text
    3. Restores the original PII values in the response
    
    Args:
        text (str): The input text containing PII
    
    Returns:
        str: The processed text with original PII values restored
    """
    # Step 1: Sanitize the input
    sanitized_text = sanitize_input(text)
    
    # Step 2: Process the text (placeholder for actual processing)
    processed_text = sanitized_text
    
    # Step 3: Restore PII in the response
    restored_text = restore_pii(processed_text)
    
    return restored_text

if __name__ == "__main__":
    # Test the PII handling
    test_text = """
    Name: John Doe 
    Address: 123 Someplace Dr 
    City, State, Zip: Somewhere, DC 12345 
    Phone: (123) 456-7890 
    Email: me@myemail.com 
    Credit Card Number: 1234 5678 9012 3456
    """
    
    print("\nOriginal text:")
    print(test_text) 
    
    # Step 1: Sanitize the input
    sanitized_text = sanitize_input(test_text)
    print("\nSanitized text:")
    print(sanitized_text)
    
    # Step 2: Restore PII in the response
    restored_text = restore_pii(sanitized_text)
    print("\nProcessed text with PII handling:")
    print(restored_text)
    
    # Start the MCP server
    mcp.run(transport="stdio") 