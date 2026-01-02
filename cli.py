import sys
import argparse
import logging
from src.core.reconstruction import ReconstructionManager
from src.core.obj2gml import Obj2GMLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="DREAM3DCITY CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Command: Reconstruct ===
    parser_recon = subparsers.add_parser("reconstruct", help="Run 3D Reconstruction (Geoflow)")
    parser_recon.add_argument("--footprint", required=True, help="Path to building footprint (GPKG/SHP)")
    parser_recon.add_argument("--pointcloud", required=True, help="Path to point cloud (LAS/LAZ)")
    parser_recon.add_argument("--output", required=True, help="Output directory")
    
    # Advanced parameters
    parser_recon.add_argument("--r_line_epsilon", type=float, default=0.4)
    parser_recon.add_argument("--r_normal_k", type=int, default=5)
    parser_recon.add_argument("--r_optimisation_data_term", type=float, default=7.0)
    parser_recon.add_argument("--r_plane_epsilon", type=float, default=0.2)
    parser_recon.add_argument("--r_plane_k", type=int, default=15)
    parser_recon.add_argument("--r_plane_min_points", type=int, default=15)
    parser_recon.add_argument("--r_plane_normal_angle", type=float, default=0.75)

    # === Command: OBJ to GML ===
    parser_gml = subparsers.add_parser("obj2gml", help="Convert OBJ to GML")
    parser_gml.add_argument("--input_dir", required=True, help="Directory containing OBJ/Text/GeoJSON files")

    args = parser.parse_args()

    if args.command == "reconstruct":
        manager = ReconstructionManager()
        advanced_params = {
            "r_line_epsilon": args.r_line_epsilon,
            "r_normal_k": args.r_normal_k,
            "r_optimisation_data_term": args.r_optimisation_data_term,
            "r_plane_epsilon": args.r_plane_epsilon,
            "r_plane_k": args.r_plane_k,
            "r_plane_min_points": args.r_plane_min_points,
            "r_plane_normal_angle": args.r_plane_normal_angle
        }
        success = manager.run_reconstruction(args.footprint, args.pointcloud, args.output, advanced_params)
        sys.exit(0 if success else 1)

    elif args.command == "obj2gml":
        manager = Obj2GMLManager()
        success = manager.run_conversion(args.input_dir)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
