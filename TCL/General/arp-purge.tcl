####################################################################################################
# TCL Script to parse ARP entries and purge dynamic ones by adding/removing from config mode

# Get output of show arp command
set arpstr [exec show arp]

# Remove whitespace
set arpstr [string trim $arpstr]

# Put output into a list
set arplst [split $arpstr "\n"]

# Get number of entries in list
set lstlen [llength $arplst]

# Want IP Address, MAC Address, ARPA
# show arp output:
# Protocol=Internet, Address=IPv4, Age=-|#, Hardware_Addr=MAC, Type=ARPA, Interface=<interface>
# Examples:
# Internet  172.16.1.1              -   ca01.2fe8.001c  ARPA   FastEthernet1/0
# Internet  172.16.1.2             58   ca02.2e1c.001c  ARPA   FastEthernet1/0
#
# Iterate through list of arp entries
# Starting from 1 to skip header/title row of command output
for {set i 1} {$i < $lstlen} {incr i} {
    # Work with each arp entry
    set line [lindex $arplst $i]
    # Save line entry in case there are parsing problems
    set saveline $line
    # Find space after "Internet"
    set argoff [string first " " $line]
    # Remove initial "Internet" from $line
    set line [string range $line $argoff end]
    # Strip whitespace from beginning of $line
    set line [string trimleft $line]
    # Find space after "IP Address"
    set argoff [string first " " $line]
    # Extract IP Address
    set ipaddr [string range $line 0 [expr $argoff - 1]]
    # Remove IP Address and left whitespace
    set line [string trimleft [string range $line $argoff end]]
    set argoff [string first " " $line]
    # Extract ARP Age
    set arpage [string range $line 0 [expr $argoff - 1]]
    ### Only want dynamic ARP entries where arpage != "-"
    # Remove age time and left whitespace
    set line [string trimleft [string range $line $argoff end]]
    set argoff [string first " " $line]
    # Extract MAC Address
    set macaddr [string range $line 0 [expr $argoff - 1]]
    # Remove MAC Address and left whitespace
    set line [string trimleft [string range $line $argoff end]]
    set argoff [string first " " $line]
    # Extract ARP Type
    set arptype [string tolower [string range $line 0 [expr $argoff - 1]]]
    ### Should validate that ARP Type == arpa
    # Remove ARP Type and left whitespace
    set line [string trimleft [string range $line $argoff end]]
    # Extract Interface
    set intf [string trimright $line]

    # Parsing status
    set parse_str [format "Parsed:  IP Address %s, MAC Address %s, " $ipaddr $macaddr]
    append parse_str [format "ARP Age %s, ARP Type %s on Interface: %s" $arpage $arptype $intf]
    puts $parse_str

    # Check if dynamic ARP entry
    if {$arpage != "-" && $arptype == "arpa"} {
        puts "Found dynamic ARP entry - purging..."
        ios_config [format "arp %s %s %s" $ipaddr $macaddr $arptype] "end"
        ios_config [format "no arp %s %s %s" $ipaddr $macaddr $arptype] "end"
    } elseif {$arpage == "-"} {
        puts [format "Skipping:  IP Address %s, MAC Address %s belongs to Interface %s" \
            $ipaddr $macaddr $intf]
    } elseif {$arptype != "arpa"} {
        puts [format "Skipping:  IP Address %s, MAC Address %s is not type \"%s\"" \
            $ipaddr $macaddr "ARPA"]
    } else {
        puts "Unexpected use case - original line/entry:\n$saveline"
    }
}

