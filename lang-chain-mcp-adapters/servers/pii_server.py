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
- Complete PII processing flow with sanitization and restoration
"""

import re
import sqlite3
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    priority: int = 0  # Higher priority patterns are checked first

class PIIDatabase:
    """Handles all database operations for PII mappings"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for storing PII mappings"""
        # Check if database exists
        db_exists = os.path.exists(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Create the table if it doesn't exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS pii_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masked_value TEXT NOT NULL,
                    original_value TEXT NOT NULL,
                    pii_type TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    UNIQUE(masked_value, session_id)
                )
            ''')
            
            # If database existed, check for missing columns and add them
            if db_exists:
                # Get existing columns
                c.execute("PRAGMA table_info(pii_mappings)")
                existing_columns = {row[1] for row in c.fetchall()}
                
                # Add missing columns if needed
                if 'context' not in existing_columns:
                    c.execute("ALTER TABLE pii_mappings ADD COLUMN context TEXT")
                if 'session_id' not in existing_columns:
                    c.execute("ALTER TABLE pii_mappings ADD COLUMN session_id TEXT")
                
                # Add unique constraint if it doesn't exist
                try:
                    c.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_masked_session 
                        ON pii_mappings(masked_value, session_id)
                    """)
                except sqlite3.OperationalError:
                    # Index might already exist
                    pass
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
        finally:
            conn.close()
    
    def clear_mappings(self, session_id: Optional[str] = None) -> None:
        """Clear PII mappings, optionally for a specific session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if session_id:
                c.execute("DELETE FROM pii_mappings WHERE session_id = ?", (session_id,))
            else:
                c.execute("DELETE FROM pii_mappings")
            conn.commit()
        except Exception as e:
            logger.error(f"Error clearing mappings: {str(e)}")
            raise
        finally:
            conn.close()
    
    def store_mapping(self, masked: str, original: str, pii_type: str, context: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """Store a new PII mapping"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """INSERT INTO pii_mappings 
                   (masked_value, original_value, pii_type, context, session_id) 
                   VALUES (?, ?, ?, ?, ?)""",
                (masked, original, pii_type, context, session_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate mapping detected for {masked}")
        except Exception as e:
            logger.error(f"Error storing mapping: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_mappings(self, session_id: Optional[str] = None) -> Dict[str, str]:
        """Retrieve PII mappings, optionally for a specific session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if session_id:
                c.execute(
                    "SELECT masked_value, original_value FROM pii_mappings WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,)
                )
            else:
                c.execute("SELECT masked_value, original_value FROM pii_mappings ORDER BY created_at DESC")
            mappings = {row[0]: row[1] for row in c.fetchall()}
            return mappings
        except Exception as e:
            logger.error(f"Error retrieving mappings: {str(e)}")
            raise
        finally:
            conn.close()

class PIIHandler:
    """Handles PII detection, masking, and restoration"""
    
    def __init__(self):
        self.db = PIIDatabase(DB_PATH)
        self.patterns = self._init_patterns()
        self.current_session_id = None
    
    def _init_patterns(self) -> Dict[str, PIIPattern]:
        """Initialize PII detection patterns with priorities"""
        return {
            'credit_card': PIIPattern(
                pattern=r'(?:Credit Card Number:?\s*)(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})',
                label='Credit Card Number:',
                description='Credit card numbers',
                priority=100
            ),
            'ssn': PIIPattern(
                pattern=r'(?:SSN:?\s*)(\d{3}[-\s]?\d{2}[-\s]?\d{4})',
                label='SSN:',
                description='Social Security Numbers',
                priority=90
            ),
            'email': PIIPattern(
                pattern=r'(?:Email:?\s*)([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                label='Email:',
                description='Email addresses',
                priority=80
            ),
            'phone': PIIPattern(
                pattern=r'(?:Phone:?\s*)((?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
                label='Phone:',
                description='Phone numbers in various formats',
                priority=70
            ),
            'name': PIIPattern(
                pattern=r'(?:Name:?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                label='Name:',
                description='Full names with proper capitalization',
                priority=60
            ),
            'address': PIIPattern(
                pattern=r'(?:Address:?\s*)(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl))',
                label='Address:',
                description='Street addresses with number and street name',
                priority=50
            ),
            'city_state_zip': PIIPattern(
                pattern=r'(?:City,\s*State,\s*Zip:?\s*)([A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)',
                label='City, State, Zip:',
                description='City, state, and ZIP code combinations',
                priority=40
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
        
        # Sort patterns by priority (highest first)
        sorted_patterns = sorted(self.patterns.items(), key=lambda x: x[1].priority, reverse=True)
        
        for pii_type, pattern_config in sorted_patterns:
            matches = re.finditer(pattern_config.pattern, current_line, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    original = match.group(1)
                    # Keep the label but mask the value
                    masked = f"{pattern_config.label} [MASKED_{pii_type.upper()}]"
                    current_line = current_line.replace(match.group(0), masked)
                    self.db.store_mapping(
                        masked, 
                        original, 
                        pii_type,
                        context=line.strip(),
                        session_id=self.current_session_id
                    )
        
        return current_line
    
    def _restore_line(self, line: str) -> str:
        """Restore PII in a single line"""
        current_line = line
        mappings = self.db.get_mappings(session_id=self.current_session_id)
        
        for masked, original in mappings.items():
            if masked in current_line:
                current_line = current_line.replace(masked, original)
        
        return current_line

# Initialize the PII handler
pii_handler = PIIHandler()

@mcp.tool()
def sanitize_input(text: str, session_id: Optional[str] = None) -> str:
    """
    Sanitize input text by masking PII.
    
    Args:
        text (str): Input text containing PII
        session_id (str, optional): Session identifier for tracking PII mappings
    
    Returns:
        str: Text with PII masked
    """
    try:
        pii_handler.current_session_id = session_id
        pii_handler.db.clear_mappings(session_id)
        lines = text.split('\n')
        processed_lines = [pii_handler._process_line(line, 'mask') for line in lines]
        return '\n'.join(processed_lines)
    except Exception as e:
        logger.error(f"Error in sanitize_input: {str(e)}")
        raise

@mcp.tool()
def restore_pii(text: str, session_id: Optional[str] = None) -> str:
    """
    Restore original PII values in the text.
    
    Args:
        text (str): Text with masked PII
        session_id (str, optional): Session identifier for retrieving PII mappings
    
    Returns:
        str: Text with original PII values restored
    """
    try:
        pii_handler.current_session_id = session_id
        lines = text.split('\n')
        processed_lines = [pii_handler._process_line(line, 'restore') for line in lines]
        return '\n'.join(processed_lines)
    except Exception as e:
        logger.error(f"Error in restore_pii: {str(e)}")
        raise

@mcp.tool()
def process_with_pii(text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process text with PII handling: sanitize, process, and restore PII.
    
    This function:
    1. Sanitizes the input text to mask PII
    2. Processes the sanitized text
    3. Restores the original PII values in the response
    
    Args:
        text (str): The input text containing PII
        session_id (str, optional): Session identifier for tracking PII mappings
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - sanitized_text: The text with PII masked
            - processed_text: The processed text (currently same as sanitized)
            - restored_text: The final text with PII restored
    """
    try:
        # Step 1: Sanitize the input
        sanitized_text = sanitize_input(text, session_id)
        
        # Step 2: Process the text (placeholder for actual processing)
        processed_text = sanitized_text
        
        # Step 3: Restore PII in the response
        restored_text = restore_pii(processed_text, session_id)
        
        return {
            "sanitized_text": sanitized_text,
            "processed_text": processed_text,
            "restored_text": restored_text
        }
    except Exception as e:
        logger.error(f"Error in process_with_pii: {str(e)}")
        raise

if __name__ == "__main__":
    # Test the PII handling
    test_text = """
    Name: John Doe 
    Address: 123 Someplace Dr 
    City, State, Zip: Somewhere, DC 12345 
    Phone: (123) 456-7890 
    Email: me@myemail.com 
    Credit Card Number: 1234 5678 9012 3456
    SSN: 123-45-6789
    """
    
    print("\nOriginal text:")
    print(test_text) 
    
    # Test with session tracking
    session_id = "test_session_123"
    
    # Step 1: Sanitize the input
    sanitized_text = sanitize_input(test_text, session_id)
    print("\nSanitized text:")
    print(sanitized_text)
    
    # Step 2: Restore PII in the response
    restored_text = restore_pii(sanitized_text, session_id)
    print("\nProcessed text with PII handling:")
    print(restored_text)
    
    # Start the MCP server
    mcp.run(transport="stdio") 