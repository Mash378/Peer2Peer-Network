# Peer2Peer-Network
A software for sharing files using the peer to peer network architecture.

#For local testing use small and large project file config given. 
#Change PeerInfo.cfg to local ports and localhost 
(ie: 1001 localhost 6001 1
    1002 localhost 6002 0
    1003 localhost 6003 0
    1004 localhost 6004 0
    1005 localhost 6005 0
    1006 localhost 6006 0)

Change file names for peers to peer_[PeerId] so the files are labeled 1001, 1002, etc so change them to peer_1001.
#Running:
In separate terminals run python peerProcess.py [peerId]
(ie: python peerProcess.py 1001)
The peers should connect and share the file and terminate when they are complete, if you look in the peer directories once finished they should all have the files. 

#May need a virtual environment for the bitarray library

# Group Members
Joshua Kitaigorod    --->       peerProcess.py, config parsing, and a little bit of the peer class
Mashroor Newaz       --->       protocol.py + peer.py
Jason He             --->       logging function and error handling
Zach Pinet           --->       peer.py


Video Demonstration: https://uflorida-my.sharepoint.com/:v:/g/personal/mashroor_newaz_ufl_edu/IQA9Lx1FMfoaRJjzl57gHtobAceBT7eYnFLSYhHdK7YoLlg?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=PZrQTj

Only people in university of Florida can access the video through the link.