import os
import subprocess
import logging
from typing import Dict, Optional, List

# Configure logger
logger = logging.getLogger(__name__)

class ReconstructionManager:
    """
    Manages the 3D Reconstruction process using Geoflow.
    """

    def __init__(self, config_dir: str = "src/config"):
        self.config_dir = config_dir
        self.geof_cmd = "geof" # Assumption: geof is in PATH

    def validate_inputs(self, footprint: str, pointcloud: str, output_dir: str) -> bool:
        """Validates that input files and output directory exist."""
        if not os.path.exists(footprint):
            logger.error(f"Footprint file not found: {footprint}")
            return False
        if not os.path.exists(pointcloud):
            logger.error(f"Point cloud file not found: {pointcloud}")
            return False
        if not os.path.isdir(output_dir):
            logger.error(f"Output directory not found: {output_dir}")
            return False
        return True

    def build_command(self, 
                      json_config: str, 
                      footprint: str, 
                      pointcloud: str, 
                      output_dir: str, 
                      advanced_params: Dict[str, float]) -> List[str]:
        """Builds the geoflow command argument list."""
        
        config_path = os.path.join(self.config_dir, json_config)
        
        cmd = [
            self.geof_cmd, 
            config_path,
            f"--input_footprint={footprint}",
            f"--input_pointcloud={pointcloud}",
            f"--output_cityjson={os.path.join(output_dir, 'model.json')}",
            f"--output_obj_lod12={os.path.join(output_dir, 'model_lod12.obj')}",
            f"--output_obj_lod13={os.path.join(output_dir, 'model_lod13.obj')}",
            f"--output_obj_lod22={os.path.join(output_dir, 'model_lod22.obj')}",
            f"--output_vector2d={os.path.join(output_dir, 'model_2d.gpkg')}"
        ]

        for k, v in advanced_params.items():
            cmd.append(f"--{k}={v}")
            
        return cmd

    def run_reconstruction(self, 
                          footprint: str, 
                          pointcloud: str, 
                          output_dir: str, 
                          advanced_params: Optional[Dict[str, float]] = None) -> bool:
        """
        Runs the reconstruction process.
        
        Args:
            footprint: Path to building footprint (GPKG/SHP).
            pointcloud: Path to point cloud (LAS/LAZ).
            output_dir: Directory to save outputs.
            advanced_params: Dictionary of advanced parameters.
        """
        if advanced_params is None:
            advanced_params = {}

        if not self.validate_inputs(footprint, pointcloud, output_dir):
            return False

        # Phase 1: Reconstruct_ (underscore version)
        # Note: The original code ran `reconstruct_.json` first, then `reconstruct.json`.
        # I will preserve this behavior.
        
        logger.info("Starting Phase 1: Pre-calculation...")
        cmd1 = self.build_command("reconstruct_.json", footprint, pointcloud, output_dir, advanced_params)
        
        try:
            logger.debug(f"Executing: {' '.join(cmd1)}")
            result1 = subprocess.run(cmd1, cwd=os.getcwd(), capture_output=True, text=True)
            if result1.returncode != 0:
                logger.error(f"Phase 1 failed: {result1.stderr}")
                return False
            logger.info(result1.stdout)
        except Exception as e:
            logger.exception("Exception during Phase 1")
            return False

        # Phase 2: Reconstruct (main version)
        logger.info("Starting Phase 2: Main Reconstruction...")
        cmd2 = self.build_command("reconstruct.json", footprint, pointcloud, output_dir, advanced_params)
        
        try:
            logger.debug(f"Executing: {' '.join(cmd2)}")
            result2 = subprocess.run(cmd2, cwd=os.getcwd(), capture_output=True, text=True)
            if result2.returncode != 0:
                logger.error(f"Phase 2 failed: {result2.stderr}")
                return False
            logger.info(result2.stdout)
        except Exception as e:
            logger.exception("Exception during Phase 2")
            return False
            
        logger.info("Reconstruction completed successfully.")
        return True
