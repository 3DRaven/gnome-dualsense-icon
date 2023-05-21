#!/usr/bin/python3

print(f"Please check that this packages installed in your systyem [python3-pydbus,python3-evdev,xdotool]")

import signal
import subprocess
import evdev #apt-get install python3-evdev
import psutil
import gi
gi.require_version("Gtk", "3.0")
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator
from gi.repository import GLib
from gi.repository import Gdk
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
import time
from threading import Thread
import re
from pydbus import SystemBus #apt-get install python3-pydbus 

battery_refresh_time_sec=10 #rescan battery of gamepad time
waiting_second_display_sec=10 #waiting to turning on second display time
gamepad_rescan_sec=3 #reconnection to gamepad time and key pressed scanner restart time
default_label="--%"
default_desc="Battery status and level"

default_gamepad_name = 'Wireless Controller' #gamepad name for connected bluetooth gamepad
default_sink_for_games = "alsa_output.pci-0000_01_00.1.hdmi-stereo" #sound ouput device for second display
default_sink_for_work = "alsa_output.usb-Audeze_Inc_Audeze_Maxwell_Dongle_0000000000000000-01.iec958-stereo" #sound output device for first display
default_tv_screen="HDMI-0" #secondary display for games
default_tv_resolution="1920x1080" #secondary display resolution
default_tv_scale="1x1" #secondary display scale
default_main_screen="DP-4" #first display name
default_main_resolution="2560x1600" #first display resolution
default_main_scale="1.5x1.5" #first display scale

#for change sound output to second display
command_sound_to_second = f"pactl set-default-sink \"{default_sink_for_games}\""
command_sound_to_first = f"pactl set-default-sink \"{default_sink_for_work}\""
#switching displays commands
command_display_second_on = f"xrandr --output {default_tv_screen} --mode {default_tv_resolution} --scale {default_tv_scale} --primary --crtc 0"
command_display_second_off = f"xrandr --output {default_tv_screen} --off"
command_display_first_on = f"xrandr --output {default_main_screen} --mode {default_main_resolution} --scale {default_main_scale} --primary --crtc 0"
command_display_first_off = f"xrandr --output {default_main_screen} --off"
#start steam in old big picture mode, because new big picture has some glitches
command_steam_start = "env GDK_SCALE=2 /usr/bin/steam -silent -oldbigpicture"

class CommandsRunner:
    def __init__(self):
        self.steam_process = None
        pass

    def run_and_wait(self,command):
            print(f"Run and wait command {command}")
            return subprocess.Popen(command, shell=True).wait()
    def just_run(self,command):
        print(f"Run command {command}")
        return subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def switch_to_first_display(self):
        print("Switch to first display")
        self.run_and_wait(command_display_first_on)
        self.run_and_wait(command_display_second_off)
        print("Moving sound to first output device")
        self.run_and_wait(command_sound_to_first)

    def wait_second_display_sec(self,sec):
            print("Waiting for turning second display on")
            loop = 0
            while True:
                if self.is_active_display(default_tv_screen) or loop > sec:
                    break
                time.sleep(1)
                loop = loop + 1

    def list_audio_sinks(self):
            print("Listing output sound devices")
            output = subprocess.check_output(['pactl', 'list', 'sinks']).decode()
            matches = re.finditer(r'node.name = "(.+)"', output, flags=re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):           
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    print(f"Found sound output device: [{match.group(groupNum)}]")

    def center_mouse_cursor(self):
            print("Centering mouse cursor")
            screen = Wnck.Screen.get_default()
            #for preventing some glitches with side pannels and mouse in new screen and resolution
            self.run_and_wait(f"xdotool mousemove {screen.get_width()//2} {screen.get_height()//2}")

    def switch_to_second_display(self):
        print("Switch to second display")
        self.run_and_wait(command_display_first_off)
        self.run_and_wait(command_display_second_on)
        self.wait_second_display_sec(waiting_second_display_sec)
        self.list_audio_sinks()
        print("Switching sound to second device")
        self.run_and_wait(command_sound_to_second)
        self.center_mouse_cursor()
    
    def start_steam(self): 
        print("Starting steam")
        self.steam_process = self.just_run(command_steam_start)

    def is_active_display(self,display_name):
        active_monitor_model = Gdk.Display.get_default().get_primary_monitor().get_model()
        print(f"Active monitor model {active_monitor_model}")
        return active_monitor_model == display_name

