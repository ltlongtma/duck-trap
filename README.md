# 🦆 Duck Trap

Catch whoever messes with your unlocked machine.

## About

At many offices there's a running joke: if you leave your computer unlocked,
anyone can walk up and post "duck" (or worse) to the team chat. **Duck Trap**
turns the tables. You leave your desk and arm it — the screen looks like your
normal desktop, but the moment someone **presses a key or touches the
trackpad**, Duck Trap **silently**:

1. 📸 Snaps a photo of them with the webcam.
2. 🔒 Locks the machine immediately.

No banner, no sound, no screen change — the intruder just sees the machine
"lock itself" and never knows they were photographed. Photos are saved **only
on your machine**, in `DuckTrap/captures`.

Works on **macOS** and **Windows**.

---

## Quick start

**Run from source (macOS). No arguments needed — it works out of the box:**

```bash
./run.sh
```

The first run creates a virtualenv and installs dependencies automatically. It
uses the bundled default decoy and the default camera. After launch there's a
short silent grace period to step away (press **ESC** to cancel). Then it's armed.

**Test safely first (capture but don't lock):**

```bash
./run.sh --no-lock --open-folder
```

Tap a key to "spring" the trap, then check the photo in the folder that opens.

### Optional flags (all placeholders — change the values)

```bash
# Use your own decoy image instead of the bundled one:
./run.sh --image ~/Desktop/my-screenshot.png

# Pick a specific camera (macOS often defaults to the iPhone camera).
# First list the exact names on YOUR machine:
./run.sh --list-cameras
# then pass the one you want, e.g.:
./run.sh --camera-name "FaceTime HD Camera"
```

`~/Desktop/my-screenshot.png` and `"FaceTime HD Camera"` are just examples —
use whatever path and camera name your machine reports.

---

## Install for non-technical users (no Python)

Prebuilt apps are produced by GitHub Actions:

1. Repo → **Actions** tab → **Build Duck Trap** → **Run workflow** (or grab the
   files from **Releases** if a version was tagged — see below).
2. Download and unzip:
   - **Windows** → `DuckTrap.exe`
   - **macOS** → `DuckTrap.app`
3. *(Optional)* A default desktop decoy ships inside the app. To use your own,
   drop an image named **`trap.png`** next to the app and it takes over.
4. **Double-click to run.** After a few seconds the trap arms silently.
   - First launch asks for **Camera** permission → **Allow**.

### First-launch security prompts (unsigned internal build)

The apps aren't code-signed (fine for internal use), so:

- **Windows** — SmartScreen: *More info → Run anyway*.
- **macOS** — Gatekeeper says *"Apple could not verify..."*. Either:
  - **System Settings → Privacy & Security** → scroll to Security → **Open Anyway**, or
  - remove the quarantine flag in Terminal:
    ```bash
    xattr -dr com.apple.quarantine ~/Downloads/DuckTrap.app
    ```

---

## Permissions

Detection uses the fullscreen window's own key/mouse events, so the only
**required** permission is **Camera**:

- **macOS**: System Settings → Privacy & Security → **Camera** → enable for the
  app (Terminal/iTerm if running from source, or DuckTrap if packaged).
- **Windows**: Settings → Privacy → **Camera** → allow apps to use the camera.

Optional:

- **Accessibility** (macOS) — lets Duck Trap lock instantly via the lock
  shortcut. Without it, locking falls back to display-sleep, which only locks if
  **System Settings → Lock Screen → "Require password... after display is off"**
  is set to **Immediately**.
- **Input Monitoring** (macOS) — only for `--global-hook`.
- **Screen Recording** (macOS) — only if you want the auto desktop-screenshot
  decoy. Otherwise use `--image` / `trap.png`.

> Running from source: macOS assigns permissions to the **terminal app** that
> launched Python (Terminal/iTerm/VS Code), not to Python. Grant them there, and
> quit + reopen the terminal so the new grant takes effect.

---

## Command-line options

```bash
python -m duck_trap [options]      # or: ./run.sh [options]
```

| Option | Meaning |
|---|---|
| `--image <path>` | Custom full-screen decoy image (PNG/JPG). |
| `--camera-name "MacBook Pro Camera"` | Pick the camera by name (avoids the iPhone camera). |
| `--list-cameras` | List camera names and exit. |
| `--camera 1` | Pick the webcam by index (if not using `--camera-name`). |
| `--sensitivity 3` | Mouse-move threshold in pixels. Lower = more sensitive. |
| `--arm-delay 6` | Silent grace period before arming (default 4s). |
| `--global-hook` | Also catch global input (needs Accessibility + Input Monitoring). |
| `--sound` | Play a sound when triggered (default: silent). |
| `--no-lock` | Capture only, don't lock (for testing). |
| `--open-folder` | Open the captures folder after firing. |
| `--test-lock` | Try locking now to verify it works, then exit. |
| `--dir <path>` | Change where photos are saved. |

Photos are saved to `~/DuckTrap/captures` (macOS/Linux) or
`C:\Users\<you>\DuckTrap\captures` (Windows), named `duck_YYYYMMDD_HHMMSS.jpg`.

---

## Releases

Push a version tag to build both apps and publish a downloadable Release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions then attaches `DuckTrap.exe` and `DuckTrap-macOS.zip` to the
**Releases** page. (Downloading Actions artifacts or Release assets requires
being signed in to GitHub with access to the repo.)

---

## Build it yourself

```bash
pip install pyinstaller
pyinstaller packaging/DuckTrap.spec --noconfirm
```

Or use `packaging/build_windows.bat` / `packaging/build_macos.sh`. Output lands
in `dist/`.

---

## How it works

- **Decoy**: prefers your image (`--image` / `trap.png`), then the bundled
  default (`duck_trap/assets/default_decoy.png` — replace it to change the
  default; `tools/make_default_decoy.py` can generate a synthetic one), then a
  live desktop screenshot, then a drawn fake desktop — shown full-screen via Tkinter.
- **Detection**: binds Tk `<Key>` / `<Button>` / `<Motion>` on the focused
  fullscreen window (no special permission). `--global-hook` adds `pynput`.
- **Capture**: OpenCV, or `imagesnap` by camera name on macOS. Taken *before*
  locking.
- **Lock (silent)**: macOS tries CGSession → `pmset displaysleepnow` →
  AppleScript ⌃⌘Q; Windows uses `LockWorkStation`.

---

## Notes

This is an internal, for-fun tool meant to run on **your own machine**. Photos
stay on your machine and are never sent anywhere.
