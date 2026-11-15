# Operational Verification Labs: Glitch Mechanics

## Objective & Operational Lab Setup

Glitch mechanics is the systematic study and exploitation of unintended software behavior in retro game hardware. Like any craft, it demands precision instrumentation, a disciplined methodology, and a thorough understanding of the materials—in this case, the memory architecture, CPU instruction flow, and data structures of 8-bit and 16-bit game platforms. These labs treat the NES and Game Boy as physical systems whose behavior can be measured, modeled, and predicted, using the same analytical rigor a machinist brings to spindle runout or a woodworker brings to grain orientation.

The analytical environment consists of three layers. First, a cycle-accurate or near-cycle-accurate emulator with integrated debugging tools serves as the primary instrument: FCEUX for the NES, and BizHawk for multi-platform work including the Game Boy. These emulators provide hex editors, memory scanners, RAM watch windows, trace loggers, and Lua scripting interfaces that function collectively as the oscilloscope and dial indicator of glitch analysis. Second, quantitative spreadsheets (Excel, LibreOffice Calc, or Google Sheets) capture frame-by-frame memory state transitions, parameter matrices, and statistical distributions of outcomes. Third, empirically derived audit rubrics provide reproducibility verification, ensuring that a documented glitch can be triggered reliably across sessions and that the underlying mechanism is understood rather than merely memorized.

### Required Tools

| Tool | Platform | Role |
|------|----------|------|
| FCEUX 2.6.0+ | NES | Hex editor, RAM search/watch, trace logger, Lua scripting |
| BizHawk 2.9+ | Game Boy / Multi-system | Memory domains, RAM watch, Lua scripting, TAS editor |
| Spreadsheet software | Any | Frame logs, parameter matrices, statistical analysis |
| Text editor | Any | Lua script authoring, CSV templates |
| ROM images (user-provided) | NES / Game Boy | Super Mario Bros. (NES), Pokemon Red or Blue (Game Boy) |

### Project Directory Structure

```
glitch_mechanics_lab/
├── smb/
│   ├── smb_wallclip_monitor.lua
│   ├── frame_log_template.csv
│   └── analysis_results.csv
├── pokemon/
│   ├── missingno_monitor.lua
│   ├── encounter_matrix.csv
│   └── species_index_table.csv
├── shared/
│   ├── audit_rubric.csv
│   └── diagnostic_checklist.md
└── results/
    ├── exercise1_findings.md
    ├── exercise2_findings.md
    └── exercise3_findings.md
```

### Initial Environment Verification

Before beginning any lab exercise, verify that the emulator and Lua scripting environment are functional. In FCEUX, load the target ROM, then open the Lua scripting window (File → Load Lua Script or via the Tools menu). Run a minimal verification script that reads a known RAM address and displays it on screen. For SMB on the NES, address `$075A` contains the game timer's frame counter, which increments every frame during gameplay. A working Lua environment will display a value that changes each frame. In BizHawk, the verification target for Pokemon Red/Blue is address `$D057`, the wild encounter rate byte for the current map, which reads as a nonzero value on most routes and zero in towns. If these reads return consistent, changing values, the environment is operational.

Use only ROM images derived from your own legitimately acquired cartridges. The analytical procedures in these labs are designed for the unmodified US release of Super Mario Bros. (NES, CRC32 `8E75DF9A`) and Pokemon Red (Game Boy, CRC32 `2BB6EEA5`) or Pokemon Blue (CRC32 `776B4CD9`). Modified or translated ROMs may have different memory layouts, and every address in this guide must be re-verified against the specific ROM in use.

---

## Exercise 1: Foundational Practical Implementation

### Case Study: Super Mario Bros. (NES) — Wall Clip Subpixel Analysis and Wrong Warp Destination

The foundational glitch in SMB speedrunning and glitch hunting is the wall clip, a collision-detection edge case that allows Mario to pass through solid tiles by exploiting the interaction between ducking hitbox reduction, backward movement physics, and subpixel positioning. Understanding this glitch requires grounding in three mechanical systems: the NES's 6502-based memory map for game state, the subpixel physics engine SMB uses for movement, and the warp destination lookup table that determines which world a pipe transports Mario to.

SMB tracks Mario's horizontal position in three layers: a page number (which 256-pixel screen slice of the level Mario occupies), a pixel offset within that page, and a subpixel fraction that represents position to a precision of 1/256 of a pixel. The page location is stored at RAM address `$006D`, the pixel position at `$0086`, and the subpixel fraction at `$0087`. Every frame, the game adds Mario's current speed to his position, accumulating the subpixel carry into the pixel position, and the pixel carry into the page number. When Mario moves left while facing right—a state the game enters when the player holds Left on the D-pad during a duck-jump—the collision check for the leftward direction uses a different code path than forward movement. This backward collision check interacts with Mario's reduced ducking hitbox in a way that fails to detect certain wall tiles, allowing position to decrement through solid geometry one subpixel at a time.

The warp zone in World 1-2 contains three pipes leading to Worlds 2, 3, and 4. The destination for each pipe is read from a data table indexed by the pipe's position within the warp zone area. When Mario enters the warp zone through the normal route (from below, through the exit pipe), the screen has scrolled to the correct position and the page location is correct, so the pipe destination lookup returns a valid world number. When Mario clips through the wall and enters the warp zone from the side, the page location value at `$006D` is in a state the warp table lookup does not expect, causing the game to read a destination value that maps to World 36, which the display routine renders as "-1" because it lacks a character for two-digit world numbers above 8. The resulting "Minus World" is a water level assembled from garbage level data that loops endlessly.

### Step 1: FCEUX Environment Setup

Load the Super Mario Bros. ROM in FCEUX. Open the Hex Editor from the Tools menu. Open the RAM Watch window from the Tools menu. Open a new Lua script window. Configure the RAM Watch with the following addresses, entering each manually through the Add button:

