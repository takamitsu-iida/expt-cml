# SRv6 uSID

## SID構造

```text
1111:2222:3333:4444 : 5555:6666:7777:8888
------------------    -------------------
locator               function

1111 : 2222 : 3333 : 4444 : 5555 : 6666 : 7777 : 8888
-----------   ----   ----   ----
Block         NodeID Func   Argument
```


## F3216

F3216は、IPv6のプレフィクス長が32ビット、SIDが16ビット、合計で48ビットです。
ロケータの定義は /48 になります。

先頭の32ビットはSRv6を形成するドメイン内で共通の値です。ローカルな環境であればfc00もしくはfd00が使われることが多いです。

SIDの16ビット部分は、特定のルータやそのルータ内で定義されるサービスを識別する役割を担います。






## FRR

```text
!
segment-routing
  srv6
    locators
      locator MAIN
        prefix fd00:aaaa:1::/48
        format usid-f3216
    !
!
```


## ISIS

```text
!
router isis 1
  net 00.0000.0000.0001.00
  is-type level-1
  segment-routing srv6
    locator MAIN
```


## Traffic Steering into SRv6

```text
ipv6 route 2001:db8:1:2::/64 eth0 segments fd00:aaaa:2:3:fe00::
ip route 192.168.2.0/24 eth0 segments fd00:aaaa:2:3:fe00::
```


## Static

- uN (Shift and forward)
- uA (Shift and L3 cross-connect)
- uDT4 (Decapsulation and IPv4 table lookup)
- uDT6 (Decapsulation and IPv6 table lookup)
- uDT46 (Decapsulation and IP table lookup)

```text
!
segment-routing
    static-sids
      sid fd00:aaaa:1::/48 locator MAIN behavior uN
      sid fd00:aaaa:1:ff10::/64 locator MAIN behavior uDT4 vrf Vrf10
      sid fd00:aaaa:1:ff20::/64 locator MAIN behavior uDT6 vrf Vrf20
      sid fd00:aaaa:1:ff30::/64 locator MAIN behavior uDT46 vrf Vrf30
      sid fd00:aaaa:1:ff40::/64 locator MAIN behavior uA interface eth1
```


## BGP L3VPN

```text
router bgp 65001
  bgp router-id 192.168.255.1
  no bgp ebgp-requires-policy
  neighbor 2001:db8:ffff::2 remote-as 65001
  neighbor 2001:db8:ffff::2 capability extended-nexthop
  ...
  address-family ipv4 vpn
    neighbor 2001:db8:ffff::2 activate
    exit-address-family
  !
  address-family ipv6 vpn
    neighbor 2001:db8:ffff::2 activate
    exit-address-family
  !
!
router bgp 65001 vrf vrff10
  bgp router-id 192.168.255.1
  no bgp ebgp-requires-policy
  sid vpn per-vrf export auto
  !
  address-family ipv4 unicast
    nexthop vpn export 2001:db8:ffff::1
    rd vpn-export 2:10
    rt vpn-both 99:99
    import vpn
    export vpn
    redistribution connected
  exit-address-family
  !
  address-family ipv6 unicast
   ...


```