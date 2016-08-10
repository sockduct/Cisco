
# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.

set appnum 1

if {[catch {cli_open} output]} {
    error $output $errorInfo
} else {
    array set cli_fd $output
}
if {[catch {cli_exec $cli_fd(fd) "enable"} output]} {
error $output $errorInfo
}
if {[catch {cli_exec $cli_fd(fd) "show int"} IntOutput]} {
error $output $errorInfo
}
if {[catch {cli_close $cli_fd(fd) $cli_fd(tty_id)} output]} {
    error $output $errorInfo
}

set start 0
set end 0
set intlist ""
set num 1
set FirstTime 1

while {1} {
	set end [string first "\n" $IntOutput $start]
	if {$end == -1} {break}
	incr end -1
	set line [string range $IntOutput $start $end]
	incr end 2
	set start $end
	if {[string index $line 0] != " "} {
		if {[regexp "(\[^ \]*) is (.*), (.*)" $line temp name state protocol] != 0} {
			if {$FirstTime == 1} {
				set FirstTime 0
				set item "<li><input type='radio' name='interfacename' value='$name' checked><b>$name</b><br>Interface is $state<br>$protocol</li>"
			} else {
				set item "<li><input type='radio' name='interfacename' value='$name'><b>$name</b><br>Interface is $state<br>$protocol</li>"
			}
			set intlist [concat $intlist $item]
		}
		incr num
	}
}