| Label | Address | Size | Type |
|-------|---------|------|------|
| PageLoc | 006D | 1 byte | Decimal |
| X_Pos | 0086 | 1 byte | Decimal |
| X_Subpix | 0087 | 1 byte | Decimal |
| Y_Pos | 0094 | 1 byte | Decimal |
| Y_Subpix | 0095 | 1 byte | Decimal |
| AutoCtrl | 0069 | 1 byte | Decimal |
| PowerUp | 0075 | 1 byte | Decimal |

These seven addresses form the core observation set for the wall clip analysis. PageLoc determines the warp destination lookup index. X_Pos and X_Subpix track Mario's horizontal position at pixel and subpixel resolution. Y_Pos and Y_Subpix do the same for vertical position, critical for detecting when Mario has fallen through the wall into the warp zone area. AutoCtrl tracks the pipe entry/exit state machine, which transitions from normal gameplay (0) to pipe-entry animation and warp execution. PowerUp confirms Mario's current state (0 for small, 1 for super, 2 for fire), which affects hitbox dimensions.

### Step 2: Lua Monitoring Script

The following Lua script provides on-screen overlay of all seven watched values, with subpixel values displayed as both raw bytes and fractional pixel equivalents. It logs all values to a CSV file every frame, creating a frame-by-frame record of the memory state during the glitch. Save this script as `smb/smb_wallclip_monitor.lua` and run it in FCEUX.

```lua
-- SMB Wall Clip Memory Analysis Monitor
-- FCEUX Lua 5.1 / 5.3 compatible
-- Logs frame-by-frame RAM state during the wall clip glitch

local ADDR = {
    PageLoc  = 0x006D,
    X_Pos    = 0x0086,
    X_Subpix = 0x0087,
    Y_Pos    = 0x0094,
    Y_Subpix = 0x0095,
    AutoCtrl = 0x0069,
    PowerUp  = 0x0075,
}

local LOG_PATH = "smb/frame_log.csv"
local log_file = io.open(LOG_PATH, "w")
if log_file then
    log_file:write("Frame,PageLoc,X_Pos,X_Subpix,Y_Pos,Y_Subpix,AutoCtrl,PowerUp,Note\n")
end

local frame = 0
local logging = true
local prev_autoctrl = 0
local prev_page = 0
local note = ""

while true do
    local v = {}
    for name, addr in pairs(ADDR) do
        v[name] = memory.readbyte(addr)
    end

    -- Detect state transitions for annotation
    if v.AutoCtrl ~= prev_autoctrl then
        note = string.format("AutoCtrl %d->%d", prev_autoctrl, v.AutoCtrl)
    elseif v.PageLoc ~= prev_page then
        note = string.format("PageLoc %d->%d", prev_page, v.PageLoc)
    else
        note = ""
    end
    prev_autoctrl = v.AutoCtrl
    prev_page = v.PageLoc

    -- On-screen overlay
    local y = 8
    gui.text(8, y, string.format("Frame: %d", frame))
    y = y + 12
    gui.text(8, y, string.format("PageLoc:   %3d  (0x%02X)", v.PageLoc, v.PageLoc))
    y = y + 12
    gui.text(8, y, string.format("X_Pos:     %3d px", v.X_Pos))
    y = y + 12
    gui.text(8, y, string.format("X_Subpix:  %3d   (%.3f px)", v.X_Subpix, v.X_Subpix / 256))
    y = y + 12
    gui.text(8, y, string.format("Y_Pos:     %3d px", v.Y_Pos))
    y = y + 12
    gui.text(8, y, string.format("Y_Subpix:  %3d   (%.3f px)", v.Y_Subpix, v.Y_Subpix / 256))
    y = y + 12
    gui.text(8, y, string.format("AutoCtrl:  %3d  (0x%02X)", v.AutoCtrl, v.AutoCtrl))
    y = y + 12
    gui.text(8, y, string.format("PowerUp:   %3d", v.PowerUp))
    y = y + 12
    if note ~= "" then
        gui.text(8, y, ">> " .. note)
    end

    -- CSV log
    if logging and log_file then
        log_file:write(string.format("%d,%d,%d,%d,%d,%d,%d,%d,%s\n",
            frame, v.PageLoc, v.X_Pos, v.X_Subpix,
            v.Y_Pos, v.Y_Subpix, v.AutoCtrl, v.PowerUp, note))
        log_file:flush()
    end

    frame = frame + 1
    emu.frameadvance()
end
```

The script opens a CSV file at startup and writes one row per frame. The `Note` column captures state transitions: when `AutoCtrl` changes, the script records the previous and new values, marking the frame where the pipe entry animation begins or the warp executes. When `PageLoc` changes, it records the page transition, which is the critical event for the wrong warp. The `flush()` call after each write ensures no data is lost if the script is stopped abruptly.

### Step 3: Performing the Wall Clip

Begin a new game. Play through World 1-1 to reach World 1-2. In the underground section, navigate to the far right end of the level where the exit pipe (the pipe that goes upward to the surface) is located. Do not enter this pipe. Instead, perform the following procedure exactly:

1. Stand on top of the exit pipe, at the rightmost edge of the pipe surface.
2. Hold Down on the controller to duck. Mario's sprite compresses to half height. This reduces his vertical hitbox, which is the enabling condition for the clip.
3. While holding Down, also hold Left on the D-pad.
4. Press and release the A button (jump) repeatedly, approximately once every 4-5 frames. Each jump while holding Left and Down causes Mario to shift leftward by a fraction of a pixel, bypassing the wall collision check.
5. Continue this rhythm for approximately 30-40 jumps. You will see Mario slowly sink through the wall to the left of the pipe.
6. Once Mario has visually passed through the wall and fallen into the warp zone area below, release Down and Left. Mario is now in the warp zone corridor.
7. Walk to the leftmost pipe and enter it by pressing Down while standing on top.

During step 5, watch the Lua overlay. The `X_Subpix` value will decrement with each jump. The `X_Pos` value will decrease by one each time the subpixel wraps from 0 to 255 (the borrow propagates to the pixel position). The `PageLoc` value should remain stable until Mario falls into the warp zone, at which point it may change as the game loads the warp zone screen. When Mario enters the pipe in step 7, `AutoCtrl` transitions from 0 to a nonzero value, and `PageLoc` will read a value inconsistent with normal warp zone entry.

