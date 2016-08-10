
# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.


set header "<html>
<head>
<title>Mihyar's page on gummyjoe: Send Email</title>
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

#set middle "<div id='middle' align='left' style='overflow: hidden; MARGIN: 20px 20px'>
#  <font face=\"arial\" size=\"4\" color=\"black\">Sending Email...</font>
#</div>"

#puts $httpsock "$header$middle$footer"
#flush $httpsock

set to [lindex $parmlist 1]
set cc [lindex $parmlist 3]
set subject [lindex $parmlist 5]
set body [lindex $parmlist 7]

set email_message "Mailservername: email.cisco.com
From: gummyjoe@cisco.com
To: $to
Cc: $cc
Subject: $subject

$body"

if {[catch {smtp_send_email $email_message} result]} {
	set result "Email send failed"
} else {
	set result "Email Sent"
}

#event_publish sub_system 798 type 1 arg1 "$to" arg2 "$cc" arg3 "$subject" arg4 "$body"

#for {set x 0} {$x<10} {incr x} {
#	if {[catch {set emailresultvar [context_retrieve emailresult emailresultvar]} errmsg]} {
#		after 1000
#	} elseif {$emailresultvar == "FH_EOK"} {
#		set result "Email Sent"
#		break
#	}
#}

set middle "<div id='middle' align='left' style='overflow: hidden; MARGIN: 20px 20px'>
  <font face=\"arial\" size=\"4\" color=\"black\">$result</font>
</div>"

set httpheader "HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

"

puts $httpsock $httpheader$header$middle$footer

#puts $httpsock "<script language='JavaScript'>
#	var div = document.getElementById(\"middle\");
#	div.innerHTML = \"<font face='arial' size='4' color='black'>$result</font>\"
#</script>"