class Indicator:
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
          time.sleep(battery_refresh_time_sec)

    def create_menu(self):
        menu = gtk.Menu()
        
        switch_to_first_display = gtk.MenuItem(label='First display')
        def switch_to_first_display_command(self):
            CommandsRunner().switch_to_first_display()
        switch_to_first_display.connect('activate', switch_to_first_display_command)
        menu.append(switch_to_first_display)
        
        switch_to_second_display = gtk.MenuItem(label='Second display')
        
        def switch_to_second_display_command(self):
            CommandsRunner().switch_to_second_display()
        switch_to_second_display.connect('activate', switch_to_second_display_command)
        menu.append(switch_to_second_display)
        
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
            capacity_file = open(f"{self.battery_path}/capacity")
            status_file = open(f"{self.battery_path}/status")
            #print("Battery info location: " + self.battery_path)
        except FileNotFoundError:
            #print("ERROR: Your controller can't be detected, refresh planned.")
            del self.battery_path
            indicator.set_label(default_label,default_desc)
        else:
            battery_percentage_left = capacity_file.readline().strip()
            status = status_file.readline().strip()
            
            if status == "Charging":
                label = "C"+battery_percentage_left+"%"
            elif status == "Full":
                label = "F"+battery_percentage_left+"%"
            else:
                label = battery_percentage_left+"%"
            indicator.set_label(label,"Battery status and level")
            capacity_file.close()
            status_file.close()