### Step 4: Frame-by-Frame Documentation and Analysis

After performing the glitch, stop the Lua script and open the generated `frame_log.csv` in your spreadsheet software. The CSV contains hundreds of rows (one per frame), but the critical data is the 10-15 frames surrounding two events: the moment Mario falls through the wall (detectable by a sudden `Y_Pos` change), and the moment the warp executes (detectable by an `AutoCtrl` transition).

Import the CSV and apply the following analysis:

**Wall Penetration Event**: Filter for rows where `Y_Pos` decreases by more than 10 in a single frame. This marks the frame where Mario falls through the floor into the warp zone area. Record the `PageLoc`, `X_Pos`, and `X_Subpix` values at this frame. Compare them to the values from a normal pipe entry (perform the level again, entering the pipe normally, and compare the logged values).

**Warp Execution Event**: Filter for rows where `AutoCtrl` changes from 0. The `PageLoc` value at this transition determines the warp destination. During normal entry, `PageLoc` should read a value consistent with the warp zone screen. During glitched entry, `PageLoc` will read a different value, which the warp destination lookup table maps to World 36 (displayed as -1).

Enter your findings into the analysis results template:

```
Event,Frame,PageLoc,X_Pos,X_Subpix,Y_Pos,Y_Subpix,AutoCtrl,Observation
Normal entry pipe,,,,,,,,
Wall clip penetration,,,,,,,,
Warp execution (normal),,,,,,,,,
Warp execution (glitched),,,,,,,,,
```

Fill each row with the frame number and RAM values at the corresponding event. The `Observation` column should note the resulting world number (2, 3, or 4 for normal; -1 for glitched).

### Expected Outcomes

The wall clip succeeds because the backward-movement collision check in SMB uses a simplified hitbox test that does not account for the reduced height of the ducking sprite. When Mario jumps while ducking and holding left, the game applies leftward velocity but the collision routine checks for walls at Mario's full standing height rather than his ducking height, causing it to miss the wall tiles that are above Mario's reduced hitbox. The subpixel accumulation from repeated small jumps moves Mario through the wall incrementally.

The wrong warp occurs because the warp zone's pipe destination table is indexed by a value derived from the screen's scroll position. Normal entry scrolls the screen to the warp zone before the pipe is entered, setting `PageLoc` to the correct index. Clipped entry bypasses the scroll, leaving `PageLoc` at a value that causes the destination lookup to read past the end of the valid warp table, returning a byte that the game interprets as World 36. The level data for World 36 does not exist as a designed level; instead, the game loads whatever data happens to be at the memory offset for World 36-1, which in the US ROM is a repeating water level layout that never reaches a flagpole, creating the endless Minus World.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Case Study: Pokemon Red/Blue (Game Boy) — MissingNo. Encounter Table Manipulation

The MissingNo. glitch is a buffer management failure in Pokemon Red and Blue that produces wild encounters determined by the bytes of the player's name. The mechanism operates through a sequence of events that leave stale data in a memory region the game uses for wild Pokemon encounter tables, combined with a map design oversight on Cinnabar Island that causes the coastal water tiles to reference this stale data rather than a properly defined encounter table.

When the player watches the Old Man's Pokemon-catching tutorial in Viridian City, the game temporarily changes the player's displayed name to "OLD MAN." To preserve the player's real name during this change, the game copies the name string to a temporary storage location. That location happens to overlap with the memory region used for wild Pokemon encounter data. After the tutorial, the player's name is restored, but the temporary copy remains in the encounter data buffer, unreferenced and uncleared.

The Cinnabar Island map has a design flaw: the eastern coast tiles are coded as water tiles that trigger wild encounters, but the map's encounter data pointer was never assigned a valid encounter table. Instead, the coastal tiles reference whatever data is currently in the encounter buffer—the same buffer where the player's name was temporarily stored during the Old Man tutorial. When the player surfs along the coast, the game reads the name bytes as encounter table data, interpreting each byte according to the encounter table structure.

The encounter table structure in Gen 1 is a 20-byte block. The first byte is the encounter rate. The next ten bytes define five encounter slots, each consisting of a level byte followed by a species index byte. When the player's 7-byte name occupies this buffer, the mapping is:

| Name Position | Buffer Offset | Encounter Table Role |
|--------------|----------------|----------------------|
| 1st character | 0 | Grass encounter rate |
| 2nd character | 1 | Level for species slot 1 |
| 3rd character | 2 | Species index for slot 1 |
| 4th character | 3 | Level for species slot 2 |
| 5th character | 4 | Species index for slot 2 |
| 6th character | 5 | Level for species slot 3 |
| 7th character | 6 | Species index for slot 3 |

The species index is the game's internal Pokemon index number, which is different from the Pokedex number. The internal index follows the order Pokemon data appears in the ROM, not the Pokedex ordering. For example, internal index `0x01` corresponds to Rhydon (Pokedex #112), and internal index `0x00` corresponds to the glitch Pokemon 'M.

The character encoding in Pokemon Red/Blue uses the following hex values:

| Character | Hex Value | Character | Hex Value |
|-----------|-----------|-----------|-----------|
| (space) | 0x7F | A | 0x80 |
| B | 0x81 | C | 0x82 |
| D | 0x83 | E | 0x84 |
| F | 0x85 | G | 0x86 |
| H | 0x87 | I | 0x88 |
| J | 0x89 | K | 0x8A |
| L | 0x8B | M | 0x8C |
| N | 0x8D | O | 0x8E |
| P | 0x8F | Q | 0x90 |
| R | 0x91 | S | 0x92 |
| T | 0x93 | U | 0x94 |
| V | 0x95 | W | 0x96 |
| X | 0x97 | Y | 0x98 |
| Z | 0x99 | ( | 0x9A |
| ) | 0x9B | : | 0x9C |
| ; | 0x9D | ! | 0x9E |
| ? | 0x9F | . | 0xA1 |
| 0 | 0xF6 | 1 | 0xF7 |
| 2 | 0xF8 | 3 | 0xF9 |
| 4 | 0xFA | 5 | 0xFB |
| 6 | 0xFC | 7 | 0xFD |
| 8 | 0xFE | 9 | 0xFF |

