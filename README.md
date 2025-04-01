# tkinter-semester-calendar

This project is a Tkinter-based application that allows users to manage their semester courses through a drag-and-drop interface. Users can organize their courses into a semester calendar, with each semester containing a maximum of 30 LP (Leistungspunkte).

## Features

- **Drag and Drop**: Easily drag and drop courses into the semester calendar.
- **Semester Management**: Supports six semesters, each with a limit of 30 LP.
- **Visual Representation**: Each course is represented as a block, with the block size corresponding to the LP of the course.
- **Course Management**: Add, remove, and organize courses within the calendar.

## Project Structure

```
tkinter-semester-calendar
├── src
│   ├── main.py                # Entry point of the application
│   ├── calendar_app.py        # Manages application logic and drag-and-drop functionality
│   ├── components             # Contains UI components
│   │   ├── drag_drop_manager.py # Handles drag-and-drop functionality
│   │   ├── course_block.py     # Represents a visual block for a course
│   │   ├── semester_frame.py    # Represents a semester and manages course layout
│   │   └── calendar_grid.py     # Manages layout of all semesters
│   ├── models                 # Contains data models
│   │   ├── course.py           # Represents a course
│   │   └── semester.py         # Represents a semester
│   ├── utils                  # Utility functions and constants
│   │   ├── constants.py        # Constant values used throughout the application
│   │   └── helpers.py          # Helper functions for loading and validating data
│   └── data                   # Data management
│       ├── course_repository.py # Manages course data storage and retrieval
│       └── save_load.py        # Functions for saving and loading application state
├── resources
│   └── default_courses.json    # Default courses in JSON format
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd tkinter-semester-calendar
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.