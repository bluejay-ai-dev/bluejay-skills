---
name: background-noise
description: Add background noise to digital humans so calls are tested under realistic conditions. Pick a built-in preset, or upload your own audio (office floor, call center, street, a specific language's ambience) and attach it across a simulation in one pass. Use when the user wants noisier or more varied call conditions, asks to upload custom ambience, mentions background noise, or invokes /bluejay:background-noise.
---

# Add background noise to digital humans

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: get digital humans calling under realistic noise, either from a built-in preset or from the user's own audio file. Uploading takes three calls plus a file PUT. Do all of it for them rather than handing them the steps.

## Steps

1. **Preset or custom?** Presets need no upload and cover most cases:
   `office`, `talking`, `traffic`, `cafe`, `park`, `tv`, `noisy_restaurant`, `hospital`, plus `none`.
   Offer these first. Go custom only when the user names ambience the presets don't cover, like a specific language's street, a call-center floor, their own recording, or a particular room.

2. **For a preset**, skip to step 5.

3. **Upload the file** (custom only). Check `list_custom_background_noises` first, since the library caps at 20 per org and the name may already be there. Then:
   1. `create_custom_background_noise_upload_url(filename)` returns `upload_url` and `storage_path`
   2. PUT the raw bytes to `upload_url`:
      ```
      curl -sS -X PUT --upload-file <file> -H "Content-Type: audio/mpeg" "<upload_url>"
      ```
      Use `audio/wav` for a `.wav`. **mp3 or wav only.** m4a and MP4 containers break the ambient player's streaming decoder and are rejected by extension.
   3. `create_custom_background_noise(name, storage_path)` to register it

   If the user gave no file, ask for a path. Don't invent audio or pick something for them.

4. **Confirm it registered.** `list_custom_background_noises` should now show it. Keep the `storage_path`, which is what the digital human references.

5. **Attach it to the digital humans.** `update_digital_humans` takes a list, so set the whole simulation in one call. Use `list_digital_humans` to get the ids, then per item:
   - preset: `{"background_noise": "cafe", "background_noise_volume": 0.4}`
   - custom: `{"background_noise": "custom", "custom_background_noise_url": "<storage_path>", "background_noise_volume": 0.4}`

   `background_noise_volume` is a **float from 0.0 to 1.0** (default 0.8). The web UI shows it as a percentage, so 40% is `0.4`. Anything above 1.0 is a 422.

6. **Verify on one call before the batch.** Run a single digital human, listen to the recording, and confirm the ambience is audible without burying the speech. Then apply to the rest. Noise that is too loud degrades the agent's own transcription and shows up as fake failures.

## Notes
- `background_noise: "custom"` without `custom_background_noise_url` is rejected. Both fields go in the same update.
- A `storage_path` only plays for digital humans in the org that uploaded it. Paths are org-prefixed and the agent fails closed on a mismatch, skipping the noise silently, so a cross-org path looks like it worked and produces a quiet call.
- Files cap at 50 MB. A short loop beats a long recording, since the player loops the file for the whole call.
- Mixing noise with `audio_quality` (`high`, `medium`, `low`, `horrible`) is how you model a genuinely bad line. Noise alone still sounds like clean audio with ambience behind it.
- Spreading a few different presets across a suite tests more than putting one preset on every digital human. Vary it unless the user wants one condition held constant.
