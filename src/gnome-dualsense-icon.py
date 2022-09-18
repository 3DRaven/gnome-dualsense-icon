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

refresh_time_sec=10
default_label="--%"
default_desc="Battery status and level"
class Indicator():
    def __init__(self):
        self.indicator = appindicator.Indicator.new("Dualsense battery", 'input-gaming', appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_label(default_label, default_desc)
        self.indicator.set_menu(self.create_menu())

        self.update = Thread(target=self.get_time)
        self.update.daemon=True
        self.update.start()

    def refresh_baterry_path(self):
        try:
            self.battery_path
        except AttributeError:
            #example: /sys/devices/pci0000:00/0000:00:08.1/0000:05:00.3/usb1/1-2/1-2.2/1-2.2:1.3/0003:054C:0CE6.0005/power_supply/ps-controller-battery-7c:66:ef:4f:79:
            self.battery_path = subprocess.check_output(["find", "/sys/devices/","-name","ps-controller-battery*"]).decode("utf-8").strip()

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
            self.refresh_baterry_path()
            f = open(f"{self.battery_path}/capacity")
            status_file = open(f"{self.battery_path}/status")
            #print("Battery info location: " + self.battery_path)
        except FileNotFoundError:
            #print("ERROR: Your controller can't be detected, refresh planned.")
            del self.battery_path
            indicator.set_label(default_label,default_desc)
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