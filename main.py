# Copyright 2016 Benji York

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pyglet
import sys
import time

import OSC
import threading
import time
import sys
import win32com.client

position = [0, 0]

def request_x32_to_send_change_notifications(client):
    """request_x32_to_send_change_notifications sends /xremote repeatedly to
    mixing desk to make sure changes are transmitted to our server.
    """
    while True:
	sys.stdout.flush()
	#print 'Sending update request'
        client.send(OSC.OSCMessage("/xremote"))
        time.sleep(7)

song_paths = [
    'C:\Users\SBC\Dropbox\SOS Christmas 2016\Medley.wav',
    'C:\Users\SBC\Dropbox\SOS Christmas 2016\O Little Town Of Bethlehem.wav',
    'C:\Users\SBC\Dropbox\SOS Christmas 2016\When Love Was Born.wav',
    'C:\Users\SBC\Dropbox\SOS Christmas 2016\A Christmas Alleluia (Live) [feat. Lauren Daigle].wav',
]

players = []
for song_path in song_paths:
    player = pyglet.media.Player()
    player.queue(pyglet.media.load(song_path))
    players.append(player)

song_index = 0

player = players[0]

def reset_track_buttons(client, except_track=None):
    for track in range(4):

        if track == except_track:
            continue
        button = track + 21
        client.send(OSC.OSCMessage('/-stat/userpar/%d/value' % button, [0]))


def handle_message(x32_address, server_udp_port):

    def queue_active_song():
        global player
	player.pause()
	player = players[song_index]

    def msgPrinter_handler(addr, tags, data, client_address):
        #print addr, data
        global song_index
        global player
	sys.stdout.flush()
        if addr == '/dca/1/fader' and data:
            if data[0] == 0:
                print 'pausing'
                player.pause()
                queue_active_song()
	    elif not player.playing:
                print 'playing'
                queue_active_song()
                player.seek(position[0] * 60 + position[1])
                player.play()
        if addr == '/-stat/userpar/33/value' and data:
            print 'setting minute to', data[0]
            position[0] = data[0]
        if addr == '/-stat/userpar/34/value' and data:
            print 'setting seconds to', data[0]
            position[1] = data[0]
        if addr.startswith('/-stat/userpar/') and addr.endswith('/value') \
                and data and data[0]:
            button = int(addr[15:17])
            if button >= 21 and button <= 24:
                song_index = button - 21
                reset_track_buttons(client, except_track=song_index)
                print 'selecting song ', song_index

    print 'Starting OSC server'
    server = OSC.OSCServer(("", server_udp_port))
    server.addMsgHandler("default", msgPrinter_handler)

    print 'Starting OSC client'
    client = OSC.OSCClient(server=server)
    client.connect((x32_address, 10023))

    reset_track_buttons(client)
    # Turn on the button for track 0.
    client.send(OSC.OSCMessage('/-stat/userpar/21/value', [127]))

    # Request the current minutes and seconds values.
    client.send(OSC.OSCMessage('/-stat/userpar/33/value'))
    client.send(OSC.OSCMessage('/-stat/userpar/34/value'))

    print 'Staring change notification thread'
    thread = threading.Thread(target=request_x32_to_send_change_notifications,
        kwargs = {"client": client})
    thread.setDaemon(True)
    thread.start()
    print 'Running'
    server.serve_forever()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--address', required = True,
                        help='name/ip-address of Behringer X32 mixing desk')
    parser.add_argument('--port', default = 10300,
                        help='UDP-port to open on this machine.')

    args = parser.parse_args()
    handle_message(args.address, args.port)
