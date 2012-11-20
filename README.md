pi-me-up
========

A quick deployment script for the Raspberry Pi.

Requirements
------------

A working pi, with SSH installed and running (as it is by default)
You'll need to know its IP address or hostname.

Python 2.5+

[Fabric](http://fabfile.org) 

[Cuisine](https://github.com/sebastien/cuisine)


Setup
-----

Download the fabfile or clone the repository.

    $ pip install fabric cuisine
    $ fab -l

That's all.

Usage
-----

To get a list of available commands:

    $ fab -l

At the moment these are
* deploy
  Installs pretty much everything to a bare Pi.
* install\_firewall     
  Installs ufw and opens ssh access to everyone.
* install\_motd         
  Installs a succulent ascii-art MOTD. In colour!
* install\_mpd          
  Installs MPD and configures it for the 3.5mm audio output.
* install\_my\_dotfiles  
  Copies down my dotfiles repository from GitHub.
* install\_usb\_wifi     
  Configures a generic USB WiFi device for DHCP.
* open\_port            
  Adds a firewall rule to allow EVERYONE access to the specified port.
* setup\_packages       
  Installs basic Raspbian package requirements.
* setup\_python         
  Installs virtualenvwrapper and some common global python packages.
* status               
  General stats about the Pi.
* update\_firmware      
  Updates firmware. See https://github.com/Hexxeh/rpi-update for more.
* upgrade\_packages     
  Does a full apt-get upgrade.

To specify your hostname, either edit the fabfile, use the _-H_ switch on the 
command line, or fabric will prompt you when you run a command.

Examples
--------

    $ fab -H 192.168.1.23 deploy
    $ fab -H 192.168.1.23 open_port:port=8080
    $ fab -H 192.168.1.23 status


Notes
-----

This isn't particularly bright. It's not like chef, and it won't gracefully 
update your current configuration, but will instead overwrite it with a 
reckless and carefree abandon. At least, it will how I write it.
Some things are easy to handle, such as adding virtualenv setup to the bash
settings, but others really need human eyes to figure out what's already in the
file.

For example, if you have eth0 configured with a static IP address and run

    $ fab install_usb_wifi

Then you'll lose that setting. This isn't a full management suite.
It's very scrappy, but that's because I haven't finished setting my Pi up how
I want it - it's going to do double-duty as a WiFi radio and an IRC/bitlbee host
so it's probably going to be geared towards that at the moment.

License
-------

MIT. See LICENCE file.

Disclaimer
----------

If you break your Pi with my script, I feel bad for you son.
