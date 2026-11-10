# Beginner Technical Lesson: Drawing

## 1. Core Mechanics & Basic Principles (How it works under the hood at a fundamental level)

Drawing is a fundamental visual art form that involves the creation of images using various tools and techniques. At its core, drawing is about the manipulation of lines, shapes, and tones to convey form, space, and emotion. The mechanics of drawing involve understanding the principles of line, shape, value, texture, and composition. Lines define the boundaries and contours of objects, shapes create form, value (light and shadow) gives depth, texture adds surface detail, and composition organizes the elements into a cohesive whole.

The human eye perceives the world in three dimensions, but drawing is a two-dimensional representation of that world. To create the illusion of depth and three-dimensionality, artists use techniques such as perspective, shading, and foreshortening. Perspective involves the use of vanishing points and converging lines to create the illusion of depth. Shading involves the use of light and shadow to create the illusion of form and volume. Foreshortening involves the distortion of objects to create the illusion of depth and distance.

## 2. Step-by-Step Component Breakdown

### Step 1: Choose Your Tools
Beginners should start with simple tools such as pencils, charcoal, or pastels. Pencils are ideal for beginners because they allow for easy erasing and blending. Charcoal and pastels are also good choices because they allow for a wide range of tones and textures.

### Step 2: Understand Basic Shapes
All objects can be broken down into basic shapes such as circles, squares, rectangles, triangles, and ellipses. By understanding these basic shapes, you can begin to draw more complex objects. For example, a house can be broken down into a rectangle for the main body and a triangle for the roof.

### Step 3: Practice Line Quality
The quality of your lines can greatly affect the overall appearance of your drawing. Practice drawing lines of varying thickness and weight. Use light, sketchy lines to establish the basic shapes and proportions of your subject, and use darker, more defined lines to add detail and definition.

### Step 4: Learn About Value and Shading
Value refers to the lightness or darkness of a color. Shading involves the use of value to create the illusion of form and volume. To create a realistic drawing, you need to understand how light and shadow interact with objects. Start by identifying the light source in your scene and then determine how light and shadow fall on the objects in your drawing.

### Step 5: Understand Composition
Composition involves the arrangement of elements within a drawing. A well-composed drawing is visually appealing and easy to understand. To create a good composition, consider the placement of objects within the frame, the use of leading lines to guide the viewer's eye, and the balance of positive and negative space.

## 3. First Working Implementation (Complete, clean, commented starter code or configuration)

While drawing is not typically associated with coding, we can use a simple example in a digital drawing software like Adobe Photoshop or a similar program to illustrate the principles of drawing. Below is a step-by-step guide to creating a simple drawing of a cube using basic shapes and shading.

### Step-by-Step Guide to Drawing a Cube

1. **Open Your Drawing Software:**
   - Open Adobe Photoshop or any other digital drawing software of your choice.

2. **Create a New Canvas:**
   - Create a new canvas with a size of 800x600 pixels.

3. **Draw the Basic Shapes:**
   - Use the rectangle tool to draw a square in the center of the canvas. This will be the front face of the cube.
   - Draw two more rectangles to represent the sides of the cube. These rectangles should be smaller and positioned at an angle to the front face to create the illusion of depth.

4. **Add Lines to Define the Edges:**
   - Use the line tool to draw lines connecting the corners of the rectangles. These lines will define the edges of the cube.

5. **Add Shading to Create Depth:**
   - Use the brush tool to add shading to the sides of the cube. Darken the sides that are farther away from the light source and lighten the sides that are closer to the light source.

6. **Refine the Drawing:**
   - Erase any unnecessary lines and refine the edges of the cube to make them smooth and clean.

### Example Code (Pseudo-code for Digital Drawing)

```plaintext
// Step 1: Create a new canvas
canvas = createCanvas(800, 600);

// Step 2: Set the light source
lightSource = (500, 300); // Position of the light source

// Step 3: Draw the front face of the cube
frontFace = drawRectangle(300, 200, 200, 200);

// Step 4: Draw the sides of the cube
side1 = drawRectangle(400, 150, 100, 100, angle=45);
side2 = drawRectangle(200, 150, 100, 100, angle=-45);

// Step 5: Add lines to define the edges
drawLine(frontFace.topLeft, side1.topLeft);
drawLine(frontFace.topRight, side1.topRight);
drawLine(frontFace.bottomLeft, side1.bottomLeft);
drawLine(frontFace.bottomRight, side1.bottomRight);

drawLine(frontFace.topLeft, side2.topLeft);
drawLine(frontFace.topRight, side2.topRight);
drawLine(frontFace.bottomLeft, side2.bottomLeft);
drawLine(frontFace.bottomRight, side2.bottomRight);

// Step 6: Add shading to create depth
shade(frontFace, lightSource, intensity=0.8);
shade(side1, lightSource, intensity=0.5);
shade(side2, lightSource, intensity=0.5);

// Step 7: Refine the drawing
refineEdges(frontFace);
refineEdges(side1);
refineEdges(side2);
```

## 4. What Can Go Wrong (Simple common mistakes and how to spot them)

### Common Mistakes:
1. **Incorrect Proportions:**
   - Ensure that the shapes and lines are proportionate to each other. Use a ruler or guide lines to help maintain accurate proportions.

2. **Poor Line Quality:**
   - Practice drawing lines of varying thickness and weight. Use light, sketchy lines to establish the basic shapes and proportions of your subject, and use darker, more defined lines to add detail and definition.

3. **Inadequate Shading:**
   - Understand how light and shadow interact with objects. Start by identifying the light source in your scene and then determine how light and shadow fall on the objects in your drawing.

4. **Poor Composition:**
   - Consider the placement of objects within the frame, the use of leading lines to guide the viewer's eye, and the balance of positive and negative space.

5. **Overcomplicating the Drawing:**
   - Start with simple shapes and gradually add detail. Avoid overcomplicating your drawing by adding too much detail too quickly.

## 5. Key Takeaways & Review Checklist

### Key Takeaways:
- **Basic Shapes:** All objects can be broken down into basic shapes such as circles, squares, rectangles, triangles, and ellipses.
- **Line Quality:** The quality of your lines can greatly affect the overall appearance of your drawing.
- **Value and Shading:** Shading involves the use of value to create the illusion of form and volume.
- **Composition:** Composition involves the arrangement of elements within a drawing.

### Review Checklist:
- [ ] Choose your tools (pencils, charcoal, pastels).
- [ ] Understand basic shapes (circles, squares, rectangles, triangles, ellipses).
- [ ] Practice line quality (light, sketchy lines vs. darker, more defined lines).
- [ ] Learn about value and shading (light and shadow).
- [ ] Understand composition (placement of objects, leading lines, balance of positive and negative space).

By following these steps and principles, you will be well on your way to creating compelling and realistic drawings. Remember, practice is key to developing your drawing skills. Keep experimenting and refining your technique.
