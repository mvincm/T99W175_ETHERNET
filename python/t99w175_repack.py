import struct, os

PAGE = 4096
DTB_SPLIT = 0x7963A0  # where DTB starts inside kernel blob

def pad(blob, page=PAGE):
    r = len(blob) % page
    return blob + b'\xff' * (page - r if r else 0)

with open('ota_mtd24_trimmed.bin', 'rb') as f:
    data = f.read()

kernel_sz = struct.unpack_from('<I', data, 8)[0]
kernel_blob = data[PAGE : PAGE + kernel_sz]

# Split kernel and original DTB
kernel_only  = kernel_blob[:DTB_SPLIT]
orig_dtb     = kernel_blob[DTB_SPLIT:]

# Load modified DTB
with open('kernel_dtb_modified', 'rb') as f:
    new_dtb = f.read()

print(f"kernel only:  {len(kernel_only):>10,}")
print(f"orig dtb:     {len(orig_dtb):>10,}")
print(f"new dtb:      {len(new_dtb):>10,}  (delta: {len(new_dtb)-len(orig_dtb):>+,})")

# New combined kernel blob = kernel + modified DTB
new_kernel_blob = kernel_only + new_dtb
new_kernel_sz   = len(new_kernel_blob)

# Rebuild header with updated kernel_sz
header = bytearray(data[:PAGE])
struct.pack_into('<I', header, 8, new_kernel_sz)

# Assemble image
out  = bytes(header)
out += pad(new_kernel_blob)

partition = 0xD80000
print(f"\nnew kernel_sz: {new_kernel_sz:>10,}")
print(f"output:        {len(out):>10,}  ({len(out):#010x})")
print(f"partition:     {partition:>10,}  ({partition:#010x})")

if len(out) <= partition:
    print(f"fits — {partition - len(out):,} bytes to spare")
    with open('ota_ipa_kernel_final.img', 'wb') as f:
        f.write(out)
        f.write(b'\xff' * (partition - len(out)))
    print("Written: ota_ipa_kernel_final.img")
else:
    print(f"DOES NOT FIT — over by {len(out) - partition:,} bytes")
    print(f"your DTB can be at most {len(orig_dtb) + (partition - len(out)):,} bytes")
