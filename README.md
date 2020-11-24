# Interceptor

### Info

To get to load Interceptor at boot, there's obviously loads of ways. For now I have been using this method:

1. Do ```sudo raspi-config  ``` and enabe auto login to command prompt.
2. Do ```crontab -e``` (doesn't need sudo), and on the last line add ```@reboot python3 /home/pi/interceptor-103.py```

This seems to work for now.

### Installation

Burn a fresh Raspberry Pi OS Lite SD card

Our aim firstly is to keep the image on the SD card at a reasonable size. To do this we must stop it from resizing to fill the whole card, which the OS will do on the first boot. To prevent this happening we need to do this after burning the image on our desktop Linux (and before first boot):

1. In /boot/cmdline.txt, remove this string: ```init=/usr/lib/raspi-config/init_resize.sh```
2. On the main partition, delete this file: ```/etc/init.d/resizefs_once```
3. Load up gparted. Resize the main partition to say a gig bigger than it is currently set.

Then we can boot the card in the Pi, and install loads of dependencies, I know it looks like I'm installing things twice, but this is actually the weird order I did it in to get it all to work:

```
sudo apt install python3-pip
sudo pip3 install gfxhat
sudo apt-get install libjpeg-dev -y
sudo apt-get install zlib1g-dev -y
sudo apt-get install libfreetype6-dev -y
sudo apt-get install liblcms1-dev -y
sudo apt-get install libopenjp2-7 -y
sudo apt-get install libtiff5 -y
pip3 install pillow
pip3 install python-rtmidi
pip3 install mido
sudo apt-get install python3-smbus
sudo pip3 install spidev
sudo apt-get install libopenjp2-7
sudo apt install libtiff5
sudo apt-get install libjack0
```
### IMPORTANT - Last step - Go to raspi-config - enable SPI interface and I2C interface


