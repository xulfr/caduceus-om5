# Caduceus v0.2.0-alpha1

For the OM-5 Mark II (E148), stock firmware 1.1. On 20 November the owner reported that the candidate from `c3bc45c` “works perfectly”. This is an overall camera success. The number of starts and the on-card checksum were not separately reported, so the installer retains its experimental acknowledgement.

- In Color Profile 1–3, press INFO on the tone page to cycle Hi/Sh → Black/White → Mid. Adjust Black and White with the dials. Changes now refresh live view without a half-press.
- On the colour wheel, INFO switches between HSL and Tint. Trash cycles Saturation, Hue and Lightness, or Shadow, Midtone and Highlight Tint. Use the dials to choose among 12 colours and adjust strength. The swatch follows each colour, and tints follow output brightness.
- Picture Mode stays open for 30 seconds after the last input. This build also guards the gamma hook during startup following an intermittent boot loop on an earlier build.
- Alpha12’s Monochrome Color Filter swatches, selection outline and centre colour are included, along with the ND32/ND64 CP icons.

Download the tagged source archive and run `python patch.py --release v0.2.0-alpha1`. Before flashing, verify that the SHA-256 of **DCOLYMP/E1489999.BIN on the card** is `2b3fd53ce24433edb662036a29e1f4ea3988c61f9a15d681f0998ebe7b4a21e6`.
