cd "C:\Users\saraa\Desktop\config_history_stats"

ssc install outreg2
clear
import delimited using 144days_cleaned.csv
save data.dta, replace

//reg interface acl
//reg acl interface

**************************************regress pairs that change together at least once***************************************************************

//file1
reg acl interface
outreg2 using greater_than_zero1.doc, replace
reg acl port
outreg2 using greater_than_zero1.doc, append
reg acl system
outreg2 using greater_than_zero1.doc, append
reg acl vrf
outreg2 using greater_than_zero1.doc, append
reg interface acl
outreg2 using greater_than_zero1.doc, append
reg interface port
outreg2 using greater_than_zero1.doc, append
reg interface system
outreg2 using greater_than_zero1.doc, append
reg interface vlan
outreg2 using greater_than_zero1.doc, append
reg interface vrf
outreg2 using greater_than_zero1.doc, append
reg port acl
outreg2 using greater_than_zero1.doc, append

//file2

reg port interface
outreg2 using greater_than_zero2.doc, replace
reg port system
outreg2 using greater_than_zero2.doc, append
reg port vlan
outreg2 using greater_than_zero2.doc, append
reg port vrf
outreg2 using greater_than_zero2.doc, append
reg system acl
outreg2 using greater_than_zero2.doc, append
reg system interface
outreg2 using greater_than_zero2.doc, append
reg system port
outreg2 using greater_than_zero2.doc, append
reg system vlan
outreg2 using greater_than_zero2.doc, append
reg system vrf
outreg2 using greater_than_zero2.doc, append
reg vlan interface
outreg2 using greater_than_zero2.doc, append

//file3

reg vlan port
outreg2 using greater_than_zero3.doc, replace
reg vlan system
outreg2 using greater_than_zero3.doc, append
reg vlan vrf
outreg2 using greater_than_zero3.doc, append
reg vrf acl
outreg2 using greater_than_zero3.doc, append
reg vrf interface
outreg2 using greater_than_zero3.doc, append
reg vrf port
outreg2 using greater_than_zero3.doc, append
reg vrf system
outreg2 using greater_than_zero3.doc, append
reg vrf vlan
outreg2 using greater_than_zero3.doc, append


******************regress pairs that have zero values in the and_matrix*******************************************

//file1

//reg acl acl
//outreg2 using zero1.doc, append
reg acl pki_ta_profile
outreg2 using zero1.doc, replace
reg acl snmp_trap
outreg2 using zero1.doc, append
reg acl user
outreg2 using zero1.doc, append
reg acl user_group
outreg2 using zero1.doc, append
reg acl vlan
outreg2 using zero1.doc, append
//reg interface interface
//outreg2 using zero1.doc, append
reg interface pki_ta_profile
outreg2 using zero1.doc, append
reg interface snmp_trap
outreg2 using zero1.doc, append
reg interface user
outreg2 using zero1.doc, append

// file2

reg interface acl
outreg2 using zero2.doc, replace
reg pki_ta_profile pki_ta_profile
outreg2 using zero2.doc, append
reg pki_ta_profile snmp_trap
outreg2 using zero2.doc, append
reg pki_ta_profile user
outreg2 using zero2.doc, append
reg pki_ta_profile user_group
outreg2 using zero2.doc, append
reg pki_ta_profile vlan
outreg2 using zero2.doc, append
reg pki_ta_profile interface
outreg2 using zero2.doc, append
reg pki_ta_profile pki_ta_profile
outreg2 using zero2.doc, append
reg pki_ta_profile snmp_trap
outreg2 using zero2.doc, append
reg port user
outreg2 using zero2.doc, append

// file3

reg port acl
outreg2 using zero3.doc, replace
reg port pki_ta_profile
outreg2 using zero3.doc, append
reg port snmp_trap
outreg2 using zero3.doc, append
reg snmp_trap user
outreg2 using zero3.doc, append
reg snmp_trap user_group
outreg2 using zero3.doc, append
reg snmp_trap vlan
outreg2 using zero3.doc, append
reg snmp_trap interface
outreg2 using zero3.doc, append
reg snmp_trap pki_ta_profile
outreg2 using zero3.doc, append
//reg snmp_trap snmp_trap
//outreg2 using zero3.doc, append
reg system user
outreg2 using zero3.doc, append

//file4

reg system acl
outreg2 using zero4.doc, replace
reg system pki_ta_profile
outreg2 using zero4.doc, append
reg user snmp_trap
outreg2 using zero4.doc, append
//reg user user
//outreg2 using zero4.doc, append
reg user user_group
outreg2 using zero4.doc, append
reg user vlan
outreg2 using zero4.doc, append
reg user_group interface
outreg2 using zero4.doc, append
reg user_group pki_ta_profile
outreg2 using zero4.doc, append
reg user_group snmp_trap
outreg2 using zero4.doc, append
reg vlan user
outreg2 using zero4.doc, append
reg vrf acl
outreg2 using zero4.doc, append


