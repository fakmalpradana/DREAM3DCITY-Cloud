# Project Structure

## Directory Layout

```text
DREAM3DCITY/
├── cli.py                   # Command Line Interface Entry Point
├── main.py                  # GUI Application Entry Point
├── go/                      # Go Source Code (Backend Utilities)
│   ├── objseparator.go      # Splitting OBJ by GeoJSON
│   ├── translate.go         # Coordinate Translation
│   ├── obj2lod2gml.go       # OBJ to CityGML LOD2 Converter
│   └── ...
├── src/
│   ├── core/                # Core Business Logic (Decoupled from GUI)
│   │   ├── reconstruction.py  # Feature A: 3D Reconstruction Logic
│   │   ├── obj2gml.py         # Feature B: OBJ to GML Pipeline Logic
│   │   ├── obj2gml_workflow.py # Underlying Workflow Implementation
│   │   ├── semantic_mapping.py # Semantic Mapping Utilities
│   │   └── obj2cityjson/       # OBJ to CityJSON Utilities
│   ├── gui/                 # Presentation Layer (PyQt5)
│   │   ├── main_window.py     # Main Window Implementation
│   │   ├── assets/          # Images and Icons
│   │   └── tabs/            # Tab Implementations (UI Widgets)
│   └── config/              # Configuration Files
│       ├── reconstruct.json
│       └── ...
└── docs/                    # Documentation
    ├── project_structure.md
    └── cli_manual.md
```

## Description

- **`cli.py`**: The entry point for running the application in headless mode via command line.
- **`main.py`**: The entry point for launching the Graphical User Interface.
- **`src/core`**: Contains the "brains" of the application. These modules can be imported by both the CLI and GUI. They manage external processes (like `geof` or Go scripts) and handle data validation.
- **`src/gui`**: Contains all PyQt5 dependent code. `tabs/` contains the specific logic for each tab in the application.
- **`go/`**: Contains the compiled or runnable Go scripts used for high-performance geometry processing.
