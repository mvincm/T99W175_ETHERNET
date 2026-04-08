# Foxconn T99W175 5G Modem – Ethernet Mode Guide - IPA version

## Disclaimer

All actions described in this repository are performed **at your own risk**.
Flashing firmware and modifying modem software may **damage your device, erase data, or void your warranty**. The author and contributors are **not responsible for any damage or issues** resulting from the use of this guide.

## Goal

The goal of this project is to enable the **Foxconn T99W175 5G modem** (based on the Qualcomm X55 platform) to operate in **IPA Ethernet mode**. IPA stands for IP Accelerator in the Qualcomm world, and for you it means download speeds of up to 900 Mbit/s (in my case). This modem is relatively inexpensive and still available on the secondary market, though it is a rather old device.

For now, this manual is **not** focused on enabling sshd, dhcpd, httpd, or simpleadmin. If you want to do those things, you could follow the initial manual.
This guide is about enabling PCIe, the r8125 chipset, and finally IPA.

---

# Initial Assumptions

Before starting, the following conditions must be met:

* The **T99W175 modem has already been modified to operate in USB mode** (instructions for this modification are widely available online).
* The modem is **visible in the operating system when connected via USB**.
* **ADB access is available**.
* You have an **M.2 to Ethernet adapter**, for example:
  * **Dual-Q 5G2PHY** from rework.network (used during testing)
  * An adapter based on the **Realtek r8125 chipset**
* The modem is **already configured to connect to the mobile network**, including:
  * APN configuration
  * A verified working internet connection via USB

In short: the modem is known to be working properly.

---

# How did I manage to enable PCIe and other features? 

Here is a brief summary (not a detailed description) and I am open to sharing the full journey with anyone interested.

1. I started by flashing the official Dell firmware F0.1.0.0.9.GC.004 to establish a common baseline that anyone can replicate.
2. I then flashed the latest firmware version I could find online: 6.0.0.6, with kernel 4.14.206.
3. This version includes the r8125.ko module, and the kernel is able to load it without errors.
4. This version also includes a systemd script that loads the module at boot.
5. I therefore assumed that the "only" limitation was the lack of PCIe bus support, through which the kernel would detect the r8125 chipset on my adapter.
6. I obtained Linksys firmware from the internet, on which Ethernet with the r8125 chipset works out of the box (kernel 4.4.117).
7. I assumed that the kernels would be fairly similar in their compilation and that the differences must lie in the DTB/DTS files.
8. I dumped the boot partition (mtd24) from the Linksys firmware.
9. I unpacked the dumped partition, resulting in two files: the kernel and the kernel_dtb.
10. I then unpacked kernel_dtb into individual DTB files (the combined DTB contains as many as 47 smaller DTB files for various architectures).
11. The correct DTB for our T99W175 is "Qualcomm Technologies, Inc. SDXPRAIRIE MTP V2".
12. I did the same for the 6.0.0.6 firmware on kernel 4.14.206.
13. As a result, I had a DTB with working PCIe and one with PCIe disabled. I decompiled these files into DTS format to compare their differences.
14. I identified the main factors affecting PCIe operation (listed below).
15. For reasons still unknown to me (due to lack of knowledge), I was unable to edit the DTS file, compile it to DTB, build the large combined DTB, and then build a complete partition image.
16. The issue was in the DTS-to-DTB compilation step (I suspect the compiler altered phandle values in a way that conflicted with the kernel).
17. I found a workaround by editing the DTB file directly in binary form using the `fdtput` tool. A DTB modified this way was compatible with the kernel.
18. After editing the binary DTB, I built the large combined DTB, then packed it with the kernel using magiskboot, resulting in a partition image for mtd24 (ota_ipa_mtd24.bin).
19. I booted the modem from this image (using `fastboot boot ota_ipa_mtd24.bin`) — and it worked! PCIe was detected, the r8125 kernel module was loaded, and it functioned correctly.
20. Success, but not complete — the compiled image was too large to flash onto the mtd24 partition.
21. However, the image contained a lot of padding (FF bytes) to fill full memory regions. I removed these using a few Python scripts (my work + Claude Code). I will share the link — it might come in handy for someone someday.
22. This produced a so-called "boot.img" file, which can be flashed using `fastboot flash boot ota_ipa_boot.img`.
23. Tests on a standalone base station allowed me to achieve download speeds of 760 Mbit/s with NAT on the modem over an Ethernet connection. This confirms that IPA is working.

---

# Enable Ethernet Support with IPA

## 1. Flash official Generic firmware

Use the **Firmware Selector Tool from Dell** to flash the following firmware and reboot the modem:

```
F0.1.0.0.9.GC.004
```

The tool can be downloaded from the Dell support page. The aim is to start from the same baseline.

## 2. Flash ota.bin firmware (6.0.0.6, kernel 4.14.206) and reboot the modem

Use the same tool from Dell, but place `ota.bin` in the folder where `QDUTool.exe` is located and run `QDUTool.exe`. This should flash `ota.bin` to your modem.

## 3. Reboot the modem into fastboot mode

```
adb reboot-bootloader
```

## 4. Boot using ota_ipa_boot.img (without flashing first, to verify it works)

```
fastboot boot ota_ipa_boot.img
```

## 5. Verify that everything works correctly

Perform basic checks and confirm the modem boots correctly and that PCIe, Ethernet, etc. are working. If everything works, proceed to the next step.

## 6. Erase the partitions

```
adb reboot-bootloader
fastboot erase boot
```

## 7. Flash ota_ipa_boot.img permanently

```
fastboot flash boot ota_ipa_boot.img
```
Reboot the modem afterward.

## 8. Enjoy T99W175 with Ethernet and IPA enabled!

---

# Addendum

How to edit the binary DTB file (Qualcomm_Technologies,_Inc._SDXPRAIRIE_MTP_V2.dtb). The following commands modify the binary DTB to enable the PCIe interface and configure the network controller:

```
fdtput -t s mtp_v2.dtb /soc/qcom,cnss-qca6390@a0000000 status "ok"
fdtput -t i mtp_v2.dtb /soc/qcom,pcie@1c00000 qcom,boot-option 0
fdtput -t s mtp_v2.dtb /soc/qcom,pcie@1c00000 status "ok"
fdtput -v -t x mtp_v2.dtb /soc/qcom,pcie@1c00000 qcom,no-l1-supported
fdtput -v -t x mtp_v2.dtb /soc/qcom,pcie@1c00000 qcom,no-l1ss-supported
``` 

Optimization Scripts. Since the original mtd24.bin partition file was too large, I used the following Python scripts to trim and repack it into the final ota_ipa_boot.img:
```
t99w175_repack.py
t99w175_size.py
t99w175_trunc.py
```

Links to ota.bin, ota_ipa_boot.img are in `links.txt` file.

---
