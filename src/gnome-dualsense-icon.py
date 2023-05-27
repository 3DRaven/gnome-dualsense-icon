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
import pydbus #apt-get install python3-pydbus 

waiting_display_on_sec=10 #waiting to turning on second display time
gamepad_rescan_sec=3 #reconnection to gamepad time and key pressed scanner restart time

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
command_display_second_on_not_primary = f"xrandr --output {default_tv_screen} --mode {default_tv_resolution} --scale {default_tv_scale} --crtc 0"
command_display_second_off = f"xrandr --output {default_tv_screen} --off"
command_display_first_on = f"xrandr --output {default_main_screen} --mode {default_main_resolution} --scale {default_main_scale} --primary --crtc 0"
command_display_first_on_not_primary = f"xrandr --output {default_main_screen} --mode {default_main_resolution} --scale {default_main_scale} --crtc 0"
command_display_first_off = f"xrandr --output {default_main_screen} --off"
#start steam in old big picture mode, because new big picture has some glitches
command_steam_start = "env GDK_SCALE=2 /usr/bin/steam -silent -oldbigpicture"

class Printer:
    def __init__(self) -> None:
        self.counter = 0
    def print_every(self, string: str, every: int = 30):
        if self.counter == every or self.counter == 0:
            print(string)
            self.counter = 0
        self.counter += 1
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

    def wait_display_on(self,max_wait_sec,display_name):
            print(f"Waiting for turning {display_name} display on")
            loop = 0
            while True:
                if self.is_display_enabled(display_name) or loop > max_wait_sec:
                    print(f"Display {display_name} on")
                    break
                time.sleep(1)
                loop = loop + 1
    
    def wait_display_off(self,max_wait_sec,display_name):
            print(f"Waiting for turning {display_name} display off")
            loop = 0
            while True:
                if not self.is_display_enabled(display_name) or loop > max_wait_sec:
                    print(f"Display {display_name} off")
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
        def command():
            print("Centering mouse cursor")
            screen = Wnck.Screen.get_default()
            #for preventing some glitches with side pannels and mouse in new screen and resolution
            self.run_and_wait(f"xdotool mousemove {screen.get_width()//2} {screen.get_height()//2}")
        GLib.idle_add( command , priority=GLib.PRIORITY_DEFAULT)    

    def switch_to_first_display(self):
        print("Switch to first display")
        # off first because some windows size will be resized for new one display automatically
        self.run_and_wait(command_display_second_off)
        self.run_and_wait(command_display_first_on)
        self.wait_display_on(waiting_display_on_sec,default_main_screen)
        print("Moving sound to first output device")
        self.run_and_wait(command_sound_to_first)


    def switch_to_second_display(self):
        print("Switch to second display")
        # off first because some windows size will be resized for new one display automatically
        self.run_and_wait(command_display_first_off)
        self.run_and_wait(command_display_second_on)
        self.wait_display_on(waiting_display_on_sec,default_tv_screen)
        self.list_audio_sinks()
        print("Switching sound to second device")
        self.run_and_wait(command_sound_to_second)
        self.center_mouse_cursor()

    def turn_on_second_display(self):
        print("Turn on second display")
        self.run_and_wait(command_display_second_on_not_primary)
        self.wait_display_on(waiting_display_on_sec,default_tv_screen)

    def turn_off_second_display(self):
        print("Turn on second display")
        self.run_and_wait(command_display_second_off)
        self.wait_display_off(waiting_display_on_sec,default_tv_screen)

    def turn_on_first_display(self):
        print("Turn on first display")
        self.run_and_wait(command_display_first_on_not_primary)
        self.wait_display_on(waiting_display_on_sec,default_main_screen)
    
    def turn_off_first_display(self):
        print("Turn on first display")
        self.run_and_wait(command_display_first_off)
        self.wait_display_on(waiting_display_on_sec,default_main_screen)
        
    def start_steam(self): 
        print("Starting steam")
        self.steam_process = self.just_run(command_steam_start)

    def is_primary_display(self,display_name):
        active_monitor_model = Gdk.Display.get_default().get_primary_monitor().get_model()
        print(f"Active monitor model {active_monitor_model}")
        return active_monitor_model == display_name
    
    def is_display_enabled(self,display_name):
        display = Gdk.Display.get_default()
        for index in range(0,display.get_n_monitors()):
            monitor = display.get_monitor(index)
            model = monitor.get_model()
            print(f"Found monitor {model}")
            if model != None and display_name in model:
                return True
        return False            
    
