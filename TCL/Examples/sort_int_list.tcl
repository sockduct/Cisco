# Sort the output of show ip interface brief
set a [split [exec "show ip int brief"] "\n"]
set b [lsort $a]
set c [llength $b]
set d 0
while {$d < $c} {
    puts [lindex $b $d]
    incr d
}

