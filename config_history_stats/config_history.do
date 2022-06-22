cd "C:\Users\saraa\Desktop\config_history_stats"

ssc install outreg2
clear
import delimited using 144days_cleaned.csv
save data.dta, replace


// regress pairs that change together at least once
reg acl interface
outreg2 using greater_than_zero.doc, append
reg acl port
outreg2 using greater_than_zero.doc, append
reg acl system
outreg2 using greater_than_zero.doc, append
reg acl vrf

outreg2 using greater_than_zero.doc, append
reg interface port
outreg2 using greater_than_zero.doc, append
reg interface system
outreg2 using greater_than_zero.doc, append
reg interface vlan
outreg2 using greater_than_zero.doc, append
reg interface vrf

outreg2 using greater_than_zero.doc, append
reg port system
outreg2 using greater_than_zero.doc, append
reg port vlan
outreg2 using greater_than_zero.doc, append
reg port vrf

outreg2 using greater_than_zero.doc, append
reg system vlan
outreg2 using greater_than_zero.doc, append
reg system vrf
outreg2 using greater_than_zero.doc, append
reg vlan vrf
outreg2 using greater_than_zero.doc, append

