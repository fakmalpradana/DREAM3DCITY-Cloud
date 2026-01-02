import sys
import os
import logging
from .obj2gml_workflow import RunObj2GML

# Configure logging
logger = logging.getLogger(__name__)

class Obj2GMLManager:
    """
    Manager for the OBJ to GML conversion process.
    Wraps the existing workflow logic.
    """
    def __init__(self):
        pass

    def run_conversion(self, input_dir: str):
        """
        Runs the OBJ to GML conversion.
        
        Args:
            input_dir: Directory containing input files.
        """
        if not os.path.isdir(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return False

        logger.info(f"Starting OBJ to GML conversion for: {input_dir}")
        
        # We use the existing class but we might need to handle the QThread part 
        # if this is running in CLI mode.
        # The original RunObj2GML inherits from QThread. 
        # For CLI usage, we should probably instantiate it and call run() directly,
        # but QThread.run() is protected.
        
        # However, since we are refactoring, we should make RunObj2GML NOT inherit from QThread directly
        # or separate the logic.
        # For now, let's try to run it. If it inherits from QThread, calling run() directly 
        # usually works in Python but is not recommended for threading.
        # But we want it synchronous for CLI.
        
        converter = RunObj2GML(input_dir)
        try:
            converter.run() # Calling run directly to execute synchronously
            return True
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False
