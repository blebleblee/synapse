# Beginner Hands-On Lab: Drawing
## Objective & Prerequisites
The objective of this hands-on lab is to familiarize beginners with the basic tools and environment necessary for digital drawing. We will use a simple vector graphics editor called Inkscape, which is free, open-source, and widely used for creating scalable vector graphics (SVG). By the end of this lab, you will have set up your environment, created your first drawing, and inspected the basic state of your work.

### Prerequisites
- A computer with an internet connection.
- Basic familiarity with using a computer and navigating file systems.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
### Step 1: Download and Install Inkscape
1. **Windows Users:**
   - Visit the official Inkscape website: [https://inkscape.org/download/](https://inkscape.org/download/).
   - Download the installer for Windows.
   - Run the installer and follow the on-screen instructions to complete the installation.

2. **Mac Users:**
   - Visit the official Inkscape website: [https://inkscape.org/download/](https://inkscape.org/download/).
   - Download the installer for macOS.
   - Open the downloaded file and drag Inkscape to your Applications folder.

3. **Linux Users:**
   - Open a terminal.
   - Use your package manager to install Inkscape. For example, on Ubuntu, you can use:
     ```bash
     sudo apt update
     sudo apt install inkscape
     ```

### Step 2: Verify Installation
1. **Windows and Mac Users:**
   - Open Inkscape from your Applications folder or Start menu.
   - A new window should appear, indicating that Inkscape is installed correctly.

2. **Linux Users:**
   - Open a terminal.
   - Type `inkscape` and press Enter.
   - A new window should appear, indicating that Inkscape is installed correctly.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
### Step 1: Launch Inkscape
- Open Inkscape from your Applications folder, Start menu, or by typing `inkscape` in the terminal.

### Step 2: Create a New Document
- Click on `File` in the top menu bar.
- Select `New` from the dropdown menu.
- A new blank document will open.

### Step 3: Draw a Circle
- Select the `Ellipse Tool` from the toolbar on the left side of the screen (it looks like a circle with a line through it).
- Click and drag on the canvas to draw a circle.
- Release the mouse button to complete the circle.

### Step 4: Change the Circle's Color
- Click on the circle to select it.
- In the `Fill and Stroke` panel on the right side of the screen, click on the color box next to `Fill` to open the color picker.
- Choose a color and click `OK`.
- The circle should now be filled with the color you selected.

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
### Step 1: Save Your Work
- Click on `File` in the top menu bar.
- Select `Save As` from the dropdown menu.
- Choose a location to save your file, name it `first_drawing.svg`, and click `Save`.

### Step 2: Inspect the SVG File
- Open the file `first_drawing.svg` in a text editor (such as Notepad on Windows, TextEdit on Mac, or any code editor like VSCode or Sublime Text).
- You should see XML code that describes your drawing, including the circle and its properties.

## Challenge Exercise (Simple self-test for beginners)
### Task: Draw a Square
- Using the `Rectangle Tool` (it looks like a square with a line through it), draw a square on your canvas.
- Change the square's color to a different color of your choice.
- Save your work as `square_drawing.svg`.
- Open the file in a text editor and inspect the SVG code to see how the square is described.

By completing this lab, you have successfully set up your environment, created your first digital drawing, and inspected the basic state of your work. Congratulations on taking your first steps in digital drawing!
