# Use cases

## ACLs to prevent source spoofing

### Description
An ACL is defined to only permit packets whose source IP address falls within a specific subnet. The ACL is applied as an inbound ACL to the interface whose adress matches the subnet specified in the ACL. An separate ACL is defined for each interface.

### Synthetic example
```
interface GigabitEthernet0/1
    ip address 10.0.1.1 255.255.255.0
    ip access-group nospoof1 in
!
interface GigabitEthernet0/2
    ip address 10.0.2.1 255.255.255.0
    ip access-group nospoof2 in
!
ip access-list standard nospoof1
    permit 10.0.1.0 0.0.0.255
    deny any
!
ip access-list standard nospoof2
    permit 10.0.2.0 0.0.0.255
    deny any
```

### Real-world example
* Northwestern

### Detection
* Detectable by Minerals? — No 🔴 — Minerals requires a minimum number of instances of a rule, and there is only one instance of each rule
* Detectable by SelfStarter? — No 🔴 — SelfStarter can infer the template for `nospoof*` ACLs, but does not consider which interfaces an ACL is applied to
* Detectable by config-mining? — Hopefully 🤞

## ACLs applied to management interfaces

### Description
An ACL is defined to only permit traffic from certain sources to be sent on management interfaces. The ACL is applied as an outbound ACL to any interface whose purpose is providing support for managing network devices.

### Synthetic example
```
interface GigabitEthernet0/1
    description DeptA users
    ip address 10.0.1.1 255.255.255.0
!
interface GigabitEthernet0/2
    description DeptB users
    ip address 10.0.2.1 255.255.255.0
!
interface GigabitEthernet0/3
    description BldgX management
    ip address 10.0.100.1 255.255.255.248
    ip access-group management out
!
interfaace GigabitEthernet0/4
    description Network admin servers
    ip address 10.0.101.1 255.255.255.248
!
ip access-list standard management
    permit 10.0.10.1 0.0.0.7
    deny any
```

### Real-world example
* UW-Madison

### Detection
* Detectable by Minerals? — No 🔴 — Minerals does not consider IP ranges or descriptions as attributes which could influence which ACLs are applied
* Detectable by SelfStarter? — No 🔴 — SelfStarter does not consider which interfaces an ACL is applied to
* Detectable by config-mining? — Hopefully 🤞

## Common set of VLANs allowed on trunk interfaces

### Description
All trunk interfaces allow certain VLANs. 

### Synthetic example
```
interface GigabitEthernet0/1
    description trunk
    switchport
    switchport trunk allowed vlan 1-10
!
interface GigabitEthernet0/2
    description non-trunk
    switchport
    switchport trunk allowed vlan 6-10
```

### Real-world example
* UWMadison?

### Detection
* Detectable by Minerals? — Partially 🟡 — Minerals could compute association rules between VLANs to determine that, e.g., if VLAN 1 is allowed, then VLAN 2 is allowed; Minerals could not detect if an interface was a trunk interface and hence should have a VLAN applied, unless there is some other attribute that identifies a trunk interface
* Detectable by SelfStarter? — No 🔴 — SelfStarter does not consider VLANs
* Detectable by config-mining? — Hopefully 🤞

## Prefix-list applied to incoming external BGP sessions
 
## Description
_(Copied from Minerals paper)_

"A local network policy requires a prefix-list to be applied on all incoming external BGP sessions. THe prefix-list turns out to be a sanity check that discards route announcements to private IP address[es]. [A] few BGP sessions in this netowrk violate this policy. One version of a correct route map consists of the following:
```
route map from_abc permit 50
match ip address prefix-list sanity
match community ...
set local-preference 90
set comm-list ... delte
set community ... additive
```
One version of the violations is as follows:
```
route map from_bdc permit 50
set local-preference 100
set comm-list ... delete
set community ... additive
```
Although the two route maps above are different in several places—different local preference values, match community statement in the first but not the second—Minerals is able to detect similarities in parts of the route maps and points out the missing prefix-list statement."

### Detection
* Detectable by Minerals? — Yes 🟢 
* Detectable by SelfStarter? — Yes 🟢
* Detectable by config-mining? — Hopefully 🤞

## Unused interfaces

### Description
_(Copied from Minerals paper)_

"In one network, 95% of the interfaces had public IP addresses, and Minerals higlighted interfaces using private IP addresses as violations. According to the operator, private IP addresses are used to bootstrap routers at the beginning of deployment and should be deleted afterwards."

### Detection
* Detectable by Minerals? — Yes 🟢 
* Detectable by SelfStarter? — No 🔴 — SelfStarter does not consider interfaces
* Detectable by config-mining? — Hopefully 🤞

## Outbound and inbound ACLs required

### Description
If an outbound ACL is applied to an interface, then a (complementary) inbound ACL must also be applied to the interface.

### Synthetic example
```
interface GigabitEthernet0/1
    ip access-group filterOut out
    ip access-group filterIn in
!
interface GigabitEthernet0/1
    ip access-group filterOut out
!
ip access-list standard filterOut
    permit 10.0.0.0 0.0.255.255
    deny any
!
ip access-list standard filterIn
    permit 10.0.0.0 0.0.255.255
    deny any
```


### Detection
* Detectable by Minerals? — Yes 🟢 — similar to the "Omitted export policies to external neighbors" error identified in Section V.A of the Minerals paper
* Detectable by SelfStarter? — No 🔴 — SelfStarter does not consider interfaces
* Detectable by config-mining? — Hopefully 🤞