The terminator character is `0x50`, which marks the end of the name string. If the name is shorter than 7 characters, the remaining bytes after the terminator contain whatever was previously in that memory location, which may be residual data from prior game operations.

### Step 1: BizHawk Environment Setup

Load the Pokemon Red or Blue ROM in BizHawk. Open the Memory Watch window (Tools → Memory Watch). Open the Lua Console (Tools → Lua Console). Create a new Lua script tab and prepare to paste the monitoring script below.

The player's name is stored in Game Boy WRAM at address `$D158`, occupying 7 bytes followed by a `$50` terminator. In BizHawk's memory model, the "System Bus" domain maps to the full Game Boy address space, so `$D158` can be read directly using that domain.

### Step 2: Lua Monitoring Script

The following script reads the player's name buffer, decodes each character, identifies the encounter-relevant positions, and displays the predicted species indices on screen. It also logs the full name buffer contents (including any padding bytes after the terminator) to a CSV file for offline analysis.

```lua
-- Pokemon Red/Blue MissingNo. Encounter Predictor
-- BizHawk Lua (EmuHawk 2.9+)
-- Monitors player name buffer and predicts wild encounters on Cinnabar coast

local DOMAIN = "System Bus"
local NAME_ADDR = 0xD158
local LOG_PATH = "pokemon/name_buffer_log.csv"

-- Gen 1 character code to display string
local function decodeChar(code)
    if code == 0x50 then return "[END]" end
    if code == 0x7F then return " " end
    if code >= 0x80 and code <= 0x99 then
        return string.char(65 + (code - 0x80))
    end
    if code >= 0xF6 and code <= 0xFF then
        return string.char(48 + (code - 0xF6))
    end
    local specials = {
        [0x9A] = "(", [0x9B] = ")", [0x9C] = ":",
        [0x9D] = ";", [0x9E] = "!", [0x9F] = "?",
        [0xA1] = ".", [0xE1] = "[M]", [0xE2] = "[F]",
    }
    if specials[code] then return specials[code] end
    return string.format("[%02X]", code)
end

local log_file = io.open(LOG_PATH, "w")
if log_file then
    log_file:write("Frame,Byte0,Byte1,Byte2,Byte3,Byte4,Byte5,Byte6,Byte7,NameStr\n")
end

local frame = 0

while true do
    -- Read 8 bytes from the name buffer (7 name chars + terminator)
    local bytes = {}
    local name_str = ""
    for i = 0, 7 do
        bytes[i] = memory.readbyte(NAME_ADDR + i, DOMAIN)
        if bytes[i] ~= 0x50 then
            name_str = name_str .. decodeChar(bytes[i])
        end
    end

    -- Determine effective name length (up to terminator)
    local name_len = 0
    for i = 0, 6 do
        if bytes[i] == 0x50 then break end
        name_len = name_len + 1
    end

    -- Display header
    gui.text(10, 8, "=== MissingNo. Encounter Predictor ===")
    gui.text(10, 22, "Name: " .. name_str .. "  (" .. name_len .. " chars)")

    -- Display full buffer contents
    local y = 38
    for i = 0, 6 do
        local display = decodeChar(bytes[i])
        local role = ""
        if i == 0 then role = "Encounter Rate"
        elseif i == 1 then role = "Lvl Slot 1"
        elseif i == 2 then role = "Species Slot 1"
        elseif i == 3 then role = "Lvl Slot 2"
        elseif i == 4 then role = "Species Slot 2"
        elseif i == 5 then role = "Lvl Slot 3"
        elseif i == 6 then role = "Species Slot 3"
        end
        gui.text(10, y, string.format("Byte %d: 0x%02X (%3d) %-16s %s",
            i, bytes[i], bytes[i], display, role))
        y = y + 12
    end

    -- Predicted encounters
    y = y + 4
    gui.text(10, y, "=== Predicted Species ===")
    y = y + 12

    local predictions = {}
    if name_len >= 3 then
        table.insert(predictions, {slot = 1, char_idx = 2, code = bytes[2]})
    end
    if name_len >= 5 then
        table.insert(predictions, {slot = 2, char_idx = 4, code = bytes[4]})
    end
    if name_len >= 7 then
        table.insert(predictions, {slot = 3, char_idx = 6, code = bytes[6]})
    end

    for _, p in ipairs(predictions) do
        gui.text(10, y, string.format("Slot %d: Species index 0x%02X (%d)",
            p.slot, p.code, p.code))
        y = y + 12
    end

    -- If name is shorter than 7, show residual bytes
    if name_len < 7 then
        y = y + 4
        gui.text(10, y, "=== Residual Bytes (past terminator) ===")
        y = y + 12
        for i = name_len + 1, 6 do
            if bytes[i] ~= 0x50 then
                gui.text(10, y, string.format("Byte %d: 0x%02X (%d) — RESIDUAL DATA",
                    i, bytes[i], bytes[i]))
                y = y + 12
            end
        end
    end

    -- Log to CSV
    if log_file then
        log_file:write(string.format("%d,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%s\n",
            frame, bytes[0], bytes[1], bytes[2], bytes[3],
            bytes[4], bytes[5], bytes[6], bytes[7], name_str))
        log_file:flush()
    end

    frame = frame + 1
    emu.frameadvance()
end
```

The script reads 8 bytes from `$D158` through `$D15F` and displays each with its character decode, raw hex, decimal value, and role in the encounter table structure. For names shorter than 7 characters, the script flags any non-terminator bytes beyond the name's end as "residual data," which are particularly interesting because they may produce unexpected encounters that differ from what published guides predict based on name characters alone.

### Step 3: Triggering the MissingNo. Glitch

Perform the following procedure in-game, with the Lua script running:

