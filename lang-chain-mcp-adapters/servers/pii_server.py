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

import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Dict, Optional

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
    """Configuration for a PII detection pattern.

    Attributes:
        pattern: Regular expression pattern for detecting PII
        label: Label used to identify the type of PII
        description: Human-readable description of the PII type
        priority: Priority level for pattern matching (higher numbers checked first)
    """

    pattern: str
    label: str
    description: str
    priority: int = 0


class PIIDatabase:
    """Handles all database operations for PII mappings.

    This class manages the SQLite database that stores mappings between
    masked and original PII values, including their types and context.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize the PII database handler.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database for storing PII mappings.

        Creates the necessary table and indexes if they don't exist,
        and handles database schema updates for existing databases.

        Raises:
            sqlite3.Error: If database initialization fails
        """
        db_exists = os.path.exists(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            c.execute(
                """
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
                """
            )

            if db_exists:
                c.execute("PRAGMA table_info(pii_mappings)")
                existing_columns = {row[1] for row in c.fetchall()}

                if "context" not in existing_columns:
                    c.execute("ALTER TABLE pii_mappings ADD COLUMN context TEXT")
                if "session_id" not in existing_columns:
                    c.execute("ALTER TABLE pii_mappings ADD COLUMN session_id TEXT")

                try:
                    c.execute(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_masked_session 
                        ON pii_mappings(masked_value, session_id)
                        """
                    )
                except sqlite3.OperationalError:
                    pass

            conn.commit()
        except sqlite3.Error as e:
            logger.error("Error initializing database: %s", str(e))
            raise
        finally:
            conn.close()

    def clear_mappings(self, session_id: Optional[str] = None) -> None:
        """Clear PII mappings from the database.

        Args:
            session_id: If provided, only clear mappings for this session

        Raises:
            sqlite3.Error: If clearing mappings fails
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if session_id:
                c.execute(
                    "DELETE FROM pii_mappings WHERE session_id = ?", (session_id,)
                )
            else:
                c.execute("DELETE FROM pii_mappings")
            conn.commit()
        except sqlite3.Error as e:
            logger.error("Error clearing mappings: %s", str(e))
            raise
        finally:
            conn.close()

    def store_mapping(
        self,
        masked: str,
        original: str,
        pii_type: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Store a new PII mapping in the database.

        Args:
            masked: The masked version of the PII
            original: The original PII value
            pii_type: Type of PII (e.g., 'email', 'phone', 'credit_card')
            context: Additional context about the PII
            session_id: Session identifier for the mapping

        Raises:
            sqlite3.Error: If storing the mapping fails
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO pii_mappings 
                (masked_value, original_value, pii_type, context, session_id) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (masked, original, pii_type, context, session_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning("Duplicate mapping detected for %s", masked)
        except sqlite3.Error as e:
            logger.error("Error storing mapping: %s", str(e))
            raise
        finally:
            conn.close()

    def get_mappings(self, session_id: Optional[str] = None) -> Dict[str, str]:
        """Retrieve PII mappings from the database.

        Args:
            session_id: If provided, only retrieve mappings for this session

        Returns:
            Dictionary mapping masked values to original values

        Raises:
            sqlite3.Error: If retrieving mappings fails
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if session_id:
                c.execute(
                    """
                    SELECT masked_value, original_value 
                    FROM pii_mappings 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC
                    """,
                    (session_id,),
                )
            else:
                c.execute(
                    """
                    SELECT masked_value, original_value 
                    FROM pii_mappings 
                    ORDER BY created_at DESC
                    """
                )
            return {row[0]: row[1] for row in c.fetchall()}
        except sqlite3.Error as e:
            logger.error("Error retrieving mappings: %s", str(e))
            raise
        finally:
            conn.close()


class PIIHandler:
    """Handles PII detection, masking, and restoration.

    This class provides the core functionality for processing PII in text,
    including detection using regex patterns, masking with standardized
    placeholders, and restoration of original values.
    """

    def __init__(self) -> None:
        """Initialize the PII handler with database connection and detection patterns."""
        self.db = PIIDatabase(DB_PATH)
        self.patterns = self._init_patterns()
        self.current_session_id: Optional[str] = None

    def _init_patterns(self) -> Dict[str, PIIPattern]:
        """Initialize PII detection patterns with priorities.

        Returns:
            Dictionary of PII patterns with their configurations
        """
        return {
            "credit_card": PIIPattern(
                pattern=(
                    r"(?:Credit Card Number:?\s*)"
                    r"(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})"
                ),
                label="Credit Card Number:",
                description="Credit card numbers",
                priority=100,
            ),
            "ssn": PIIPattern(
                pattern=r"(?:SSN:?\s*)(\d{3}[-\s]?\d{2}[-\s]?\d{4})",
                label="SSN:",
                description="Social Security Numbers",
                priority=90,
            ),
            "email": PIIPattern(
                pattern=(
                    r"(?:Email:?\s*)"
                    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})"
                ),
                label="Email:",
                description="Email addresses",
                priority=80,
            ),
            "phone": PIIPattern(
                pattern=(
                    r"(?:Phone:?\s*)"
                    r"((?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
                ),
                label="Phone:",
                description="Phone numbers in various formats",
                priority=70,
            ),
            "name": PIIPattern(
                pattern=r"(?:Name:?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                label="Name:",
                description="Full names with proper capitalization",
                priority=60,
            ),
            "address": PIIPattern(
                pattern=(
                    r"(?:Address:?\s*)"
                    r"(\d+\s+[A-Za-z\s]+"
                    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
                    r"Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl))"
                ),
                label="Address:",
                description="Street addresses with number and street name",
                priority=50,
            ),
            "city_state_zip": PIIPattern(
                pattern=(
                    r"(?:City,\s*State,\s*Zip:?\s*)"
                    r"([A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)"
                ),
                label="City, State, Zip:",
                description="City, state, and ZIP code combinations",
                priority=40,
            ),
        }

    def process_line(self, line: str, operation: str) -> str:
        """Process a single line of text for PII handling.

        Args:
            line: The line of text to process
            operation: Either 'mask' or 'restore'

        Returns:
            The processed line
        """
        if not line.strip():
            return line

        if operation == "mask":
            return self._mask_line(line)
        return self._restore_line(line)

    def _mask_line(self, line: str) -> str:
        """Mask PII in a single line.

        Args:
            line: The line to process

        Returns:
            The line with PII masked
        """
        current_line = line
        sorted_patterns = sorted(
            self.patterns.items(), key=lambda x: x[1].priority, reverse=True
        )

        for pii_type, pattern_config in sorted_patterns:
            matches = re.finditer(pattern_config.pattern, current_line, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    original = match.group(1)
                    masked = f"{pattern_config.label} [MASKED_{pii_type.upper()}]"
                    current_line = current_line.replace(match.group(0), masked)
                    self.db.store_mapping(
                        masked,
                        original,
                        pii_type,
                        context=line.strip(),
                        session_id=self.current_session_id,
                    )

        return current_line

    def _restore_line(self, line: str) -> str:
        """Restore PII in a single line.

        Args:
            line: The line to process

        Returns:
            The line with PII restored
        """
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
    """Sanitize input text by masking PII.

    Args:
        text: Input text containing PII
        session_id: Session identifier for tracking PII mappings

    Returns:
        Text with PII masked

    Raises:
        sqlite3.Error: If database operations fail
    """
    try:
        pii_handler.current_session_id = session_id
        pii_handler.db.clear_mappings(session_id)
        lines = text.split("\n")
        processed_lines = [pii_handler.process_line(line, "mask") for line in lines]
        return "\n".join(processed_lines)
    except sqlite3.Error as e:
        logger.error("Error in sanitize_input: %s", str(e))
        raise


@mcp.tool()
def restore_pii(text: str, session_id: Optional[str] = None) -> str:
    """Restore original PII values in the text.

    Args:
        text: Text with masked PII
        session_id: Session identifier for retrieving PII mappings

    Returns:
        Text with original PII values restored

    Raises:
        sqlite3.Error: If database operations fail
    """
    try:
        pii_handler.current_session_id = session_id
        lines = text.split("\n")
        processed_lines = [pii_handler.process_line(line, "restore") for line in lines]
        return "\n".join(processed_lines)
    except sqlite3.Error as e:
        logger.error("Error in restore_pii: %s", str(e))
        raise


if __name__ == "__main__":
    # Test data for demonstration
    TEST_TEXT = """
    Name: John Doe 
    Address: 123 Someplace Dr 
    City, State, Zip: Somewhere, DC 12345 
    Phone: (123) 456-7890 
    Email: me@myemail.com 
    Credit Card Number: 1234 5678 9012 3456
    SSN: 123-45-6789
    """

    # Test session configuration
    TEST_SESSION_ID = "test_session_123"
    # Test the PII handling
    print("\nOriginal text:")
    print(TEST_TEXT)

    # Step 1: Sanitize the input
    test_sanitized = sanitize_input(TEST_TEXT, TEST_SESSION_ID)  # pylint: disable=c0103
    print("\nSanitized text:")
    print(test_sanitized)

    # Step 2: Restore PII in the response
    test_restored = restore_pii(  # pylint: disable=c0103
        test_sanitized, TEST_SESSION_ID
    )
    print("\nProcessed text with PII handling:")
    print(test_restored)

    # Start the MCP server
    mcp.run(transport="stdio")
