# Brawlspace

A browser fighting game built on [fiiight](https://github.com/mathmati/fiiight)
(upstream commit `9e4b23c`), which is [Ikemen GO](https://github.com/ikemen-engine/Ikemen-GO)
compiled to WebAssembly.

Brawlspace runs fully client-side on WebGL2 and WebAudio, so any static host can serve it.
It supports keyboard, gamepad, and touch controls.

This is the base for building new fighters. The starting roster is deliberately small:

| Fighter | Purpose |
|---|---|
| `kfm720` (Kung Fu Man) | Playable fighter and the template new characters are copied from |
| `tinker` (Tinker) | Gadgeteer with a radar gauntlet, generated from a single illustration (see below) |
| `grapeman` (GrapeMan) | Grape-costumed bruiser who fires grapes, also generated from one illustration |
| `juanana` (Juanana) | Banana-suited raver: glow-stick projectiles, a banana-peel trap, and the Rave Barrage super |
| `cuddlepuss` (CuddlePuss) | Cat-suited bruiser (1100 life, slow walk) who coughs up Hairball projectiles |
| `hotnight` (HotNight) | Throws water bottles, heals with Hydrate, wallops with her tote bag; Bulk Buy Barrage super |
| `Training` | Training dummy, excluded from random and arcade picks |

## Build and run locally

You need Go 1.24 (the wasm build is pure Go, with no cgo or C toolchain), `zip`, and Node or Python.

```sh
export PATH=$HOME/sdk/go1.24.7/bin:$PATH GOTOOLCHAIN=local
bash build/wasm.sh                 # engine -> web/ikemen.wasm, content -> web/content.zip
bash build/wasm.sh --shell-only    # after content-only changes (skips the Go compile)
python3 web/serve.py 8080          # then open http://localhost:8080
```

## Add a new fighter

```sh
python3 -I tools/new_character.py blaze "Blaze" --author "Your Name"
bash build/wasm.sh --shell-only
```

The script:

- Copies the KFM 720 template into `content/chars/blaze/`, with files renamed to `blaze.*`.
- Sets the name and author in the character's `.def` file.
- Adds the fighter to `content/data/select.def`.

From there, make the character your own:

| File | What to change |
|---|---|
| `blaze.sff` | Sprites (draw new art; KFM 720's work files are a good reference for poses) |
| `blaze.snd` | Sounds |
| `blaze.air` | Animations and hitboxes |
| `blaze.cns` | Stats and move states |
| `blaze.cmd` | Command inputs |
| `movelist.dat` | Move list shown in the pause menu |

To add a stage, put its `.def` and `.sff` in `content/stages/`, then list it under `[ExtraStages]`
in `content/data/select.def`.

## Fighters built from one drawing (Tinker, GrapeMan, Juanana, CuddlePuss, HotNight)

Each of these fighters lives in `tools/fighters/<id>/`:

| File | Purpose |
|---|---|
| `source.png` | The illustration |
| `make_frames.py` | Landmarks plus the projectile art |
| `<id>_states.cns`, `<id>_anims.air` | Projectile move and animations |
| `build.py` | Stats, quotes and move list |

The shared pipeline is `tools/fighters/cutout.py`, which poses the art, and `tools/fighters/assemble.py`, which builds the character files.

Source images can have a plain white background or a painted grey/white checkerboard (`"background": "checker"`).
Use `"holes"` to clear small white gaps the automatic cut-out keeps, such as between an arm and the body.
Use `"leg_shapes"` to trace the legs exactly when capes or props hang over them (see Juanana).

To add another fighter, copy `tools/fighters/grapeman/`, swap in the new image, update the landmarks in `make_frames.py`, and rename things in `build.py`.

Tinker's frames are generated from `tools/fighters/tinker/source.png`:

1. The script cuts the figure out of the white background.
2. It splits him at the belt.
3. It poses the two halves (lean, lunge, squash, swing, tumble) to produce a frame for every sprite number KFM 720 uses.

He therefore runs on KFM's animations, timing and hitboxes, plus his own **Radar Pulse** projectile (↓↘→ + P).

```sh
python3 -I tools/fighters/tinker/build.py            # repack art/ and rebuild the character files
python3 -I tools/fighters/tinker/build.py --frames   # regenerate art/ from source.png first (~1 min)
python3 -I tools/fighters/grapeman/build.py --frames # same for GrapeMan (Grape Shot: ↓↘→ + P)
python3 -I tools/fighters/juanana/build.py --frames  # same for Juanana (Glow Stick Toss, Banana Peel: ↓↙← + K)
python3 -I tools/fighters/cuddlepuss/build.py --frames # same for CuddlePuss (Hairball: ↓↘→ + P)
python3 -I tools/fighters/hotnight/build.py --frames   # same for HotNight (Water Bottle Toss, Hydrate, Tote Bag Swing)
```

To upgrade the animation, drop a hand-drawn PNG into `tools/fighters/tinker/art/` with the same name
(for example `210_20.png`) and rebuild without `--frames`. Keep `axis.txt` in step if the anchor moves.

## Stages

| Stage | Source |
|---|---|
| `stage0-720` (Training Room HD) | Stock |
| `sluttywood` (SluttyWood) | Generated from one illustration by `tools/stages/sluttywood/make_stage.py` |

For SluttyWood, the script scales `source.jpg` to fill a 720p screen and sets the ground line on the street.
It also adds a softly pulsing glow layer built from the neon signs and string lights, plus the stage-select thumbnail (sprite 9000,1).

Stages listed under `[ExtraStages]` in `content/data/select.def` can be picked in modes with stage select (VS, Quick Match, Training).
Arcade uses each fighter's home stage: the second item on that fighter's `[Characters]` line.

## Title logo

The title-screen logo is generated, not hand-drawn:

1. Edit `tools/logo/make_logo.py` (it draws the logo as SVG).
2. Run `python3 -I tools/logo/make_logo.py`, which renders four transparent 699×257 layers with headless Chrome.
3. Run `python3 -I tools/logo/patch_sff.py`, which swaps them into sprites 0,0–0,3 of `content/data/ikemen1/system.sff`. It's safe to re-run.

Anything under `content/` overrides the engine's stock data, including the screenpack in
`content/data/ikemen1/`.

## Deploy

`.github/workflows/deploy-pages.yml` builds the game and publishes `web/` to the `gh-pages` branch
on every push to `main`. To turn the site on, go to Settings → Pages → Source and pick
"Deploy from a branch", branch `gh-pages`.

For itch.io, zip the contents of `web/` and upload them as an HTML project.

## Limits

- **No online multiplayer in the browser.** Web pages can't open raw sockets, so versus is
  same-device for now. A WebRTC transport is listed as future work upstream.
- Tracker music (`.xm`/`.mod`) isn't supported. Use mp3, ogg, or wav.
- The stock screenpack expects music files that aren't bundled (`sound/Title.mp3`, `Select.mp3`).
  Those screens are silent until you add your own.

## Licenses

- Engine and browser port: MIT (`LICENSE`, `engine/LICENCE.txt`).
- Screenpack assets: CC-BY 3.0.
- Kung Fu Man 720 and the Training dummy (a KFM edit) are Elecbyte **CC BY-NC**. Any fighter
  scaffolded from KFM inherits that license until its sprites and sounds are replaced with original work.
- Full provenance is in `content/MANIFEST-fiiight.md` and `README-fiiight.md`.
