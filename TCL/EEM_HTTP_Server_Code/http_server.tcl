::cisco::eem::event_register_none maxrun 4294967295.000

# Created on Monday, April 7, 2008 using IDEEM(TM) Software--Nidus Software Corp.

namespace import ::cisco::eem::*
namespace import ::cisco::lib::*

set svcPort 80
global events
set events 0
global parameters
global httpsock
set httpsock ""

# Handles the input from the client and  client shutdown
proc  svcHandler {sock} {
  global events
  global httpsock
  set httpsock $sock
  fconfigure $sock -encoding binary -translation binary
  set events 1
}

# Accept-Connection handler for Server. 
# called When client makes a connection to the server
# Its passed the channel we're to communicate with the client on, 
# The address of the client and the port we're using
#
# Setup a handler for (incoming) communication on 
# the client channel - send connection Reply and log connection
proc accept {sock addr port} {
  # Setup handler for future communication on client socket
  fileevent $sock readable [list svcHandler $sock]

  # Read  # Readinput in lines, disable blocking I/O
  fconfigure $sock -buffering line -blocking 0 -encoding binary

  # log the connection
#  puts "Accepted connection from $addr:$port"
}


# Create a server socket on port $svcPort. 
# Call proc accept when a client attempts a connection.
set srvrsock [socket -server accept $svcPort]
while {1} {
  vwait events
  set events 0
  global parameters
  catch {set l [gets $httpsock]}    ;# get the client packet
  if {$l != ""} {
    if {$l == "exit" || $l == "close" || $l == "GET /exit HTTP/1.1"} {
      catch {puts $httpsock "EEM HTTP server exited"}
      catch {close $httpsock}
      break
    } elseif {[regexp "GET /(.*) HTTP/1.1" $l temp request] != 0} {
    	puts "$l"
    	if {[regexp "(.*)\\?(.*)" $request temp filename param] == 0} {
    		set param ""
    		set filename $request
    	}
    	set ::parameters $param
    	puts "file name:  $filename"
    	puts "Parameters: $::parameters"
    	if {$filename == ""} {set filename "index.html"}
    	set ext ""
	set data ""

	catch {open [file join disk0: $filename] r} output
	if {[string first "couldn't open" $output] != -1} {
		puts $output
          catch {puts $httpsock "HTTP/1.1 404 Not Found
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

<html><head>
<title>File Not Found On Router gummyjoe</title>
</head>
<body>
<font face=\"arial\" size=\"4\" color=\"red\">404 File $filename Not Found On Router gummyjoe.<br></font>
</body>
</html>"}
		catch {close $httpsock}
	} else {
	    # File was opened successfully
	    set filehandle $output
	    fconfigure $filehandle -encoding binary -translation binary
		while {1} {
			if {[catch {read $filehandle 1000} fileinput]} {
				puts "\nFile read failed: fd = $filehandle"
				catch {puts $httpsock "HTTP/1.1 500 Internal Server Error
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

<html><head>
<title>Error reading file On router gummyjoe</title>
</head>
<body>
<font face=\"arial\" size=\"4\" color=\"red\">Error reading file $filename On Router gummyjoe.<br></font>
</body>
</html>"}
				break
			} else {
				if {$fileinput == ""} {break}
				append data $fileinput
			}
		}
		close $filehandle
	}

      if {$data != ""} {
	    	if {[regexp "(.*)\\.(.*)" $filename temp name ext] == 1 && $ext == "tcl"} {
    			# The file is a tcl script.
    			# Run it passing the parameters
    			# Reply to client with output
    			set parmlist [list]
    			append parameters &
    			set start 0
    			while {1} {
    				set end [string first & $parameters $start]
    				if {$end == -1} {break}
    				set endname [string first = $parameters $start]
    				if {$endname == -1} {break}
    				incr endname -1
    				set paramname [string range $parameters $start $endname]
    				incr endname 2
    				if {$endname == $end} {
    					set paramval ""
    				} else {
    					incr end -1
    						set paramval [string range $parameters $endname $end]
    				}
    				incr end 2
    				set start $end
    				set paramval [string map {+ " "} $paramval]
    				# Remove special chars
    				while {1} {
    					if {[regexp "%(\[0-9a-fA-F\]\[0-9a-fA-F\])" $paramval temp Specialchar] != 0} {
    						set newchar [format "%c" "0x$Specialchar"]
    						set index [string first $temp $paramval]
    						set start1 $index
    						incr index 2
    						set paramval [string replace $paramval $start1 $index $newchar]
					} else {
						break
					}
    				}
    				lappend parmlist $paramname $paramval
    			}
		      if {[catch {eval $data} output]} {
      			catch {puts $httpsock "HTTP/1.1 500 Internal Server Error
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

Error in script:\n\n"}
      			catch {puts $httpsock $output}
		      }
#			[eval $data]
         	} else {
         		set filelen [string bytelength $data]
         		switch $ext {
				ico  {set ContentType "image/vnd.microsoft.icon"}
				png  {set ContentType "image/png"}
				jpeg {set ContentType "image/jpg"}
				jpg  {set ContentType "image/jpg"}
				gif  {set ContentType "image/gif"}
				html {set ContentType "text/html; charset=UTF-8"}
				htm  {set ContentType "text/html; charset=UTF-8"}
				default {set ContentType "application/octet-stream"}
    			}
		      catch {puts $httpsock "HTTP/1.1 200 OK
Content-Type: $ContentType
Content-Transfer-Encoding: binary
Content-Length: $filelen

$data"}
			}
	}
    } else {
      catch {puts $httpsock "HTTP/1.1 404 Not Found
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: binary

<html><head>
<title>File Not Found On Router gummyjoe</title>
</head>
<body>
<font face=\"arial\" size=\"4\" color=\"red\">404 File Not Found On Router gummyjoe.<br></font>
</body>
</html>"}
    }
    catch {close $httpsock}
  }
}
close $srvrsock
puts "EEM HTTP server exited"
