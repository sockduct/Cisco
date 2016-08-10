
# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.


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

while {1} {
	set end [string first "\n" $IntOutput $start]
	if {$end == -1} {break}
	incr end -1
	set line [string range $IntOutput $start $end]
	incr end 2
	set start $end
	if {[string index $line 0] != " "} {
		if {[regexp "(\[^ \]*) is (.*), (.*)" $line temp name state protocol] != 0} {
			set item "<option value='$name'>$name</option>"
			set intlist [concat $intlist $item]
		}
		incr num
	}
}

set appnum "Interface Trigger"

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
		Progress();
	}
	else
	{
		EnableButton.value = 'Enable';
		prog = 2;
		value = 'Disabl';
		Progress();
	}
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

#<form name='bandwidthmon' action='InterfaceTrigger.tcl' method='GET' target='_blank'>

set middle "
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-bottom-style: solid;border-bottom-color:#999999; border-bottom-width:1px; FLOAT: left; WIDTH: 710px; HEIGHT: 130px; MARGIN: 10px 10px'>
  <p><font face='arial' size='4' color='black'>Application 3 Description: <i>Interface Trigger</i></font>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span id='AppStatus'><font face='arial' size='4' color='red'>(Disabled)</font></span></p>
  This application allows you to select an interface, a statistical counter and a comparision operation. 
  When the comparision returns true, a lists of CLI commands is run on this router.
</div>
<div align='left' style='BACKGROUND-COLOR: white; border-right-style: solid;border-right-color:#999999; border-right-width:1px;
  WIDTH: 350px; FLOAT: left;HEIGHT: 380px; MARGIN: 10px 10px'>
  <font face='arial' size='4'>Select Interface</font><br>
  <select name='interface' style='WIDTH: 300px'>
    $intlist
  </select><br><br>
  <font face='arial' size='4'>Select Counter</font><br>
  <select name='counter' style='WIDTH: 300px'>
    <option value='transmit_rate_bps'>Interface transmit rate in bits/sec</option>
    <option value='transmit_rate_pps'>Interface transmit rate in pkts/sec</option>
    <option value='input_errors'>Number of damaged packets received</option>
    <option value='input_errors_crc'>Number of packets received with CRC errors</option>
    <option value='input_errors_frame'>Number of framing ERR packets received</option>
    <option value='input_errors_overrun'>Number of overruns and resource errors</option>
    <option value='input_packets_dropped'>Number of packets dropped from input Q</option>
    <option value='interface_resets'>Number of times an interface has been reset</option>
    <option value='output_buffer_failures'>Number of failed buffers</option>
    <option value='output_buffer_swappedout'>Number of packets swapped to DRAM</option>
    <option value='output_errors'>Number of packets errored on output</option>
    <option value='output_errors_underrun'>Number of underruns on output</option>
    <option value='output_packets_dropped'>Number of packets dropped from output Q</option>
    <option value='receive_broadcasts'>Number of broadcast packets received</option>
    <option value='receive_giants'>Number of too large packets received</option>
    <option value='receive_rate_bps'>Interface receive rate in bits/sec</option>
    <option value='receive_rate_pps'>Interface receive rate in pkts/sec</option>
    <option value='receive_runts'>Number of too small packets received</option>
    <option value='receive_throttle'>Number of times the receiver was disabled</option>
    <option value='reliability'>Interface reliability as a fraction of 255</option>
    <option value='rxload'>Receive rate as a fraction of 255</option>
    <option value='txload'>Transmit rate as a fraction of 255</option>
  </select><br><br>
  <font face='arial' size='4'>Select Operation</font><br>
  <select name='op' style='WIDTH: 300px'>
    <option value='eq'>Equal to</option>
    <option value='ge'>Greater than or equal to</option>
    <option value='gt'>Greater than</option>
    <option value='le'>Less than or equal to</option>
    <option value='lt'>Less than</option>
    <option value='ne'>Not equal to</option>
  </select><br><br>
  <font face='arial' size='4'>Value </font>&#060;1-4294967295&#062;<br>
  <input type='text' name='value' value='Value to compare to' onblur='init_field(this,\"Value to compare to\");'
    onFocus='clear_field(this,\"Value to compare to\");' style='WIDTH: 300px; MARGIN: 0px 0px'><br><br>
  <font face='arial' size='4'>Value Type</font><br>
  <select name='type' style='WIDTH: 300px'>
    <option value='value'>Value specifies an absolute number</option>
    <option value='increment'>Value specifies an increment</option>
    <option value='rate'>Value specifies the rate of change over a period</option>
  </select><br><br><br>
  <input id='EnableButton' type='submit' value='Enable' OnClick='ToggleApp()' style='WIDTH: 300px'>
</div>
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; FLOAT: left; WIDTH: 345px; HEIGHT: 380px; MARGIN: 10px 10px'>
  <div align='left'>
    <p><font face='arial' size='4' color='black'>CLI Commands to Run On Trigger.</font></p>
    <textarea name='cli' onblur='init_field(this,\"CLI Commands\");' onFocus='clear_field(this,\"CLI Commands\");' style='WIDTH: 330px;
      HEIGHT: 310px; color:#000000; font-family: arial; font-size: 10pt'>CLI Commands</textarea><br><br>
  </div>
</div>
"
#</form>

set httpheader "HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

"

puts $httpsock $httpheader$header$middle$footer
