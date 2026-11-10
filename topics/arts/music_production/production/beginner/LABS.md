# Beginner Hands-On Lab: Production
## Objective & Prerequisites
The objective of this hands-on lab is to familiarize you with the basic setup and execution of a music production environment. By the end of this lab, you will have installed and verified the necessary tools, executed your first command, and inspected the basic state of your setup. This lab assumes you have a basic understanding of operating systems and command-line interfaces.

### Prerequisites:
- A computer with an operating system (Windows, macOS, or Linux).
- Administrative or sudo access to install software.
- A text editor or Integrated Development Environment (IDE) of your choice (e.g., Visual Studio Code, Sublime Text).
- Basic familiarity with command-line operations.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
In this exercise, we will install and verify the installation of a Digital Audio Workstation (DAW) and a command-line tool for audio processing.

### Step 1: Install a DAW
For this lab, we will use **Ableton Live Lite**, a widely-used DAW that is free and suitable for beginners.

#### On Windows:
1. Visit the [Ableton Live Lite download page](https://www.ableton.com/en/products/live-lite/).
2. Click on the "Download" button.
3. Follow the installation instructions provided by the installer.

#### On macOS:
1. Visit the [Ableton Live Lite download page](https://www.ableton.com/en/products/live-lite/).
2. Click on the "Download" button.
3. Follow the installation instructions provided by the installer.

#### On Linux:
Ableton Live Lite is not natively available for Linux, but you can use **Bitwig Studio**, which is also free and powerful.

1. Visit the [Bitwig Studio download page](https://www.bitwig.com/en/products/bitwig-studio.html).
2. Click on the "Download" button.
3. Follow the installation instructions provided by the installer.

### Step 2: Install a Command-Line Audio Tool
We will use **FFmpeg**, a powerful multimedia framework that can record, convert, and stream audio and video.

#### On Windows:
1. Download the FFmpeg build from [Zeranoe FFmpeg](https://ffmpeg.zeranoe.com/builds/).
2. Extract the downloaded files to a directory of your choice (e.g., `C:\ffmpeg`).
3. Add the `bin` directory to your system's PATH environment variable.
4. Open a Command Prompt and type `ffmpeg -version` to verify the installation.

#### On macOS:
1. Open Terminal.
2. Install Homebrew if you haven't already by running:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install FFmpeg by running:
   ```bash
   brew install ffmpeg
   ```
4. Verify the installation by running:
   ```bash
   ffmpeg -version
   ```

#### On Linux:
1. Open Terminal.
2. Install FFmpeg using your package manager. For example, on Ubuntu, run:
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
3. Verify the installation by running:
   ```bash
   ffmpeg -version
   ```

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
In this exercise, we will create a simple audio file using FFmpeg and then open it in Ableton Live Lite.

### Step 1: Create a Simple Audio File
Open a terminal and run the following command to create a 5-second sine wave audio file at 440 Hz (A4 note):

```bash
ffmpeg -f lavfi -i anoisesrc=f=440:d=5 -ar 44100 -ac 2 output.wav
```

**Expected Output:**
You should see output similar to the following, indicating that the file is being generated:

```
ffmpeg version 4.4.1 Copyright (c) 2000-2021 the FFmpeg developers
  built with gcc 11.1.0 (GCC)
  configuration: --enable-gpl --enable-version3 --enable-sdl2 --enable-fontconfig --enable-gnutls --enable-iconv --enable-libass --enable-libdav1d --enable-libbluray --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libopus --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libtheora --enable-libtwolame --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libxvid --enable-libzimg --enable-lzma --enable-libvmaf --enable-libzmq --enable-libzvbi --enable-avfilter --enable-chromaprint --enable-frei0r --enable-libfreetype --enable-libfribidi --enable-libgme --enable-gnutls --enable-gmp --enable-libgsm --enable-libjack --enable-libmfx --enable-libmp3lame --enable-libmysofa --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librsvg --enable-librubberband --enable-libshine --enable-libsoxr --enable-libspeex --enable-libsrt --enable-libssh --enable-libtensorflow --enable-libtesseract --enable-libtwolame --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxvid --enable-libzimg --enable-libzmq --enable-libzvbi --enable-amf --enable-cuvid --enable-d3d11va --enable-nvenc --enable-nvdec --enable-dxva2 --enable-vaapi --enable-vdpau
  libavutil      56. 70.100 / 56. 70.100
  libavcodec     58.134.100 / 58.134.100
  libavformat    58. 76.100 / 58. 76.100
  libavdevice    58. 13.100 / 58. 13.100
  libavfilter     7.110.100 /  7.110.100
  libswscale      5.  9.100 /  5.  9.100
  libswresample   3.  9.100 /  3.  9.100
  libpostproc    55.  9.100 / 55.  9.100
Input #0, lavfi, from 'anoisesrc=f=440:d=5':
  Duration: N/A, start: 0.000000, bitrate: 705 kb/s
    Stream #0:0: Audio: pcm_f32le, 44100 Hz, mono, flt, 1411 kb/s
Stream mapping:
  Stream #0:0 -> #0:0 (pcm_f32le (native) -> pcm_s16le (native))
Press [q] to stop, [?] for help
size=NaNkB time=00:00:05.00 bitrate=N/A speed=1.01x    
video:0kB audio:441kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%
```

### Step 2: Open the Audio File in Ableton Live Lite
1. Launch Ableton Live Lite.
2. Create a new project.
3. Drag and drop the `output.wav` file into the Ableton Live Lite session view.

**Expected Output:**
You should see the waveform of the audio file appear in the session view, and you should be able to play it back by clicking the play button.

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
In this exercise, we will inspect the basic state of our setup by checking the properties of the audio file we created.

### Step 1: Inspect the Audio File Properties
Open a terminal and run the following command to inspect the properties of the `output.wav` file:

```bash
ffmpeg -i output.wav
```

**Expected Output:**
You should see output similar to the following, indicating the properties of the audio file:

```
Input #0, wav, from 'output.wav':
  Metadata:
    encoder         : Lavf58.76.100
  Duration: 00:00:05.00, bitrate: 1411 kb/s
    Stream #0:0: Audio: pcm_s16le ([1][0][0][0] / 0x0001), 44100 Hz, stereo, s16, 1411 kb/s
```

## Challenge Exercise (Simple self-test for beginners)
Create a 10-second audio file with a 440 Hz sine wave and a 880 Hz sine wave (A4 and A5 notes) mixed together. Use FFmpeg to generate the file and then open it in Ableton Live Lite.

### Step 1: Create the Mixed Audio File
Open a terminal and run the following command to create the mixed audio file:

```bash
ffmpeg -f lavfi -i "sine=f=440:d=10[s0]; sine=f=880:d=10[s1]; [s0][s1]amix=inputs=2:duration=longest" -ar 44100 -ac 2 mixed_output.wav
```

### Step 2: Open the Mixed Audio File in Ableton Live Lite
1. Drag and drop the `mixed_output.wav` file into the Ableton Live Lite session view.
2. Play the file and observe the waveform and sound.

**Expected Output:**
You should see the waveform of the mixed audio file appear in the session view, and you should be able to play it back by clicking the play button. The sound should be a combination of the A4 and A5 notes.

Congratulations! You have completed the Beginner Hands-On Lab for Production. You have set up your environment, created your first audio file, and inspected its properties.
