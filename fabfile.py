#!/usr/bin/env python
# vim: set fileencoding=UTF-8 :

from cuisine import (file_exists, dir_exists, file_write, text_strip_margin,
    package_upgrade, package_clean)
from cuisine import package_ensure as _package_ensure
from cuisine import package_update as _package_update
from fabric.api import sudo, run, env, hide, cd, task
from fabric.contrib.files import append
from fabric.utils import puts
from fabric.colors import red, green

LOCAL_PREFIX = "/usr/local/bin"
INDENT = "→ "

env.user = "pi"
#env.hosts = ["rpi"]


def install_binary_from_URL(url):
    """ Download a file from a URL and install it to the current prefix
    directory. Make sure you trust the URL...
    """
    context = {
        "p": LOCAL_PREFIX,
        "u": url,
        "f": url.split("/")[-1],
    }
    puts("Installing {u} to {p}/{f}".format(**context))
    with hide("output", "running"):
        if file_exists("{p}/{f}".format(**context)):
            sudo("rm {p}/{f}".format(**context))
        sudo("wget {u} -O {p}/{f}".format(**context))
        sudo("chmod +x {p}/{f}".format(**context))


def sudo_file_write(filename, contents):
    """ (Over)write a file as root. This is a substitute for fabric"s
    file_write for writing global configuration files.
    """
    with hide("output", "running"):
        temp_file = run("mktemp")
        file_write(temp_file, contents)
        sudo("cp -r {s} {d}".format(s=temp_file, d=filename))
        sudo("chmod 644 {}".format(filename))
        sudo("rm {}".format(temp_file))


def package_update():
    """ Pretty-printing wrapper for package_update
    """
    if not hasattr(package_update, "done"):
        puts(green("{} updating packages".format(INDENT)))
        with hide("output", "running"):
            _package_update()
        package_update.done = True


def package_ensure(package):
    """ Prettier-printing version of cuisine's package_ensure.
    Doesn't display anything if it's already been called for this package in
    this fabric session.
    """
    if not hasattr(package_ensure, "checked"):
        package_ensure.checked = []
    if package not in package_ensure.checked:
        with hide("running", "output"):
            puts("{i} checking {p}".format(i=INDENT, p=package))
            _package_ensure(package)
            package_ensure.checked.append(package)


def global_pip_install(package):
    """ Pretty-printing, internal wrapper for 'sudo pip install'.
    Doesn't bother to run if it's already been called for this package in
    this fabric session.
    """
    if not hasattr(global_pip_install, "checked"):
        global_pip_install.checked = []
    if package not in global_pip_install.checked:
        with hide("running", "output"):
            package_ensure("python-pip")
            puts("{i} checking {p}".format(i=INDENT, p=package))
            sudo("pip install {}".format(package))
            global_pip_install.checked.append(package)


@task
def install_my_dotfiles():
    """ Copies down my dotfiles repository from GitHub.
    Installs only those files which might be relevant to the Raspberry Pi.
    See http://github.com/moopet/dotfiles
    """
    puts(green("Installing dotfiles"))
    dotfiles = (
        ".vimrc",
        ".ackrc",
        ".htoprc",
        ".gitignore",
        ".gitconfig",
        ".fonts",  # patched font for vim-powerline
        ".tmux.conf",
    )
    with hide("output", "running"), cd("/tmp"):
        if dir_exists("dotfiles"):
            with cd("dotfiles"):
                run("git pull")
        else:
            run("git clone git://github.com/moopet/dotfiles.git")
        for f in dotfiles:
            puts("{i} {f}".format(i=INDENT, f=f))
            run("cp -r dotfiles/{} ~/".format(f))


@task
def install_usb_wifi(ssid, psk):
    """ Configures a generic USB WiFi device for DHCP.
    This overwrites /etc/network/interfaces, so any changes you have made
    will be lost;  eth0 is reset to DHCP.
    usage: install_usb_wifi:ssid=<MY_SSID>,psk=<MY_PSK>
    """

    puts(green("Installing USB WiFi device"))
    wpa_conf = text_strip_margin("""
        |network={{
        |    ssid="{ssid}"
        |    proto=RSN
        |    key_mgmt=WPA-PSK
        |    pairwise=CCMP TKIP
        |    group=CCMP TKIP
        |    psk="{psk}"
        |}}
    """.format(ssid=ssid, psk=psk))

    interfaces = text_strip_margin("""
        |auto lo

        |iface lo inet loopback
        |iface eth0 inet dhcp

        |auto wlan0
        |iface wlan0 inet dhcp
        |wpa-conf /etc/wpa.conf
    """)

    sudo("ifdown --force wlan0; true")
    sudo_file_write("/etc/network/interfaces", interfaces)
    sudo_file_write("/etc/wpa.conf", wpa_conf)
    sudo("ifup wlan0")


@task
def install_motd():
    """ Installs a succulent ascii-art MOTD. In colour!
    The raspberry was by RPi forum user b3n, taken from
    http://www.raspberrypi.org/phpBB3/viewtopic.php?f=2&t=5494
    """

    puts(green("Installing succulent MOTD"))
    motd = text_strip_margin("""
        |
        |{g}      .~~.   .~~.
        |{g}     ". \ " " / ."
        |{r}      .~ .~~~..~.
        |{r}     : .~."~".~. :    {b}                       __                      {o}     _
        |{r}    ~ (   ) (   ) ~   {b}    _______ ____ ___  / /  ___ __________ __  {o}___  (_)
        |{r}   ( : "~".~."~" : )  {b}   / __/ _ `(_-</ _ \/ _ \/ -_) __/ __/ // / {o}/ _ \/ /
        |{r}    ~ .~ (   ) ~. ~   {p}  /_/  \_,_/___/ .__/_.__/\__/_/ /_/  \_, / {o}/ .__/_/
        |{r}     (  : "~" :  )    {p}              /_/                    /___/ {o}/_/
        |{r}      "~ .~~~. ~"
        |{r}          "~"
        |{n}
        |
        |""".format(
            g="[32m",
            r="[31m",
            b="[34m",
            o="[33m",
            p="[35m",
            n="[m",
        )
    )
    with hide("output", "running"):
        sudo_file_write("/etc/motd", motd)