1. Start a new game or load an existing save. Name the player character "AAAAAAA" (seven A's) for the first test case. This produces species index `0x80` (128 decimal) for all three species slots, since every odd-positioned character is A.

2. Play through the game until you reach Viridian City and can access the Old Man who demonstrates Pokemon catching. He is located on the north side of Viridian City, blocking the path to Route 2 until you deliver Oak's Parcel.

3. Talk to the Old Man and answer "No" to his question about whether you know how to catch Pokemon. Watch the full catching demonstration. When he throws the Poke Ball and catches the Weedle, the game has stored your player's name in the encounter data buffer.

4. After the tutorial ends, use Fly to travel immediately to Cinnabar Island. Do not enter any building, do not walk through any grass, and do not engage in any wild encounter between the tutorial and arriving at Cinnabar. Any map transition that loads new encounter data will overwrite the name bytes in the buffer.

5. At Cinnabar Island, walk to the east coast. Face the water and use Surf. Move up and down along the coastline, staying on the water tiles that are directly adjacent to the land tiles of Cinnabar Island. Do not surf further east into the open water.

6. Within a few seconds of surfing on the coast, a wild encounter will trigger. The encountered Pokemon will be determined by the name bytes in the buffer. Record the species name and level of the encountered Pokemon.

7. Run from the encounter (or catch it). Continue surfing up and down the coast. Multiple encounters will occur, cycling through the species determined by the 3rd, 5th, and 7th characters of the name, with some encounters being MissingNo. or 'M variants.

### Step 4: Systematic Name Variation Testing

The core of this exercise is building a quantitative matrix that maps player name characters to encountered Pokemon. Test each of the following names, following the complete procedure (Old Man tutorial → Fly to Cinnabar → Surf on coast) for each one:

**Test Matrix A — Varying the 3rd character (Species Slot 1)**

| Test Name | Char 3 | Hex | Species Index | Encountered Pokemon |
|-----------|--------|-----|---------------|---------------------|
| AAAAAAA | A | 0x80 | 128 | |
| BBBBBBB | B | 0x81 | 129 | |
| CCCCCCC | C | 0x82 | 130 | |
| DDDDDDD | D | 0x83 | 131 | |
| EEEEEEE | E | 0x84 | 132 | |
| FFFFFFF | F | 0x85 | 133 | |
| GGGGGGG | G | 0x86 | 134 | |
| HHHHHHH | H | 0x87 | 135 | |
| IIIIIII | I | 0x88 | 136 | |
| JJJJJJJ | J | 0x89 | 137 | |
| KKKKKKK | K | 0x8A | 138 | |
| LLLLLLL | L | 0x8B | 139 | |
| MMMMMMM | M | 0x8C | 140 | |
| NNNNNNN | N | 0x8D | 141 | |
| OOOOOOO | O | 0x8E | 142 | |
| PPPPPPP | P | 0x8F | 143 | |
| QQQQQQQ | Q | 0x90 | 144 | |
| RRRRRRR | R | 0x91 | 145 | |
| SSSSSSS | S | 0x92 | 146 | |
| TTTTTTT | T | 0x93 | 147 | |
| UUUUUUU | U | 0x94 | 148 | |
| VVVVVVV | V | 0x95 | 149 | |
| WWWWWWW | W | 0x96 | 150 | |
| XXXXXXX | X | 0x97 | 151 | |
| YYYYYYY | Y | 0x98 | 152 | |
| ZZZZZZZ | Z | 0x99 | 153 | |

To execute each test: start a new game, name the player with the test name, play to Viridian City, perform the Old Man tutorial, Fly to Cinnabar, surf the coast, and record at least 10 encounters per test name. For each encounter, record the species name, the level, and whether the Pokemon is a glitch Pokemon (MissingNo., 'M, or other anomalous species).

The level of each encounter is determined by the even-positioned characters (2nd, 4th, 6th). For names where all characters are the same letter, all three level values will be identical. The hex value of that letter becomes the level. For "AAAAAAA", the encounter level for all slots is `0x80` = 128. Since Gen 1 displays levels up to 100, a level-128 encounter will display as level 128 (the game does not cap the display for glitch encounters), confirming that the level byte is read directly from the name.

### Step 5: Building the Encounter Prediction Matrix

Create a spreadsheet file `pokemon/encounter_matrix.csv` with the following column structure:

```
TestName,Char3,Char3_Hex,Char3_Species,Char5,Char5_Hex,Char5_Species,Char7,Char7_Hex,Char7_Species,Encounter1_Name,Encounter1_Level,Encounter2_Name,Encounter2_Level,Encounter3_Name,Encounter3_Level,Glitch_Flag,Notes
```

For each test name, record the observed encounters. The `Glitch_Flag` column should be set to 1 if the encountered Pokemon is MissingNo., 'M, or any other glitch species, and 0 if it is a valid Pokemon. The `Notes` column should capture any anomalous behavior: sprite corruption, game slowdown, missing audio, or save data corruption.

After completing Test Matrix A (26 test names), you will have a partial species index table mapping internal index numbers 128 through 153 to their corresponding Pokemon. Some of these indices will map to valid Pokemon; others will map to glitch Pokemon or MissingNo. variants.

**Test Matrix B — Varying name length to observe residual data**

Names shorter than 7 characters leave bytes in the buffer that are not part of the name. These bytes may contain residual data from prior game operations, producing encounters that depend on game state rather than name content. Test the following names to observe this effect:

| Test Name | Length | Expected Slots Active | Residual Bytes |
|-----------|--------|----------------------|----------------|
| A | 1 char | Slot 1 only (byte 2 = residual) | Bytes 2-6 |
| AB | 2 chars | Slot 1 only (byte 2 = residual) | Bytes 2-6 |
| ABC | 3 chars | Slot 1 active; slots 2-3 residual | Bytes 4-6 |
| ABCDE | 5 chars | Slots 1-2 active; slot 3 residual | Byte 6 |
| ABCDEFG | 7 chars | All 3 slots active | None |

For each short name, run the Lua script and observe what bytes appear in the positions past the terminator. Surf the coast and record encounters. The residual bytes will vary depending on what the game was doing before the name was set—whether the player had just completed a battle, entered a building, or performed other actions that wrote data to the buffer region. This is why the MissingNo. encounter for short names is less predictable and why some players report encountering different Pokemon with the same short name.

### Step 6: Statistical Analysis of Encounter Distributions

After collecting encounter data for at least 10 test names from Matrix A, perform the following statistical analysis in the spreadsheet:

**Encounter Rate Distribution**: For each test name, count the number of encounters over a fixed time period (surfn for exactly 2 minutes of real time, or 60 encounters, whichever comes first). The encounter rate is determined by the 1st character of the name (the encounter rate byte). Calculate the mean and standard deviation of encounter frequency across test names with different first characters. Names starting with letters near the end of the alphabet (high hex values) should produce higher encounter rates, since the encounter rate byte scales with the character's hex value.

**Species Distribution**: For each test name, tally the number of times each predicted species appears versus the number of times MissingNo. or other glitch species appear. Calculate the percentage of encounters that match the predicted species versus glitch encounters. A well-functioning encounter table should produce the predicted species in approximately 20% of encounters (since there are 5 slots, each with roughly equal probability). Deviations from this ratio indicate that the encounter table structure is being read differently than expected, possibly due to the encounter rate byte affecting slot weighting.

**Chi-Square Test**: For a test name where all three species slots predict the same species (e.g., "AAAAAAA" predicts species index 128 for all three slots), perform a chi-square goodness-of-fit test on the encounter distribution. If the encounter table is read correctly, all encounters should be the same species. If MissingNo. appears at a rate higher than expected (above 5%), the residual bytes or encounter table structure is introducing additional species not predicted by the name analysis.

Record all statistical results in the analysis results document, including the raw data, calculated means, standard deviations, and any chi-square test results.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The first two exercises establish the mechanism and parameter space of two glitch families. This exercise pushes both glitches to their boundaries, documenting the exact conditions under which they succeed, fail, and produce crash states. Stress testing in glitch mechanics serves the same purpose as destructive testing in materials science: it reveals the failure modes and the precise thresholds at which the system transitions from functional to broken, which in turn confirms the mechanism hypothesized in the earlier exercises.

### Part A: SMB Wall Clip Boundary Mapping

The wall clip in SMB depends on Mario's subpixel position at the moment the duck-jump is initiated. Not all subpixel values allow the clip; the collision check has a narrow window where the ducking hitbox fails to detect the wall tile. This exercise maps that window precisely.

**Procedure:**

1. Load SMB in FCEUX with the Lua monitoring script running.
2. Reach the wall clip location in World 1-2 (on top of the exit pipe).
3. Use FCEUX's frame advance feature (press the Frame Advance key, default is the period key) to step through the game one frame at a time.
4. At each frame, note the `X_Subpix` value displayed by the Lua script. The subpixel value cycles through 0-255 as Mario moves.
5. For each of the following target subpixel values, use FCEUX's memory editor to set `$0087` (X_Subpix) to the target value, then perform the duck-jump-left sequence for exactly one jump:
   - Target values: 0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0, 0xE0 (every 32 subpixels, covering the full range)
6. After each test jump, observe whether Mario moved left (clip succeeded) or was blocked (clip failed). Record the result.

Build a boundary map in `smb/boundary_map.csv`:

```
Subpix_Target,Subpix_Actual,Clip_Result,X_Pos_After,X_Subpix_After,Notes
0x00,,,,,
0x20,,,,,
0x40,,,,,
0x60,,,,,
0x80,,,,,
0xA0,,,,,
0xC0,,,,,
0xE0,,,,,
```

After the coarse sweep, perform a fine sweep around any subpixel value where the clip transitions from success to failure. For example, if the clip succeeds at 0x40 but fails at 0x60, test values 0x44, 0x48, 0x4C, 0x50, 0x54, 0x58, 0x5C to find the exact boundary.

The boundary reveals the collision check's effective hitbox height when ducking. The clip succeeds when the subpixel position places Mario's reduced hitbox below the wall tile's collision detection threshold. The boundary should correspond to a consistent subpixel offset that represents the geometric relationship between the ducking hitbox (approximately 12 pixels tall versus 16 pixels standing) and the wall tile position.

**Crash Conditions:**

Test the following edge cases to document failure modes:

1. **Small Mario wall clip**: Perform the clip as small Mario (PowerUp = 0) instead of super Mario (PowerUp = 1). Small Mario's hitbox is already reduced, so the ducking hitbox is different. Record whether the clip is possible and if the resulting warp differs.

2. **Fire Mario wall clip**: Perform the clip as fire Mario (PowerUp = 2). The hitbox is the same as super Mario, but test to confirm.

3. **Pipe entry from different positions**: After clipping through the wall, enter the middle pipe and the right pipe instead of the leftmost pipe. Record the warp destination for each. Different pipes read different offsets in the warp table, producing different invalid world numbers.

4. **Multiple clips in sequence**: After reaching the Minus World, attempt to perform another wall clip. The Minus World's level data is garbage, so collision detection may behave differently. Document any crashes.

**Recovery Protocol:**

If the game crashes during stress testing (black screen, frozen frame, garbage graphics), the recovery is simple: reset the emulator. However, document the crash condition in a crash log:

```
Crash_Condition,PowerUp,Subpix,PageLoc,AutoCtrl,Symptom,Reproducible
Small Mario clip at subpix 0x80,0,0x80,?,?,Black screen,Yes
```

### Part B: Pokemon MissingNo. Boundary Testing

The MissingNo. encounter depends on the name buffer contents, but several boundary conditions can produce unexpected results or crashes.

**Procedure:**

1. **Minimum length name**: Name the player with a single character (e.g., "A"). The encounter table buffer will have 1 byte of name data followed by the terminator and 5 bytes of residual data. Surf the Cinnabar coast and record encounters. The residual bytes determine species slots 2 and 3, and these bytes vary based on prior game state. Run the Lua script to observe what bytes are actually in the buffer.

2. **All-spaces name**: Name the player with 7 spaces. Each space is `0x7F` (127). All three species slots will read species index 127. Record what Pokemon appears at index 127 and whether the game crashes.

3. **Maximum hex value characters**: Name the player "9999999". Each 9 is `0xFF` (255), the highest valid character code. Species index 255 may be beyond the species table, producing a glitch entity or crashing. Record the result.

4. **Special character names**: Name the player using special characters where possible: "!!!!!!!!" (7 exclamation marks, each `0x9E`). Species index `0x9E` (158) tests the upper range of the internal species table. Record what appears.

5. **Name buffer corruption**: After triggering the MissingNo. encounter at least once, check whether the name buffer has been corrupted by viewing it in the Lua script or BizHawk's memory viewer. Some MissingNo. encounters corrupt the player's name or other save data by writing garbage to the name buffer during the encounter. If corruption is detected, document which bytes changed and to what values.

**Crash Conditions and Recovery:**

MissingNo. encounters can corrupt save data, particularly the Hall of Fame data and item inventory. Document any corruption observed:

```
Condition,Name,Species_Encountered,Level,Corruption_Type,Corrupted_Addresses,Reproducible
9999999,9999999,?,?,Crash/Black screen,,Yes
All spaces,[7 spaces],?,?,?,?,No
```

If the game crashes during an encounter (freezing on the battle screen with garbled graphics), perform the following recovery:

1. Reset the emulator (do not save state).
2. If the save file is corrupted (player name changed, items duplicated, badges removed), document the corruption in the crash log.
3. If the save file is unrecoverable, start a new game. This is expected behavior for certain MissingNo. variants, particularly 'M (index 0x00), which is known to corrupt the save file's checksum.

For safe testing, create a save state before each MissingNo. encounter test. If corruption occurs, load the save state to restore the pre-corruption state. This is the equivalent of a machinist's practice of keeping a reference workpiece: it provides a known-good baseline to return to after destructive testing.

### Part C: Diagnostic Audit Rubric

After completing all boundary tests, compile a diagnostic audit rubric that verifies the reproducibility of both glitches. This rubric serves as a quality control checklist for future glitch analysis work.

Create the file `shared/audit_rubric.csv`:

```
Test_ID,Glitch_Type,Condition,Expected_Result,Actual_Result,Pass_Fail,Reproducibility_Score,Notes
SMB-01,Wall Clip,Super Mario, clip succeeds at subpix 0x40-0x80,Minus World reached,,,1 of 5 attempts
SMB-02,Wall Clip,Small Mario, clip succeeds at subpix ?,???,,,1 of 5 attempts
SMB-03,Wall Clip,Fire Mario, clip succeeds same as super,???,,,
SMB-04,Wall Clip,Middle pipe entry,Warp to World ???,,,,
SMB-05,Wall Clip,Right pipe entry,Warp to World ???,,,,
PKM-01,MissingNo.,Name AAAAAAA,Species idx 128 at level 128,,,,
PKM-02,MissingNo.,Name BBBBBBB,Species idx 129 at level 129,,,,
PKM-03,MissingNo.,Name ZZZZZZZ,Species idx 153 at level 153,,,,
PKM-04,MissingNo.,Name 9999999,Species idx 255 / crash,,,,
PKM-05,MissingNo.,Name [1 char],Residual-dependent species,,,,
PKM-06,MissingNo.,Name [7 spaces],Species idx 127,,,,
```

The Reproducibility Score column records how many times the glitch was successfully reproduced out of 5 attempts. A score of 5/5 indicates a deterministic glitch (always triggers under the specified conditions). A score of 1/5 or 2/5 indicates a non-deterministic glitch that depends on uncontrolled variables, such as residual memory state or frame timing. The Pass/Fail column records whether the actual result matches the expected result based on the mechanism analysis.

---

## Operational Reference Guide & Diagnostic Checklist

### NES RAM Address Reference — Super Mario Bros.

| Address | Label | Size | Description |
|---------|-------|------|-------------|
| $001E | LevelOffset | 1 byte | Internal level/world tracking for display |
| $0033 | FacingDir | 1 byte | Player facing direction (0=right, 1=left) |
| $0057 | X_Speed | 1 byte | Player horizontal velocity (signed) |
| $0069 | AutoCtrl | 1 byte | Auto-control state machine (0=normal, nonzero=pipe/flagpole) |
| $006D | PageLoc | 1 byte | Player page (screen slice) location — determines warp lookup |
| $0075 | PowerUp | 1 byte | Power-up state (0=small, 1=super, 2=fire) |
| $0086 | X_Pos | 1 byte | Player X position on current screen (pixels) |
| $0087 | X_Subpix | 1 byte | Player X subpixel fraction (0-255, where 256=1 pixel) |
| $0094 | Y_Pos | 1 byte | Player Y position (pixels) |
| $0095 | Y_Subpix | 1 byte | Player Y subpixel fraction (0-255) |

To verify any address in FCEUX: open the Hex Editor, navigate to the address, and modify the value during gameplay. If the on-screen behavior changes correspondingly (e.g., changing `$0086` moves Mario's horizontal position), the address mapping is confirmed for the ROM version in use.

### Game Boy WRAM Address Reference — Pokemon Red/Blue

| Address | Label | Size | Description |
|---------|-------|------|-------------|
| $D158 | wPlayerName | 7 bytes + $50 | Player's name string, character-encoded |
| $D35E | wCurMap | 1 byte | Current map index number |
| $D368 | wPlayerX | 1 byte | Player X position on current map (tiles) |
| $D369 | wPlayerY | 1 byte | Player Y position on current map (tiles) |
| $D057 | wEncounterRate | 1 byte | Current map wild encounter rate |

To verify the player name address in BizHawk: open the Memory Viewer (Tools → Memory Viewer), set the domain to "System Bus" or "WRAM", navigate to `$D158`, and verify that the bytes match the characters of the player's name using the character encoding table above. Changing a byte in the viewer should change the corresponding letter of the player's name on the next screen that displays it (such as the Pokemon menu or a Pokemon Center).

### Pokemon Gen 1 Internal Species Index — Partial Reference

The following table provides confirmed internal index-to-species mappings. Build the complete table through empirical observation as described in Exercise 2.

| Index (Hex) | Index (Dec) | Pokemon | Pokedex # | Notes |
|-------------|-------------|---------|-----------|-------|
| 0x00 | 0 | 'M | — | Glitch, level 0 variant; corrupts save data |
| 0x01 | 1 | Rhydon | 112 | First entry in internal data order |
| 0x02 | 2 | Kangaskhan | 115 | |
| 0x03 | 3 | Nidoran♂ | 32 | |
| 0x04 | 4 | Clefairy | 35 | |
| 0x05 | 5 | Spearow | 21 | |
| 0x06 | 6 | Voltorb | 100 | |
| 0x07 | 7 | Nidoran♀ | 29 | |
| 0x08 | 8 | Jigglypuff | 39 | |
| 0x09 | 9 | Exeggutor | 103 | |
| 0x0A | 10 | Exeggcute | 102 | |
| 0x0B | 11 | Grimer | 88 | |
| 0x0C | 12 | Gengar | 94 | |
| 0x0D | 13 | Nidorino | 33 | |
| 0x0E | 14 | Nidorina | 30 | |
| 0x0F | 15 | Geodude | 74 | |
| 0x10 | 16 | Porygon | 137 | |
| 0x11 | 17 | Omastar | 139 | |
| 0x12 | 18 | Omanyte | 138 | |
| 0x13 | 19 | Jolteon | 135 | |
| 0x14 | 20 | Lickitung | 108 | |

Indices 0x15 through 0x7E and 0x80 through 0xBE must be determined empirically. To determine a mapping: set the player's name so that the 3rd character produces the target species index (e.g., for index 0x80, the 3rd character must be A = 0x80), trigger the MissingNo. glitch, and record the encountered Pokemon's name from the battle screen. Cross-reference the name with the Pokedex to get the Pokedex number.

### Glitch Verification Diagnostic Checklist

Before reporting any glitch finding, verify it against this checklist:

**1. Reproducibility**: Can the glitch be triggered at least 3 out of 5 attempts under the documented conditions? If not, identify the uncontrolled variable (timing, prior game state, residual memory) and control for it.

**2. Mechanism Identified**: Can the observed behavior be explained by a specific memory state, code path, or data structure interaction? A glitch that can be triggered but not explained is an observation, not a finding. Use the emulator debugger to trace the code path that reads the anomalous data.

**3. Parameter Space Mapped**: Has at least one parameter been varied systematically (e.g., name characters, subpixel positions) and the result recorded for each variation? If the glitch only occurs at one specific parameter value, the parameter space mapping confirms that specificity.

**4. Failure Mode Documented**: What happens when the glitch fails? Does the game simply not warp, or does it crash, display garbage, or corrupt data? The failure mode is as diagnostic as the success mode—it reveals the boundary of the mechanism.

**5. ROM Version Verified**: Has the glitch been tested on the specific ROM version documented? Different ROM revisions may have bug fixes that eliminate the glitch. Record the ROM's CRC32 or SHA1 hash alongside all findings.

**6. Memory State Captured**: Has the relevant memory state been captured (via Lua logging, memory viewer screenshots, or save states) at the moment the glitch triggers? This state is the evidence that supports the mechanism explanation.

**7. Boundary Defined**: For at least one parameter, has the exact transition point between success and failure been identified? The boundary confirms the mechanism: if the glitch transitions at a subpixel value that corresponds to the geometric relationship between the hitbox and the wall tile, the mechanism explanation is confirmed.

### Troubleshooting Decision Tree

**SMB wall clip does not work:**

- Is Mario in World 1-2? The clip location is specific to this level's tile layout.
- Is Mario standing on top of the exit pipe (not inside it)? The clip requires a specific tile alignment.
- Is Mario ducking (holding Down) while jumping and holding Left? All three inputs are required simultaneously.
- Is the jump rhythm correct? Approximately one jump every 4-5 frames, not continuously held. Continuously holding jump does not produce repeated small jumps; it produces one jump followed by nothing until the button is released.
- Check `$0087` (X_Subpix) in the Lua overlay. If it is not changing with each jump, the backward movement is not being applied. Verify that Left is held, not Right.
- Check `$0075` (PowerUp). If Mario is small (0), the hitbox dimensions are different. Try as super Mario (1).

**MissingNo. does not appear on Cinnabar coast:**

- Did you talk to the Old Man and watch the full tutorial? The name copy only occurs during the tutorial sequence. If you skipped it (by already having the Pokedex), the buffer is not populated.
- Did you Fly directly to Cinnabar? Walking, surfing, or entering buildings on the way may load new encounter data that overwrites the buffer.
- Are you surfing on the correct tiles? The encounter-triggering tiles are the water tiles directly adjacent to Cinnabar Island's east coast. Surfing further east may use a different encounter table.
- Check the Lua overlay for the name buffer contents. If the bytes at `$D158` are all zeros or do not match your name, the buffer was overwritten. Repeat the Old Man tutorial and Fly to Cinnabar again without any intermediate encounters.
- Is the ROM the unmodified US version? Japanese versions, European versions, and ROM hacks have different memory layouts. Verify the CRC32.

**Lua script displays no values or errors:**

- In FCEUX: verify the script is running (check for error messages in the Lua output window). Ensure `memory.readbyte` is called with the correct address format (decimal or hex with `0x` prefix).
- In BizHawk: verify the memory domain name is correct for the Game Boy core in use. If "System Bus" does not work, try removing the domain parameter to use the default domain, or try "WRAM" with adjusted offsets (`$D158 - $C000 = $0x1158`).
- Ensure `emu.frameadvance()` is called at the end of the main loop. Without it, the script blocks the emulator and no values update.
- If `io.open` fails (file logging does not work), the emulator may restrict file access. Remove the logging portions of the script and rely on the on-screen overlay for data collection.
