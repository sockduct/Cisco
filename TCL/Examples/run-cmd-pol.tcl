################################################################################
#
# Basic TCL Script Template to run one or more IOS commands
#
# Note:  To use EEM libraries, you must run TCL script as an EEM TCL Policy
#
# Follow setup directions below to execute script
#
# Description:  Script runs a command and sends output to vty
#
# To do:  Would probably be more useful to send output to a file
################################################################################

################################################################################
# EEM Event Detector Subsystem to Register With (required)
################################################################################
# Register with "None" to run manually
::cisco::eem::event_register_none

################################################################################
# Namespace import (optional)
################################################################################
# Libraries to import - must run as EEM TCL Policy to use these
# Necessary for event_reqinfo
namespace import ::cisco::eem::*
# Necessary for cli_open
namespace import ::cisco::lib::*

################################################################################
# Check entry status (optional) - determine whether earlier policy has been run
# for same event; based on result of previous policy this policy may or may not
# be executed
################################################################################

################################################################################
# TCL Script Body (required)
################################################################################
# Verify that all the environment variables exist. If any of them are not
# available, print out an error message and quit:
#
# None currently used

# Log about usage
action_syslog priority info msg "Executing TCL Script to run IOS commands..."

# Command to run
set cmd "show clock"

# Open handle to CLI
if {[catch {cli_open} output]} {
    error $output $errorInfo
} else {
    array set cli_fd $output
}

# Enter privileged mode (enable) 
if {[catch {cli_exec $cli_fd(fd) "enable"} output]} {
    error $output $errorInfo
}

# Issue the command and save the result in cmd_out
if {[catch {cli_exec $cli_fd(fd) $cmd} cmd_out]} {
    error $output $errorInfo
}

# Close the CLI handle
if {[catch {cli_close $cli_fd(fd) $cli_fd(tty_id)} output]} {
    error $output $errorInfo
}

# Result
puts "Command output:  $cmd_out"

################################################################################
# Set exit status (optional)
################################################################################

# Cisco IOS Required Configuration:
# Configure after TCL script created and loaded onto IOS devie
################################################################################
# Environment variables (optional) used by TCL script - must be defined in IOS
################################################################################
#
# Note:  Variables beginning with underscore (_) are reserved for Cisco
#        internal use and could be overwritten by the system
#
# Populate <parameters>
#
# Configure the command to use:
#event manager environment _show_cmd show interface | include errors
#

################################################################################
# Register directory and TCL script (required)
################################################################################
# TCL script must already by loaded on IOS device!
#
## Configure the file location of the script:
#event manager directory user policy <"disk0:/"|"flash:/">
#event manager directory user policy "disk0:/scripts"
event manager directory user policy "disk0:/"
#
## Specify the name of the script:
event manager policy run-cmd-pol.tcl
#event manager policy run-cmd-pol.tcl type user
#
end
#
## Execute script:
#event manager run run-cmd-pol.tcl

