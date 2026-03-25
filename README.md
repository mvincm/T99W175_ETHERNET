# Foxconn T99W175 5G Modem – Ethernet Mode Guide

## Disclaimer

All actions described in this repository are performed **at your own risk**.

Flashing firmware and modifying modem software may **damage your device, erase data, or void your warranty**. The author and contributors are **not responsible for any damage or issues** resulting from the use of this guide.

## Goal

The goal of this project is to enable the **Foxconn T99W175 5G modem** (based on the Qualcomm X55 platform) to operate in **Ethernet mode**.

This modem is relatively inexpensive and widely available on the secondary market while still allowing download speeds close to **~900 Mbit/s** under ideal conditions.

Another objective is to allow usage of the web administration panel **T99W175SimpleAdmin**, developed by Brazzo978 and available on GitHub:

[https://github.com/Brazzo978/T99W175-simpleadmin](https://github.com/Brazzo978/T99W175-simpleadmin)

BTW:
Big UP for [Brazzo978](https://github.com/Brazzo978), Thanks for your work!

---

# Initial Assumptions

Before starting, the following conditions must be met:

* The **T99W175 modem has already been modified to operate in USB mode** (instructions for this modification are widely available online).
* The modem is **visible in the operating system when connected via USB**.
* **ADB access is available**.
* You have an **M.2 to Ethernet adapter**, for example:

  * **Dual-Q 5G2PHY** from rework.network (used during testing)
  * Adapter based on **Realtek r8125 chipset**
* The modem is **already configured to connect to the mobile network**, including:

  * APN configuration
  * Verified working internet connection via USB

In short: the modem is known to be working properly.

---

# Current Limitation

Due to the use of publicly available firmware files from modem manufacturers/distributors, it is currently **NOT possible to exceed ~300 Mbit/s download speed**.

This limitation occurs because **IPA mode (IP Accelerator)** is not available.

Without IPA, the modem simply cannot process higher traffic rates due to CPU limitations.

This behavior is typical for firmware using **Linux kernel 4.14.117**.

* **Kernel 4.14.206** includes **IP acceleration support**
* However, that version **does not include unlocked Ethernet over PCIe support**

There is firmware for this modem that supports **both features**, but it is **not publicly available**.

Work is ongoing to find a way to unlock:

* IPA acceleration
* Ethernet functionality simultaneously

If you are interested in helping, please get in touch.

---

# Part 1 – Enable Ethernet Support

## 1. Flash official Generic firmware

Use the **Firmware Selector Tool from Dell** to flash the following firmware:

```
F0.1.0.0.9.GC.004
```

The tool can be downloaded from the Dell support page. The aim is to start work from the same bottomline.

---

## 2. Reboot the modem into fastboot mode

```
adb reboot-bootloader
```

---

## 3. Erase the partitions

```
fastboot erase modem
fastboot erase boot
fastboot erase recovery
fastboot erase fsg
```

---

## 4. Reboot the modem

A reboot is required because **ADB will not allow erasing a system partition that is currently in use**.

```
fastboot reboot
```

---

## 5. Erase the partitions

```
fastboot erase system
fastboot erase recoveryfs
fastboot reboot
```

---

## 6. Flash modem partitions (see link in firmware catalog to download files)

```
fastboot flash modem NON-HLOS.ubi
fastboot flash system sysfs.ubi
fastboot flash fsg fsg.ubi
fastboot flash recovery recovery.img
fastboot flash recoveryfs recoveryfs.ubi
```

---

## 7. Boot using boot.img (without flashing first, to check if it works) 

```
fastboot boot boot.img
```

---

## 8. Verify that everything works correctly

Perform basic checks and confirm the modem boots correctly.

---

## 9. Flash boot.img permanently

```
fastboot flash boot boot.img
```

Reboot the modem afterward.

---

## 10. Configure the modem

Use **AT commands** to configure network access:

* APN
* Operator registration
* Other required parameters

You may use a prepared script (see below).

---

# Part 2 – Upload Missing Files

## 1. Remount root partition as read-write

```
adb shell mount -o remount,rw /
```

---

## 2. Upload required files and generate ssh keys

```
adb push ethtool /usr/bin
adb push jq /usr/bin
adb push curl /usr/bin
adb push atcli_smd8 /usr/bin
adb push atcli /usr/bin
adb push sshd /usr/sbin
adb push modem_config /usr/bin
adb push httpd.service /lib/systemd/system
adb push sshd.service /lib/systemd/system
adb shell chmod 755 /usr/bin/ethtool /usr/bin/jq /usr/bin/curl /usr/bin/atcli_smd8 /usr/bin/atcli /usr/sbin/sshd /usr/bin/modem_config
adb shell ln -s /usr/sbin/sshd /usr/sbin/dropbearkey
adb shell mkdir /etc/dropbear
adb shell dropbearkey -t rsa -f /etc/dropbear/dropbear_rsa_host_key -s 2048
adb shell dropbearkey -t ed25519 -f /etc/dropbear/dropbear_ed25519_host_key
adb shell 600 /etc/dropbear/dropbear_rsa_host_key /etc/dropbear/dropbear_ed25519_host_key
```

---

## 3. Enable services

```
adb shell systemctl enable sshd
adb shell systemctl enable httpd
adb shell systemctl daemon-reload
```

---

## 4. Configure the modem

Run the `modem_config` script and adjust your configuration:

* APN
* Network settings
* Other parameters if necessary

---

## 5. Remount root partition as read-only

```
adb shell mount -o remount,ro /
```

---

## 6. Reboot the modem

```
adb shell reboot
```

---

# Part 3 – Install T99W175 SimpleAdmin

Follow the original instructions from **Brazzo978**, but note the differences below because this firmware differs slightly.

## Key differences

1. The main HTTP server directory is:

```
/WEBSERVER/www
```

2. Backup original files first, for example:

```
/WEBSERVER/www_org
```

3. Files can be uploaded using:

```
adb push
```

instead of SSH.

4. SimpleAdmin authentication requires the partition containing the files to be **mounted as RW**.

You have two options:

### Option A

Disable authentication in the configuration file.

### Option B

Move the files to a partition that is **RW by default** and modify:

```
httpd.service
```

5. Ensure `modem_config` correctly set the following options in:

```
/etc/data/mobileap_cfg.xml
```

```
<AutoConnect>1</AutoConnect>
<FirstPreferredBackhaul>wwan</FirstPreferredBackhaul>
<MobileAPEnableAtBootup>1</MobileAPEnableAtBootup>
```

---

# TODO / Known Limitations

## 1. DHCP is not working

You must configure a static IP on your computer/router and deafult GW, for example:

```
192.168.225.2/24, 192.168.225.1
```

---

## 2. IP Passthrough

Not tested yet. Most likely it will not work until DHCP works.

---

## 3. Temperature AT command

This firmware does not support:

```
AT^TEMP?
```

---

## 4. Performance limitation

Due to **kernel 4.14.117**, **IPA acceleration is not available**, therefore maximum throughput is limited to approximately **300 Mbit/s**.

## 5. Final thoughts

Still not 100% ready but we are going forward. I'm open for any comments/help !!!