class Indicator:
    def __init__(self, dbus: pydbus.SystemBus, device_info_manager, default_icon_name: str = 'input-gaming', default_battery_percentage:str = '--', default_battery_state: str = '?', default_gamepad_name: str = 'Wireless Controller'):
        self.dbus: pydbus.SystemBus = dbus
        self.default_gamepad_name: str = default_gamepad_name
        self.default_icon_name: str = default_icon_name
        self.last_battery_icon_name: str = default_icon_name
        self.default_battery_percentage: str = default_battery_percentage
        self.last_battery_percentage: str = default_battery_percentage
        self.default_battery_state: str = default_battery_state
        self.last_battery_state: str = default_battery_state
        self.indicator:appindicator.Indicator = appindicator.Indicator.new("Dualsense battery", self.last_battery_icon_name, appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_label(default_battery_percentage+'%', "Battery status and level")
        self.indicator.set_menu(self.create_menu())
        self.device_info_manager = device_info_manager
        self.gamepad = None
        self.subscribe_to_battery()
        
        
    def subscribe_to_battery(self):
        def device_added_command(*event):
            print(f"Recieved device added event {event}")
            self.subscribe_to_devices()
        def device_removed_command(*event):
            print(f"Recieved device removed event {event}")
            self.indicator.set_label(self.default_battery_percentage+'%',"Battery status and level")
            self.indicator.set_icon_full(self.default_icon_name,"Battery icon")

        self.device_info_manager.DeviceAdded.connect(device_added_command)
        self.device_info_manager.DeviceRemoved.connect(device_removed_command)
        
        self.subscribe_to_devices()

    def subscribe_to_devices(self):
        for device_path in self.device_info_manager.EnumerateDevices():
            device = self.dbus.get('org.freedesktop.UPower', device_path)
            print(f"Power data for device {device.Model} with path {device_path}")
            if self.default_gamepad_name in device.Model:
                def command(external_self,properties,array):
                    self.update_status(properties,array)
                print(f"Subscribe to dbus device {device.Model} state changing")
                device.PropertiesChanged.connect(command)
                self.update_status({'IconName': device.IconName, 'State': device.State, 'Percentage': device.Percentage},[])

    # Indicator cahnged {'UpdateTime': 1684691028, 'IconName': 'battery-good-charging-symbolic', 'State': 1, 'Percentage': 35.0} []    
    def update_status(self,properties,array):
        print(f"Recieved properties changed event: {properties} last state: {self.last_battery_icon_name} {self.last_battery_percentage} {self.last_battery_state}")
        #low-charging
        #caution-charging
        #full
        if 'IconName' in properties and 'charging' in properties['IconName']:
            self.last_battery_state = "C" #Charging
        elif 'IconName' in properties and 'low' in properties['IconName']:
            self.last_battery_state = "" #Low battery
        elif 'IconName' in properties and 'caution' in properties['IconName']:
            self.last_battery_state = "" #Very low battery
        elif 'IconName' in properties and 'full' in properties['IconName']:
            self.last_battery_state = "" #Full battery
        elif 'IconName' in properties and 'battery-good' in properties['IconName']:
            self.last_battery_state = "" #middle battery cherge        
        
        if 'Percentage' in properties:
            self.last_battery_percentage = properties['Percentage']
        # if 'IconName' in properties:
        #     self.last_battery_icon_name = properties['IconName']
        self.indicator.set_label(self.last_battery_state+str(self.last_battery_percentage)+"%","Battery status and level")
        # self.indicator.set_icon_full(self.last_battery_icon_name,"Battery icon")

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

class SteamWatcher:
    def __init__(self,dbus,device_info_manager,default_gamepad_name: str = 'Wireless Controller'):
        self.commamd_runner = CommandsRunner()
        self.last_time_window = None
        self.device_info_manager = device_info_manager
        self.dbus = dbus
        self.default_gamepad_name = default_gamepad_name
        self.printer = Printer()
        self.subscribe_to_battery()
        self.watch_steam()

    def subscribe_to_battery(self):
        def device_added_command(*event):
            print(f"Recieved device added event {event}")
            for device_path in self.device_info_manager.EnumerateDevices():
                device = self.dbus.get('org.freedesktop.UPower', device_path)
                if self.default_gamepad_name in device.Model:
                    self.gamepad_events_watcher = Thread(target=self.watch_keys)
                    self.gamepad_events_watcher.daemon=True
                    self.gamepad_events_watcher.start()
        def device_removed_command(*event):
            print(f"Recieved device removed event {event}")
            self.gamepad_device = None

        self.device_info_manager.DeviceAdded.connect(device_added_command)
        self.device_info_manager.DeviceRemoved.connect(device_removed_command)
        
        self.gamepad_device = self.find_gamepad_by_name() 
        if self.gamepad_device != None:
            device_added_command(None)

    def is_steam_running(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'steam':
                return True
        return False
    
    def find_gamepad_by_name(self):
        devices = [evdev.InputDevice(device) for device in evdev.list_devices()]
        for device in devices:
            print(f"Found device '{device.name}'")
            if default_gamepad_name in device.name:
                return device
        return None
    
    def watch_keys(self):
        try:
            self.gamepad_device = self.find_gamepad_by_name()    
            if not self.gamepad_device:
                    raise Exception(f"Gamepad device {default_gamepad_name} not found")  
            print(f"Found gamepad device path '{self.gamepad_device}'")
            for event in self.gamepad_device.read_loop():
                # print(f"Gamepad key pressed {evdev.categorize(event)}")
                if event.code == evdev.ecodes.BTN_MODE and event.value == 1:
                    print(f"Gamepad key pressed {evdev.categorize(event)}")
                    if not self.is_steam_running():
                        self.commamd_runner.start_steam()
                    else:
                        print("Steam already started")
                if event.code == evdev.ecodes.BTN_NORTH and event.value == 1:
                    if evdev.ecodes.BTN_SELECT in self.gamepad_device.active_keys():
                        print(f"Gamepad key pressed {evdev.categorize(event)} with active BTN_SELECT")
                        if  self.commamd_runner.is_primary_display(default_main_screen):
                            self.commamd_runner.switch_to_second_display()
                        else:
                            self.commamd_runner.switch_to_first_display()
                if event.code == evdev.ecodes.BTN_WEST and event.value == 1:
                    if evdev.ecodes.BTN_SELECT in self.gamepad_device.active_keys():
                        print(f"Gamepad key pressed {evdev.categorize(event)} with active BTN_SELECT")
                        if  self.commamd_runner.is_display_enabled(default_main_screen):
                            self.commamd_runner.turn_off_first_display()
                        else:
                            self.commamd_runner.turn_on_first_display()
                if event.code == evdev.ecodes.BTN_EAST and event.value == 1:
                    if evdev.ecodes.BTN_SELECT in self.gamepad_device.active_keys():
                        print(f"Gamepad key pressed {evdev.categorize(event)} with active BTN_SELECT")
                        if  self.commamd_runner.is_display_enabled(default_tv_screen):  
                            self.commamd_runner.turn_off_second_display()
                        else:
                            self.commamd_runner.turn_on_second_display()

        except Exception as e:
            self.printer.print_every(f"Connection error {str(e)}")

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
                if self.is_steam_main_window(instance_class_name) and self.last_time_window != instance_class_name and self.commamd_runner.is_primary_display(default_main_screen):
                    print("Opened main steam window on main display")
                    opened_window.activate(True)
                    opened_window.maximize ()
                if self.is_steam_big_picture_window(instance_class_name) and self.last_time_window != instance_class_name:
                    print("Opened Big Picture steam window")
                    self.commamd_runner.switch_to_second_display()
                    opened_window.activate(True)
                    # opened_window.make_above()
                    opened_window.maximize()
                    opened_window.set_fullscreen(True)
                self.last_time_window = instance_class_name
        
        def do_window_closed(this_screen: Wnck.Screen, closed_window: Wnck.Window):
                instance_class_name = closed_window.get_class_instance_name()
                if self.is_steam_main_window(instance_class_name):
                    print("Closed main steam window")
                if self.is_steam_big_picture_window(instance_class_name):
                    print("Closed Big Picture steam window")
                if self.is_steam_big_picture_window(instance_class_name) and self.commamd_runner.is_primary_display(default_tv_screen):
                    print("Big Picture steam window closed on second display")
                    self.commamd_runner.switch_to_first_display()
                    
        screen.connect('window-opened', do_window_opened)
        screen.connect('window-closed', do_window_closed)

#Reconnecting gamepad process in Ubuntu has some problems, so we need to reconnect it periodically
class GamepadWatcher():
    def __init__(self, adapter_index: int, dbus: pydbus.SystemBus):
        self.adapter_index: int = adapter_index
        self.dbus: pydbus.SystemBus = dbus
        self.device_manager = self.dbus.get('org.bluez', '/')
        self.devices = self.device_manager.GetManagedObjects()  
        self.gamepads = self.filter_devices(self.dbus,self.devices,self.adapter_index)
        
        self.subscribe_to_all_device_state_changed()
        self.subscribe_to_devices_added()
        self.subscribe_to_devices_removed()

        for path in self.gamepads:
            self.gamepads[path].infinite_connection_attempts()

    def subscribe_to_devices_added(self):
        def command(device_path,device):
            device_properties = self.get_gamepad_properties(device,device_path)
            if device_properties != None:
                print(f"Gamepad added {device_path}")
                self.gamepads[device_path] = device_properties
                device_properties.infinite_connection_attempts()
                device_properties.subscribe_to_properties_changed()
        self.device_manager.InterfacesAdded.connect(command)

    def subscribe_to_devices_removed(self):
        def command(device_path,device_info):
            if device_path in self.gamepads:
                print(f"Gamepad removed {device_path}")
                del self.gamepads[device_path]
        self.device_manager.InterfacesRemoved.connect(command)
        
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
                    print(f"Found bluetooth device {device_name}")
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
                printer = Printer()
                while True:
                    try:
                        if(self.is_paired() and self.is_connected()):
                            self.connection_attempts_started = False
                            break
                        else:
                            if not self.is_connected() and self.proxy != None:
                                printer.print_every(f"Try to connect device {self.name}")
                                self.proxy.Connect()
                                printer.print_every(f"Device connectd {self}")
                            if not self.is_paired() and self.proxy != None:
                                printer.print_every(f"Try to pair device {self.name}")
                                self.proxy.Pair()
                                printer.print_every(f"Device paired {self}")    
                            self.connection_attempts_started = False
                            break
                    except Exception as e:
                        printer.print_every(f"Error in connection to device process {str(e)}")
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
            print(f"Subscribe to device {self.name} state changing")
            self.proxy.PropertiesChanged.connect(command)
            self.subscribed = True

    def __str__(self):
        is_paired = self.is_paired()
        is_connected = self.is_connected()
        return f"Name {self.name} adapter {self.adapter} address {self.address} paired {is_paired} connected {is_connected} subscribed {self.subscribed}"

def main():
    print("Press gamepad button X (north) + select to switch between displays and sound sources")
    print("Press gamepad button PS (mode) to start steam if it is not started")
    print()
    print()
    #commands for introspect bluetooth dbus from command line
    # gdbus introspect --system --dest org.bluez --object-path /org/bluez
    # gdbus introspect --system --dest org.bluez --object-path /
    # gdbus introspect --system --dest org.bluez --object-path /org/bluez/hci0

    dbus = pydbus.SystemBus()
    upower_manager = dbus.get('org.freedesktop.UPower', '/org/freedesktop/UPower')
    Indicator(dbus,upower_manager)
    SteamWatcher(dbus,upower_manager)
    GamepadWatcher(0,dbus)
    GamepadWatcher(1,dbus)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()

if __name__ == "__main__":
    main()


#поменять просто включение/выключение на раскладку экранов с размещением
#если включен второй и пытаются включить первый, то он должен быть слева от второго и наоборот. При этом primary дисплей надо сохранять тем, который есть в данный момент.
#Так как убунта просто делать два отдельных экрана не умеет.
#добавить включение выключение экранов с доп кнопок мышки 
#запуск отдельной панели на втором экране gnome-panel --display=:0.1 & Но это именно второй экран.
#lsusb -t далее шина, порт корневого хаба, порт хаба подключения echo -1 /sys/bus/usb/devices/1-2.2/power/autosuspend_delay_ms
#echo -1 > /sys/bus/usb/devices/3-4/power/autosuspend_delay_ms
#echo -1 > /sys/bus/usb/devices/1-2.2/power/autosuspend_delay_ms