# Questions

**Is it safe?** Alpha9, which the installer now makes, has not been run on a camera. Alpha8 booted on the owner’s OM-5 Mark II and has [known UI defects](../research/OM5II-ALPHA8-CAMERA-2026-11-15.md). Alpha5 and alpha6 boot-looped on the owner's camera, as three earlier builds did. The installer refuses alpha1–alpha7. [Safety](SAFETY.md).

**Which cameras?** The OM-5 Mark II on firmware 1.1 only. The patcher refuses any other file. The original OM-5
has a separate [pre-alpha for testers](OM5_PREALPHA.md), never run on any camera.

**Why only three look slots, when the OM-3 has twenty?** The OM-3's firmware had hundreds of kilobytes of room that
its project could open up and prove on a camera. The OM-5 Mark II has about six kilobytes spread over ten places.
The three slots are OM's own Color Profiles, which were still inside the firmware, hidden; a look is written into
a slot's own settings, which costs almost no code. Ten looks ride on the card and the trash button swaps them in.

**Why no grain, Glow, Halation, split toning, Blacks / Whites?** No room, and each needs its own research on this
camera's image processor. Looks made for the OM-3 that use them lose those parts here.

**Does it work on the original OM-5?** Not yet known. There is a [pre-alpha for testers](OM5_PREALPHA.md) that has
never run on any camera. Only try it if you accept the risk and want to help.

**Do I need the card in the camera?** Only to choose a look. A chosen look is stored in the camera.

**Can I use an OM-3 `LOOKS.BIN`?** No, the file is different (`OM5F`, see [formats](FORMATS.md)). LookLab's library
has the OM-3 project's looks, adapted.

**The look's name did not appear.** The name is the title of the Picture Mode screen while the highlight is on the
strip of picture modes, and the top line of the super control panel while its Picture Mode cell is highlighted.
Names have at most 12 characters. (An empty slot's title reads "Picture Mode" after you visit the rows below, until
you move along the strip.)

**Does it change RAW files?** No. Like any picture mode it changes the JPEG, and the preview.

**How do I remove it?** Flash OM's firmware back: [Safety › Going back](SAFETY.md#going-back-to-oms-firmware).

**Can OM update the camera afterwards?** Yes; an official update replaces all of this.

**Who makes this?** Volunteers. It builds on Caduceus for the E-P7 (cakelesscoder) and for the OM-3
(androidfanman), and on fishcu's PEN-F research. The project is open for the community to carry on.
