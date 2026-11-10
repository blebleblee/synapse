# Beginner Hands-On Lab: Audio Engineering
## Objective & Prerequisites
### Objective
The objective of this lab is to set up your audio engineering environment and execute your first commands using a Digital Audio Workstation (DAW) and command-line tools. By the end of this lab, you should be able to verify your setup, perform a simple audio task, and inspect the basic state of your project.

### Prerequisites
- Basic computer skills.
- A computer with audio input/output capabilities.
- A DAW software installed (e.g., Audacity, FL Studio, Ableton Live Lite).
- Command-line interface (CLI) access (e.g., Terminal on macOS/Linux, Command Prompt/PowerShell on Windows).

## Exercise 1: Environment Setup & Sanity Check
### Verify DAW Installation
1. Open your DAW software.
2. Create a new project to ensure that the software is installed correctly and is functioning.

### Verify Command-Line Tools
1. Open your command-line interface.
2. Type the following command to check if `ffmpeg` is installed. `ffmpeg` is a powerful multimedia framework that can record, convert, and stream audio and video in various formats.
   ```bash
   ffmpeg -version
   ```
   - **Expected Output:** A version number and build information for `ffmpeg` should be displayed.

3. Type the following command to check if `sox` (Sound eXchange) is installed. `sox` is a command-line utility that can convert various formats of computer audio files in to other formats.
   ```bash
   sox --version
   ```
   - **Expected Output:** A version number for `sox` should be displayed.

## Exercise 2: Your First Working Experiment
### Recording a Simple Audio Clip
1. Open your DAW software.
2. Create a new project.
3. Insert a new audio track.
4. Arm the track for recording by clicking the record button on the track.
5. Start recording by pressing the record button in the transport controls.
6. Speak or play an instrument into the microphone for about 5 seconds.
7. Stop recording by pressing the stop button in the transport controls.
8. Play back the recorded audio to verify that it was captured correctly.

### Converting Audio Format Using Command-Line
1. Open your command-line interface.
2. Navigate to the directory where your recorded audio file is located.
3. Use `ffmpeg` to convert the audio file to a different format. For example, if your file is named `recording.wav`, you can convert it to `recording.mp3` using the following command:
   ```bash
   ffmpeg -i recording.wav recording.mp3
   ```
   - **Expected Output:** A new file named `recording.mp3` should be created in the same directory.

## Exercise 3: Inspecting Basic State
### Inspect DAW Project
1. In your DAW, inspect the project timeline to see the recorded audio clip.
2. Check the properties of the audio track to ensure that the recording is correctly assigned to the track.

### Inspect Command-Line Output
1. In your command-line interface, inspect the output of the `ffmpeg` command to ensure that the conversion was successful.
2. Use the `ls` command (or `dir` on Windows) to list the files in the directory and verify that the new `recording.mp3` file is present.

## Challenge Exercise (Simple self-test for beginners)
### Combine Audio Clips
1. In your DAW, record a second audio clip on a new track.
2. Use the DAW's editing tools to combine the two audio clips into a single track.
3. Export the combined audio as a new file.
4. Use `sox` to inspect the properties of the exported file. For example, to check the duration and sample rate, use the following command:
   ```bash
   soxi -D -r exported_audio.mp3
   ```
   - **Expected Output:** The duration and sample rate of the exported audio file should be displayed.

By completing this lab, you have successfully set up your audio engineering environment, performed a simple audio task, and inspected the basic state of your project. Congratulations on taking your first steps in audio engineering!
