## VDC-Store - caching storage infrastructure

This module provides an interface to VDC-Store which is an alternative storage infrastructure for OpenNebula. It provides a shared platform with support for local SSD caching, replication, live migration, snapshots and compression.

## Development

To contribute bug patches or new features, you can use the github Pull Request model. It is assumed that code and documentation are contributed under the Apache License 2.0. 

More info:
* [How to Contribute](http://opennebula.org/addons/contribute/)
* Support: [OpenNebula user mailing list](http://opennebula.org/community/mailinglists)
* Development: [OpenNebula developers mailing list](http://opennebula.org/community/mailinglists)
* Issues Tracking: [Github issues](https://github.com/OpenNebula/addon-storage-vdc/issues)

## Authors

* Leader: Gareth Bult (gareth[at]linux.co.uk)

## Compatibility

This add-on is compatible with OpenNebula 4.4

## Client features

* Local SSD caching (LFU)
* RAID10 replication against multiple servers
* Automatic failover and recvovery
* Presents as a standard Linux block device
* Suport for TRIM
* Bandwidth management for multi-tennant load balancing
* Support for Live Migration
* Support for inline Snapshots
* Cache analysis / size advisor

## Server features

* Backend support for replication
* Backend support for live migration
* Backend support for snapshots
* Backend support for TRIM and sparse storage
* Inline / transparent compression
* LSFS style storage with sequential only writes

## Limitations

* Imagination.

## Requirements

* Server hosts need to be running a kernel that supports FALLOCATE
* KVM needs to be relatively recent (3.2+)

## Installation

http://www.vdc-store.com/item/vdc-nebula/?theme=opennebula

## Configuration

http://www.vdc-store.com/item/setting-up-opennebula-sunstone/?theme=opennebula

## Usage 

http://www.vdc-store.com/items/opennebula/

## References

* Detailed documentation can be found at http://vdc-store.com

## License

Apache v2.0 license.

