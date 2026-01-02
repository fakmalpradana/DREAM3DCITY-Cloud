# DREAM3DCITY CLI Manual

The CLI allows you to run specific modules of DREAM3DCITY without the Graphical User Interface.

## Usage

Run the CLI using Python:

```bash
python cli.py [COMMAND] [ARGUMENTS]
```

## Commands

### 1. 3D Reconstruction

Runs the Geoflow reconstruction pipeline.

**Syntax:**
```bash
python cli.py reconstruct --footprint <PATH> --pointcloud <PATH> --output <DIR> [OPTIONS]
```

**Arguments:**

| Flag | Description | Required | Default |
|------|-------------|----------|---------|
| `--footprint` | Path to building footprint file (GPKG or SHP) | **Yes** | - |
| `--pointcloud` | Path to point cloud file (LAS or LAZ) | **Yes** | - |
| `--output` | Output directory for the generated models | **Yes** | - |
| `--r_line_epsilon` | Max distance between line and inliers | No | 0.4 |
| `--r_normal_k` | Neighbors for normal estimation | No | 5 |
| `--r_optimisation_data_term` | Model detail level | No | 7.0 |
| `--r_plane_epsilon` | Max distance plane/inliers | No | 0.2 |
| `--r_plane_k` | Neighbors for region growing | No | 15 |
| `--r_plane_min_points` | Minimum plane inliers | No | 15 |
| `--r_plane_normal_angle` | Max dot product(normal1, normal2) | No | 0.75 |

**Example:**
```bash
python cli.py reconstruct \
  --footprint ./data/footprint.gpkg \
  --pointcloud ./data/lidar.las \
  --output ./results \
  --r_plane_epsilon 0.1
```

### 2. OBJ to GML

Converts OBJ files in a directory to CityGML.

**Syntax:**
```bash
python cli.py obj2gml --input_dir <DIR>
```

**Arguments:**

| Flag | Description | Required |
|------|-------------|----------|
| `--input_dir` | Directory containing the input files (OBJ, Text, GeoJSON) | **Yes** |

**Example:**
```bash
python cli.py obj2gml --input_dir ./my_obj_project/
```
