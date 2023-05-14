# Functions

1. Indicator for Gnome shell to show PS5 Dualsense gamepad battery status as icon.
2. Fast switch to first and second display from indicatore menu.
3. Reconnect gamepad if it was disconnected. Ubuntu has some problems with reconnection PS5 gamepad after gamepad sleep.
4. Switching displays if steam started in Big Picture mode and revert back if Big Picture mode closed
    If you have two displays, one for work and one for games (such as a laptop display and a projector), 
    this script will change the sound to the secondary output and set the projector as the main display 
    when Steam Big Picture mode is started. When Big Picture mode is stopped, everything will revert back 
    to the main display. Switching between displays involves turning off the main display and turning on 
    the secondary display. This method was selected because multimonitor configurations sometimes have 
    glitches when starting games on the secondary display, even if it is set as the primary display.
5. Start steam by gamepad key pressing if Steam was stopped

All settings in script variables inside .py