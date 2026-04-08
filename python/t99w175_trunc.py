REAL_DATA_END    = 0x00B31810
FASTBOOT_PART    = 0x00C40000

with open('ota_ipa_kernel_final.img', 'rb') as f:
    data = f.read(REAL_DATA_END)

assert len(data) == REAL_DATA_END, f"file shorter than expected: {len(data)}"

out = data + b'\xff' * (FASTBOOT_PART - REAL_DATA_END)

with open('ota_ipa_kernel_fastboot.img', 'wb') as f:
    f.write(out)

print(f"real data:  {REAL_DATA_END:#010x}  ({REAL_DATA_END:,})")
print(f"padded to:  {FASTBOOT_PART:#010x}  ({FASTBOOT_PART:,})")
print(f"written:    ota_ipa_kernel_fastboot.img")