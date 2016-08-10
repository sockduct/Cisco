################################################################################
# Example TCL Script
# 
# Example detects a syslog message indicating a change in an OSPF neighbor
# relationship, collects information from the IOS device, and sends it to a
# particular e-mail address.
#
# The environment variables used in this script are syslog message, syslog
# pattern, show command output, e-mail, directory, and policy. The script
# activation and the output can be easily modified by changing the environment
# variables.
#

################################################################################
# EEM Event Detector Subsystem to Register With (required)
################################################################################
# Register with syslog monitor to watch for passed pattern
::cisco::eem::event_register_syslog pattern $_syslog_pattern

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
if {![info exists _show_cmd]} {
    set result "Policy cannot be run:  variable _show_cmd has not been set"
    error $result $errorInfo
}
if {![info exists _syslog_pattern]} {
    set result \
        "Policy cannot be run:  variable _syslog_pattern has not been set"
    error $result $errorInfo
}
if {![info exists _email_server]} {
    set result \
    "Policy cannot be run: variable _email_server has not been set"
    error $result $errorInfo
}
if {![info exists _email_from]} {
    set result \
    "Policy cannot be run: variable _email_from has not been set"
    error $result $errorInfo
}
if {![info exists _email_to]} {
    set result \
    "Policy cannot be run: variable _email_to has not been set"
    error $result $errorInfo
}
if {![info exists _email_cc]} {
    #_email_cc is an option, must set to empty string if not set.
    set _email_cc ""
}

# Execute _show_cmd 
if [catch {cli_open} result] {
    error $result $errorInfo
} else {
    array set cli1 $result
}
if [catch {cli_exec $cli1(fd) "en"} result] {
    error $result $errorInfo
}
if [catch {cli_exec $cli1(fd) $_show_cmd} result] {
    error $result $errorInfo
} else {
    set cmd_output $result
}
if [catch {cli_close $cli1(fd) $cli1(tty_id)} result] {
    error $result $errorInfo
}

# Optionally log results of executing _show_cmd
set msg [format "Command \"%s\" executed successfully" $_show_cmd]
action_syslog priority info msg $msg
if {$_cerrno != 0} {
    set result [format "component=%s; subsys err=%s; posix err=%s;\n%s" \
        $_cerr_sub_num $_cerr_sub_err $_cerr_posix_err $_cerr_str]
    error $result
}

# Generate an E-mail
set routername [info hostname]
if {[string match "" $routername]} {
    error "Host name is not configured"
}

if [catch {smtp_subst [file join $tcl_library email_template_cmd.tm]} result] {
    error $result $errorInfo
}

if [catch {smtp_send_email $result} result] {
    error $result $errorInfo
}

# Optionally log sending of E-mail notification

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
## Specify where the e-mail should be sent:
#config terminal
#event manager environment _email_to <target@example.com>
#
## Configure the command to be captured when the syslog pattern is seen:
#event manager environment _show_cmd <show cdp neighbor>
#
## Specify from whom the e-mail should be sent:
#event manager environment _email_from <sender@example.com>
#
## Set the syslog pattern that triggers the script
#event manager environment _syslog_pattern <%OSPF-5-ADJCHG>
#
## Set the environment variable of the e-mail server:
#event manager environment _email_server <smtp.example.com>
#-or-
#event manager environment _email_server <password@smtp.example.com>

################################################################################
# Register directory and TCL script (required)
################################################################################
# TCL script must already by loaded on IOS device!
#
## Configure the file location of the script:
#event manager directory user policy <"disk0:/"|"flash:/">
#
## Specify the name of the script:
#event manager policy <syslog_email.tcl>

