
# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.


# Run CLI commands
if {[catch {cli_open} output]} {
    error $output $errorInfo
} else {
    array set cli_fd $output
}
if {[catch {cli_exec $cli_fd(fd) "enable"} output]} {
error $output $errorInfo
}
if {[catch {cli_exec $cli_fd(fd) "sh ver"} shver_output]} {
error $output $errorInfo
}
if {[catch {cli_exec $cli_fd(fd) " "} blank_output]} {
error $output $errorInfo
}
if {[catch {cli_exec $cli_fd(fd) "sh event man ver"} eemver_output]} {
error $output $errorInfo
}
if {[catch {cli_close $cli_fd(fd) $cli_fd(tty_id)} output]} {
    error $output $errorInfo
}

if {[regexp "(\[0-9a-zA-Z\]*)#" $blank_output temp Hostname] == 0} {
	set Hostname "?"
}

if {[regexp "Version (\[0-9a-zA-Z\\(\\)\\:\\.\]*)" $shver_output temp IOSVersion] == 0} {
	set IOSVersion "?"
}

if {[regexp "Cisco IOS Software, (\[0-9a-zA-Z\]*) Software \\((\[0-9a-zA-Z\\-\]*)\\)" $shver_output temp Platform Imagetype] == 0} {
	set Platform "?"
	set Imagetype "?"
	set CryptoImage "?"
} else {
	set Imagetype [string tolower $Imagetype]
	if {[string first "k9" $Imagetype] == -1} {
		set CryptoImage "No"
	} else {
		set CryptoImage "Yes"
	}
}

if {[regexp "uptime is (\[0-9a-zA-Z, \]*)" $shver_output temp Uptime] == 0} {
	set Uptime "?"
}

if {[regexp "Embedded Event Manager Version (\[0-9\\.\]*)" $eemver_output temp EEMVersion] == 0} {
	set EEMVersion "2.2"
}

if {[regexp "Cisco (\[0-9a-zA-Z\\(\\)\\:\\-\\. \]*) processor .* with (.*) bytes of memory" $shver_output temp Processor Memory] == 0} {
	set Processor "?"
	set Memory "?"
}

if {[regexp "(\[0-9\]*K) bytes of NVRAM." $shver_output temp NVRAM] == 0} {
	set NVRAM "?"
}

if {[regexp "Configuration register is (0x\[0-9a-fAF\]*)" $shver_output temp ConfigReg] == 0} {
	set ConfigReg "?"
}

if {[regexp "( \[0-9\]*MHz)" $shver_output temp Speed] == 0} {
	set Speed "?"
}


set header "<html>
<head>
<title>Mihyar's page on gummyjoe</title>
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


set middle "
<div align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-right-style: solid;border-right-color:#999999; border-right-width:1px; WIDTH: 250px; FLOAT: left;HEIGHT: 528px; MARGIN: 10px 10px'>
  <font face='arial' size='4'>Router Information</font><br>
  <ul>
    <li><b>Hostname</b><br>$Hostname</li>
    <li><b>Platform</b><br>$Platform</li>
    <li><b>IOS Version</b><br>$IOSVersion</li>
    <li><b>EEM Version</b><br>$EEMVersion</li>
    <li><b>Uptime</b><br>$Uptime</li>
    <li><b>Image type</b><br>$Imagetype</li>
    <li><b>Crypto Image</b><br>$CryptoImage</li>
    <li><b>Processor</b><br>$Processor</li>
    <li><b>Processor Speed</b><br>$Speed</li>
    <li><b>Memory</b><br>$Memory</li>
    <li><b>NVRAM</b><br>$NVRAM</li>
    <li><b>Config Reg.</b><br>$ConfigReg</li>
    </ul>
</div>
<div  align='left' style='overflow: hidden;BACKGROUND-COLOR: white; border-bottom-style: solid;border-bottom-color:#999999; border-bottom-width:1px; FLOAT: left; WIDTH: 445px; HEIGHT: 130px; MARGIN: 10px 10px'>
  <p><font face='arial' size='4' color='black'>Run CLI command</font></p>
  <form name='runcli' action='runcli.tcl' method='GET' target='_blank'>
  <div align='left'>
  <input type='text' name='CLIcommand' value='CLI Command' onblur='init_field(this,\"CLI Command\");' onFocus='clear_field(this,\"CLI Command\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'>
  <br><br>
  <input type='submit' value='RUN'>
  </div>
  </form>
</div>
<div style='overflow: hidden;BACKGROUND-COLOR: white; FLOAT: left; WIDTH: 445px; HEIGHT: 380px; MARGIN: 10px 10px'>
  <p><font face='arial' size='4' color='black'>Send Email From gummyjoe</font></p>
  <form name='sendemail' action='sendemail.tcl' method='GET' target='_blank'>
  <div>
  <input type='text' name='to' value='To: email address' onblur='init_field(this,\"To: email address\");' onFocus='clear_field(this,\"To: email address\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  <input type='text' name='cc' value='Cc: email address' onblur='init_field(this,\"Cc: email address\");' onFocus='clear_field(this,\"Cc: email address\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  <input type='text' name='subject' value='Subject' onblur='init_field(this,\"Subject\");' onFocus='clear_field(this,\"Subject\");' style='WIDTH: 440px; color:#000000; font-family: arial; font-size: 10pt'><br><br>
  <textarea name='body' onblur='init_field(this,\"Body\");' onFocus='clear_field(this,\"Body\");' style='WIDTH: 440px; HEIGHT: 140px; color:#000000; font-family: arial; font-size: 10pt'>Body</textarea><br><br>
  <input type='submit' value='Send'>
  </div>
  </form>
</div>"

set httpheader "HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

"

puts $httpsock $httpheader$header$middle$footer
