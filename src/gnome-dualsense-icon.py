#!/usr/bin/python3
import os
import gi
import signal
import subprocess
gi.require_version("Gtk", "3.0")
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk as gtk, AppIndicator3 as appindicator
from gi.repository import GLib
import time
from threading import Thread

#example: /sys/devices/pci0000:00/0000:00:08.1/0000:05:00.3/usb1/1-2/1-2.2/1-2.2:1.3/0003:054C:0CE6.0005/power_supply/ps-controller-battery-7c:66:ef:4f:79:
battery = subprocess.check_output(["find", "/sys/devices/","-name","ps-controller-battery*"]).decode("utf-8").strip()
print("Battery info location: "+battery)
refresh_time_sec=10

class Indicator():
    def __init__(self):
        self.indicator = appindicator.Indicator.new("Dualsense battery", os.path.abspath('gamepad-icon.png'), appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_label("--%", "Battery status and level")
        self.indicator.set_menu(self.create_menu())

        self.update = Thread(target=self.get_time)
        self.update.daemon=True
        self.update.start()

    def get_time(self):
      loop = 0
      while True:
          GLib.idle_add( self.update_capacity, self.indicator , priority=GLib.PRIORITY_DEFAULT)
          time.sleep(refresh_time_sec)

    def create_menu(self):
        menu = gtk.Menu()
        exittray = gtk.MenuItem(label='Exit')
        exittray.connect('activate', quit)
        menu.append(exittray)
        menu.show_all()
        return menu
        
    def quit(self, source):
        gtk.main_quit()

    def update_capacity(self, indicator):
        try:
            f = open(f"{battery}/capacity")
            status_file = open(f"{battery}/status")
        except FileNotFoundError:
            print("ERROR: Your controller can't be detected.")
            sys.exit()
        else:
            battery_percentage_left = f.readline().strip()
            status = status_file.readline().strip()
            
            if status == "Charging":
                label = "C"+battery_percentage_left+"%"
            elif status == "Full":
                label = "F"+battery_percentage_left+"%"
            else:
                label = battery_percentage_left+"%"
            indicator.set_label(label,"Battery status and level")
            f.close()
            status_file.close()

Indicator()
signal.signal(signal.SIGINT, signal.SIG_DFL)
gtk.main()