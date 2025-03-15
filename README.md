# Xbox 256MB upgrade mod

Upgrade the original Xbox to quadruple its original RAM size. Why? Because we can. **For advanced modders only!** Understand the risks and drawbacks before attempting.

# Xblast OS for RAM testing and flashing

See the [bitbucket downloads](https://bitbucket.org/prehistoricman/lpcmod_os/downloads/) and the [bitbucket readme](https://bitbucket.org/prehistoricman/lpcmod_os/src/master/README.md) for the RAM testing BIOS that lets you check each RAM chip individually.

# BIOS patching

Use Python 3 to run the patcher script BIOS_patcher_256MB.py. This patcher works on X2 and X3 BIOSes. Others not tested. Some BIOSes such as EvoX will run 256MB memory after applying this patch but will not be able to use the extra memory. They require additional patching.

Usage:

    python BIOS_patcher_256MB.py <BIOS file path> [-m] [-d]

The `-m` option will slow the RAM speed to 150MHz from the default of 200MHz. **I have found this is necessary on all my Xboxes to run 256MB stably.** You can recover some lost performance by overclocking the BIOS before applying the 256MB patch using a tool such as XBOverclock.

The `-d` option will attempt to adjust the slew and drive trims for the DQS pin. Try this if the system isn't stable.

This script will produce a patched version of the BIOS with `.patched256` appended to the name.

For example:

    python BIOS_patcher_256MB.py x2.5035.v16plus.137.bin -m

# Interposer PCB

This mod uses 256Mbit memory chips HY5DU573222F-28. They are only available in a BGA package, so we need an interposer to convert it to the Xbox's TQFP footprint.

PCB gerbers appropriate for PCBWay are in the github release.

256Mbit_RAM_interposer_v2_flex is my recommended design. It's intended to be manufactured in flexible PCB to be slim, easy to handle, and have enough outline precision to correctly make the castellated holes at the edge of the PCB. You can try ordering it in rigid fibreglass PCB but many manufacturers won't have the required tolerance on the board outline to avoid ripping the castellations apart.

256Mbit_RAM_interposer_rigidflex is my earlier design where the two inner layers are flexible and extend from the board, becoming pins and mimicing the original TQFP package. **This design suffers from the pins being too weak**: they get micro fractures from bending and therefore lose conductivity. This design would be ideal if the flexible layers could be on the bottom side of the board.

# Theory

This is just extra information for those who seek it.

See my video about this mod: [How I put 256MB of RAM in the original Xbox](https://www.youtube.com/watch?v=1idSEhUT4PM)

In short, we can double the memory from 128MB to 256MB by adding 1 more bit of addressing to the memory array. This is done by adding an additional 'column' since the Xbox is already maxed out on address 'rows'. To enable the use of that extra column bit, we have to write to the DRAM controller register called `NV_PFB_CFG1` in the Xbox's startup code (Xcodes). In the same register, we also have to set the AP pin to A9 to account for the flip of A8 and A9 in the interposer. Why are they flipped in the interposer? Because this DRAM controller unfortunately doesn't properly account for the location of the AP pin within the column address. The RAM chip accepts its column address on A0-A7+A9, skipping the A8 pin because its job is to be the AP pin. Instead, the NV2A uses A8 as the most significant bit in the column address (in 9 columns mode) and thus the function of the AP bit is lost and only half of memory is addressable.
