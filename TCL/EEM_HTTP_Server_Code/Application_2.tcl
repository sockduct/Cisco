
# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.

set appnum 2

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

#<form name='bandwidthmon' action='syslogcatch.tcl' method='GET' target='_blank'>

set middle "
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-bottom-style: solid;border-bottom-color:#999999; border-bottom-width:1px; FLOAT: left; WIDTH: 710px; HEIGHT: 130px; MARGIN: 10px 10px'>
  <p><font face='arial' size='4' color='black'>Application 2 Description: <i>SysLog Catcher</i></font>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span id='AppStatus'><font face='arial' size='4' color='red'>(Disabled)</font></span></p>
  This application allows you to specify a regular expression to match syslog messages. When there is a match, a list of CLI commands is run 
  on this router. You can specify a count and a time sliding window (e.g. three syslog messages in an hour).
</div>
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; FLOAT: left; WIDTH: 700px; HEIGHT: 380px; MARGIN: 10px 10px'>
  <div align='left'>
  Syslog Pattern (Regexp).<br>
  <input type='text' name='pattern' value='SysLog Pattern' onblur='init_field(this,\"SysLog Pattern\");' onFocus='clear_field(this,\"SysLog Pattern\");' style='WIDTH: 700px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  Syslog Message Count.<br>
  <input type='text' name='count' value='1' style='WIDTH: 50px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  Sliding Time Window (min). 0 means no window.<br>
  <input type='text' name='window' value='0' style='WIDTH: 50px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  CLI Commands to Run On Syslog Detection.<br>
  <textarea name='cli' onblur='init_field(this,\"CLI Commands\");' onFocus='clear_field(this,\"CLI Commands\");' style='WIDTH: 700px; HEIGHT: 120px; color:#000000; font-family: arial; font-size: 10pt'>CLI Commands</textarea><br><br>
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
