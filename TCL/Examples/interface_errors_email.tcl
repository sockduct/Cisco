################################################################################
# Example TCL Script
# 
# Example checks interface counters, and if errors are seen, it generates an
# e-mail to the configured account.
#


################################################################################
# EEM Event Detector Subsystem to Register With (required)
################################################################################
# Register with cron - run per configured schedule
::cisco::eem::event_register_timer cron name crontimer2 cron_entry $_cron_entry maxrun_sec 240

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

if {![info exists _show_cmd]} {
    set result \
        "Policy cannot be run: variable _show_cmd has not been set"
    error $result $errorInfo
}

#query the event info and log a message
array set arr_einfo [event_reqinfo]

if {$_cerrno != 0} {
    set result [format "component=%s; subsys err=%s; posix err=%s;\n%s" \
        $_cerr_sub_num $_cerr_sub_err $_cerr_posix_err $_cerr_str]
    error $result 
}

global timer_type timer_time_sec 
set timer_type $arr_einfo(timer_type)
set timer_time_sec $arr_einfo(timer_time_sec)

#log a message
set msg [format "timer event: timer type %s, time expired %s" \
        $timer_type [clock format $timer_time_sec]]

action_syslog priority info msg $msg
if {$_cerrno != 0} {
    set result [format "component=%s; subsys err=%s; posix err=%s;\n%s" \
	$_cerr_sub_num $_cerr_sub_err $_cerr_posix_err $_cerr_str]
    error $result 
}

# 1. execute the show command
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
 
# 2. log the success of the CLI command 
set msg [format "Command \"%s\" executed successfully" $_show_cmd]
action_syslog priority info msg $msg
if {$_cerrno != 0} {
    set result [format "component=%s; subsys err=%s; posix err=%s;\n%s" \
        $_cerr_sub_num $_cerr_sub_err $_cerr_posix_err $_cerr_str]
    error $result
}

# 3. get input / output errors
set mylist [split $cmd_output " "]
set newlist [split $cmd_output " "]
set inputerror 0
set outputerror 0
set curpos [lsearch $mylist input]
while {$curpos > 0} {
    set prev [expr $curpos - 1]
    set curerror [lindex $mylist $prev]
    if {$curerror > 0} {incr inputerror}
    set newlist [lreplace $newlist $curpos $curpos junk]
    set curpos [lsearch $newlist input]
}
set curpos [lsearch $mylist output]
while {$curpos > 0} {
    set prev [expr $curpos - 1]
    set curerror [lindex $mylist $prev]
    if {$curerror > 0} {incr outputerror}
    set newlist [lreplace $newlist $curpos $curpos junk]
    set curpos [lsearch $newlist output]
}

# 4. check if there were interface errors
if {$inputerror < 1 && $outputerror < 1} {
    set result "no interface errors found"
    error $result 
}

# 5. send the email out 
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
# Specify where the e-mail should be sent:
config terminal
event manager environment _email_to <target@example.com>
#
# Specify from whom the e-mail should be sent:
event manager environment _email_from <sender@example.com>
#
# Set the environment variable of the e-mail server:
event manager environment _email_server <smtp.example.com>
#-or-
#event manager environment _email_server <password@smtp.example.com>
#
# Configure the command to be captured when the syslog pattern is seen:
event manager environment _show_cmd show interface | include errors
#
# Configure the cron entry to be used for scheduling:
event manager environment _cron_entry 0-59/2 0-23/1 * * 0-7
#

################################################################################
# Register directory and TCL script (required)
################################################################################
# TCL script must already by loaded on IOS device!
#
## Configure the file location of the script:
#event manager directory user policy <"disk0:/"|"flash:/">
event manager directory user policy "disk0:/"
#
## Specify the name of the script:
event manager policy interface_errors_email.tcl

