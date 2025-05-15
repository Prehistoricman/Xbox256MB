import sys
import os
#import argparse

# args:
# file name/path
# -m to decrease mem speed
# -d to change DQS and DRV slew trims

mem_speed_patch = False
if "-m" in sys.argv:
    mem_speed_patch = True
slew_trims_patch = False
if "-d" in sys.argv:
    slew_trims_patch = True

file_name = sys.argv[1]

####### read file

file_contents = bytearray()
with open(file_name, "rb") as infile:
    file_contents = bytearray(infile.read())


####### patcher

#This is a lazy approach to search for the last xcode which is the same in all BIOSes

#TODO account for when there is something in the nearby space (see some Cerb versions which need the slew table moving)

def xcode_index_to_file_index(n):
    return 0x80 + n * 9
def get_xcode(n):
    index = xcode_index_to_file_index(n)
    return file_contents[index:index+9]

end_xcode_index = 0
#Scan from the end of the file to the start for the end xcode
end_xcode = bytes([0xEE, 0x06, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
xcode_index = (len(file_contents) - 0x80) // 9 - 1
while xcode_index != 0:
    if get_xcode(xcode_index) == end_xcode:
        end_xcode_index = xcode_index
        break
    xcode_index -= 1
if end_xcode_index == 0:
    print("Could not find END xcode! This isn't a valid Xbox BIOS!")
    exit(1)

patch256 = bytes([
0x04, 0x10, 0x00, 0x01, 0x80, 0x00, 0x00, 0x00, 0x0F, #xcode_pciout(0x80010010, 0x0f000000);
0x04, 0x20, 0xF0, 0x00, 0x80, 0x00, 0x0F, 0xF0, 0x0F, #xcode_pciout(0x8000f020, 0x0ff00f00);
0x03, 0x04, 0x02, 0x10, 0x0F, 0x10, 0x90, 0x44, 0x11, 0x03, 0x48, 0x10, 0x00, 0x00, 0xBE, 0xBA, 0xFE, 0xCA, 0x02, 0x10, 0x12, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x01, 0x00, 0x00, 0x07, 0x03, 0x00, 0x00, 0x00, 0x10, 0x12, 0x00, 0x0F, 0x02, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0xBE, 0xBA, 0xFE, 0xCA, 0x2D, 0x00, 0x00, 0x00, 0x03, 0x04, 0x02, 0x10, 0x0F, 0x00, 0x80, 0x44, 0x11, 0x02, 0x10, 0x12, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x06, 0xFF, 0xFE, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x07, 0x03, 0x00, 0x00, 0x00, 0x10, 0x12, 0x00, 0x0F, 0x09, 0x00, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x04, 0x84, 0x00, 0x00, 0x80, 0xFF, 0xFF, 0xFF, 0x0F, 0x03, 0x00, 0x02, 0x10, 0x0F, 0x03, 0x01, 0x07, 0x03, 0x03, 0x34, 0x12, 0x00, 0x08, 0xEF, 0xBE, 0xAD, 0xDE, 0x02, 0x34, 0x12, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x08, 0xEF, 0xBE, 0xAD, 0xDE, 0x09, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x12, 0x00, 0x00, 0x00, 0x04, 0x84, 0x00, 0x00, 0x80, 0xFF, 0xFF, 0xFF, 0x07, 0x03, 0x00, 0x02, 0x10, 0x0F, 0x03, 0x00, 0x07, 0x03,
0x04, 0x20, 0xF0, 0x00, 0x80, 0x00, 0xFD, 0xF0, 0xFD, #xcode_pciout(0x8000f020, 0xfdf0fd00);
0x04, 0x10, 0x00, 0x01, 0x80, 0x00, 0x00, 0x00, 0xFD  #xcode_pciout(0x80010010, 0xfd000000);
])

if patch256 in file_contents:
    print("Already patched for 256MB!")
    exit(1)

#Handle slews table first because it can be directly after xcodes, meaning we don't have enough space
slews_header = b" NN>VC]JdPjU"
if slew_trims_patch:
    if slews_header not in file_contents:
        print("Could not find slew trim array to patch! Remove -d option or try a different BIOS")
        exit(1)
    
    location = file_contents.find(slews_header) + 12 #+12 to skip header
    print("Slew trims patch: slew table found at 0x%X" % location)
    for i in range(15):
        #19 bytes per slew table entry
        file_contents[location + i * 19 + 12] = 0x0E #Low DQS slew trim
        file_contents[location + i * 19 + 13] = 0x0E #High DQS slew trim
        file_contents[location + i * 19 + 15] = 0x0E #DQS drive trim

#Move slews table if it's in our way
if slews_header in file_contents:
    location = file_contents.find(slews_header)
    #If last xcode plus patch is at a higher address than the slews table
    if (xcode_index_to_file_index(end_xcode_index + 1) + len(patch256)) > location:
        #Check if it's got a pointer in the BIOS header
        pointer = int.from_bytes(file_contents[0x7C:0x80], "little")
        if pointer != location:
            print("Could not move slews table at 0x%X! Pointer in BIOS header is 0x%X" % (location, pointer))
            exit(1)
        #Be lazy and move it along by the size of the patch
        pointer += len(patch256)
        file_contents[0x7C:0x80] = pointer.to_bytes(4, "little")
        #Copy and paste table
        table = file_contents[location:location + 0xD6]
        file_contents[location:location + 0xD6] = bytes(0xD6) #Zero it
        file_contents[pointer:pointer + 0xD6] = table
        print("Moved slews table from 0x%X to 0x%X" % (location, pointer))
        

print("Patching for 256MB...")

#Find last instance of 11 00 C0 00 00 10 00 00 00
nearend_xcode = bytes([0x04, 0x10, 0x00, 0x01, 0x80, 0x00, 0x00, 0x00, 0xFD])
xcode_index = end_xcode_index
while xcode_index != 0:
    if get_xcode(xcode_index) == nearend_xcode:
        break
    xcode_index -= 1
if xcode_index == 0:
    print("Could not find xcode that's usually near the end! Can't patch this BIOS!")
    exit(1)
xcode_index += 1 #Put the patch after this xcode

#Scan for xcodes that jump into or beyond the patch and fix them
for index in range(xcode_index):
    xcode = get_xcode(index)
    if xcode[0] == 0x8 or xcode[0] == 0x9: #If it's a jump
        #Decode the jump offset
        offset = xcode[5] + (xcode[6] << 8) + (xcode[7] << 16) + (xcode[8] << 24)
        if offset > 0x80000000:
            offset -= 0x100000000
        destination = xcode_index_to_file_index(index + 1) + offset #Jumps are relative to the next instruction
        if destination >= xcode_index_to_file_index(xcode_index + 1): #If it's jumping into the second xcode or later
            offset += len(patch256)
            #Write back offset, adjusted for our patch size
            addr = xcode_index_to_file_index(index)
            file_contents[addr + 5] = (offset >>  0) & 0xFF
            file_contents[addr + 6] = (offset >>  8) & 0xFF
            file_contents[addr + 7] = (offset >> 16) & 0xFF
            file_contents[addr + 8] = (offset >> 24) & 0xFF
            print("Fixed xcode goto at 0x%X" % addr)

#Insert patch
file_contents = (file_contents[:xcode_index_to_file_index(xcode_index)] + 
        patch256 +
        file_contents[xcode_index_to_file_index(xcode_index):])
end_xcode_index += len(patch256) // 9 #This pushes the end xcode later

#Remove that many bytes from after the end xcode, if they are 00
after_end_data_index = xcode_index_to_file_index(end_xcode_index + 1)
after_end_data = file_contents[after_end_data_index:after_end_data_index+len(patch256)]
if after_end_data != bytes(len(patch256)): #If it's not all 0x00
    print("Not enough space for the patch! Can't patch this BIOS!")
    exit(1)
file_contents = file_contents[:after_end_data_index] + file_contents[after_end_data_index+len(patch256):]
print("256MB patch applied at 0x%X" % xcode_index_to_file_index(xcode_index))

#Patch RAM initialisation for swapped A8/A9
RAM_MRS_xcode1 = bytes([0x03, 0xC0, 0x02, 0x10, 0x0F, 0x32, 0x01, 0x00, 0x00])
RAM_MRS_xcode2 = bytes([0x03, 0xC8, 0x02, 0x10, 0x0F, 0x32, 0x01, 0x00, 0x00])
for xcode_index in range(end_xcode_index):
    if get_xcode(xcode_index) == RAM_MRS_xcode1 or get_xcode(xcode_index) == RAM_MRS_xcode2:
        #01 is the original value. Change to 02
        byte_index = xcode_index_to_file_index(xcode_index) + 6
        if file_contents[byte_index] == 0x01:
            file_contents[byte_index] = 0x02
            print("RAM init patch: Byte at 0x%X changed from 1 to 2" % byte_index)

if mem_speed_patch:
    #Scan for xcode that starts with 04 6C 03 00
    MPLL_xcode = bytes([0x04, 0x6C, 0x03, 0x00])
    for xcode_index in range(end_xcode_index):
        if get_xcode(xcode_index)[:len(MPLL_xcode)] == MPLL_xcode:
            file_index = xcode_index_to_file_index(xcode_index)
            target_byte = file_contents[file_index + 7]
            if target_byte != 0: #It's set to 0 intentionally (don't know why though) and we shouldn't fiddle with it
                new_byte = target_byte & 0x0F | 0x30 #Set MEM_PDIV = 3
                print("Mem speed patch: Byte at 0x%X changed from 0x%X to 0x%X" % (file_index, target_byte, new_byte))
                file_contents[file_index + 7] = new_byte

####### output file

outfile_name = os.path.splitext(file_name)[0] + ".patched256.bin"
print("Saved patched BIOS as", outfile_name)
with open(outfile_name, "wb") as outfile:
    outfile.write(file_contents)

print("Done")