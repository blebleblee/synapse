# Operational Verification Labs: Audio Plugins

## Objective & Lab Setup

This laboratory aims to provide hands-on experience in the implementation, testing, and verification of audio plugins. Through this lab, you will delve into the foundational aspects of audio plugin development, parameter variation, and fault injection using the JUCE framework, a popular C++ library for audio applications. The exercises will be conducted in a Linux environment with the necessary tools and packages installed.

### Required Domain-Specific Tools, Environments, Packages, or Simulators

To complete this lab, you will need the following tools and software:

- **JUCE Framework**: Download and install the JUCE framework from the official website (https://juce.com/).
- **CMake**: Ensure CMake is installed on your system. You can install it using your package manager, e.g., `sudo apt-get install cmake`.
- **GCC/G++**: Install the GNU Compiler Collection for C++ development, e.g., `sudo apt-get install g++`.
- **Git**: Install Git for version control, e.g., `sudo apt-get install git`.
- **Audio Host**: Use an audio host like Bitwig Studio, Ableton Live, or REAPER to load and test your plugins.
- **Plotting Tool**: Install a plotting tool like GNU Octave or Python with Matplotlib for graphing responses.

## Exercise 1: Foundational Practical Implementation

### Step-by-Step Runnable Exercise Demonstrating the Core Concept

#### Step 1: Set Up Your Development Environment

Begin by setting up your development environment with the JUCE framework:

1. Clone the JUCE repository:
   ```
   git clone https://github.com/juce-framework/JUCE.git
   cd JUCE/extras/Projucer/Builds/LinuxMakefile
   make
   ```

2. Launch the Projucer:
   ```
   ./Projucer
   ```

3. Create a new Audio Plugin project:
   - Navigate to File > New Project > Audio Plug-In.
   - Configure the project settings, such as project name and company name, and select the desired plugin format.
   - Save the project.

#### Step 2: Implement a Simple Gain Plugin

Implement a simple gain control plugin by modifying the generated project files:

1. Open the `PluginProcessor.cpp` file in your preferred text editor.

2. Modify the `processBlock` method to implement a simple gain control:
   ```cpp
   void SimpleGainAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
   {
       const float gain = *gainParameter;
       buffer.applyGain (gain);
   }
   ```

3. Add a gain parameter in the `PluginProcessor.h` file:
   ```cpp
   juce::AudioParameterFloat* gainParameter;
   ```

4. Initialize the gain parameter in the `PluginProcessor.cpp` file:
   ```cpp
   SimpleGainAudioProcessor::SimpleGainAudioProcessor()
       : AudioProcessor (BusesProperties()
                         #if ! JucePlugin_IsMidiEffect
                          #if ! JucePlugin_IsSynth
                           .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                          #endif
                           .withOutput ("Output", juce::AudioChannelSet::stereo(), true)
                         #endif
                        )
   {
       addParameter (gainParameter = new juce::AudioParameterFloat ("gain", "Gain", 0.0f, 1.0f, 0.5f));
   }
   ```

5. Update the `PluginEditor.cpp` file to add a gain slider:
   ```cpp
   SimpleGainAudioProcessorEditor::SimpleGainAudioProcessorEditor (SimpleGainAudioProcessor& p)
       : AudioProcessorEditor (&p), audioProcessor (p)
   {
       gainSlider.setSliderStyle (juce::Slider::SliderStyle::LinearHorizontal);
       gainSlider.setTextBoxStyle (juce::Slider::NoTextBox, false, 0, 0);
       gainSlider.setRange (0.0f, 1.0f);
       gainSlider.setValue (audioProcessor.gainParameter->get());
       gainSlider.onValueChange = [this] { audioProcessor.gainParameter->setValueNotifyingHost (gainSlider.getValue()); };
       addAndMakeVisible (gainSlider);
       setSize (400, 300);
   }

   void SimpleGainAudioProcessorEditor::paint (juce::Graphics& g)
   {
       g.fillAll (getLookAndFeel().findColour (juce::ResizableWindow::backgroundColourId));
   }

   void SimpleGainAudioProcessorEditor::resized()
   {
       gainSlider.setBounds (10, 10, getWidth() - 20, 20);
   }
   ```

6. Build the plugin:
   - In the Projucer, click on "Build" to generate the build files.
   - Navigate to the build directory and run `make` to compile the plugin.

7. Load the plugin in your audio host and verify that the gain control works as expected.

## Exercise 2: Parameter Variation & Empirical Analysis

### Testing Different Configurations, Measuring Outputs, and Graphing Responses

#### Step 1: Implement a Low-Pass Filter

Enhance your plugin by adding a low-pass filter:

1. Add a low-pass filter parameter in the `PluginProcessor.h` file:
   ```cpp
   juce::AudioParameterFloat* cutoffParameter;
   ```

2. Initialize the cutoff parameter in the `PluginProcessor.cpp` file:
   ```cpp
   SimpleGainAudioProcessor::SimpleGainAudioProcessor()
       : AudioProcessor (BusesProperties()
                         #if ! JucePlugin_IsMidiEffect
                          #if ! JucePlugin_IsSynth
                           .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                          #endif
                           .withOutput ("Output", juce::AudioChannelSet::stereo(), true)
                         #endif
                        )
   {
       addParameter (gainParameter = new juce::AudioParameterFloat ("gain", "Gain", 0.0f, 1.0f, 0.5f));
       addParameter (cutoffParameter = new juce::AudioParameterFloat ("cutoff", "Cutoff", 20.0f, 20000.0f, 1000.0f));
   }
   ```

3. Implement the low-pass filter in the `processBlock` method:
   ```cpp
   void SimpleGainAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
   {
       const float gain = *gainParameter;
       const float cutoff = *cutoffParameter;
       juce::IIRFilter filter;
       filter.setLowPass (getSampleRate(), cutoff);
       filter.process (buffer);
       buffer.applyGain (gain);
   }
   ```

4. Update the `PluginEditor.cpp` file to add a cutoff slider:
   ```cpp
   SimpleGainAudioProcessorEditor::SimpleGainAudioProcessorEditor (SimpleGainAudioProcessor& p)
       : AudioProcessorEditor (&p), audioProcessor (p)
   {
       gainSlider.setSliderStyle (juce::Slider::SliderStyle::LinearHorizontal);
       gainSlider.setTextBoxStyle (juce::Slider::NoTextBox, false, 0, 0);
       gainSlider.setRange (0.0f, 1.0f);
       gainSlider.setValue (audioProcessor.gainParameter->get());
       gainSlider.onValueChange = [this] { audioProcessor.gainParameter->setValueNotifyingHost (gainSlider.getValue()); };
       addAndMakeVisible (gainSlider);

       cutoffSlider.setSliderStyle (juce::Slider::SliderStyle::LinearHorizontal);
       cutoffSlider.setTextBoxStyle (juce::Slider::NoTextBox, false, 0, 0);
       cutoffSlider.setRange (20.0f, 20000.0f);
       cutoffSlider.setValue (audioProcessor.cutoffParameter->get());
       cutoffSlider.onValueChange = [this] { audioProcessor.cutoffParameter->setValueNotifyingHost (cutoffSlider.getValue()); };
       addAndMakeVisible (cutoffSlider);
       setSize (400, 300);
   }

   void SimpleGainAudioProcessorEditor::paint (juce::Graphics& g)
   {
       g.fillAll (getLookAndFeel().findColour (juce::ResizableWindow::backgroundColourId));
   }

   void SimpleGainAudioProcessorEditor::resized()
   {
       gainSlider.setBounds (10, 10, getWidth() - 20, 20);
       cutoffSlider.setBounds (10, 40, getWidth() - 20, 20);
   }
   ```

With these steps, you will have a basic audio plugin capable of applying gain and low-pass filtering. Test the plugin in your audio host to ensure that both functionalities work as intended.