class SteamWatcher:
    def __init__(self):
        self.commamd_runner = CommandsRunner()
        self.last_time_window = None

        self.gamepad_events_watcher = Thread(target=self.watch_keys)
        self.gamepad_events_watcher.daemon=True
        self.gamepad_events_watcher.start()

        self.watch_steam()

    def is_steam_running(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'steam':
                return True
        return False
    
    def find_gamepad_by_name(self):
        print("Finding gamepad by name")
        devices = [evdev.InputDevice(device) for device in evdev.list_devices()]
        for device in devices:
            print(f"Found device '{device.name}'")
            if default_gamepad_name in device.name:
                return device
        return None
    
    def watch_keys(self):
        while True:
            try:
                gamepad_device = self.find_gamepad_by_name()
                if not gamepad_device:
                        raise Exception(f"Gamepad device {default_gamepad_name} not found")  
                print(f"Found gamepad device path '{gamepad_device}'")
                for event in gamepad_device.read_loop():
                    if event.value == 1:
                        print(f"Gamepad key pressed {evdev.categorize(event)}")
                        print(gamepad_device.active_keys())
                    if event.code == evdev.ecodes.BTN_MODE and event.value == 1 and self.commamd_runner.is_active_display(default_main_screen):
                        self.commamd_runner.switch_to_second_display()
                        if not self.is_steam_running():
                            self.commamd_runner.start_steam()
                        else:
                            print("Steam already started")
                    if event.code == evdev.ecodes.BTN_A and event.value == 1:
                        if evdev.ecodes.BTN_SELECT in gamepad_device.active_keys():
                            if  self.commamd_runner.is_active_display(default_main_screen):
                                self.commamd_runner.switch_to_second_display()
                            else:
                                self.commamd_runner.switch_to_first_display()
            except Exception as e:
                print(f"Keys scan error {str(e)}")
                time.sleep(gamepad_rescan_sec)
                
    def is_steam_main_window(self,class_name):
        return class_name == 'Steam'

    def is_steam_big_picture_window(self,class_name):
        return class_name == 'steam'
        
    def watch_steam(self):
        gtk.init([])
        screen: Wnck.Screen = Wnck.Screen.get_default()
        screen.force_update()
        
        def do_window_opened(this_screen: Wnck.Screen, opened_window: Wnck.Window):
                instance_class_name = opened_window.get_class_instance_name()
                if self.is_steam_main_window(instance_class_name) and self.last_time_window != instance_class_name and self.commamd_runner.is_active_display(default_main_screen):
                    print("Opened main steam window on main display")
                    opened_window.activate(True)
                    # opened_window.maximize ()
                if self.is_steam_big_picture_window(instance_class_name) and self.last_time_window != instance_class_name:
                    print("Opened Big Picture steam window")
                    opened_window.activate(True)
                    # opened_window.make_above()
                    # opened_window.set_fullscreen(True)
                self.last_time_window = instance_class_name
        
        def do_window_closed(this_screen: Wnck.Screen, closed_window: Wnck.Window):
                instance_class_name = closed_window.get_class_instance_name()
                if self.is_steam_main_window(instance_class_name):
                    print("Closed main steam window")
                if self.is_steam_big_picture_window(instance_class_name):
                    print("Closed Big Picture steam window")
                if self.is_steam_big_picture_window(instance_class_name) and self.commamd_runner.is_active_display(default_tv_screen):
                    print("Big Picture steam window closed on second display")
                    self.commamd_runner.switch_to_first_display()
                    
        screen.connect('window-opened', do_window_opened)
        screen.connect('window-closed', do_window_closed)

#Reconnecting gamepad process in Ubuntu has some problems, so we need to reconnect it periodically
class GamepadWatcher():
    def __init__(self, adapter_index):
        self.adapter_index = adapter_index
        self.dbus = SystemBus()
        self.manager = self.dbus.get('org.bluez', '/')
        # self.adapter = bus.get('org.bluez','/org/bluez/hci0')
        self.devices = self.manager.GetManagedObjects()  
        self.gamepads = self.filter_devices(self.dbus,self.devices,self.adapter_index)
        
        self.subscribe_to_all_device_state_changed()
        self.subscribe_to_devices_added()
        
        for path in self.gamepads:
            self.gamepads[path].infinite_connection_attempts()

    def subscribe_to_devices_added(self):
        def command(device_path,device):
            device_properties = self.get_gamepad_properties(device,device_path)
            if device_properties != None:
                self.gamepads[device_path] = device_properties
                print(f"Gamepad added {device_path} {device_properties}")
                device_properties.infinite_connection_attempts()
                device_properties.subscribe_to_properties_changed()

        self.manager.InterfacesAdded.connect(command)
        
    def subscribe_to_all_device_state_changed(self):
            paths_to_delete = []
            for path in self.gamepads:    
                try:
                    self.gamepads[path].subscribe_to_properties_changed()
                except Exception as e:
                    print(f"Subscription to gamepad error it will be removed {str(e)}")
                    paths_to_delete.append(path)
            
            for path in paths_to_delete:
                del self.gamepads[path]

    def filter_devices(self,dbus,devices,adapter_index):
        gamepads = {}
        for device_path in devices:
            if f"hci{adapter_index}" in device_path:
                device_properties = self.get_gamepad_properties(devices[device_path],device_path) 
                if  device_properties != None:
                    gamepads[device_path] = device_properties
        return gamepads

    def get_gamepad_properties(self,device_info,device_path):
        if 'org.bluez.Device1' in device_info: 
                device_props = device_info['org.bluez.Device1']
                if  'Name' in device_props:
                    device_name = device_props['Name']
                    if default_gamepad_name in device_name:
                        return  DeviceProperties(self.dbus,device_path)
        return None
    
    def scan_devices():
        pass

class DeviceProperties:
    def __init__(self,dbus,path):
        self.dbus = dbus
        self.path = path
        self.proxy = self.dbus.get('org.bluez',path)
        self.adapter = self.proxy.Adapter
        self.address = self.proxy.Address
        self.name = self.proxy.Name
        
        self.subscribed = False
        self.connection_attempts_started = False

    def is_connected(self):
        try:
            if self.proxy != None:
                return self.proxy.Connected
            else: 
                return False
        except:
            return False

    def is_paired(self):
        try:
            if self.proxy != None:
                return self.proxy.Paired
            else:
                return False
        except:
            return False
        
    def infinite_connection_attempts(self):
        def infinite_connections():
            if not self.connection_attempts_started and self.proxy != None:
                self.connection_attempts_started = True
                while True:
                    try:
                        if(self.is_paired() and self.is_connected()):
                            self.connection_attempts_started = False
                            break
                        else:
                            if not self.is_connected() and self.proxy != None:
                                print(f"Try to connect device {self.name}")
                                self.proxy.Connect()
                                print(f"Device connectd {self}")
                            if not self.is_paired() and self.proxy != None:
                                print(f"Try to pair device {self.name}")
                                self.proxy.Pair()
                                print(f"Device paired {self}")    
                            self.connection_attempts_started = False
                            break
                    except Exception as e:
                        print(f"Connection error: {str(e)} to {self.name}")
                        self.refresh_proxy()
                        time.sleep(gamepad_rescan_sec)


        connections = Thread(target=infinite_connections)
        connections.daemon=True
        connections.start()

    def refresh_proxy(self):
        try:
            self.proxy = self.dbus.get('org.bluez',self.path)
        except:
            self.proxy = None

    def command(self,properties,array):
        if  (('Connected' in properties and properties['Connected'] == False) or 
            ('Paired' in properties and properties['Paired'] == False)):
            print(f"Connection status changed {self.name}")
            self.infinite_connection_attempts()
        elif 'ServicesResolved' in properties and properties['ServicesResolved'] == False:
            print(f"Device {self.name} removed")
            self.proxy = None
        elif 'ServicesResolved' in properties and properties['ServicesResolved'] == True:
            print(f"Device {self.name} reverted")
            self.refresh_proxy()
            self.infinite_connection_attempts()

    def subscribe_to_properties_changed(self):
        if self.subscribed == False:
            def command(external_self,properties,array):
                self.command(properties,array)
            print(f"Try to subscribe to device {self.name} state changing")
            self.proxy.PropertiesChanged.connect(command)
            self.subscribed = True

    def __str__(self):
        is_paired = self.is_paired()
        is_connected = self.is_connected()
        return f"Name {self.name} adapter {self.adapter} address {self.address} paired {is_paired} connected {is_connected} subscribed {self.subscribed}"

def main():
    Indicator()
    SteamWatcher()
    GamepadWatcher(0)
    GamepadWatcher(1)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()

# Проверяем, является ли данный файл основным исполняемым файлом
if __name__ == "__main__":
    main()