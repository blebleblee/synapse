# Beginner Hands-On Lab: Hardware Sequencing

## Objective & Prerequisites
The objective of this lab is to familiarize you with the basics of hardware sequencing using a popular hardware sequencer, such as the Korg Volca Sample. This lab assumes you have a basic understanding of music theory and are familiar with connecting electronic instruments. Ensure you have the following items:
- Korg Volca Sample or any other hardware sequencer.
- MIDI cables and power supply for your sequencer.
- A DAW (Digital Audio Workstation) like Ableton Live, FL Studio, or Logic Pro (optional, for further exploration).
- Headphones or speakers to monitor audio output.

## Exercise 1: Environment Setup & Sanity Check
### Step 1: Power Up Your Sequencer
1. Connect your Korg Volca Sample to a power source.
2. Press and hold the **POWER** button until the display lights up.

### Step 2: Connect to a DAW (Optional)
1. Connect the **MIDI OUT** port of the Volca Sample to the **MIDI IN** port of your DAW using a MIDI cable.
2. Open your DAW and ensure it is set up to receive MIDI input from the Volca Sample.

### Step 3: Verify Audio Output
1. Press the **SAMPLE** button to select a sample.
2. Press the **TRIG** button to trigger the sample.
3. Listen to the output through your headphones or speakers to ensure the sample plays correctly.

## Exercise 2: Your First Working Experiment
### Step 1: Set Up a Simple Sequence
1. Press the **SEQ** button to enter sequence mode.
2. Press the **PATTERN** button to select Pattern 00.
3. Press the **STEP** button to navigate to Step 01.
4. Press the **TRIG** button to set a trigger at Step 01.
5. Press the **STEP** button to navigate to Step 02 and set another trigger.
6. Continue setting triggers at Steps 03, 04, 05, and 06.

### Step 2: Play the Sequence
1. Press the **PLAY** button to start the sequence.
2. Observe the LED lights on the steps to confirm the sequence is playing correctly.
3. Listen to the output to ensure the sample is triggered at the correct steps.

### Expected Output
- The sample should play at Steps 01, 02, 03, 04, 05, and 06.
- The LED lights on the steps should light up in sequence as the pattern plays.

## Exercise 3: Inspecting Basic State
### Step 1: Check the Display
1. Observe the display to ensure it shows the correct pattern and step numbers.
2. Verify that the **SEQ** button is lit, indicating sequence mode.

### Step 2: Monitor MIDI Output (Optional)
1. In your DAW, open the MIDI monitor or MIDI input section.
2. Start the sequence and observe the incoming MIDI messages.
3. Confirm that the MIDI messages correspond to the steps where triggers are set.

### Expected Output
- The display should correctly reflect the current pattern and step.
- The MIDI monitor should show MIDI note-on messages at the steps where triggers are set.

## Challenge Exercise: Simple Self-Test for Beginners
### Step 1: Create a Simple Melody
1. Press the **SAMPLE** button to select a different sample, such as a drum sound.
2. Navigate to Pattern 01 using the **PATTERN** button.
3. Set triggers at Steps 01, 03, 05, and 07.
4. Press the **PLAY** button to start the sequence.

### Step 2: Modify the Sequence
1. Navigate to Step 02 and set a trigger.
2. Navigate to Step 04 and set a trigger.
3. Navigate to Step 06 and set a trigger.
4. Press the **PLAY** button to start the sequence.

### Expected Output
- The sequence should now play a simple rhythm with triggers at Steps 01, 02, 03, 04, 05, 06, and 07.
- The LED lights should light up in sequence as the pattern plays.
- The sample should play at the correct steps, creating a simple rhythmic pattern.

By completing this lab, you should have a basic understanding of how to set up and use a hardware sequencer. Feel free to explore further by experimenting with different samples, patterns, and settings.