set header "<html>
<head>
<title>Mihyar's page on gummyjoe: Application $appnum</title>
<style type='text/css'>
<!--
.header A:link {color: #FFFFFF; text-decoration: none}
.header A:visited {color: #FFFFFF; text-decoration: none}
.header A:active {color: #FFFFFF; text-decoration: none}
.header A:hover {color: #D0DDDD; text-decoration: none}
-->
</style>
<script>
// clear default value from field when selected
function clear_field(field, value) {if(field.value == value) field.value = '';}
function init_field(field, value) {if(field.value == '') field.value = value;}
var prog
var value
function Progress() {
	if (prog < 6) {
		var ProgMon = value + 'ing';
		for (i = 0; i <= prog; i++)
		{
			ProgMon += '.';
		}
		document.getElementById('AppStatus').innerHTML = '<font face=\"arial\" size=\"4\" color=\"red\">' + ProgMon + '</font>';
		prog++;
		setTimeout('Progress()',1000);
	}
	else
	{
		document.getElementById('AppStatus').innerHTML = '<font face=\"arial\" size=\"4\" color=\"red\">(' + value + 'ed)</font>';
	}
}
function ToggleApp()
{
	var EnableButton = document.getElementById('EnableButton');
	if (EnableButton.value == 'Enable')
	{
		EnableButton.value = 'Disable';
		prog = 2;
		value = 'Enabl';
	}
	else
	{
		EnableButton.value = 'Enable';
		prog = 2;
		value = 'Disabl';
	}
	Progress();
}
</script>
</head>
<body>
<div align='center' style='color:#555555; font-family: arial; font-size: 24pt;overflow: hidden;BACKGROUND-COLOR: white; 
    VERTICAL-ALIGN: middle; line-height: 75px; border-style: solid;border-color:#999999; border-width:1px; WIDTH: 750px; HEIGHT: 75px;
    MARGIN: 10px 10px'>
  <img border='0' style='FLOAT: left' src='logo.gif'>
  Mihyar's page on gummyjoe router
</div>
<div align='center' class='header' style='color:#FFFFFF; font-family: arial; font-size: 12pt;overflow: hidden;
  BACKGROUND-IMAGE: url(sitearea-nav.jpg); BACKGROUND-POSITION: 0% 60%; VERTICAL-ALIGN: middle; border-style: 
  solid;border-color: white; border-width:1px; WIDTH: 750px; HEIGHT: 24px; line-height: 22px; MARGIN: 10px 10px'>
  <a href='Mihyar.tcl'>Home</a>
  &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; 
  <a href='Application_1.tcl'>Bandwidth Monitor</a>
  &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
  <a href='Application_2.tcl'>SysLog Catcher</a>
  &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
  <a href='Application_3.tcl'>Interface Trigger</a>
  &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
  <a href='Application_4.tcl'>Network Balancer</a>
</div>
<div align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-style: solid;border-color:#999999; border-width:1px; WIDTH: 750px;  HEIGHT: 550px; MARGIN: 10px 10px'>"

set footer "</div>
<div align='right' style='overflow: hidden;BACKGROUND-IMAGE: url(sitearea-nav.jpg);
  BACKGROUND-POSITION: 0% 60%; color:#FFFFFF; font-family: arial; font-size: 7pt; VERTICAL-ALIGN: middle; border-style: solid;
  border-color: white; border-width:1px; WIDTH: 750px; HEIGHT: 24px; line-height: 22px; MARGIN-LEFT: 10px'>
  <B>Cisco Systems, Inc. Cisco Confidential&nbsp;&nbsp;&nbsp;&nbsp;</B>
</div>
</body>
</html>"

#<form id='bandwidthmon' name='bandwidthmon' action='bandwidthmon.tcl' method='GET' target='_blank'>

set middle "
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-bottom-style: solid;border-bottom-color:#999999; border-bottom-width:1px; FLOAT: left; WIDTH: 710px; HEIGHT: 130px; MARGIN: 10px 10px'>
  <p><font face='arial' size='4' color='black'>Application 1 Description: <i>Bandwidth Monitor</i></font>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span id='AppStatus'><font face='arial' size='4' color='red'>(Disabled)</font></span></p>
  This application allows you to select an interface for bandwidth monitoring. You can specify two thresholds in pps.
  When the up-threshold is crossed going up or the down-threshold is crossed going down, lists of CLI commands are run on this router.
</div>
<div align='left' style='overflow: scroll;BACKGROUND-COLOR: white; border-right-style: solid;border-right-color:#999999; border-right-width:1px; WIDTH: 250px; FLOAT: left;HEIGHT: 380px; MARGIN: 10px 10px'>
  <font face='arial' size='4'>Select Interface</font><br>
  <ol>$intlist</ol>
</div>
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; FLOAT: left; WIDTH: 445px; HEIGHT: 380px; MARGIN: 10px 10px'>
  <div align='left'>
  <input type='radio' name='updown' value='updown' checked>Up & Down&nbsp;&nbsp;&nbsp;&nbsp;
  <input type='radio' name='updown' value='up'> Up Only&nbsp;&nbsp;&nbsp;&nbsp;
  <input type='radio' name='updown' value='down'>Down Only<br><br>
  <input type='text' name='up' value='Up Threshold (pps)' onblur='init_field(this,\"Up Threshold (pps)\");' onFocus='clear_field(this,\"Up Threshold (pps)\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  <textarea name='upcli' onblur='init_field(this,\"Up Threshold CLI Commands\");' onFocus='clear_field(this,\"Up Threshold CLI Commands\");' style='WIDTH: 440px; HEIGHT: 90px; color:#000000; font-family: arial; font-size: 10pt'>Up Threshold CLI Commands</textarea><br><br>
  <input type='text' name='down' value='Down Threshold (pps)' onblur='init_field(this,\"Down Threshold (pps)\");' onFocus='clear_field(this,\"Down Threshold (pps)\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  <textarea name='downcli' onblur='init_field(this,\"Down Threshold CLI Commands\");' onFocus='clear_field(this,\"Down Threshold CLI Commands\");' style='WIDTH: 440px; HEIGHT: 90px; color:#000000; font-family: arial; font-size: 10pt'>Down Threshold CLI Commands</textarea><br><br>
  <input id='EnableButton' type='submit' value='Enable' OnClick='ToggleApp()' style='WIDTH: 300px'>
  </div>
</div>
"

#</form>

set httpheader "HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

"

puts $httpsock $httpheader$header$middle$footer
