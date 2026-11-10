# Beginner Technical Lesson: Color Theory

## 1. Core Mechanics & Basic Principles (How it works under the hood at a fundamental level)

Color theory is a fundamental aspect of visual arts, encompassing the principles of how colors interact and relate to each other. At its core, color theory is based on the physics of light and the way the human eye perceives it. Light is composed of different wavelengths, and when these wavelengths are combined, they create the spectrum of colors we see. The visible spectrum ranges from approximately 380 nanometers (violet) to 700 nanometers (red).

The human eye contains photoreceptors called rods and cones. Rods are responsible for vision in low light conditions, while cones are responsible for color vision. There are three types of cones, each sensitive to different wavelengths of light: short-wavelength (S) cones, medium-wavelength (M) cones, and long-wavelength (L) cones. These cones send signals to the brain, which interprets them as different colors.

The primary colors of light, known as the additive color system, are red, green, and blue (RGB). When these colors are combined in different intensities, they can produce a wide range of colors. For example, combining red and green light produces yellow, while combining all three colors at full intensity produces white light. This system is used in digital displays, such as computer monitors and televisions.

In contrast, the primary colors of pigments, known as the subtractive color system, are cyan, magenta, and yellow (CMY). When pigments are mixed, they absorb certain wavelengths of light and reflect others. For instance, mixing cyan and magenta pigments absorbs red light and reflects blue and green light, resulting in a blue color. Mixing all three pigments at full intensity absorbs all wavelengths of light, producing black.

## 2. Step-by-Step Component Breakdown

### 2.1 Understanding the Color Wheel

The color wheel is a visual representation of the relationships between colors. It is typically organized into three categories: primary colors, secondary colors, and tertiary colors.

- **Primary Colors**: These are the fundamental colors that cannot be created by mixing other colors. In the additive color system, the primary colors are red, green, and blue. In the subtractive color system, the primary colors are cyan, magenta, and yellow.
- **Secondary Colors**: These are created by mixing two primary colors in equal parts. In the additive system, the secondary colors are cyan (green + blue), magenta (red + blue), and yellow (red + green). In the subtractive system, the secondary colors are red (magenta + yellow), green (cyan + yellow), and blue (cyan + magenta).
- **Tertiary Colors**: These are created by mixing a primary color with a secondary color adjacent to it on the color wheel. For example, mixing red and orange produces red-orange, while mixing blue and violet produces blue-violet.

### 2.2 Color Harmonies

Color harmonies refer to combinations of colors that are aesthetically pleasing. Some common color harmonies include:

- **Monochromatic**: Using different shades, tints, and tones of a single color.
- **Analogous**: Using colors that are adjacent to each other on the color wheel.
- **Complementary**: Using colors that are directly opposite each other on the color wheel.
- **Triadic**: Using three colors that are evenly spaced around the color wheel.
- **Split Complementary**: Using a color and the two colors adjacent to its complement.
- **Double Complementary**: Using two pairs of complementary colors.
- **Tetradic**: Using four colors that form two complementary pairs.

### 2.3 Color Schemes

Color schemes are specific combinations of colors used in a design. Some common color schemes include:

- **Monochromatic**: Using different shades, tints, and tones of a single color.
- **Analogous**: Using colors that are adjacent to each other on the color wheel.
- **Complementary**: Using colors that are directly opposite each other on the color wheel.
- **Triadic**: Using three colors that are evenly spaced around the color wheel.
- **Tetradic**: Using four colors that form two complementary pairs.

## 3. First Working Implementation (Complete, clean, commented starter code or configuration)

For this example, we will create a simple web page that demonstrates the use of color harmonies. We will use HTML and CSS to create a color wheel and display different color harmonies.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Color Theory Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .color-wheel {
            width: 300px;
            height: 300px;
            border-radius: 50%;
            background: conic-gradient(
                red, yellow, green, cyan, blue, magenta, red
            );
            position: relative;
        }
        .color-sample {
            width: 100px;
            height: 100px;
            margin: 10px;
            border: 1px solid #000;
        }
        .color-harmony {
            display: flex;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Color Theory Example</h1>
    <div class="color-wheel"></div>
    <div class="color-harmony">
        <div class="color-sample" style="background-color: red;"></div>
        <div class="color-sample" style="background-color: green;"></div>
        <div class="color-sample" style="background-color: blue;"></div>
    </div>
    <div class="color-harmony">
        <div class="color-sample" style="background-color: yellow;"></div>
        <div class="color-sample" style="background-color: cyan;"></div>
        <div class="color-sample" style="background-color: magenta;"></div>
    </div>
    <div class="color-harmony">
        <div class="color-sample" style="background-color: #ff6347;"></div>
        <div class="color-sample" style="background-color: #4682b4;"></div>
        <div class="color-sample" style="background-color: #3cb371;"></div>
    </div>
</body>
</html>
```

### Explanation

- **Color Wheel**: The `.color-wheel` class uses a `conic-gradient` to create a circular gradient that represents the color wheel.
- **Color Samples**: The `.color-sample` class is used to display individual color samples. The `background-color` property is set to different colors to demonstrate color harmonies.
- **Color Harmonies**: The `.color-harmony` class is used to group color samples together. In this example, we display three sets of color harmonies: primary colors, secondary colors, and tertiary colors.

## 4. What Can Go Wrong (Simple common mistakes and how to spot them)

- **Incorrect Color Model**: Using the wrong color model (additive vs. subtractive) can lead to unexpected results. Ensure you are using the correct color model for your medium.
- **Improper Color Mixing**: When mixing colors, ensure you are using the correct proportions. For example, mixing equal parts of red and green light produces yellow, while mixing equal parts of red and green pigments produces brown.
- **Overuse of Colors**: Using too many colors can make a design look cluttered and overwhelming. Stick to a few color harmonies to create a cohesive design.
- **Ignoring Color Psychology**: Colors can evoke different emotions and moods. Consider the psychological effects of colors when choosing a color scheme.

## 5. Key Takeaways & Review Checklist

### Key Takeaways

- **Additive vs. Subtractive Color Systems**: Understand the difference between the additive and subtractive color systems and how they are used in different mediums.
- **Color Wheel**: Familiarize yourself with the color wheel and the relationships between colors.
- **Color Harmonies**: Learn about different color harmonies and how to use them to create aesthetically pleasing designs.
- **Color Schemes**: Experiment with different color schemes to find what works best for your design.

### Review Checklist

- [ ] Understand the difference between additive and subtractive color systems.
- [ ] Know the primary, secondary, and tertiary colors.
- [ ] Be able to identify and create different color harmonies.
- [ ] Understand how to use color schemes effectively in your designs.
- [ ] Be aware of the psychological effects of colors and how they can influence emotions and moods.
