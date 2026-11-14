# Questions

**Is it safe?** Not known. It has never run on a camera, and three earlier builds failed. [Safety](SAFETY.md).

**Which cameras?** The OM-5 Mark II on firmware 1.1 only. The patcher refuses any other file. The OM-5 (first
model) has a separate developer-only donor builder, with hardware compatibility unverified ([roadmap](../ROADMAP.md)).

**Why only three film slots, when the OM-3 has twenty?** The OM-3's firmware had hundreds of kilobytes of room that
its project could open up and prove on a camera. The OM-5 Mark II has about six kilobytes spread over ten places.
The three slots are OM's own Color Profiles, which were still inside the firmware, hidden; a film is written into
a slot's own settings, which costs almost no code. Ten films ride on the card and the trash button swaps them in.

**Why no grain, Glow, Halation, split toning, Blacks / Whites?** No room, and each needs its own research on this
camera's image processor. Films made for the OM-3 that use them lose those parts here.

**Do I need the card in the camera?** Only to choose a film. A chosen film is stored in the camera.

**Can I use an OM-3 `LOOKS.BIN`?** No, the file is different (`OM5F`, see [formats](FORMATS.md)). LookLab's library
has the OM-3 project's films, adapted.

**The film's name did not appear.** The name is the title of the Picture Mode screen while the highlight is on the
strip of picture modes, and the top line of the super control panel while its Picture Mode cell is highlighted.
After visiting the rows below, the title reads "Picture Mode" until you move along the strip. Names have at most
12 characters.

**Does it change RAW files?** No. Like any picture mode it changes the JPEG, and the preview.

**How do I remove it?** Flash OM's firmware back: [Safety › Going back](SAFETY.md#going-back-to-oms-firmware).

**Can OM update the camera afterwards?** Yes; an official update replaces all of this.

**Who makes this?** Volunteers. It builds on Caduceus for the E-P7 (cakelesscoder) and for the OM-3
(androidfanman), and on fishcu's PEN-F research. The project is open for the community to carry on.