@task
def setup_packages():
    """ Installs basic Raspbian package requirements.
    """
    puts(green("Installing packages"))
    package_update()

    with hide("running"):
        package_ensure("git-core")
        package_ensure("mpc")
        package_ensure("mpd")
        # Sometimes I use screen, sometimes I use tmux ...
        package_ensure("screen")
        package_ensure("tmux")
        # ... but I always use vim.
        package_ensure("vim")
        package_ensure("python-pip")

        package_ensure("ack-grep")
        ack_filename = "{}/ack".format(LOCAL_PREFIX)
        if file_exists(ack_filename):
            sudo("rm {}".format(ack_filename))
        sudo("ln -s /usr/bin/ack-grep {}".format(ack_filename))

    install_binary_from_URL(
        "https://raw.github.com/sjl/friendly-find/master/ffind"
    )


@task
def reboot():
    """ Reboots. Yup. """
    puts(red("Rebooting"))
    sudo("reboot")


@task
def setup_python():
    """ Installs virtualenvwrapper and some common global python packages.
    """
    puts(green("Setting up global python environment"))
    global_pip_install("ipython")
    global_pip_install("ipdb")
    global_pip_install("virtualenv")
    global_pip_install("virtualenvwrapper")
    puts("adding virtualenvwrapper to .bashrc".format(INDENT))
    with hide("everything"):
        append(".bashrc", "export WORKON_HOME=~/.virtualenvs")
        append(".bashrc", ". $(which virtualenvwrapper.sh)")


@task
def update_firmware():
    """ Updates firmware. See https://github.com/Hexxeh/rpi-update for more
    information.
    """
    package_update()
    puts(red("Updating firmware"))
    with hide("output", "running"):
        package_ensure("ca-certificates")
        sudo("wget http://goo.gl/1BOfJ -O /usr/bin/rpi-update")
        sudo("chmod +x /usr/bin/rpi-update")
    sudo("rpi-update")


@task
def install_firewall():
    """ Installs ufw and opens ssh access to everyone.
    """
    puts(green("Installing/configuring firewall"))
    with hide("output", "running"):
        package_ensure("ufw")
        sudo("ufw allow proto tcp from any to any port 22")
        sudo("ufw --force enable")


@task
def open_port(port):
    """ Adds a firewall rule to allow EVERYONE access to the specified port.
    """
    puts(green("Configuring firewall to allow all on port {}".format(port)))
    with hide("output", "running"):
        install_firewall()
        sudo("ufw allow proto tcp from any to any port {}".format(port))
        sudo("ufw --force enable")


@task
def install_mpd():
    """ Installs MPD and configures it for the 3.5mm audio output.
    Allows passwordless connection from any host on port 6600.
    """
    package_ensure("mpc")
    package_ensure("mpd")
    package_ensure("ufw")
    with hide("output", "running"):
        sudo("ufw allow proto tcp from any to any port 6600")
        sudo("ufw --force enable")
        mpd = text_strip_margin("""
            |music_directory         "/var/lib/mpd/music"
            |playlist_directory      "/var/lib/mpd/playlists"
            |db_file                 "/var/lib/mpd/tag_cache"
            |log_file                "/var/log/mpd/mpd.log"
            |pid_file                "/var/run/mpd/pid"
            |state_file              "/var/lib/mpd/state"
            |sticker_file            "/var/lib/mpd/sticker.sql"
            |user                    "mpd"
            |port                    "6600"
            |filesystem_charset      "UTF-8"
            |id3v1_encoding          "UTF-8"
            |follow_outside_symlinks "yes"
            |follow_inside_symlinks  "yes"
            |zeroconf_enabled        "yes"
            |zeroconf_name           "Raspberry Pi"
            |volume_normalization    "yes"
            |max_connections         "10"
            |input {
            |    plugin              "curl"
            |}
            |audio_output {
            |    type                "alsa"
            |    name                "3.5mm Headphone Jack"
            |    device              "hw:0,0"
            |    format              "44100:16:2"
            |    mixer_device        "default"
            |    mixer_control       "PCM"
            |    mixer_index         "0"
            |}
            |audio_output {
            |    type                "alsa"
            |    name                "USB Audio"
            |    device              "hw:0,0"
            |    format              "44100:16:2"
            |    mixer_device        "software"
            |    mixer_control       "PCM"
            |    mixer_index         "1"
            |}
            |mixer_type              "software"
        """)

    sudo_file_write("/etc/mpd.conf", mpd)
    sudo("/etc/init.d/mpd restart")


@task
def upgrade_packages():
    """ Pretty-printing wrapper for package_upgrade
    """
    package_update()
    puts(green("{} upgrading all packages".format(INDENT)))
    with hide("output", "running"):
        package_upgrade()
    package_clean()


@task
def status():
    """ General stats about the Pi. """
    with hide("running", "stderr"):
        run("mpc")
        run("uptime")
        run("df -h")


@task
def deploy():
    """ Installs pretty much everything to a bare Pi.
    """
    puts(green("Starting deployment"))
    upgrade_packages()
    setup_packages()
    install_firewall()
    setup_python()
    install_my_dotfiles()
    install_mpd()
    install_motd()
