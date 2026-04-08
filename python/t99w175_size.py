# kernel_sz from header = 11,732,947 = 0xB31000... wait
# but magiskboot reported KERNEL_DTB_SZ [3777587]
# so magiskboot split them itself by parsing internal structure

# Let's find where kernel ends and DTB begins inside the blob
with open('ota_mtd24_trimmed.bin', 'rb') as f:
    data = f.read()

import struct
PAGE = 4096
kernel_sz = struct.unpack_from('<I', data, 8)[0]
kernel_blob = data[PAGE : PAGE + kernel_sz]

print(f"kernel blob size: {len(kernel_blob):,}")

# Search for DTB magic 0xEDFE0DD0 (big-endian) or 0xD00DFEED
dtb_magic_be = b'\xed\xfe\x0d\xd0'
dtb_magic_le = b'\xd0\x0d\xfe\xed'

pos_be = kernel_blob.find(dtb_magic_be)
pos_le = kernel_blob.find(dtb_magic_le)

print(f"DTB magic (BE 0xEDFE0DD0) at offset: {pos_be:#x} ({pos_be:,})")
print(f"DTB magic (LE 0xD00DFEED) at offset: {pos_le:#x} ({pos_le:,})")

# Also check what magiskboot's kernel_dtb file is
import os
if os.path.exists('kernel_dtb'):
    print(f"\nmagiskboot kernel_dtb size: {os.path.getsize('kernel_dtb'):,}")
if os.path.exists('kernel'):
    print(f"magiskboot kernel size:     {os.path.getsize('kernel'):,}")